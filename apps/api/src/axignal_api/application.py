from axignal_api.human_review import router as human_review_router
from axignal_api.main import app
from axignal_api.persistent_document_research import router as document_research_router
from axignal_api.persistent_research import router as persistent_research_router
from axignal_api.research import router as prototype_research_router
from axignal_api.validation import router as validation_router

app.include_router(prototype_research_router)
app.include_router(document_research_router)
app.include_router(persistent_research_router)
app.include_router(human_review_router)
app.include_router(validation_router)

__all__ = ["app"]
