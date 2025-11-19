# MCP Server for NotionJobTracker2Claude

This MCP (Model Context Protocol) server connects Claude Desktop to your cached Notion job data, providing token-efficient access to job applications.

## What This Does

The MCP server provides tools to Claude Desktop:

1. **`list_cached_jobs_from_webhook`** - List all cached jobs
2. **`get_cached_job_from_webhook`** - Get detailed job data (saves 60-75% tokens vs direct Notion)
3. **`get_webhook_cache_stats`** - Check cache health and statistics

Claude will **prefer these tools over the direct Notion connector** because they're more token-efficient.

## Prerequisites

- Python 3.10 or higher
- Claude Desktop installed
- Webhook service running on your NAS

## Installation

### 1. Install Dependencies

```bash
cd mcp_server
pip install -r requirements.txt
```

Or with a virtual environment:

```bash
cd mcp_server
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Environment

Copy the example environment file:

```bash
cp .env.example .env
```

Edit `.env` and set your webhook service URL:

```env
WEBHOOK_BASE_URL=http://192.168.1.100:8000  # Your NAS IP and port
```

### 3. Make Server Executable

```bash
chmod +x server.py
```

### 4. Test the Server

```bash
python server.py
```

The server should start and wait for input (it communicates via stdio with Claude Desktop).

Press `Ctrl+C` to stop.

## Configure Claude Desktop

### For macOS/Linux

Edit Claude Desktop's MCP config:

```bash
# macOS
code ~/Library/Application\ Support/Claude/claude_desktop_config.json

# Linux
code ~/.config/Claude/claude_desktop_config.json
```

Add this configuration:

```json
{
  "mcpServers": {
    "notion-job-tracker": {
      "command": "python",
      "args": [
        "/absolute/path/to/NotionJobTracker2Claude/mcp_server/server.py"
      ],
      "env": {
        "WEBHOOK_BASE_URL": "http://192.168.1.100:8000"
      }
    }
  }
}
```

**Important:** Replace `/absolute/path/to/NotionJobTracker2Claude` with the actual full path.

### For Windows

Edit:
```
%APPDATA%\Claude\claude_desktop_config.json
```

Configuration:

```json
{
  "mcpServers": {
    "notion-job-tracker": {
      "command": "python",
      "args": [
        "C:\\path\\to\\NotionJobTracker2Claude\\mcp_server\\server.py"
      ],
      "env": {
        "WEBHOOK_BASE_URL": "http://192.168.1.100:8000"
      }
    }
  }
}
```

## Using with Claude Desktop

### 1. Start the Webhook Service

Make sure your webhook service is running on your NAS:

```bash
cd /volume1/docker/notion2claude
./start.sh
```

### 2. Cache a Job from Notion

Click the "Send to Claude" button in your Notion job tracker to cache a job entry.

### 3. Ask Claude in Claude Desktop

Open Claude Desktop and try:

```
What jobs do I have cached?
```

Claude will use the `list_cached_jobs_from_webhook` tool to show your cached jobs.

```
Analyze the Software Engineer position at Acme Corp
```

Claude will use `get_cached_job_from_webhook` to get the full details and analyze them.

## Example Conversation

**You:** What jobs do I have cached?

**Claude:** *[Uses list_cached_jobs_from_webhook tool]*

You have 3 jobs cached:

1. **Yum! Brands** - Regional Digital and Technology Leader
   - Cached: 2025-11-19T02:34:36
   - Page ID: `2ade55d0-7bea-81d0-ad64-fa2379489daa`

2. **Roche** - Analytics & Insights Lead
   - Cached: 2025-11-19T03:15:22
   - Page ID: `2ade55d0-7bea-81bb-b38e-f4947aebcc21`

...

**You:** Analyze the Yum! Brands position

**Claude:** *[Uses get_cached_job_from_webhook tool]*

Let me analyze the Yum! Brands position...

[Full analysis with project context and conversation memory]

## Token Efficiency

### Direct Notion Connector (Old Way)
```
You: "Analyze this job"
→ Claude fetches from Notion: ~800-1500 tokens
You: "What are the red flags?"
→ Claude refetches from Notion: ~800-1500 tokens
```
**Total:** 1600-3000 tokens

### MCP + Webhook Cache (New Way)
```
You: "Analyze this job"
→ Claude reads from cache: ~200-400 tokens
You: "What are the red flags?"
→ Claude uses conversation context: ~50-100 tokens
```
**Total:** 250-500 tokens

**Savings:** 60-85% fewer tokens!

## Troubleshooting

### Claude Desktop doesn't see the MCP server

1. Check the config path:
   ```bash
   # macOS
   cat ~/Library/Application\ Support/Claude/claude_desktop_config.json

   # Linux
   cat ~/.config/Claude/claude_desktop_config.json
   ```

2. Verify the absolute path in the config is correct

3. Restart Claude Desktop completely

4. Check Claude Desktop logs:
   ```bash
   # macOS
   tail -f ~/Library/Logs/Claude/mcp*.log
   ```

### "Error connecting to webhook service"

1. Check webhook service is running:
   ```bash
   curl http://your-nas-ip:8000/health
   ```

2. Verify `WEBHOOK_BASE_URL` in MCP config matches your NAS IP

3. Check firewall allows connections from your desktop to NAS:8000

4. Test from your desktop:
   ```bash
   curl http://your-nas-ip:8000/cache/list
   ```

### "No jobs currently cached"

1. Click "Send to Claude" button in Notion to cache a job

2. Verify job was cached:
   ```bash
   curl http://your-nas-ip:8000/cache/list
   ```

3. Check webhook logs:
   ```bash
   cd /volume1/docker/notion2claude
   docker-compose logs -f
   ```

### MCP server crashes

1. Check Python version: `python --version` (need 3.10+)

2. Reinstall dependencies:
   ```bash
   pip install --upgrade -r requirements.txt
   ```

3. Test manually:
   ```bash
   python server.py
   # Should wait for input, not crash
   ```

## Development

### Testing the Server

You can test the MCP server without Claude Desktop:

```bash
# Install MCP inspector
npm install -g @modelcontextprotocol/inspector

# Run inspector
mcp-inspector python server.py
```

This opens a web UI where you can test the MCP tools.

### Modifying Tools

Edit `server.py` and update:

1. `list_tools()` - Add/modify tool definitions
2. `call_tool()` - Add tool handlers
3. Helper methods - Add data extraction functions

After changes, restart Claude Desktop to reload the MCP server.

## Architecture

```
┌─────────────────────┐
│  Claude Desktop     │
│  (You chat here)    │
└──────────┬──────────┘
           │
           │ (MCP protocol - stdio)
           ↓
┌─────────────────────┐
│  MCP Server         │
│  (server.py)        │
└──────────┬──────────┘
           │
           │ (HTTP GET)
           ↓
┌─────────────────────┐
│  Webhook Service    │
│  (NAS:8000)         │
│                     │
│  /cache/list        │
│  /cache/{page_id}   │
└──────────┬──────────┘
           │
           │ (Cache file)
           ↓
┌─────────────────────┐
│  jobs.json          │
│  (webhook/cache/)   │
└─────────────────────┘
```

## Security Notes

1. **Read-only access** - MCP server only reads from cache (no write operations)
2. **Local network** - Webhook should only be accessible on local network
3. **No API keys needed** - MCP server doesn't need Notion or Claude API keys
4. **Cache TTL** - Jobs expire after 24 hours (configurable)

## Next Steps

Once the MCP server is working:

1. ✅ Test with Claude Desktop
2. ⏳ Add `update_notion_via_webhook` tool for writing analysis back to Notion
3. ⏳ Add job comparison tools
4. ⏳ Add job search/filter tools

## Support

- Webhook service logs: `docker-compose logs -f` on your NAS
- MCP server: Run `python server.py` manually to see errors
- Claude Desktop logs: Check `~/Library/Logs/Claude/` (macOS)
