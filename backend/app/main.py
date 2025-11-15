import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config import settings
from .routers import health
from .db import engine
from .models import Base
from .routes_users import router as users_router 

from .api import router as api_router 
from .routers import bot_proxy

log = logging.getLogger("uvicorn.error")
app = FastAPI(title="MaxBot", debug=settings.debug)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.allowed_origins.split(",")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    )

@app.on_event("startup")
async def on_startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    lines = []
    for r in app.routes:
        path = getattr(r, "path", None)
        methods = getattr(r, "methods", None)
        if path and methods:
            lines.append(f"{','.join(sorted(methods))} {path}")
    lines = "\n".join(sorted(set(lines)))
    log.info("Mounted routes:\n%s", lines)

app.include_router(health.router, prefix="/api/v1")
app.include_router(api_router)        
app.include_router(bot_proxy.router)  
app.include_router(users_router)     

@app.get("/")
async def root():
    return {"name": settings.app_name, "ok": True}