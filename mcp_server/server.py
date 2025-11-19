#!/usr/bin/env python3
"""
MCP Server for NotionJobTracker2Claude
Provides tools for Claude Desktop to access cached job data from webhook service
"""
import asyncio
import os
import json
from typing import Any, Sequence
import httpx
from mcp.server import Server
from mcp.types import Tool, TextContent, ImageContent, EmbeddedResource
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Webhook service configuration
WEBHOOK_BASE_URL = os.getenv("WEBHOOK_BASE_URL", "http://localhost:8000")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "")


class NotionJobTrackerMCPServer:
    """MCP Server for accessing cached Notion job tracker data"""

    def __init__(self):
        self.server = Server("notion-job-tracker")
        self.http_client = httpx.AsyncClient(timeout=30.0)

        # Register tool handlers
        self.server.list_tools = self.list_tools
        self.server.call_tool = self.call_tool

    async def list_tools(self) -> list[Tool]:
        """List available MCP tools"""
        return [
            Tool(
                name="list_cached_jobs_from_webhook",
                description=(
                    "List all job applications cached in the webhook service. "
                    "This is the PREFERRED way to access Notion job data (more token-efficient than direct Notion API). "
                    "Returns a summary list with: company, position, cached_at, expires_at. "
                    "Use this first to see what jobs are available, then use get_cached_job_from_webhook for details."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            ),
            Tool(
                name="get_cached_job_from_webhook",
                description=(
                    "Get detailed job application data from webhook cache (token-efficient). "
                    "This is the PREFERRED way to access full Notion job details. "
                    "Returns: company, position, location, status, url, fit-gap analysis, salary, notes, etc. "
                    "Much more efficient than using direct Notion connector (saves 60-75% tokens). "
                    "Use list_cached_jobs_from_webhook first to get available page_ids."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "page_id": {
                            "type": "string",
                            "description": "The Notion page ID of the job entry to retrieve"
                        }
                    },
                    "required": ["page_id"]
                }
            ),
            Tool(
                name="get_webhook_cache_stats",
                description=(
                    "Get cache statistics and health status of the webhook service. "
                    "Shows: total cached jobs, max capacity, TTL settings, oldest/newest entries."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            )
        ]

    async def call_tool(self, name: str, arguments: dict[str, Any]) -> Sequence[TextContent | ImageContent | EmbeddedResource]:
        """Handle tool calls from Claude"""

        if name == "list_cached_jobs_from_webhook":
            return await self._list_cached_jobs()

        elif name == "get_cached_job_from_webhook":
            page_id = arguments.get("page_id")
            if not page_id:
                return [TextContent(
                    type="text",
                    text="Error: page_id is required"
                )]
            return await self._get_cached_job(page_id)

        elif name == "get_webhook_cache_stats":
            return await self._get_cache_stats()

        else:
            return [TextContent(
                type="text",
                text=f"Error: Unknown tool '{name}'"
            )]

    async def _list_cached_jobs(self) -> Sequence[TextContent]:
        """List all cached jobs from webhook service"""
        try:
            response = await self.http_client.get(f"{WEBHOOK_BASE_URL}/cache/list")
            response.raise_for_status()
            data = response.json()

            if not data.get("success"):
                return [TextContent(
                    type="text",
                    text="Error: Failed to retrieve cached jobs"
                )]

            jobs = data.get("jobs", [])
            stats = data.get("cache_stats", {})

            if not jobs:
                return [TextContent(
                    type="text",
                    text="No jobs currently cached. Click the 'Send to Claude' button in Notion to cache job entries."
                )]

            # Format job list
            result = f"📋 **Cached Jobs ({len(jobs)}/{stats.get('max_entries', 10)})**\n\n"

            for i, job in enumerate(jobs, 1):
                company = job.get("company") or "Unknown Company"
                title = job.get("title", company)
                page_id = job.get("page_id", "")
                cached_at = job.get("cached_at", "")

                result += f"{i}. **{title}**\n"
                if company and company != title:
                    result += f"   Company: {company}\n"
                result += f"   Page ID: `{page_id}`\n"
                result += f"   Cached: {cached_at}\n\n"

            result += "\n💡 Use `get_cached_job_from_webhook(page_id)` to get full details for a specific job."

            return [TextContent(type="text", text=result)]

        except httpx.HTTPError as e:
            return [TextContent(
                type="text",
                text=f"Error connecting to webhook service: {str(e)}\n\nMake sure the webhook service is running at {WEBHOOK_BASE_URL}"
            )]

    async def _get_cached_job(self, page_id: str) -> Sequence[TextContent]:
        """Get detailed job data from webhook cache"""
        try:
            response = await self.http_client.get(f"{WEBHOOK_BASE_URL}/cache/{page_id}")
            response.raise_for_status()
            data = response.json()

            if not data.get("success"):
                return [TextContent(
                    type="text",
                    text=f"Error: Job not found in cache. Page ID: {page_id}"
                )]

            job = data.get("job_entry", {})

            # Format job details
            result = f"# 📄 Job Application Details\n\n"

            # Company & Position
            company = job.get("company") or job.get("title") or "Unknown"
            position = job.get("position") or "N/A"
            result += f"**Company:** {company}\n"
            result += f"**Position:** {position}\n\n"

            # Location
            location = self._extract_location_from_raw(job.get("raw_properties", {}))
            if location:
                result += f"**Location:** {location}\n"

            # Status
            status = job.get("status")
            if status:
                result += f"**Status:** {status}\n"

            # URL
            url = job.get("url")
            if url:
                result += f"**URL:** {url}\n"

            result += "\n---\n\n"

            # Fit-Gap Analysis
            fit_gap = self._extract_fit_gap_from_raw(job.get("raw_properties", {}))
            if fit_gap:
                result += f"## 🎯 Fit-Gap Analysis\n\n{fit_gap}\n\n"

            # ATS Score
            ats_score = self._extract_ats_score_from_raw(job.get("raw_properties", {}))
            if ats_score:
                result += f"**ATS Score:** {ats_score}\n\n"

            # Work Type
            work_type = self._extract_work_type_from_raw(job.get("raw_properties", {}))
            if work_type:
                result += f"**Work Type:** {work_type}\n\n"

            # Salary
            salary = self._extract_salary_from_raw(job.get("raw_properties", {}))
            if salary:
                result += f"**Salary:** {salary}\n\n"

            # Description & Notes
            description = job.get("description")
            if description:
                result += f"## 📝 Description\n\n{description}\n\n"

            notes = job.get("notes")
            if notes:
                result += f"## 📌 Notes\n\n{notes}\n\n"

            # Dates
            raw_props = job.get("raw_properties", {})
            last_updated = raw_props.get("Last Updated", {}).get("date", {})
            if last_updated and last_updated.get("start"):
                result += f"**Last Updated:** {last_updated['start']}\n"

            applied_date = raw_props.get("Applied Date", {}).get("date", {})
            if applied_date and applied_date.get("start"):
                result += f"**Applied Date:** {applied_date['start']}\n"

            result += f"\n---\n**Page ID:** `{job.get('page_id')}`"

            return [TextContent(type="text", text=result)]

        except httpx.HTTPError as e:
            return [TextContent(
                type="text",
                text=f"Error connecting to webhook service: {str(e)}"
            )]

    async def _get_cache_stats(self) -> Sequence[TextContent]:
        """Get webhook cache statistics"""
        try:
            response = await self.http_client.get(f"{WEBHOOK_BASE_URL}/health")
            response.raise_for_status()
            data = response.json()

            stats = data.get("cache_stats", {})

            result = "## 📊 Webhook Cache Statistics\n\n"
            result += f"**Status:** {data.get('status', 'unknown')}\n"
            result += f"**Cached Jobs:** {stats.get('total_entries', 0)} / {stats.get('max_entries', 10)}\n"
            result += f"**TTL:** {stats.get('ttl_hours', 24)} hours\n"

            if stats.get('oldest_entry'):
                result += f"**Oldest Entry:** {stats['oldest_entry']}\n"
            if stats.get('newest_entry'):
                result += f"**Newest Entry:** {stats['newest_entry']}\n"

            result += f"\n**Webhook URL:** {WEBHOOK_BASE_URL}\n"

            return [TextContent(type="text", text=result)]

        except httpx.HTTPError as e:
            return [TextContent(
                type="text",
                text=f"Error connecting to webhook service: {str(e)}"
            )]

    # Helper methods to extract data from raw_properties

    def _extract_location_from_raw(self, raw_props: dict) -> str:
        """Extract location from raw properties"""
        location_prop = raw_props.get("Location", {})
        if location_prop.get("type") == "rich_text":
            rich_text = location_prop.get("rich_text", [])
            if rich_text:
                return "".join([t.get("plain_text", "") for t in rich_text])
        return ""

    def _extract_fit_gap_from_raw(self, raw_props: dict) -> str:
        """Extract fit-gap analysis from raw properties"""
        fit_gap_prop = raw_props.get("Fit-Gap Analysis", {})
        if fit_gap_prop.get("type") == "rich_text":
            rich_text = fit_gap_prop.get("rich_text", [])
            if rich_text:
                return "".join([t.get("plain_text", "") for t in rich_text])
        return ""

    def _extract_ats_score_from_raw(self, raw_props: dict) -> str:
        """Extract ATS score from raw properties"""
        ats_prop = raw_props.get("ATS Score", {})
        if ats_prop.get("type") == "number":
            score = ats_prop.get("number")
            if score is not None:
                return f"{score}%"
        return ""

    def _extract_work_type_from_raw(self, raw_props: dict) -> str:
        """Extract work type from raw properties"""
        work_type_prop = raw_props.get("Work Type", {})
        if work_type_prop.get("type") == "select":
            select = work_type_prop.get("select", {})
            return select.get("name", "")
        return ""

    def _extract_salary_from_raw(self, raw_props: dict) -> str:
        """Extract salary from raw properties"""
        salary_prop = raw_props.get("Salary", {})
        if salary_prop.get("type") == "rich_text":
            rich_text = salary_prop.get("rich_text", [])
            if rich_text:
                salary = "".join([t.get("plain_text", "") for t in rich_text])
                if salary.strip():
                    return salary
        return ""

    async def run(self):
        """Run the MCP server"""
        from mcp.server.stdio import stdio_server

        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                self.server.create_initialization_options()
            )

    async def cleanup(self):
        """Clean up resources"""
        await self.http_client.aclose()


async def main():
    """Main entry point"""
    server = NotionJobTrackerMCPServer()
    try:
        await server.run()
    finally:
        await server.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
