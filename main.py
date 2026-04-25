"""InsightBrowser Hosting - Agent Hosting Platform
Port: 7001
"""

import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import os

from config import HOST, PORT, DEBUG, BASE_DIR
from models import init_db
from routes.api import router as api_router
from routes.pages import router as pages_router

app = FastAPI(
    title="InsightBrowser Hosting",
    description="Agent 托管平台 - 让每个人都能拥有自己的 Agent 站",
    version="2.0.0"
)

# Mount static files
static_dir = os.path.join(BASE_DIR, "static")
os.makedirs(static_dir, exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Mount assets (QR codes etc)
assets_dir = os.path.join(BASE_DIR, "assets")
os.makedirs(assets_dir, exist_ok=True)
app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

# Register routers
app.include_router(pages_router)
app.include_router(api_router)


@app.on_event("startup")
async def startup():
    """Initialize database on startup"""
    init_db()
    print(f"""
╔══════════════════════════════════════════════╗
║        InsightBrowser Hosting v2.0          ║
║       Agent 托管平台已启动 ✓                ║
║                                              ║
║  首页:      http://localhost:{PORT}           ║
║  创建站点:  http://localhost:{PORT}/create    ║
║  我的站点:  http://localhost:{PORT}/my-sites  ║
║  定价:      http://localhost:{PORT}/pricing   ║
║  API:       http://localhost:{PORT}/api/sites ║
╚══════════════════════════════════════════════╝
""")


@app.get("/robots.txt", response_class=HTMLResponse)
async def robots():
    return "User-agent: *\nDisallow: /"


if __name__ == "__main__":
    uvicorn.run("main:app", host=HOST, port=PORT, reload=DEBUG)
