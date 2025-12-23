# app/tools/jira.py

import httpx
import os
from dotenv import load_dotenv

# Load .env early and once
load_dotenv()

# Load credentials — fail fast if missing (good for production)
JIRA_BASE_URL = os.getenv("JIRA_URL", "https://rvce-cnyi.atlassian.net").rstrip("/")
JIRA_EMAIL = os.getenv("JIRA_EMAIL")
JIRA_TOKEN = os.getenv("JIRA_API_TOKEN")

if not JIRA_EMAIL:
    raise RuntimeError("JIRA_EMAIL is required in .env file")
if not JIRA_TOKEN:
    raise RuntimeError("JIRA_API_TOKEN is required in .env file")

# Tool 1: Get issue
async def get_jira_issue(issue_key: str) -> str:
    """Retrieve summary, status, and assignee for a JIRA issue."""
    url = f"{JIRA_BASE_URL}/rest/api/3/issue/{issue_key}"

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                url,
                auth=(JIRA_EMAIL, JIRA_TOKEN),
                headers={"Accept": "application/json"},
                timeout=15.0
            )

            if resp.status_code == 404:
                return f"❌ Issue '{issue_key}' not found."
            if resp.status_code == 401:
                return "❌ Authentication failed — invalid email or token."
            if resp.status_code != 200:
                return f"❌ JIRA error {resp.status_code}: {resp.text[:200]}"

            data = resp.json()
            fields = data["fields"]
            summary = fields.get("summary", "No summary")
            status = fields.get("status", {}).get("name", "Unknown")
            assignee = fields.get("assignee")
            assignee_name = assignee.get("displayName", "Unassigned") if assignee else "Unassigned"

            return f"""
📋 **JIRA Issue: {data['key']}**

📌 **Summary:** {summary}
📊 **Status:** {status}
👤 **Assignee:** {assignee_name}
            """.strip()

    except httpx.TimeoutException:
        return "❌ Timeout reaching JIRA server"
    except Exception as e:
        return f"❌ Unexpected error: {str(e)}"


# Tool 2: Create issue
async def create_jira_issue(
    project_key: str,
    summary: str,
    description: str,
    issue_type: str = "Task",
    labels: list[str] | None = None,
) -> str:
    """Create a new JIRA issue."""
    url = f"{JIRA_BASE_URL}/rest/api/3/issue"

    fields = {
        "project": {"key": project_key},
        "summary": summary,
        "description": {
            "type": "doc",
            "version": 1,
            "content": [{"type": "paragraph", "content": [{"type": "text", "text": description}]}]
        },
        "issuetype": {"name": issue_type},
    }
    if labels:
        fields["labels"] = labels

    payload = {"fields": fields}

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                url,
                auth=(JIRA_EMAIL, JIRA_TOKEN),
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=20.0
            )

            if resp.status_code in (200, 201):
                data = resp.json()
                key = data["key"]
                issue_url = f"{JIRA_BASE_URL}/browse/{key}"
                return f"""
✅ **Issue Created!**

📋 **Key:** {key}
🔗 **Link:** {issue_url}
📌 **Summary:** {summary}
📊 **Type:** {issue_type}
                """.strip()
            else:
                return f"❌ Failed to create issue ({resp.status_code}): {resp.text[:300]}"

    except Exception as e:
        return f"❌ Error creating issue: {str(e)}"