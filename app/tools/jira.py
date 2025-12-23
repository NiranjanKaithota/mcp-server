# app/tools/jira.py

import httpx
from fastmcp.server.dependencies import get_http_headers

async def get_jira_issue(issue_key: str) -> str:
    """
    Retrieve summary, status, and assignee for a JIRA issue.
    
    Args:
        issue_key: The JIRA issue key (e.g., KAN-2)
    """
    try:
        headers = get_http_headers()

        jira_url = headers.get("x-jira-url")
        jira_email = headers.get("x-jira-email")
        jira_token = headers.get("x-jira-token")

        if not all([jira_url, jira_email, jira_token]):
            missing = [k for k, v in {
                "x-jira-url": jira_url,
                "x-jira-email": jira_email,
                "x-jira-token": jira_token
            }.items() if not v]
            return f"❌ Missing required headers: {', '.join(missing)}"

        base_url = jira_url.rstrip("/")
        url = f"{base_url}/rest/api/3/issue/{issue_key}"

        async with httpx.AsyncClient() as client:
            resp = await client.get(
                url,
                auth=(jira_email, jira_token),
                headers={"Accept": "application/json"},
                timeout=15.0
            )

            if resp.status_code == 404:
                return f"❌ Issue '{issue_key}' not found."
            if resp.status_code == 401:
                return "❌ Authentication failed — check your email and API token."
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


#-- Create new ticket
async def create_jira_issue(
    project_key: str,
    summary: str,
    description: str,
    issue_type: str = "Task",
    assignee_email: str | None = None,
    labels: list[str] | None = None,
) -> str:
    """
    Create a new issue in JIRA.
    
    Args:
        project_key: The JIRA project key (e.g., "KAN")
        summary: The issue title
        description: Detailed description (supports ADF or plain text)
        issue_type: Type of issue (Task, Bug, Story, Epic, etc.) — default: Task
        assignee_email: Email of person to assign (optional)
        labels: List of labels to add (optional)
    """
    try:
        headers = get_http_headers()
        jira_url = headers.get("x-jira-url")
        jira_email = headers.get("x-jira-email")
        jira_token = headers.get("x-jira-token")

        if not all([jira_url, jira_email, jira_token]):
            missing = [k for k, v in {
                "x-jira-url": jira_url,
                "x-jira-email": jira_email,
                "x-jira-token": jira_token
            }.items() if not v]
            return f"❌ Missing headers: {', '.join(missing)}"

        base_url = jira_url.rstrip("/")
        url = f"{base_url}/rest/api/3/issue"

        # Build the payload
        fields = {
            "project": {"key": project_key},
            "summary": summary,
            "description": {
                "type": "doc",
                "version": 1,
                "content": [
                    {
                        "type": "paragraph",
                        "content": [
                            {"type": "text", "text": description}
                        ]
                    }
                ]
            },
            "issuetype": {"name": issue_type},
        }

        if assignee_email:
            fields["assignee"] = {"accountId": None}  # We'll resolve via search
        if labels:
            fields["labels"] = labels

        payload = {"fields": fields}

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                url,
                auth=(jira_email, jira_token),
                json=payload,
                headers={"Accept": "application/json", "Content-Type": "application/json"},
                timeout=20.0
            )

            if resp.status_code in (200, 201):
                data = resp.json()
                key = data["key"]
                issue_url = f"{base_url}/browse/{key}"
                return f"""
✅ **JIRA Issue Created Successfully!**

📋 **Key:** {key}
🔗 **Link:** {issue_url}
📌 **Summary:** {summary}
📊 **Type:** {issue_type}
                """.strip()

            else:
                error_msg = resp.text[:300]
                return f"❌ Failed to create issue: {resp.status_code}\n{error_msg}"

    except httpx.TimeoutException:
        return "❌ Timeout while creating issue"
    except Exception as e:
        return f"❌ Unexpected error: {str(e)}"