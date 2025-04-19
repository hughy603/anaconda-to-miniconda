"""Configuration management for GitHub Actions validation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Self

from pydantic import BaseModel, Field


class ValidationConfig(BaseModel):
    """Configuration for GitHub Actions workflow validation."""

    changed_only: bool = Field(False, description="Only validate workflows that have changed")
    verbose: bool = Field(False, description="Enable verbose output")
    dry_run: bool = Field(False, description="List workflows without running them")
    skip_lint: bool = Field(False, description="Skip actionlint validation")
    default_event: str = Field("push", description="Default event type")
    secrets_file: str = Field(".github/local-secrets.json", description="Path to secrets file")
    cache_path: str = Field("./.act-cache", description="Path to cache directory")
    custom_image: str = Field("", description="Custom Docker image to use")
    job_timeout: int = Field(300, description="Timeout in seconds for each job")
    validation_timeout: int = Field(
        1800, description="Timeout in seconds for the entire validation"
    )
    workflow_file: str = Field("", description="Specific workflow file to validate")
    workflow_events: dict[str, str] = Field(
        default_factory=lambda: {
            "ci.yml": "push",
            "docs.yml": "push",
            "release.yml": "push",
            "benchmark.yml": "push",
            "maintenance.yml": "schedule",
            "security-scan.yml": "push",
            "validate-workflows.yml": "pull_request",
            "*": "push",
        },
        description="Mapping of workflow files to event types",
    )

    # Pydantic configuration for ValidationConfig
    model_config = {
        "extra": "ignore",
    }

    @classmethod
    def from_file(cls, path: str | None = None) -> Self:
        """Load configuration from a file."""
        if not path:
            default_paths = [
                Path.cwd() / ".github-actions-validator.json",
                Path.home() / ".config" / "github-actions-validator.json",
            ]
            for p in default_paths:
                if p.exists():
                    path = str(p)
                    break

        if path and Path(path).exists():
            try:
                with open(path) as f:
                    settings_dict = json.load(f)
                return cls(**settings_dict)
            except json.JSONDecodeError as e:
                print(f"Warning: Could not parse {path} as JSON: {e}")

        return cls(
            changed_only=False,
            verbose=False,
            dry_run=False,
            skip_lint=False,
            default_event="push",
            secrets_file=".github/local-secrets.json",
            cache_path="./.act-cache",
            custom_image="",
            job_timeout=300,
            validation_timeout=1800,
            workflow_file="",
        )

    @classmethod
    def from_env(cls) -> Self:
        """Load configuration from environment variables."""
        return cls(
            changed_only=False,
            verbose=False,
            dry_run=False,
            skip_lint=False,
            default_event="push",
            secrets_file=".github/local-secrets.json",
            cache_path="./.act-cache",
            custom_image="",
            job_timeout=300,
            validation_timeout=1800,
            workflow_file="",
        )

    @classmethod
    def create(cls, config_file: str | None = None, **overrides: object) -> Self:
        """Create a configuration with precedence: CLI args > env vars > config file > defaults."""
        config = cls.from_file(config_file)

        env_config = cls.from_env()
        # Create a default instance for comparison
        default_instance = cls(
            changed_only=False,
            verbose=False,
            dry_run=False,
            skip_lint=False,
            default_event="push",
            secrets_file=".github/local-secrets.json",
            cache_path="./.act-cache",
            custom_image="",
            job_timeout=300,
            validation_timeout=1800,
            workflow_file="",
        )

        for field in ValidationConfig.model_fields:
            env_value = getattr(env_config, field)
            default_value = getattr(default_instance, field)
            if env_value != default_value:
                setattr(config, field, env_value)

        for key, value in overrides.items():
            if value is not None and hasattr(config, key):
                setattr(config, key, value)

        return config

    def get_event_for_workflow(self, workflow_file: Path) -> str:
        """Get the event type for a workflow file.

        Args:
            workflow_file: The workflow file

        Returns:
            The event type to use for the workflow
        """
        # Get event type from workflow events mapping
        return self.workflow_events.get(
            workflow_file.name, self.workflow_events.get("*", self.default_event)
        )
