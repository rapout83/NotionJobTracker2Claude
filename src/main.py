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
from .claude_client import ClaudeJobProcessor

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
claude_client: Optional[ClaudeJobProcessor] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown"""
    global notion_client, claude_client

    # Startup
    logger.info("Starting NotionJobTracker2Claude webhook service...")
    try:
        notion_client = NotionJobTrackerClient()
        claude_client = ClaudeJobProcessor()
        logger.info("Clients initialized successfully")
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
    return {
        "status": "healthy",
        "notion_client": "initialized" if notion_client else "not initialized",
        "claude_client": "initialized" if claude_client else "not initialized"
    }


@app.post("/webhook/notion", response_model=WebhookResponse)
async def notion_webhook(
    request: Request,
    x_webhook_secret: Optional[str] = Header(None)
):
    """
    Webhook endpoint to receive Notion page triggers

    This endpoint:
    1. Receives a Notion page ID
    2. Fetches the job entry from Notion
    3. Sends it to Claude for processing
    4. Returns Claude's response

    Args:
        request: Raw request to inspect payload
        x_webhook_secret: Secret for authentication

    Returns:
        WebhookResponse with Claude's analysis
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

    # Verify webhook secret
    verify_webhook_secret(x_webhook_secret)

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

        # Process with Claude
        if not claude_client:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Claude client not initialized"
            )

        claude_response = claude_client.process_job_entry(job_entry)
        logger.info(f"Claude processing completed for: {page_id}")

        return WebhookResponse(
            success=True,
            message="Job entry processed successfully",
            page_id=page_id,
            claude_response=claude_response
        )

    except Exception as e:
        logger.error(f"Error processing webhook: {e}", exc_info=True)
        return WebhookResponse(
            success=False,
            message="Error processing job entry",
            page_id=page_id,
            error=str(e)
        )


@app.post("/process", response_model=WebhookResponse)
async def process_job_entry(request: ClaudeRequest):
    """
    Direct endpoint to process a job entry with Claude

    This is useful for testing or manual triggering without Notion webhook

    Args:
        request: ClaudeRequest with job_entry data

    Returns:
        WebhookResponse with Claude's analysis
    """
    logger.info(f"Processing job entry: {request.job_entry.title}")

    try:
        if not claude_client:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Claude client not initialized"
            )

        claude_response = claude_client.process_job_entry(
            request.job_entry,
            prompt_template=request.prompt_template,
            max_tokens=request.max_tokens
        )

        return WebhookResponse(
            success=True,
            message="Job entry processed successfully",
            page_id=request.job_entry.page_id,
            claude_response=claude_response
        )

    except Exception as e:
        logger.error(f"Error processing job entry: {e}", exc_info=True)
        return WebhookResponse(
            success=False,
            message="Error processing job entry",
            page_id=request.job_entry.page_id,
            error=str(e)
        )


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
