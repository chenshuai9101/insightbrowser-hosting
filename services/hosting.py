"""InsightBrowser Hosting - Core Hosting Service"""

import json
from models import get_site, get_sites, create_site, update_site, delete_site, increment_call_count, generate_agent_json, generate_site_template
from config import REGISTRY_URL, PUBLIC_BASE_URL, PLANS


class HostingService:
    """Core hosting service logic"""

    @staticmethod
    def create_hosted_site(name, site_type, description, capabilities, data_source="manual", data_config=None, owner="default", plan="free"):
        """Create a new hosted site with all scaffolding"""
        # Create site in database
        site_id = create_site(name, site_type, description, capabilities, data_source, data_config, owner, plan)

        # Generate agent.json
        generate_agent_json(site_id)

        # Generate template code
        template = generate_site_template(site_id)

        return site_id, template

    @staticmethod
    def get_site(site_id):
        """Get site details"""
        site = get_site(site_id)
        if site:
            # Parse JSON fields
            if isinstance(site.get("capabilities"), str):
                site["capabilities"] = json.loads(site["capabilities"])
            if isinstance(site.get("data_config"), str):
                site["data_config"] = json.loads(site["data_config"])
        return site

    @staticmethod
    def list_sites(owner="default"):
        """List all sites for an owner"""
        sites = get_sites(owner)
        for site in sites:
            if isinstance(site.get("capabilities"), str):
                site["capabilities"] = json.loads(site["capabilities"])
        return sites

    @staticmethod
    def update_site(site_id, **kwargs):
        """Update a hosted site"""
        update_site(site_id, **kwargs)

    @staticmethod
    def delete_site(site_id):
        """Delete a hosted site"""
        delete_site(site_id)

    @staticmethod
    def get_agent_json(site_id):
        """Get agent.json for a site"""
        site = get_site(site_id)
        if site and site.get("agent_json"):
            return json.loads(site["agent_json"])
        return None

    @staticmethod
    def record_call(site_id):
        """Record a call to a hosted site"""
        increment_call_count(site_id)

    @staticmethod
    def check_plan_limits(owner="default", plan="free"):
        """Check if owner can create more sites under their plan"""
        config = PLANS.get(plan, PLANS["free"])
        sites = get_sites(owner)
        max_sites = config["max_sites"]

        if max_sites == -1:  # unlimited
            return True, 0

        current_count = len(sites)
        if current_count >= max_sites:
            return False, max_sites - current_count

        return True, max_sites - current_count

    @staticmethod
    def get_plans():
        """Get pricing plans"""
        return PLANS

    @staticmethod
    def register_with_registry(site_id):
        """Register a hosted site with the InsightBrowser Registry.

        按 Registry 的真实契约 POST /api/register（旧代码误用 /api/agents，
        且 payload 形状不匹配，导致注册永远失败）。
        """
        import requests
        try:
            site = get_site(site_id)
            if not site:
                return {"success": False, "error": "Site not found"}

            capabilities = json.loads(site["capabilities"]) if isinstance(site.get("capabilities"), str) else site.get("capabilities") or []
            payload = {
                "name": site["name"],
                "type": site["site_type"],
                "description": site.get("description", ""),
                "owner": site.get("owner", "default"),
                "endpoint": f"{PUBLIC_BASE_URL}/api/site/{site_id}",
                "capabilities": [
                    {"name": c.get("name", c.get("id", "capability")),
                     "description": c.get("description", "")}
                    for c in capabilities
                ],
            }

            resp = requests.post(
                f"{REGISTRY_URL}/api/register",
                json=payload,
                timeout=10
            )
            if resp.status_code in (200, 201):
                data = resp.json()
                return {
                    "success": True,
                    "registry_id": data.get("site_id") or data.get("id"),
                    "site_id": site_id,
                }
            else:
                return {"success": False, "error": f"Registry returned {resp.status_code}: {resp.text}"}
        except requests.exceptions.ConnectionError:
            return {"success": False, "error": "Cannot connect to Registry server"}
        except Exception as e:
            return {"success": False, "error": str(e)}


# Singleton
hosting_service = HostingService()
