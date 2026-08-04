import type {
  SubscriberWorkspaceActionResult,
  SubscriberWorkspaceAuditEvent,
  SubscriberWorkspaceEventType
} from "./subscriber-workspace-contract";

function projectedType(
  event: SubscriberWorkspaceAuditEvent
): SubscriberWorkspaceEventType {
  if (event.type !== "decision.recorded") return event.type;

  if (event.object_type === "clarification" && event.details.state === "draft") {
    return "clarification.drafted";
  }
  if (event.object_type === "commercial_model") {
    if (event.details.approved === true) return "commercial.approved";
    if (event.details.updated === true) return "commercial.updated";
  }
  if (event.object_type === "submission_package") {
    if (event.details.approved === true) return "submission.approved";
    if (event.details.status === "ready") return "submission.prepared";
  }

  return event.type;
}

export function projectSubscriberWorkspaceAuditEvent(
  event: SubscriberWorkspaceAuditEvent
): SubscriberWorkspaceAuditEvent {
  const type = projectedType(event);
  return type === event.type ? event : { ...event, type };
}

export function projectSubscriberWorkspaceActionResult(
  result: SubscriberWorkspaceActionResult
): SubscriberWorkspaceActionResult {
  return result.event
    ? { ...result, event: projectSubscriberWorkspaceAuditEvent(result.event) }
    : result;
}

export function projectSubscriberWorkspaceEventsResult<T extends {
  events: SubscriberWorkspaceAuditEvent[];
}>(result: T): T {
  return {
    ...result,
    events: result.events.map(projectSubscriberWorkspaceAuditEvent)
  };
}
