"""
Claude API client for processing job tracker entries
"""
import os
import logging
from typing import Optional
from anthropic import Anthropic

from .models import JobEntry

logger = logging.getLogger(__name__)


class ClaudeJobProcessor:
    """Client for processing job entries with Claude API"""

    DEFAULT_PROMPT_TEMPLATE = """I have a job application entry from my job tracker. Please help me analyze this opportunity and provide insights.

Job Details:
- Position: {position}
- Company: {company}
- Status: {status}
- Description: {description}
- Notes: {notes}
- URL: {url}

Please provide:
1. A brief analysis of this opportunity
2. Key points to research about the company
3. Suggested talking points or questions for an interview
4. Any red flags or concerns to be aware of
5. Recommended next steps

Be concise but thorough in your analysis."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None
    ):
        """
        Initialize Claude client

        Args:
            api_key: Anthropic API key (defaults to env var)
            model: Claude model to use (defaults to env var or latest)
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.model = model or os.getenv("CLAUDE_MODEL", "claude-sonnet-4-5-20250929")

        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY must be provided or set in environment")

        self.client = Anthropic(api_key=self.api_key)
        logger.info(f"Claude client initialized with model: {self.model}")

    def format_job_entry(self, job_entry: JobEntry) -> str:
        """
        Format job entry data into a readable string

        Args:
            job_entry: JobEntry object

        Returns:
            Formatted string
        """
        return f"""
Title: {job_entry.title}
Company: {job_entry.company or 'N/A'}
Position: {job_entry.position or 'N/A'}
Status: {job_entry.status or 'N/A'}
Description: {job_entry.description or 'N/A'}
Notes: {job_entry.notes or 'N/A'}
URL: {job_entry.url or 'N/A'}
""".strip()

    def create_prompt(
        self,
        job_entry: JobEntry,
        template: Optional[str] = None
    ) -> str:
        """
        Create a prompt from job entry using template

        Args:
            job_entry: JobEntry object
            template: Custom prompt template (uses default if None)

        Returns:
            Formatted prompt string
        """
        template = template or self.DEFAULT_PROMPT_TEMPLATE

        return template.format(
            title=job_entry.title,
            company=job_entry.company or "Not specified",
            position=job_entry.position or "Not specified",
            status=job_entry.status or "Not specified",
            description=job_entry.description or "Not specified",
            notes=job_entry.notes or "Not specified",
            url=job_entry.url or "Not specified"
        )

    def process_job_entry(
        self,
        job_entry: JobEntry,
        prompt_template: Optional[str] = None,
        max_tokens: int = 4096
    ) -> str:
        """
        Process a job entry with Claude API

        Args:
            job_entry: JobEntry object to process
            prompt_template: Custom prompt template (optional)
            max_tokens: Maximum tokens for response

        Returns:
            Claude's response text
        """
        try:
            prompt = self.create_prompt(job_entry, prompt_template)

            logger.info(f"Sending job entry to Claude: {job_entry.page_id}")
            logger.debug(f"Prompt: {prompt}")

            message = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )

            response_text = message.content[0].text
            logger.info(f"Received response from Claude for page: {job_entry.page_id}")
            logger.debug(f"Response length: {len(response_text)} characters")

            return response_text

        except Exception as e:
            logger.error(f"Error processing job entry with Claude: {e}")
            raise
