"""
Cache manager for storing job entries from Notion
Implements time-based (24h TTL) and count-based (max 10 jobs) eviction
"""
import json
import logging
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
from .models import JobEntry

logger = logging.getLogger(__name__)


class CachedJob:
    """Represents a cached job entry with metadata"""

    def __init__(self, job_entry: JobEntry, cached_at: Optional[datetime] = None):
        self.job_entry = job_entry
        self.cached_at = cached_at or datetime.utcnow()

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            "job_entry": self.job_entry.model_dump(),
            "cached_at": self.cached_at.isoformat()
        }

    @classmethod
    def from_dict(cls, data: dict) -> "CachedJob":
        """Create from dictionary"""
        job_entry = JobEntry(**data["job_entry"])
        cached_at = datetime.fromisoformat(data["cached_at"])
        return cls(job_entry=job_entry, cached_at=cached_at)

    def is_expired(self, ttl_hours: int = 24) -> bool:
        """Check if cache entry is expired"""
        expiry_time = self.cached_at + timedelta(hours=ttl_hours)
        return datetime.utcnow() > expiry_time


class JobCacheManager:
    """Manages job entry cache with TTL and size limits"""

    def __init__(
        self,
        cache_dir: str = "webhook/cache",
        max_entries: int = 10,
        ttl_hours: int = 24
    ):
        """
        Initialize cache manager

        Args:
            cache_dir: Directory to store cache files
            max_entries: Maximum number of cached entries
            ttl_hours: Time-to-live for cache entries in hours
        """
        self.cache_dir = Path(cache_dir)
        self.cache_file = self.cache_dir / "jobs.json"
        self.max_entries = max_entries
        self.ttl_hours = ttl_hours

        # Create cache directory if it doesn't exist
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Initialize cache
        self._cache: Dict[str, CachedJob] = {}
        self._load_cache()

        logger.info(f"Cache manager initialized: {self.cache_dir}, max={max_entries}, ttl={ttl_hours}h")

    def _load_cache(self):
        """Load cache from disk"""
        if not self.cache_file.exists():
            logger.info("No existing cache file found, starting fresh")
            return

        try:
            with open(self.cache_file, 'r') as f:
                data = json.load(f)

            self._cache = {
                page_id: CachedJob.from_dict(cached_job)
                for page_id, cached_job in data.items()
            }

            logger.info(f"Loaded {len(self._cache)} entries from cache")

            # Clean expired entries on load
            self._clean_expired()

        except Exception as e:
            logger.error(f"Error loading cache: {e}")
            self._cache = {}

    def _save_cache(self):
        """Save cache to disk"""
        try:
            data = {
                page_id: cached_job.to_dict()
                for page_id, cached_job in self._cache.items()
            }

            with open(self.cache_file, 'w') as f:
                json.dump(data, f, indent=2)

            logger.debug(f"Saved {len(self._cache)} entries to cache")

        except Exception as e:
            logger.error(f"Error saving cache: {e}")

    def _clean_expired(self):
        """Remove expired entries from cache"""
        expired = [
            page_id for page_id, cached_job in self._cache.items()
            if cached_job.is_expired(self.ttl_hours)
        ]

        for page_id in expired:
            del self._cache[page_id]
            logger.info(f"Removed expired entry: {page_id}")

        if expired:
            self._save_cache()

    def _enforce_size_limit(self):
        """Enforce maximum cache size by removing oldest entries"""
        if len(self._cache) <= self.max_entries:
            return

        # Sort by cached_at time (oldest first)
        sorted_entries = sorted(
            self._cache.items(),
            key=lambda x: x[1].cached_at
        )

        # Remove oldest entries until we're under the limit
        to_remove = len(self._cache) - self.max_entries
        for page_id, _ in sorted_entries[:to_remove]:
            del self._cache[page_id]
            logger.info(f"Removed oldest entry to enforce size limit: {page_id}")

        self._save_cache()

    def add(self, job_entry: JobEntry) -> bool:
        """
        Add or update a job entry in cache

        Args:
            job_entry: JobEntry to cache

        Returns:
            True if successfully cached
        """
        try:
            # Clean expired entries first
            self._clean_expired()

            # Add or update entry
            cached_job = CachedJob(job_entry)
            self._cache[job_entry.page_id] = cached_job

            logger.info(f"Cached job entry: {job_entry.page_id} ({job_entry.title})")

            # Enforce size limit
            self._enforce_size_limit()

            # Save to disk
            self._save_cache()

            return True

        except Exception as e:
            logger.error(f"Error adding to cache: {e}")
            return False

    def get(self, page_id: str) -> Optional[JobEntry]:
        """
        Get a job entry from cache

        Args:
            page_id: Notion page ID

        Returns:
            JobEntry if found and not expired, None otherwise
        """
        # Clean expired entries
        self._clean_expired()

        cached_job = self._cache.get(page_id)

        if not cached_job:
            logger.debug(f"Cache miss for: {page_id}")
            return None

        if cached_job.is_expired(self.ttl_hours):
            logger.info(f"Cache hit but expired: {page_id}")
            del self._cache[page_id]
            self._save_cache()
            return None

        logger.debug(f"Cache hit for: {page_id}")
        return cached_job.job_entry

    def list_all(self) -> List[Dict]:
        """
        List all cached job entries with metadata

        Returns:
            List of dictionaries with job entry and cache metadata
        """
        # Clean expired entries
        self._clean_expired()

        result = []
        for page_id, cached_job in self._cache.items():
            result.append({
                "page_id": page_id,
                "title": cached_job.job_entry.title,
                "company": cached_job.job_entry.company,
                "cached_at": cached_job.cached_at.isoformat(),
                "expires_at": (cached_job.cached_at + timedelta(hours=self.ttl_hours)).isoformat()
            })

        # Sort by cached_at (newest first)
        result.sort(key=lambda x: x["cached_at"], reverse=True)

        return result

    def clear(self) -> int:
        """
        Clear all cached entries

        Returns:
            Number of entries removed
        """
        count = len(self._cache)
        self._cache = {}
        self._save_cache()

        logger.info(f"Cleared {count} entries from cache")
        return count

    def delete(self, page_id: str) -> bool:
        """
        Delete a specific entry from cache

        Args:
            page_id: Notion page ID

        Returns:
            True if entry was found and deleted
        """
        if page_id in self._cache:
            del self._cache[page_id]
            self._save_cache()
            logger.info(f"Deleted cache entry: {page_id}")
            return True

        logger.debug(f"Cache entry not found for deletion: {page_id}")
        return False

    def stats(self) -> Dict:
        """
        Get cache statistics

        Returns:
            Dictionary with cache stats
        """
        self._clean_expired()

        if not self._cache:
            return {
                "total_entries": 0,
                "max_entries": self.max_entries,
                "ttl_hours": self.ttl_hours,
                "oldest_entry": None,
                "newest_entry": None
            }

        cached_times = [cached_job.cached_at for cached_job in self._cache.values()]

        return {
            "total_entries": len(self._cache),
            "max_entries": self.max_entries,
            "ttl_hours": self.ttl_hours,
            "oldest_entry": min(cached_times).isoformat(),
            "newest_entry": max(cached_times).isoformat()
        }
