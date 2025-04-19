"""Tests for the caching module."""

import os
import time
from unittest import mock

import pytest
from conda_forge_converter.caching import PackageMetadataCache


class TestPackageMetadataCache:
    """Tests for the PackageMetadataCache class."""

    @pytest.fixture()
    def temp_cache_dir(self, tmp_path):
        """Create a temporary cache directory."""
        cache_dir = tmp_path / "cache"
        cache_dir.mkdir()
        return cache_dir

    @pytest.fixture()
    def cache(self, temp_cache_dir):
        """Create a PackageMetadataCache instance with a temporary cache directory."""
        return PackageMetadataCache(cache_dir=temp_cache_dir)

    def test_init(self, temp_cache_dir):
        """Test initializing the cache."""
        cache = PackageMetadataCache(cache_dir=temp_cache_dir)
        assert cache.cache_dir == temp_cache_dir
        assert cache.repodata_cache.exists()
        assert cache.package_info_cache.exists()

    def test_repodata_cache(self, cache):
        """Test caching repository data."""
        # Test with non-existent cache
        assert cache.get_repodata("conda-forge") is None

        # Test setting and getting cache
        test_data = {"packages": {"numpy-1.20.0": {"version": "1.20.0"}}}
        cache.set_repodata("conda-forge", test_data)
        cached_data = cache.get_repodata("conda-forge")
        assert cached_data == test_data

    def test_package_info_cache(self, cache):
        """Test caching package information."""
        # Test with non-existent cache
        assert cache.get_package_info("numpy") is None

        # Test setting and getting cache
        test_data = {"version": "1.20.0", "depends": ["python >=3.7"]}
        cache.set_package_info("numpy", test_data)
        cached_data = cache.get_package_info("numpy")
        assert cached_data == test_data

    def test_cache_expiration(self, cache, temp_cache_dir):
        """Test cache expiration."""
        # Create a cache file
        test_data = {"version": "1.20.0"}
        cache.set_package_info("numpy", test_data)

        # Modify the file time to make it appear older
        cache_file = temp_cache_dir / "package_info" / "conda-forge_numpy.json"
        old_time = time.time() - (25 * 3600)  # 25 hours ago
        os.utime(cache_file, (old_time, old_time))

        # Cache should be expired (default max_age_hours is 24)
        assert cache.get_package_info("numpy") is None

    def test_clear_cache(self, cache):
        """Test clearing the cache."""
        # Create some cache files
        cache.set_repodata("conda-forge", {"packages": {}})
        cache.set_package_info("numpy", {"version": "1.20.0"})
        cache.set_package_info("pandas", {"version": "1.3.0"})

        # Clear the cache
        count = cache.clear_cache()
        assert count == 3
        assert cache.get_repodata("conda-forge") is None
        assert cache.get_package_info("numpy") is None
        assert cache.get_package_info("pandas") is None

    def test_clear_cache_with_age(self, cache, temp_cache_dir):
        """Test clearing the cache with age filter."""
        # Create some cache files
        cache.set_repodata("conda-forge", {"packages": {}})
        cache.set_package_info("numpy", {"version": "1.20.0"})
        cache.set_package_info("pandas", {"version": "1.3.0"})

        # Make one file appear older
        cache_file = temp_cache_dir / "package_info" / "conda-forge_numpy.json"
        old_time = time.time() - (25 * 3600)  # 25 hours ago
        os.utime(cache_file, (old_time, old_time))

        # Clear cache files older than 12 hours
        count = cache.clear_cache(older_than_hours=12)
        assert count == 1
        assert cache.get_repodata("conda-forge") is not None
        assert cache.get_package_info("numpy") is None
        assert cache.get_package_info("pandas") is not None

    @mock.patch("conda_forge_converter.caching.logger")
    def test_cache_error_handling(self, mock_logger, cache, temp_cache_dir):
        """Test error handling in cache operations."""
        # Test error when reading cache
        cache_file = temp_cache_dir / "repodata" / "conda-forge.json"
        cache_file.write_text("invalid json")
        assert cache.get_repodata("conda-forge") is None
        mock_logger.warning.assert_called_once()
        mock_logger.warning.reset_mock()

        # Test error when writing cache
        with mock.patch("pathlib.Path.open", side_effect=PermissionError("Permission denied")):
            cache.set_repodata("conda-forge", {"packages": {}})
            mock_logger.warning.assert_called_once()
