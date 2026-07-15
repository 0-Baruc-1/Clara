from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.core.config import settings
from app.mcp_server import clara_mcp

@asynccontextmanager
async def lifespan(_: FastAPI):
    async with clara_mcp.session_manager.run():
        yield


app = FastAPI(title="Clara API", version="0.1.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=[settings.frontend_origin], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.include_router(router)
app.mount("/mcp", clara_mcp.streamable_http_app())
