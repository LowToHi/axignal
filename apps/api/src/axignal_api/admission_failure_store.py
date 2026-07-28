from __future__ import annotations

from psycopg.types.json import Jsonb

from axignal_api.admission_queue import AdmissionReviewJob


class AdmissionFailureStoreMixin:
    def record_failure(
        self,
        *,
        job: AdmissionReviewJob,
        error_code: str,
        error_detail: str,
        quarantined: bool,
    ) -> None:
        handoff_state = "QUARANTINED" if quarantined else "REJECTED"
        run_state = "QUARANTINED" if quarantined else "FAILED"
        with self._cursor("axignal_admission_runtime", job.tenant_id) as cursor:
            cursor.execute(
                """
                INSERT INTO axignal_global.admission_job_failures (
                  tenant_id, research_run_id, admission_handoff_id, job_payload,
                  error_code, error_detail, quarantined
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    job.tenant_id,
                    job.research_run_id,
                    job.admission_handoff_id,
                    Jsonb(job.as_payload()),
                    error_code,
                    error_detail[:2_000],
                    quarantined,
                ),
            )
            cursor.execute(
                """
                UPDATE axignal_global.admission_handoffs
                SET state = %s WHERE admission_handoff_id = %s AND state = 'PENDING'
                """,
                (handoff_state, job.admission_handoff_id),
            )
            cursor.execute(
                """
                UPDATE tenant_private.research_runs
                SET state = %s, error_code = %s, error_detail = %s,
                    updated_at = now()
                WHERE research_run_id = %s
                """,
                (run_state, error_code, error_detail[:2_000], job.research_run_id),
            )
