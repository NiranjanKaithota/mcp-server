from fastmcp import FastMCP
from dotenv import load_dotenv
import os

load_dotenv()
# os.environ["JIRA_URL"] = os.getenv("JIRA_URL", "")
# os.environ["JIRA_EMAIL"] = os.getenv("JIRA_EMAIL", "")
# os.environ["JIRA_API_TOKEN"] = os.getenv("JIRA_API_TOKEN", "")

mcp = FastMCP(name="Enterprise Integrator")

# Import and register the tool from the separate module
from tools.jira import get_jira_issue, create_jira_issue

# Register it using the instance decorator
mcp.tool(get_jira_issue)
mcp.tool(create_jira_issue)

# You can easily add more tools later:
# from app.tools.github import search_prs
# mcp.tool(search_prs)

def main():
    print("=" * 70)
    print("🚀 Enterprise MCP Server (Clean Architecture)")
    print("=" * 70)
    print("   Endpoint → http://localhost:8000/sse")
    # print("   Registered Tools:")
    # print("     • get_jira_issue")
    print("=" * 70)
    print("✅ Server ready! Connect in Cursor and query JIRA issues.\n")

    mcp.run(transport="sse", port=8000)

if __name__ == "__main__":
    main()