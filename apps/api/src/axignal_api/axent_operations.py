"""AXENT operational pipeline (cierre funcional E2E).

Turns a conversational order into a governed domain operation:

    mensaje
    → intención (tool tipificada)
    → resolución de referencias ("la primera y la tercera" → refs reales
      de los resultados de la conversación)
    → preview (invocación PENDING + confirmación con hash)
    → confirmación del usuario (mensaje de confirmación o endpoint)
    → ejecución vía ToolRegistry (policy + autoridades de dominio)
    → PostgreSQL
    → respuesta con el objeto creado/actualizado

Everything is persisted (conversation, invocation, confirmation, action)
and every material step is append-only.
"""

from __future__ import annotations

import re
from typing import Any
from uuid import UUID

from axignal_api.axent_core_repository import AxentCoreRepository
from axignal_api.axent_tool_registry import AxentToolExecutor, ToolExecutionError

# --- Ordinal reference resolution --------------------------------------------

_ORDINAL_WORDS = {
    "primera": 0, "primer": 0, "primero": 0, "1ª": 0, "1a": 0, "1": 0,
    "segunda": 1, "segundo": 1, "2ª": 1, "2a": 1, "2": 1,
    "tercera": 2, "tercer": 2, "tercero": 2, "3ª": 2, "3a": 2, "3": 2,
    "cuarta": 3, "cuarto": 3, "4ª": 3, "4a": 3, "4": 3,
    "quinta": 4, "quinto": 4, "5ª": 4, "5a": 4, "5": 4,
}

_ORDINAL_PATTERN = re.compile(
    r"\b(primera|primer|primero|segunda|segundo|tercera|tercer|tercero|"
    r"cuarta|cuarto|quinta|quinto|\d+[ªa]?)\b",
    re.IGNORECASE,
)

_WORKSPACE_PATTERN = re.compile(
    r"al workspace\s+([A-Za-z0-9ÁÉÍÓÚáéíóúñÑ _-]{2,60})", re.IGNORECASE
)

_TASK_PATTERN = re.compile(
    r"tarea\s+(?:para|de|sobre)?\s*(?:revisar|revisión|preparar|analizar|"
    r"completar|validar)?\s*([A-Za-z0-9ÁÉÍÓÚáéíóúñÑ _-]{3,120})",
    re.IGNORECASE,
)

_PRIORITY_WORDS = {"alta": "HIGH", "alto": "HIGH", "media": "MEDIUM",
                   "medio": "MEDIUM", "baja": "LOW", "bajo": "LOW"}

_INTENT_ORDER = (
    ("add_to_workspace", re.compile(
        r"\b(añade|agrega|incorpora|mete|añadir|agregar)\b.*\b(workspace|área|espacio)\b",
        re.IGNORECASE)),
    ("create_pursuit", re.compile(
        r"\bcrea\s+un\s+pursuit\b|\bcrear\s+pursuit\b|\bnuevo\s+pursuit\b|\bcrear\s+un\s+pursuit\b",
        re.IGNORECASE)),
    ("create_task", re.compile(
        r"\bcrea\s+una\s+tarea\b|\bcrear\s+una\s+tarea\b|\bcrea\s+tarea\b|\bcrear\s+tarea\b",
        re.IGNORECASE)),
    ("update_internal_priority", re.compile(
        r"\bprioridad\s+(alta|alta|media|baja|medio|bajo)\b",
        re.IGNORECASE)),
    ("dismiss_opportunity", re.compile(
        r"\b(descarta|descarta la|descartar)\b", re.IGNORECASE)),
    ("compare_opportunities", re.compile(
        r"\bcompara\b|\bcomparar\b|\bcompara la\b|\bcompara las\b",
        re.IGNORECASE)),
)

_CONFIRM_WORDS = {"sí", "si", "confirmo", "confirmar", "adelante", "ok",
                  "okey", "hecho", "vale", "de acuerdo", "acepto", "sí, confirma",
                  "si, confirma", "confirmado", "sí, adelante", "si, adelante",
                  "confirma la operación", "confirmar operación"}
_REJECT_WORDS = {"no", "cancela", "cancelar", "no confirmo", "rechaza",
                 "no, cancela", "no, cancelar"}


def resolve_ordinal_refs(text: str, ordered_refs: list[str]) -> list[str]:
    """Map 'la primera y la tercera' (and direct refs) to real refs."""
    if not ordered_refs:
        return []
    selected: list[str] = []
    for match in _ORDINAL_PATTERN.finditer(text):
        token = match.group(1).lower()
        index = _ORDINAL_WORDS.get(token)
        if index is None:
            continue
        if 0 <= index < len(ordered_refs):
            ref = ordered_refs[index]
            if ref not in selected:
                selected.append(ref)
    # Direct refs mentioned explicitly (e.g. opp_ted_123456_2026).
    for ref in ordered_refs:
        if re.search(rf"\b{re.escape(ref)}\b", text) and ref not in selected:
            selected.append(ref)
    return selected


def is_confirmation(text: str) -> bool:
    return text.strip().casefold() in _CONFIRM_WORDS or (
        "confirma" in text.casefold() and len(text) < 40
    )


def is_rejection(text: str) -> bool:
    return text.strip().casefold() in _REJECT_WORDS


def detect_intent(text: str) -> tuple[str, dict[str, Any]] | None:
    """Detect the operational intent and its raw parameters (deterministic)."""
    lowered = text.casefold()
    for tool_name, pattern in _INTENT_ORDER:
        if pattern.search(text):
            params: dict[str, Any] = {}
            if tool_name == "add_to_workspace":
                match = _WORKSPACE_PATTERN.search(text)
                if not match:
                    return None
                params["workspace_title"] = match.group(1).strip()
            elif tool_name == "create_pursuit":
                params["decision"] = "BID" if "no_bid" not in lowered else "NO_BID"
            elif tool_name == "create_task":
                match = _TASK_PATTERN.search(text)
                params["title"] = match.group(1).strip() if match else "Tarea"
            elif tool_name == "update_internal_priority":
                priority = next(
                    (word for word in _PRIORITY_WORDS if word in lowered), None
                )
                if priority is None:
                    return None
                params["priority"] = _PRIORITY_WORDS[priority]
            return tool_name, params
    return None


class AxentOperationPipeline:
    """Resolves conversational orders into confirmed, persisted operations."""

    def __init__(
        self,
        *,
        core: AxentCoreRepository,
        executor: AxentToolExecutor,
        dsn: str,
    ) -> None:
        self.core = core
        self.executor = executor
        self.dsn = dsn

    # --- Conversation context ------------------------------------------------

    def last_ordered_opportunity_refs(
        self, *, tenant_id: UUID, conversation_id: UUID
    ) -> list[str]:
        """Ordered refs cited by the most recent assistant message."""
        messages = self.core.get_messages(
            tenant_id=tenant_id, conversation_id=conversation_id
        )
        for message in reversed(messages):
            if message.get("message_role") != "ASSISTANT":
                continue
            citations = self.core.get_citations(
                tenant_id=tenant_id, message_id=message["message_id"]
            )
            refs = [
                citation["authority_id"]
                for citation in citations
                if citation["authority_type"] == "OPPORTUNITY"
            ]
            if refs:
                return refs
        return []

    def pending_confirmation(
        self, *, tenant_id: UUID, conversation_id: UUID
    ) -> dict[str, Any] | None:
        """Most recent PENDING confirmation for this conversation."""
        rows = self.core.list_pending_confirmations(
            tenant_id=tenant_id, conversation_id=conversation_id
        )
        return rows[0] if rows else None

    def execute_tool(
        self,
        *,
        tenant_id: UUID,
        actor_subject: str,
        conversation_id: UUID,
        tool_name: str,
        parameters: dict[str, Any],
        risk_class: str,
    ) -> dict[str, Any]:
        """Execute the tool, persisting invocation + action around it."""
        invocation = self.core.create_invocation(
            tenant_id=tenant_id, conversation_id=conversation_id,
            tool_name=tool_name, tool_version="v1",
            parameters=parameters, risk_class=risk_class,
        )
        invocation_id = invocation["invocation_id"]
        try:
            result = self.executor.execute(
                tool_name=tool_name, parameters=parameters,
                tenant_id=tenant_id, actor_subject=actor_subject,
            )
        except ToolExecutionError as exc:
            self.core.complete_invocation(
                tenant_id=tenant_id, invocation_id=invocation_id,
                state="FAILED", error_code=str(exc),
            )
            raise
        self.core.complete_invocation(
            tenant_id=tenant_id, invocation_id=invocation_id, state="EXECUTED",
        )
        receipt = result.get("receipt", result)
        self.core.record_action(
            tenant_id=tenant_id, conversation_id=conversation_id,
            invocation_id=invocation_id, action_type=tool_name,
            object_type=_object_type_for(tool_name),
            object_ref=_object_ref_for(tool_name, parameters, receipt),
            parameters=parameters, receipt=receipt, outcome="SUCCESS",
            actor_subject=actor_subject,
        )
        return result


def _object_type_for(tool_name: str) -> str:
    return {
        "create_pursuit": "PURSUIT",
        "update_pursuit_state": "PURSUIT",
        "add_to_workspace": "WORKSPACE",
        "link_opportunity_to_workspace": "WORKSPACE",
        "create_task": "TASK",
        "update_internal_priority": "PURSUIT",
        "record_outcome": "OUTCOME",
        "record_bid_no_bid": "PURSUIT",
        "dismiss_opportunity": "OPPORTUNITY",
    }.get(tool_name, "OBJECT")


def _object_ref_for(
    tool_name: str, parameters: dict[str, Any], receipt: dict[str, Any]
) -> str:
    if tool_name in ("create_pursuit", "update_pursuit_state",
                     "update_internal_priority", "record_bid_no_bid"):
        return (
            parameters.get("pursuit_ref")
            or receipt.get("pursuit_ref")
            or "n/a"
        )
    if tool_name in ("add_to_workspace", "link_opportunity_to_workspace"):
        return receipt.get("workspace_id") or parameters.get("workspace_id") or "n/a"
    if tool_name == "create_task":
        return receipt.get("task_ref") or "n/a"
    if tool_name == "record_outcome":
        return receipt.get("outcome_ref") or "n/a"
    if tool_name == "dismiss_opportunity":
        return parameters.get("opportunity_ref") or "n/a"
    return parameters.get("opportunity_ref", "n/a")
