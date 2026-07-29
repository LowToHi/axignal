from axignal_api.entitlements import router as entitlement_router
from axignal_api.human_review import router as human_review_router
from axignal_api.main import app
from axignal_api.persistent_document_research import router as document_research_router
from axignal_api.persistent_research import router as persistent_research_router
from axignal_api.persistent_ted_research import router as ted_research_router
from axignal_api.pilot_health import router as pilot_health_router
from axignal_api.research import router as prototype_research_router
from axignal_api.retention_routes import router as retention_router
from axignal_api.validation import router as validation_router

app.include_router(pilot_health_router)
app.include_router(prototype_research_router)
app.include_router(document_research_router)
app.include_router(persistent_research_router)
app.include_router(ted_research_router)
app.include_router(entitlement_router)
app.include_router(retention_router)
app.include_router(human_review_router)
app.include_router(validation_router)

__all__ = ["app"]
