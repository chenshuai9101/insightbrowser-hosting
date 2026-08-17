"""InsightBrowser Hosting - API Routes"""

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse, PlainTextResponse
from pydantic import BaseModel
from typing import List, Optional
from models import generate_site_template
from models import verify_owner_key
from services.hosting import hosting_service
from config import DEFAULT_OWNER

router = APIRouter(prefix="/api")


# Pydantic models for request validation

class CapabilityParam(BaseModel):
    name: str
    type: str = "string"
    description: str = ""
    required: bool = False


class Capability(BaseModel):
    id: str
    name: str
    description: str = ""
    parameters: List[CapabilityParam] = []


class CreateSiteRequest(BaseModel):
    name: str
    site_type: str = "other"
    description: str = ""
    capabilities: List[Capability] = []
    data_source: str = "manual"
    data_config: dict = {}
    owner: str = "default"
    register_registry: bool = False


class UpdateSiteRequest(BaseModel):
    name: Optional[str] = None
    site_type: Optional[str] = None
    description: Optional[str] = None
    capabilities: Optional[List[Capability]] = None
    data_source: Optional[str] = None
    data_config: Optional[dict] = None
    status: Optional[str] = None


def _require_owner(request: Request, owner: str) -> str:
    """校验 X-Owner-Key，返回 owner。"""
    key = request.headers.get("X-Owner-Key", "")
    if not verify_owner_key(owner, key):
        raise HTTPException(status_code=401, detail="X-Owner-Key 无效或缺失")
    return owner


@router.post("/sites")
async def api_create_site(request: Request, req: CreateSiteRequest):
    """Create a new hosted site (需要 X-Owner-Key)."""
    _require_owner(request, req.owner)
    # Convert capabilities to dict
    caps = [c.dict() for c in req.capabilities]

    # 套餐由服务端分配（新建一律 free），客户端不可自选。
    allowed, remaining = hosting_service.check_plan_limits(req.owner, "free")
    if not allowed:
        raise HTTPException(status_code=403, detail={
            "error": "Plan limit reached",
            "message": "免费版站点数已达上限，请联系管理员升级套餐。"
        })

    site_id, template = hosting_service.create_hosted_site(
        name=req.name,
        site_type=req.site_type,
        description=req.description,
        capabilities=caps,
        data_source=req.data_source,
        data_config=req.data_config,
        owner=req.owner,
        plan="free"
    )

    # Optionally register with Registry
    registry_result = None
    if req.register_registry:
        registry_result = hosting_service.register_with_registry(site_id)

    return {
        "id": site_id,
        "name": req.name,
        "message": "Site created successfully",
        "agent_json_url": f"/api/site/{site_id}/agent.json",
        "template": template,
        "registry_registration": registry_result
    }


@router.get("/sites")
async def api_list_sites(owner: str = "default"):
    """List all hosted sites for an owner"""
    sites = hosting_service.list_sites(owner)
    return {"sites": sites, "count": len(sites)}


@router.get("/site/{site_id}")
async def api_get_site(site_id: int):
    """Get detailed info about a site"""
    site = hosting_service.get_site(site_id)
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")
    return site


@router.put("/site/{site_id}")
async def api_update_site(site_id: int, request: Request, req: UpdateSiteRequest):
    """Update a hosted site (需要 X-Owner-Key)."""
    site = hosting_service.get_site(site_id)
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")
    _require_owner(request, site["owner"])

    updates = {}
    for field in ["name", "site_type", "description", "data_source", "status"]:
        value = getattr(req, field, None)
        if value is not None:
            updates[field] = value

    if req.capabilities is not None:
        updates["capabilities"] = [c.dict() for c in req.capabilities]

    if req.data_config is not None:
        updates["data_config"] = req.data_config

    if updates:
        hosting_service.update_site(site_id, **updates)

    return {"message": "Site updated successfully", "id": site_id}


@router.delete("/site/{site_id}")
async def api_delete_site(site_id: int, request: Request):
    """Delete a hosted site (需要 X-Owner-Key)."""
    site = hosting_service.get_site(site_id)
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")
    _require_owner(request, site["owner"])
    hosting_service.delete_site(site_id)
    return {"message": "Site deleted successfully", "id": site_id}


@router.post("/site/{site_id}/query")
async def api_site_query(site_id: int, request: Request):
    """AHP /action 兼容入口：托管站的能力执行端点。

    Registry 的 call_agent 会 POST {endpoint}/action，Hosting 直接给出
    统一应答（真实能力逻辑由模板代码实现，此处为平台层占位）。
    """
    site = hosting_service.get_site(site_id)
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")
    try:
        data = await request.json()
    except Exception:
        data = {}
    action = data.get("action", "query")
    return {
        "success": True,
        "status": "ok",
        "site_id": site_id,
        "agent": site["name"],
        "action": action,
        "data": data.get("data", {}),
    }


@router.post("/site/{site_id}/action")
async def api_site_action(site_id: int, request: Request):
    """AHP /action 协议入口：Registry call_agent 会 POST {endpoint}/action。"""
    site = hosting_service.get_site(site_id)
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")
    try:
        data = await request.json()
    except Exception:
        data = {}
    return {
        "success": True,
        "status": "ok",
        "site_id": site_id,
        "agent": site["name"],
        "action": data.get("action", "call"),
        "data": data.get("data", {}),
    }


@router.get("/site/{site_id}/agent.json")
async def api_get_agent_json(site_id: int):
    """Get generated agent.json for a site"""
    agent = hosting_service.get_agent_json(site_id)
    if not agent:
        raise HTTPException(status_code=404, detail="agent.json not found for this site")
    return JSONResponse(content=agent)


@router.get("/site/{site_id}/template")
async def api_get_template(site_id: int):
    """Get generated Python template for a site"""
    template = generate_site_template(site_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found for this site")
    return PlainTextResponse(content=template, media_type="text/plain")


@router.post("/site/{site_id}/register")
async def api_register_site(site_id: int, request: Request):
    """Register a site with the InsightBrowser Registry (需要 X-Owner-Key)."""
    site = hosting_service.get_site(site_id)
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")
    _require_owner(request, site["owner"])
    result = hosting_service.register_with_registry(site_id)
    if not result.get("success"):
        return JSONResponse(content=result, status_code=502)
    return result


@router.get("/plans")
async def api_get_plans():
    """Get pricing plans"""
    return {"plans": hosting_service.get_plans()}
