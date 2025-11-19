"""
FastAPI webhook server for NotionJobTracker2Claude
"""
import os
import logging
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException, Header, Request, status
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

from .models import NotionWebhookPayload, WebhookResponse, ClaudeRequest
from .notion_client import NotionJobTrackerClient
from .cache import JobCacheManager

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# Global clients (initialized on startup)
notion_client: Optional[NotionJobTrackerClient] = None
cache_manager: Optional[JobCacheManager] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown"""
    global notion_client, cache_manager

    # Startup
    logger.info("Starting NotionJobTracker2Claude webhook service...")
    try:
        notion_client = NotionJobTrackerClient()
        cache_manager = JobCacheManager(
            cache_dir=os.getenv("CACHE_DIR", "webhook/cache"),
            max_entries=int(os.getenv("CACHE_MAX_ENTRIES", "10")),
            ttl_hours=int(os.getenv("CACHE_TTL_HOURS", "24"))
        )
        logger.info("Clients and cache manager initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize clients: {e}")
        raise

    yield

    # Shutdown
    logger.info("Shutting down NotionJobTracker2Claude webhook service...")


# Initialize FastAPI app
app = FastAPI(
    title="NotionJobTracker2Claude",
    description="Webhook service to send Notion job tracker entries to Claude AI",
    version="0.1.0",
    lifespan=lifespan
)


def verify_webhook_secret(x_webhook_secret: Optional[str] = Header(None)) -> bool:
    """
    Verify webhook secret for authentication

    Args:
        x_webhook_secret: Secret from webhook header

    Returns:
        True if valid, raises HTTPException otherwise
    """
    expected_secret = os.getenv("WEBHOOK_SECRET")

    if not expected_secret:
        logger.warning("WEBHOOK_SECRET not configured - skipping verification")
        return True

    if not x_webhook_secret or x_webhook_secret != expected_secret:
        logger.warning("Invalid webhook secret received")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid webhook secret"
        )

    return True


@app.get("/")
async def root():
    """Root endpoint - health check"""
    return {
        "service": "NotionJobTracker2Claude",
        "status": "running",
        "version": "0.1.0"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    cache_stats = cache_manager.stats() if cache_manager else {}
    return {
        "status": "healthy",
        "notion_client": "initialized" if notion_client else "not initialized",
        "cache_manager": "initialized" if cache_manager else "not initialized",
        "cache_stats": cache_stats
    }


@app.post("/webhook/notion", response_model=WebhookResponse)
async def notion_webhook(
    request: Request
):
    """
    Webhook endpoint to receive Notion page triggers

    This endpoint:
    1. Receives a Notion page ID from automation
    2. Fetches the job entry from Notion
    3. Caches it for MCP access
    4. Returns success status

    Note: Webhook secret is NOT required for this endpoint since
    Notion automations cannot send custom headers.

    Args:
        request: Raw request to inspect payload

    Returns:
        WebhookResponse with cache status
    """
    # Log the raw payload for debugging
    body = await request.body()
    logger.info(f"Raw webhook payload: {body.decode()}")

    try:
        payload_dict = await request.json()
        logger.info(f"Parsed JSON payload: {payload_dict}")
    except Exception as e:
        logger.error(f"Failed to parse JSON: {e}")
        return WebhookResponse(
            success=False,
            message="Invalid JSON payload",
            error=str(e)
        )

    # Try to extract page_id from various possible formats
    # Notion automation sends: {"data": {"id": "...", ...}}
    page_id = None
    if "data" in payload_dict and isinstance(payload_dict["data"], dict):
        page_id = payload_dict["data"].get("id")

    # Fallback to top-level fields for manual triggers
    if not page_id:
        page_id = payload_dict.get("page_id") or payload_dict.get("pageId") or payload_dict.get("id")

    if not page_id:
        logger.error(f"No page_id found in payload: {payload_dict}")
        return WebhookResponse(
            success=False,
            message="Missing page_id in payload",
            error=f"Received fields: {list(payload_dict.keys())}"
        )

    # No webhook secret verification for Notion automation (can't send custom headers)

    logger.info(f"Received webhook for page_id: {page_id}")

    try:
        # Fetch job entry from Notion
        if not notion_client:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Notion client not initialized"
            )

        job_entry = notion_client.get_job_entry(page_id)
        logger.info(f"Fetched job entry: {job_entry.title}")

        # Cache the job entry for MCP access
        if not cache_manager:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Cache manager not initialized"
            )

        cache_success = cache_manager.add(job_entry)

        if cache_success:
            logger.info(f"Job entry cached successfully: {page_id}")
            return WebhookResponse(
                success=True,
                message=f"Job entry cached successfully. Use Claude Desktop with MCP to analyze.",
                page_id=page_id,
                claude_response=None
            )
        else:
            logger.error(f"Failed to cache job entry: {page_id}")
            return WebhookResponse(
                success=False,
                message="Failed to cache job entry",
                page_id=page_id,
                error="Cache operation failed"
            )

    except Exception as e:
        logger.error(f"Error processing webhook: {e}", exc_info=True)
        return WebhookResponse(
            success=False,
            message="Error processing job entry",
            page_id=page_id,
            error=str(e)
        )


# Removed /process endpoint - Claude API processing moved to MCP architecture
# Use Claude Desktop with MCP to analyze cached job entries


# ============================================================================
# Cache Management Endpoints (for MCP integration)
# ============================================================================

@app.post("/cache/notion")
async def cache_from_notion(
    request: Request,
    x_webhook_secret: Optional[str] = Header(None)
):
    """
    Manually cache a job entry from Notion

    This is an alternative to the webhook endpoint for manual caching.
    Expects: {"page_id": "notion_page_id"}

    Returns:
        Cached job entry data
    """
    verify_webhook_secret(x_webhook_secret)

    try:
        payload = await request.json()
        page_id = payload.get("page_id")

        if not page_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing page_id in request"
            )

        if not notion_client or not cache_manager:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Services not initialized"
            )

        # Fetch and cache
        job_entry = notion_client.get_job_entry(page_id)
        cache_manager.add(job_entry)

        logger.info(f"Manually cached job entry: {page_id}")

        return {
            "success": True,
            "message": "Job entry cached successfully",
            "job_entry": job_entry.model_dump()
        }

    except Exception as e:
        logger.error(f"Error caching from Notion: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@app.get("/cache/list")
async def list_cached_jobs():
    """
    List all cached job entries with metadata

    Returns:
        List of cached jobs with cache metadata
    """
    if not cache_manager:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Cache manager not initialized"
        )

    jobs = cache_manager.list_all()
    stats = cache_manager.stats()

    return {
        "success": True,
        "total_entries": len(jobs),
        "cache_stats": stats,
        "jobs": jobs
    }


@app.get("/cache/{page_id}")
async def get_cached_job(page_id: str):
    """
    Get a specific cached job entry by page_id

    This endpoint is used by MCP to retrieve cached job data efficiently.

    Args:
        page_id: Notion page ID

    Returns:
        Cached job entry if found
    """
    if not cache_manager:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Cache manager not initialized"
        )

    job_entry = cache_manager.get(page_id)

    if not job_entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job entry not found in cache: {page_id}"
        )

    logger.info(f"Retrieved cached job entry: {page_id}")

    return {
        "success": True,
        "job_entry": job_entry.model_dump()
    }


@app.delete("/cache/clear")
async def clear_cache(x_webhook_secret: Optional[str] = Header(None)):
    """
    Clear all cached entries

    Requires webhook secret for security.

    Returns:
        Number of entries removed
    """
    verify_webhook_secret(x_webhook_secret)

    if not cache_manager:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Cache manager not initialized"
        )

    count = cache_manager.clear()

    logger.info(f"Cache cleared: {count} entries removed")

    return {
        "success": True,
        "message": f"Cleared {count} cached entries",
        "entries_removed": count
    }


@app.delete("/cache/{page_id}")
async def delete_cached_job(
    page_id: str,
    x_webhook_secret: Optional[str] = Header(None)
):
    """
    Delete a specific cached job entry

    Requires webhook secret for security.

    Args:
        page_id: Notion page ID

    Returns:
        Success status
    """
    verify_webhook_secret(x_webhook_secret)

    if not cache_manager:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Cache manager not initialized"
        )

    deleted = cache_manager.delete(page_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job entry not found in cache: {page_id}"
        )

    logger.info(f"Deleted cached entry: {page_id}")

    return {
        "success": True,
        "message": f"Deleted cached entry: {page_id}"
    }


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")

    logger.info(f"Starting server on {host}:{port}")
    uvicorn.run(
        "src.main:app",
        host=host,
        port=port,
        reload=True,
        log_level=os.getenv("LOG_LEVEL", "info").lower()
    )
