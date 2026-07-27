from axignal_api.main import app
from axignal_api.research import router as research_router

app.include_router(research_router)

__all__ = ["app"]
