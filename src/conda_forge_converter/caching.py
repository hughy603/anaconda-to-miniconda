"""Caching functionality for conda-forge-converter."""

import json
import time
from pathlib import Path

from .utils import logger


class PackageMetadataCache:
    """Cache for package metadata to speed up repeated operations."""

    def __init__(self, cache_dir: Path | None = None):
        """Initialize the cache.

        Args:
            cache_dir: Directory to store cache files. Defaults to ~/.conda_forge_converter/cache.
        """
        self.cache_dir = cache_dir or Path.home() / ".conda_forge_converter" / "cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.repodata_cache = self.cache_dir / "repodata"
        self.repodata_cache.mkdir(exist_ok=True)
        self.package_info_cache = self.cache_dir / "package_info"
        self.package_info_cache.mkdir(exist_ok=True)
        logger.debug(f"Initialized package metadata cache at {self.cache_dir}")

    def get_repodata(self, channel: str) -> dict | None:
        """Get cached repository data for a channel.

        Args:
            channel: The conda channel name

        Returns:
            The cached repository data or None if not cached or expired
        """
        cache_file = self.repodata_cache / f"{channel}.json"
        if cache_file.exists() and self._is_cache_valid(cache_file):
            try:
                with cache_file.open() as f:
                    data = json.load(f)
                    logger.debug(f"Using cached repodata for channel {channel}")
                    return data
            except Exception as e:
                logger.warning(f"Error reading cache file {cache_file}: {e!s}")
                return None
        return None

    def set_repodata(self, channel: str, data: dict) -> None:
        """Cache repository data for a channel.

        Args:
            channel: The conda channel name
            data: The repository data to cache
        """
        cache_file = self.repodata_cache / f"{channel}.json"
        try:
            with cache_file.open("w") as f:
                json.dump(data, f)
            self._update_cache_timestamp(cache_file)
            logger.debug(f"Cached repodata for channel {channel}")
        except Exception as e:
            logger.warning(f"Error writing cache file {cache_file}: {e!s}")

    def get_package_info(self, package_name: str, channel: str = "conda-forge") -> dict | None:
        """Get cached package information.

        Args:
            package_name: The name of the package
            channel: The conda channel name

        Returns:
            The cached package information or None if not cached or expired
        """
        cache_file = self.package_info_cache / f"{channel}_{package_name}.json"
        if cache_file.exists() and self._is_cache_valid(cache_file):
            try:
                with cache_file.open() as f:
                    data = json.load(f)
                    logger.debug(f"Using cached package info for {package_name} from {channel}")
                    return data
            except Exception as e:
                logger.warning(f"Error reading cache file {cache_file}: {e!s}")
                return None
        return None

    def set_package_info(self, package_name: str, data: dict, channel: str = "conda-forge") -> None:
        """Cache package information.

        Args:
            package_name: The name of the package
            data: The package information to cache
            channel: The conda channel name
        """
        cache_file = self.package_info_cache / f"{channel}_{package_name}.json"
        try:
            with cache_file.open("w") as f:
                json.dump(data, f)
            self._update_cache_timestamp(cache_file)
            logger.debug(f"Cached package info for {package_name} from {channel}")
        except Exception as e:
            logger.warning(f"Error writing cache file {cache_file}: {e!s}")

    def clear_cache(self, older_than_hours: int | None = None) -> int:
        """Clear the cache.

        Args:
            older_than_hours: Only clear cache files older than this many hours.
                If None, clear all cache files.

        Returns:
            Number of cache files removed
        """
        count = 0
        for cache_dir in [self.repodata_cache, self.package_info_cache]:
            for cache_file in cache_dir.glob("*.json"):
                if older_than_hours is None or not self._is_cache_valid(
                    cache_file, older_than_hours
                ):
                    try:
                        cache_file.unlink()
                        count += 1
                    except Exception as e:
                        logger.warning(f"Error removing cache file {cache_file}: {e!s}")
        logger.info(f"Cleared {count} cache files")
        return count

    def _is_cache_valid(self, cache_file: Path, max_age_hours: int = 24) -> bool:
        """Check if cache is still valid based on age.

        Args:
            cache_file: Path to the cache file
            max_age_hours: Maximum age in hours for the cache to be considered valid

        Returns:
            True if the cache is valid, False otherwise
        """
        if not cache_file.exists():
            return False

        # Check if cache is older than max_age_hours
        mtime = cache_file.stat().st_mtime
        age = time.time() - mtime
        return age < (max_age_hours * 3600)

    def _update_cache_timestamp(self, cache_file: Path) -> None:
        """Update the cache timestamp.

        Args:
            cache_file: Path to the cache file
        """
        cache_file.touch()
