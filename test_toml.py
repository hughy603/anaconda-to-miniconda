#!/usr/bin/env python3
"""Test script for toml module."""

try:
    import toml

    print("toml module imported successfully!")
    print(f"toml module: {toml}")
except ImportError as e:
    print(f"Error importing toml: {e}")
