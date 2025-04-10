"""Test version import."""

from conda_forge_converter import __version__


def test_version():
    """Test that version is a string."""
    assert isinstance(__version__, str)
    assert __version__ != ""
