"""InsightBrowser Hosting - Database Models"""

import sqlite3
import json
import os
from datetime import datetime
from config import DATABASE


def get_db():
    """Get database connection"""
    os.makedirs(os.path.dirname(DATABASE), exist_ok=True)
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    """Initialize database tables"""
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS sites (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            site_type TEXT NOT NULL DEFAULT 'other',
            description TEXT NOT NULL,
            capabilities TEXT NOT NULL DEFAULT '[]',
            data_source TEXT NOT NULL DEFAULT 'manual',
            data_config TEXT DEFAULT '{}',
            status TEXT NOT NULL DEFAULT 'running',
            call_count INTEGER NOT NULL DEFAULT 0,
            last_active TEXT,
            plan TEXT NOT NULL DEFAULT 'free',
            owner TEXT NOT NULL DEFAULT 'default',
            agent_json TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
            updated_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
        );
    """)
    conn.commit()
    conn.close()


def create_site(name, site_type, description, capabilities, data_source="manual", data_config=None, owner="default", plan="free"):
    """Create a new hosted site"""
    conn = get_db()
    capabilities_json = json.dumps(capabilities, ensure_ascii=False)
    data_config_json = json.dumps(data_config or {}, ensure_ascii=False)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor = conn.execute(
        """INSERT INTO sites (name, site_type, description, capabilities, data_source, data_config, status, owner, plan, created_at, updated_at)
           VALUES (?, ?, ?, ?, ?, ?, 'running', ?, ?, ?, ?)""",
        (name, site_type, description, capabilities_json, data_source, data_config_json, owner, plan, now, now)
    )
    site_id = cursor.lastrowid
    conn.commit()

    # Auto-generate agent.json
    generate_agent_json(site_id, conn)

    conn.close()
    return site_id


def get_site(site_id):
    """Get site by ID"""
    conn = get_db()
    row = conn.execute("SELECT * FROM sites WHERE id = ?", (site_id,)).fetchone()
    conn.close()
    if row:
        return dict(row)
    return None


def get_sites(owner="default"):
    """Get all sites for an owner"""
    conn = get_db()
    rows = conn.execute("SELECT * FROM sites WHERE owner = ? ORDER BY created_at DESC", (owner,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def update_site(site_id, **kwargs):
    """Update site fields"""
    conn = get_db()
    allowed = ["name", "site_type", "description", "capabilities", "data_source", "data_config", "status", "plan", "call_count", "last_active"]
    updates = []
    values = []

    for k, v in kwargs.items():
        if k in allowed:
            if k in ("capabilities", "data_config") and isinstance(v, (list, dict)):
                v = json.dumps(v, ensure_ascii=False)
            updates.append(f"{k} = ?")
            values.append(v)

    if updates:
        updates.append("updated_at = datetime('now', 'localtime')")
        values.append(site_id)
        conn.execute(f"UPDATE sites SET {', '.join(updates)} WHERE id = ?", values)
        conn.commit()

        # Regenerate agent.json if certain fields changed
        if any(k in kwargs for k in ("name", "description", "capabilities", "site_type")):
            generate_agent_json(site_id, conn)

    conn.close()


def delete_site(site_id):
    """Delete a site"""
    conn = get_db()
    conn.execute("DELETE FROM sites WHERE id = ?", (site_id,))
    conn.commit()
    conn.close()


def increment_call_count(site_id):
    """Increment call count for a site"""
    conn = get_db()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn.execute("UPDATE sites SET call_count = call_count + 1, last_active = ?, updated_at = datetime('now', 'localtime') WHERE id = ?", (now, site_id))
    conn.commit()
    conn.close()


def generate_agent_json(site_id, conn=None):
    """Generate agent.json content for a site according to AHP v0.1 protocol"""
    close_conn = False
    if conn is None:
        conn = get_db()
        close_conn = True

    row = conn.execute("SELECT * FROM sites WHERE id = ?", (site_id,)).fetchone()
    if not row:
        if close_conn:
            conn.close()
        return None

    site = dict(row)
    capabilities = json.loads(site["capabilities"]) if isinstance(site["capabilities"], str) else site["capabilities"]

    agent = {
        "ahp_version": "0.1",
        "agent": {
            "id": f"hosted-{site['id']}",
            "name": site["name"],
            "type": site["site_type"],
            "description": site["description"],
            "hosted_by": "InsightBrowser Hosting",
            "endpoint": f"/api/sites/{site['id']}/query"
        },
        "capabilities": capabilities,
        "meta": {
            "created_at": site["created_at"],
            "updated_at": site["updated_at"],
            "call_count": site["call_count"],
            "status": site["status"],
            "data_source": site["data_source"]
        }
    }

    agent_json = json.dumps(agent, ensure_ascii=False, indent=2)
    conn.execute("UPDATE sites SET agent_json = ? WHERE id = ?", (agent_json, site_id))
    conn.commit()

    if close_conn:
        conn.close()

    return agent


def generate_site_template(site_id):
    """Generate a Python + FastAPI skeleton for a hosted site"""
    site = get_site(site_id)
    if not site:
        return None

    capabilities = json.loads(site["capabilities"]) if isinstance(site["capabilities"], str) else site["capabilities"]
    cap_routes = []
    for cap in capabilities:
        cap_id = cap.get("id", "unknown")
        cap_name = cap.get("name", "Unnamed")
        cap_desc = cap.get("description", "")
        params = cap.get("parameters", [])
        param_docs = "\n".join([f"        - {p.get('name', '?')}: {p.get('description', '')} ({p.get('type', 'string')})" for p in params])

        route_code = f"""
@app.post("/api/capabilities/{cap_id}")
async def capability_{cap_id}(request: Request):
    \"\"\"{cap_name}: {cap_desc}\"\"\"
    data = await request.json()
    # Parameters:
{param_docs}
    # TODO: Implement the actual capability logic
    return {{"status": "ok", "capability": "{cap_id}", "data": data}}
"""
        cap_routes.append(route_code)

    template = f'''"""
{site["name"]} - Auto-generated Agent Site
AHP v0.1 Protocol
Generated by InsightBrowser Hosting
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import json
import os

app = FastAPI(title="{site["name"]}", version="1.0.0")

# Agent metadata
AGENT_META = {json.dumps(json.loads(site["agent_json"]) if site.get("agent_json") else {{}}, ensure_ascii=False, indent=4)}

@app.get("/agent.json")
async def get_agent_json():
    """Return agent.json for Registry registration"""
    return JSONResponse(content=AGENT_META)

@app.get("/health")
async def health():
    return {{"status": "ok", "agent": "{site["name"]}"}}

{"".join(cap_routes)}
@app.post("/api/query")
async def query(request: Request):
    """Generic query endpoint"""
    data = await request.json()
    return {{"status": "ok", "agent": "{site["name"]}", "response": "Query received"}}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
'''
    return template
