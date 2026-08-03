from axignal_api.axent_admin_routes import router as axent_admin_router
from axignal_api.axent_consent_routes import router as axent_consent_router
from axignal_api.axent_routes import router as axent_router
from axignal_api.billing_read_routes import router as billing_read_router
from axignal_api.billing_reconciliation_routes import (
    router as billing_reconciliation_router,
)
from axignal_api.billing_routes import router as billing_router
from axignal_api.billing_test_routes import router as billing_test_router
from axignal_api.entitlements import router as entitlement_router
from axignal_api.human_review import router as human_review_router
from axignal_api.identity_entitlement_routes import (
    router as identity_entitlement_router,
)
from axignal_api.identity_routes import router as identity_router
from axignal_api.main import app
from axignal_api.organic_routes import router as organic_router
from axignal_api.persistent_document_research import router as document_research_router
from axignal_api.persistent_research import router as persistent_research_router
from axignal_api.persistent_ted_research import router as ted_research_router
from axignal_api.pilot_health import router as pilot_health_router
from axignal_api.research import router as prototype_research_router
from axignal_api.retention_routes import router as retention_router
from axignal_api.seat_routes import router as seat_router
from axignal_api.subscriber_workspace_routes import router as subscriber_workspace_router
from axignal_api.validation import router as validation_router

app.include_router(pilot_health_router)
app.include_router(identity_router)
app.include_router(identity_entitlement_router)
app.include_router(organic_router)
app.include_router(prototype_research_router)
app.include_router(document_research_router)
app.include_router(persistent_research_router)
app.include_router(ted_research_router)
app.include_router(subscriber_workspace_router)
app.include_router(axent_router)
app.include_router(axent_consent_router)
app.include_router(axent_admin_router)
app.include_router(entitlement_router)
app.include_router(billing_router)
app.include_router(billing_read_router)
app.include_router(billing_reconciliation_router)
app.include_router(billing_test_router)
app.include_router(seat_router)
app.include_router(retention_router)
app.include_router(human_review_router)
app.include_router(validation_router)

__all__ = ["app"]
