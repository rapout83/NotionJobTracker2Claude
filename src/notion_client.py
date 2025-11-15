"""
Notion API client for fetching job tracker entries
"""
import os
import logging
from typing import Dict, Any, Optional
from notion_client import Client
from notion_client.errors import APIResponseError

from .models import JobEntry

logger = logging.getLogger(__name__)


class NotionJobTrackerClient:
    """Client for interacting with Notion Job Tracker database"""

    def __init__(self, api_key: Optional[str] = None, database_id: Optional[str] = None):
        """
        Initialize Notion client

        Args:
            api_key: Notion integration token (defaults to env var)
            database_id: Notion database ID (defaults to env var)
        """
        self.api_key = api_key or os.getenv("NOTION_API_KEY")
        self.database_id = database_id or os.getenv("NOTION_DATABASE_ID")

        if not self.api_key:
            raise ValueError("NOTION_API_KEY must be provided or set in environment")

        self.client = Client(auth=self.api_key)
        logger.info("Notion client initialized")

    def get_page(self, page_id: str) -> Dict[str, Any]:
        """
        Retrieve a page from Notion

        Args:
            page_id: The Notion page ID

        Returns:
            Page data dictionary
        """
        try:
            logger.info(f"Fetching Notion page: {page_id}")
            page = self.client.pages.retrieve(page_id=page_id)
            return page
        except APIResponseError as e:
            logger.error(f"Error fetching Notion page {page_id}: {e}")
            raise

    def parse_job_entry(self, page_data: Dict[str, Any]) -> JobEntry:
        """
        Parse Notion page data into JobEntry model

        Args:
            page_data: Raw page data from Notion API

        Returns:
            JobEntry object
        """
        properties = page_data.get("properties", {})
        page_id = page_data.get("id", "")

        # Extract common job tracker fields
        # Note: Adjust these property names based on your actual Notion database schema
        title = self._extract_title(properties)
        company = self._extract_text(properties.get("Company"))
        position = self._extract_text(properties.get("Position"))
        status = self._extract_select(properties.get("Status"))
        description = self._extract_rich_text(properties.get("Description"))
        notes = self._extract_rich_text(properties.get("Notes"))
        url = self._extract_url(properties.get("URL"))

        return JobEntry(
            page_id=page_id,
            title=title,
            company=company,
            position=position,
            status=status,
            description=description,
            notes=notes,
            url=url,
            raw_properties=properties
        )

    def _extract_title(self, properties: Dict[str, Any]) -> str:
        """Extract title from properties"""
        # Try common title field names
        for field_name in ["Name", "Title", "Job Title"]:
            if field_name in properties:
                prop = properties[field_name]
                if prop.get("type") == "title" and prop.get("title"):
                    return "".join([t.get("plain_text", "") for t in prop["title"]])
        return "Untitled"

    def _extract_text(self, prop: Optional[Dict[str, Any]]) -> Optional[str]:
        """Extract text from a property"""
        if not prop:
            return None
        if prop.get("type") == "rich_text" and prop.get("rich_text"):
            return "".join([t.get("plain_text", "") for t in prop["rich_text"]])
        return None

    def _extract_rich_text(self, prop: Optional[Dict[str, Any]]) -> Optional[str]:
        """Extract rich text from a property"""
        return self._extract_text(prop)

    def _extract_select(self, prop: Optional[Dict[str, Any]]) -> Optional[str]:
        """Extract select option from a property"""
        if not prop:
            return None
        if prop.get("type") == "select" and prop.get("select"):
            return prop["select"].get("name")
        return None

    def _extract_url(self, prop: Optional[Dict[str, Any]]) -> Optional[str]:
        """Extract URL from a property"""
        if not prop:
            return None
        if prop.get("type") == "url":
            return prop.get("url")
        return None

    def get_job_entry(self, page_id: str) -> JobEntry:
        """
        Get a job entry by page ID

        Args:
            page_id: The Notion page ID

        Returns:
            JobEntry object
        """
        page_data = self.get_page(page_id)
        return self.parse_job_entry(page_data)
