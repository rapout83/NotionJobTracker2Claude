"""
Pydantic models for the NotionJobTracker2Claude service
"""
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class NotionWebhookPayload(BaseModel):
    """Model for incoming Notion webhook payload"""
    page_id: str = Field(..., description="Notion page ID")
    database_id: Optional[str] = Field(None, description="Notion database ID")
    action: str = Field(default="process", description="Action to perform")
    properties: Optional[Dict[str, Any]] = Field(None, description="Page properties")


class JobEntry(BaseModel):
    """Model for a job tracker entry"""
    page_id: str
    title: str
    company: Optional[str] = None
    position: Optional[str] = None
    status: Optional[str] = None
    description: Optional[str] = None
    notes: Optional[str] = None
    url: Optional[str] = None
    raw_properties: Dict[str, Any] = Field(default_factory=dict)


class ClaudeRequest(BaseModel):
    """Model for Claude API request"""
    job_entry: JobEntry
    prompt_template: Optional[str] = None
    max_tokens: int = Field(default=4096, ge=1, le=8192)


class WebhookResponse(BaseModel):
    """Model for webhook response"""
    success: bool
    message: str
    page_id: Optional[str] = None
    claude_response: Optional[str] = None
    error: Optional[str] = None
