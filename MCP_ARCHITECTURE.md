# MCP Architecture Guide

This document explains the Model Context Protocol (MCP) architecture for the NotionJobTracker2Claude system.

## Overview

The webhook service now operates as a **caching layer** instead of directly calling the Claude API. This architecture provides:

- **Token efficiency**: Pre-fetch Notion data once, avoid repeated fetches
- **Project context**: Use Claude Desktop with full conversation history
- **Cost savings**: Use your Claude Pro subscription instead of paying for API calls
- **Better workflow**: Analyze jobs in Claude Desktop with full project knowledge

## Architecture Diagram

```
┌─────────────────┐
│  Notion Button  │ ──① Trigger──> ┌──────────────────────┐
└─────────────────┘                │  Webhook Service     │
                                   │  (FastAPI on NAS)    │
                                   │                      │
                                   │  • Fetch from Notion │
                                   │  • Cache job data    │
                                   │  • Provide REST API  │
                                   └──────────────────────┘
                                            │
                                            │ ② HTTP GET
                                            ↓
┌─────────────────┐                ┌──────────────────────┐
│ Claude Desktop  │ ──③ MCP────────│   MCP Server         │
│                 │                │                      │
│ • Project       │                │  • list_cached_jobs  │
│ • Conversation  │                │  • get_cached_job    │
│ • Memory        │                │  • update_notion     │
└─────────────────┘                └──────────────────────┘
```

## Workflow

### 1. Cache Job Entry from Notion

When you click a button in Notion:

```
User clicks button in Notion
  ↓
Notion sends webhook to: http://your-nas:8000/webhook/notion
  ↓
Webhook service:
  1. Receives Notion page_id
  2. Fetches full job entry from Notion
  3. Caches it locally (24h TTL, max 10 jobs)
  4. Returns success
```

**Result**: Job entry is now cached and ready for Claude Desktop to access efficiently.

### 2. Analyze with Claude Desktop

In Claude Desktop, you interact with your project:

```
You: "What jobs do I have cached?"
  ↓
Claude calls MCP tool: list_cached_jobs
  ↓
MCP server calls: GET http://your-nas:8000/cache/list
  ↓
Returns list of cached jobs with metadata
  ↓
You: "Analyze the Software Engineer position at Acme Corp"
  ↓
Claude calls MCP tool: get_cached_job(page_id)
  ↓
MCP server calls: GET http://your-nas:8000/cache/{page_id}
  ↓
Returns full job entry data (already in cache - no Notion API call!)
  ↓
Claude analyzes with full project context and conversation history
```

**Benefits**:
- Uses cached data (saves tokens)
- Has full conversation history (not available in Claude API)
- Has access to your entire project knowledge
- Costs $0 beyond your Claude Pro subscription

### 3. Update Notion Fields (Future)

After analysis, Claude can write back to Notion:

```
You: "Update the Notes field with your analysis"
  ↓
Claude calls MCP tool: update_notion_field(page_id, field, value)
  ↓
MCP server calls: POST http://your-nas:8000/update/{page_id}
  ↓
Webhook service updates Notion via API
  ↓
Returns success
```

## Token Efficiency Comparison

### Old Approach: Direct Notion Connector

```
You: "Analyze this job"
  ↓
Claude fetches from Notion directly
  • Tokens: ~800-1500 per fetch
  • Every single request refetches data
  • No caching
```

**Cost per analysis**: 800-1500 tokens

### New Approach: MCP + Cache

```
Step 1: Cache (one-time)
  Notion webhook → Cache
  • Tokens: 0 (no Claude involved)

Step 2: Analyze (multiple times)
  You: "Analyze this job"
  Claude reads from cache via MCP
  • Tokens: ~200-400 (already in Claude's context)

  You: "What are the red flags?"
  Claude uses same cached data
  • Tokens: ~50-100 (already in conversation)

  You: "Compare with other jobs"
  Claude reads other cached jobs
  • Tokens: ~200-400 per job (from cache)
```

**Cost per analysis**: 200-400 tokens (first time), 50-100 tokens (follow-ups)

**Savings**: 60-75% token reduction

## Cache Management

### Automatic Cleanup

The cache automatically manages itself:

- **TTL (Time-To-Live)**: 24 hours
  - Jobs older than 24h are automatically removed
- **Size Limit**: 10 jobs maximum
  - When limit reached, oldest jobs are removed
- **On-Demand**: Clean expired entries when accessed

### Manual Management

You can also manage the cache manually:

```bash
# List cached jobs
curl http://your-nas:8000/cache/list

# Get specific job
curl http://your-nas:8000/cache/{page_id}

# Clear all cache
curl -X DELETE http://your-nas:8000/cache/clear \
  -H "X-Webhook-Secret: your_secret"

# Delete specific job
curl -X DELETE http://your-nas:8000/cache/{page_id} \
  -H "X-Webhook-Secret: your_secret"
```

### Cache Storage

Cache is stored in: `/volume1/docker/notion2claude/webhook/cache/jobs.json`

```json
{
  "page_id_123": {
    "job_entry": {
      "page_id": "page_id_123",
      "title": "Software Engineer at Acme Corp",
      "company": "Acme Corp",
      "position": "Software Engineer",
      "status": "Applied",
      "description": "...",
      "notes": "...",
      "url": "https://..."
    },
    "cached_at": "2025-11-19T10:30:00Z"
  }
}
```

## MCP Server Implementation

### Tools Provided to Claude Desktop

The MCP server will provide these tools:

#### 1. `list_cached_jobs_from_webhook`

```
Description: List all jobs cached in the webhook service
Parameters: None
Returns: List of jobs with metadata (title, company, cached_at, expires_at)
```

**Why this name?**: Makes it clear this uses the webhook cache, not direct Notion access.

#### 2. `get_cached_job_from_webhook`

```
Description: Get detailed job entry from webhook cache (token-efficient)
Parameters:
  - page_id: Notion page ID
Returns: Full job entry data
```

**Why this name?**: Explicitly indicates this is the token-efficient cached version.

#### 3. `update_notion_via_webhook` (Future)

```
Description: Update a Notion field via webhook service
Parameters:
  - page_id: Notion page ID
  - field_name: Field to update (e.g., "Notes", "Analysis")
  - value: New value to set
Returns: Success status
```

**Why this name?**: Clear that updates go through webhook, not direct Notion API.

### MCP Server Code Structure

```
mcp_server/
├── server.py              # MCP server implementation
├── config.json           # MCP server configuration
└── README.md             # Setup instructions
```

**Next steps**: Implement the MCP server (coming soon)

## Environment Variables

### Required

```env
# Notion API
NOTION_API_KEY=your_notion_integration_token
NOTION_DATABASE_ID=your_database_id

# Webhook Security
WEBHOOK_SECRET=your_secret_key
```

### Cache Configuration

```env
# Cache settings (defaults shown)
CACHE_DIR=webhook/cache
CACHE_MAX_ENTRIES=10
CACHE_TTL_HOURS=24
```

### Deprecated

```env
# No longer needed - using MCP instead
# ANTHROPIC_API_KEY=...
# CLAUDE_MODEL=...
```

## API Endpoints

### Webhook Endpoints

#### POST `/webhook/notion`

Receive Notion automation trigger and cache job entry.

**Request**:
```json
{
  "data": {
    "id": "notion_page_id",
    "properties": { ... }
  }
}
```

**Response**:
```json
{
  "success": true,
  "message": "Job entry cached successfully. Use Claude Desktop with MCP to analyze.",
  "page_id": "notion_page_id"
}
```

### Cache Endpoints (for MCP)

#### GET `/cache/list`

List all cached jobs.

**Response**:
```json
{
  "success": true,
  "total_entries": 3,
  "cache_stats": {
    "total_entries": 3,
    "max_entries": 10,
    "ttl_hours": 24,
    "oldest_entry": "2025-11-19T08:00:00Z",
    "newest_entry": "2025-11-19T10:30:00Z"
  },
  "jobs": [
    {
      "page_id": "...",
      "title": "Software Engineer at Acme Corp",
      "company": "Acme Corp",
      "cached_at": "2025-11-19T10:30:00Z",
      "expires_at": "2025-11-20T10:30:00Z"
    }
  ]
}
```

#### GET `/cache/{page_id}`

Get specific cached job entry.

**Response**:
```json
{
  "success": true,
  "job_entry": {
    "page_id": "...",
    "title": "Software Engineer at Acme Corp",
    "company": "Acme Corp",
    "position": "Software Engineer",
    "status": "Applied",
    "description": "...",
    "notes": "...",
    "url": "https://..."
  }
}
```

#### POST `/cache/notion`

Manually cache a job entry (alternative to webhook).

**Request**:
```json
{
  "page_id": "notion_page_id"
}
```

**Headers**: `X-Webhook-Secret: your_secret`

#### DELETE `/cache/clear`

Clear all cached entries.

**Headers**: `X-Webhook-Secret: your_secret`

#### DELETE `/cache/{page_id}`

Delete specific cached entry.

**Headers**: `X-Webhook-Secret: your_secret`

### Health Check

#### GET `/health`

Check service health and cache stats.

**Response**:
```json
{
  "status": "healthy",
  "notion_client": "initialized",
  "cache_manager": "initialized",
  "cache_stats": {
    "total_entries": 3,
    "max_entries": 10,
    "ttl_hours": 24
  }
}
```

## Deployment on NAS

### File Structure

```
/volume1/docker/notion2claude/
├── src/
│   ├── main.py              # FastAPI app (updated for caching)
│   ├── cache.py             # Cache manager (NEW)
│   ├── notion_client.py     # Notion API client
│   ├── claude_client.py     # Deprecated (not used)
│   └── models.py            # Pydantic models
├── webhook/
│   ├── cache/
│   │   └── jobs.json        # Cached job entries
│   └── logs/
│       ├── access.log
│       └── error.log
├── docker-compose.yml
├── Dockerfile
├── .env
└── start.sh
```

### Starting the Service

```bash
cd /volume1/docker/notion2claude
./start.sh
```

The service will:
1. Create `webhook/cache` directory
2. Start FastAPI server on port 8000
3. Initialize cache manager
4. Listen for Notion webhooks

### Checking Status

```bash
# Check service health
curl http://localhost:8000/health

# View logs
docker-compose logs -f

# Check cached jobs
curl http://localhost:8000/cache/list
```

## Next Steps

1. ✅ Webhook service updated to cache instead of calling Claude API
2. ✅ Cache manager implemented with TTL and size limits
3. ✅ Cache REST API endpoints created
4. ⏳ Implement MCP server
5. ⏳ Configure Claude Desktop to use MCP server
6. ⏳ Test end-to-end workflow
7. ⏳ Add Notion field update functionality

## Benefits Summary

| Feature | Old (Claude API) | New (MCP + Cache) |
|---------|------------------|-------------------|
| **Cost** | ~$1-2/month API | $0 (uses Claude Pro) |
| **Tokens per analysis** | 800-1500 | 200-400 (60-75% less) |
| **Project context** | ❌ No | ✅ Yes |
| **Conversation memory** | ❌ No | ✅ Yes |
| **Follow-up questions** | 800-1500 tokens each | 50-100 tokens each |
| **Data freshness** | Always fresh | Cached (24h TTL) |
| **Setup complexity** | Simple | Moderate (needs MCP) |

## Troubleshooting

### Cache not working

```bash
# Check cache directory exists
ls -la /volume1/docker/notion2claude/webhook/cache/

# Check permissions
chmod -R 755 /volume1/docker/notion2claude/webhook/

# Check logs
docker-compose logs -f
```

### Cache not clearing old entries

```bash
# Check cache stats
curl http://localhost:8000/health

# Manually clear cache
curl -X DELETE http://localhost:8000/cache/clear \
  -H "X-Webhook-Secret: your_secret"
```

### MCP can't reach webhook

```bash
# Test from Claude Desktop's machine
curl http://your-nas-ip:8000/cache/list

# If fails, check:
# 1. Webhook service running: docker ps
# 2. Port accessible: telnet your-nas-ip 8000
# 3. Firewall rules on NAS
```

## Security Considerations

1. **Webhook Secret**: Always use `X-Webhook-Secret` header for write operations
2. **Cache Access**: Read operations (GET) don't require secret for MCP convenience
3. **Network**: Keep webhook service on local network (don't expose to internet)
4. **API Keys**: Store in `.env` file (git-ignored)
5. **Cache Data**: Cached jobs are stored in plain JSON (encrypt disk if needed)

## Support

- Webhook service logs: `docker-compose logs -f`
- Cache location: `/volume1/docker/notion2claude/webhook/cache/`
- API documentation: http://localhost:8000/docs (FastAPI auto-generated)
