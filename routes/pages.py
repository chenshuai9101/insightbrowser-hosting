"""InsightBrowser Hosting - Page Routes (Jinja2 templates)"""

from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from typing import Optional
import os
import json

from services.hosting import hosting_service
from config import PLANS, SITE_TYPES, BASE_DIR

router = APIRouter()
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))


@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Homepage"""
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "plans": PLANS, "site_types": SITE_TYPES}
    )


@router.get("/create", response_class=HTMLResponse)
async def create_page(request: Request):
    """Create a hosted site - form page"""
    return templates.TemplateResponse(
        "create.html",
        {"request": request, "site_types": SITE_TYPES, "plans": PLANS}
    )


@router.post("/create", response_class=HTMLResponse)
async def create_site(
    request: Request,
    name: str = Form(...),
    site_type: str = Form("other"),
    description: str = Form(""),
    capabilities_json: str = Form("[]"),
    data_source: str = Form("manual"),
    plan: str = Form("free"),
    register_registry: str = Form("off")
):
    """Handle site creation form submission"""
    try:
        capabilities = json.loads(capabilities_json)
    except json.JSONDecodeError:
        capabilities = []

    # Check plan limits
    allowed, remaining = hosting_service.check_plan_limits("default", plan)
    if not allowed:
        return templates.TemplateResponse(
            "create.html",
            {
                "request": request,
                "site_types": SITE_TYPES,
                "plans": PLANS,
                "error": f"您的 {PLANS[plan]['name']} 已达到上限，请升级套餐。"
            }
        )

    site_id, template = hosting_service.create_hosted_site(
        name=name,
        site_type=site_type,
        description=description,
        capabilities=capabilities,
        data_source=data_source,
        owner="default",
        plan=plan
    )

    # Optionally register with Registry
    registry_result = None
    if register_registry == "on":
        registry_result = hosting_service.register_with_registry(site_id)

    return RedirectResponse(url=f"/site/{site_id}?created=true", status_code=303)


@router.get("/my-sites", response_class=HTMLResponse)
async def my_sites(request: Request):
    """List all hosted sites for the user"""
    sites = hosting_service.list_sites("default")
    return templates.TemplateResponse(
        "my_sites.html",
        {"request": request, "sites": sites}
    )


@router.get("/site/{site_id}", response_class=HTMLResponse)
async def site_detail(request: Request, site_id: int, created: Optional[str] = None):
    """Site detail and management page"""
    site = hosting_service.get_site(site_id)
    if not site:
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "error": "托管站不存在"},
            status_code=404
        )
    return templates.TemplateResponse(
        "site_detail.html",
        {
            "request": request,
            "site": site,
            "site_types": SITE_TYPES,
            "just_created": created == "true",
            "plans": PLANS
        }
    )


@router.post("/site/{site_id}/update", response_class=HTMLResponse)
async def update_site(
    request: Request,
    site_id: int,
    name: str = Form(...),
    site_type: str = Form("other"),
    description: str = Form(""),
    capabilities_json: str = Form("[]"),
    data_source: str = Form("manual"),
    status: str = Form("running")
):
    """Handle site update form submission"""
    try:
        capabilities = json.loads(capabilities_json)
    except json.JSONDecodeError:
        capabilities = []

    hosting_service.update_site(
        site_id,
        name=name,
        site_type=site_type,
        description=description,
        capabilities=capabilities,
        data_source=data_source,
        status=status
    )

    return RedirectResponse(url=f"/site/{site_id}?updated=true", status_code=303)


@router.post("/site/{site_id}/delete")
async def delete_site(site_id: int):
    """Handle site deletion"""
    hosting_service.delete_site(site_id)
    return RedirectResponse(url="/my-sites?deleted=true", status_code=303)


@router.post("/site/{site_id}/toggle-status")
async def toggle_site_status(site_id: int):
    """Toggle site status (running/stopped)"""
    site = hosting_service.get_site(site_id)
    if not site:
        return RedirectResponse(url="/my-sites", status_code=303)

    new_status = "stopped" if site["status"] == "running" else "running"
    hosting_service.update_site(site_id, status=new_status)
    return RedirectResponse(url=f"/site/{site_id}", status_code=303)


@router.get("/pricing", response_class=HTMLResponse)
async def pricing(request: Request):
    """Pricing page with payment QR codes"""
    return templates.TemplateResponse(
        "pricing.html",
        {"request": request, "plans": PLANS}
    )
