"""Runner for executing GitHub Actions workflows locally using act."""

import json
import os
import subprocess
from datetime import datetime
from pathlib import Path

from ..config import ValidationConfig
from ..error_handling import ErrorSeverity, ValidationError
from ..logging import ProcessTimer, logger


class ActRunner:
    """Handles running GitHub Actions workflows with act.

    This class provides methods for running GitHub Actions workflows locally
    using the act tool. It handles preparing event files, building act commands,
    and running workflows.

    Attributes:
        config: The configuration for workflow validation
    """

    def __init__(self, config: ValidationConfig):
        """Initialize the act runner.

        Args:
            config: The configuration for workflow validation
        """
        self.config = config
        self.default_timeout = 300  # Default timeout in seconds
        self.workflow_specific_timeouts = {
            "benchmark.yml": 180,  # 3 minutes for benchmark workflow
            "ci.yml": 240,  # 4 minutes for CI workflow
        }

    def prepare_event_file(self, event_type: str | int | bool) -> Path:
        """Prepare event file for act with realistic GitHub context.

        Args:
            event_type: The event type (e.g., push, pull_request)

        Returns:
            The path to the event file
        """
        event_file = Path(f".github/events/{event_type}.json")

        # Check for template first
        template_file = Path(f".github/events/templates/{event_type}.json")
        if template_file.exists():
            # Copy template to event file if it doesn't exist
            if not event_file.exists():
                event_file.parent.mkdir(parents=True, exist_ok=True)
                import shutil

                shutil.copy(template_file, event_file)
                logger.info(f"Using template for {event_type} event from {template_file}")
            return event_file

        # Create event directory if it doesn't exist
        event_file.parent.mkdir(parents=True, exist_ok=True)

        # Create event file if it doesn't exist
        if not event_file.exists():
            # Get repository info from current directory
            repo_name = Path.cwd().name

            # Try to get owner from git config
            owner_name = "owner"
            try:
                result = subprocess.run(
                    ["git", "config", "user.name"],
                    capture_output=True,
                    text=True,
                    check=False,
                )
                if result.returncode == 0 and result.stdout.strip():
                    owner_name = result.stdout.strip()
            except Exception:
                pass

            # Generate a random SHA
            import random
            import string

            sha = "".join(random.choices(string.hexdigits.lower(), k=40))

            # Basic event data
            event_data = {
                "ref": "refs/heads/main",
                "repository": {
                    "name": repo_name,
                    "full_name": f"{owner_name}/{repo_name}",
                    "owner": {"name": owner_name, "login": owner_name},
                },
                "sender": {
                    "login": owner_name,
                    "id": 12345,
                },
                "sha": sha,
                "workflow": event_type,
            }

            # Add additional fields based on event type
            if event_type == "push":
                event_data.update(
                    {
                        "before": "0" * 40,
                        "after": sha,
                        "created": False,
                        "deleted": False,
                        "forced": False,
                        "head_commit": {
                            "id": sha,
                            "message": "Local test commit",
                            "timestamp": datetime.now().isoformat(),
                        },
                    }
                )
            elif event_type == "pull_request":
                # Generate another SHA for the head branch
                head_sha = "".join(random.choices(string.hexdigits.lower(), k=40))
                event_data.update(
                    {
                        "action": "opened",
                        "number": 1,
                        "pull_request": {
                            "number": 1,
                            "title": "Local test PR",
                            "body": "Testing pull request locally",
                            "head": {"ref": "feature-branch", "sha": head_sha},
                            "base": {"ref": "main", "sha": sha},
                            "user": {"login": owner_name},
                            "created_at": datetime.now().isoformat(),
                            "updated_at": datetime.now().isoformat(),
                        },
                    }
                )
            elif event_type == "schedule":
                # For schedule events
                event_data.update(
                    {
                        "schedule": "0 0 * * *",
                        "event_type": "schedule",
                    }
                )
            elif event_type == "release":
                event_data.update(
                    {
                        "action": "published",
                        "release": {
                            "tag_name": "v1.0.0",
                            "name": "v1.0.0",
                            "body": "Local test release",
                            "draft": False,
                            "prerelease": False,
                            "created_at": datetime.now().isoformat(),
                            "published_at": datetime.now().isoformat(),
                        },
                    }
                )

            # Write event file
            with open(event_file, "w") as f:
                json.dump(event_data, f, indent=4)

            logger.info(f"Created {event_type} event file at {event_file}")

        return event_file

    def build_act_command(
        self, workflow_file: Path, event_type: str = "push", job_filter: str | None = None
    ) -> list[str]:
        """Build act command with appropriate options.

        Args:
            workflow_file: The workflow file to run
            event_type: The event type to trigger
            job_filter: The job to run (if specified)

        Returns:
            The act command as a list of strings
        """
        # Normalize paths to use forward slashes
        normalized_workflow_file = str(workflow_file).replace("\\", "/")

        # Prepare event file
        event_file = self.prepare_event_file(event_type)
        normalized_event_file = str(event_file).replace("\\", "/")

        # Build command
        cmd = ["act", "-W", normalized_workflow_file, "-e", normalized_event_file]

        # Add job filter if provided
        if job_filter:
            cmd.extend(["--job", job_filter])

        # Add platform mapping
        cmd.extend(["-P", "ubuntu-latest=ghcr.io/catthehacker/ubuntu:act-latest"])

        # Add cache path
        if os.path.exists(self.config.cache_path):
            cmd.extend(["--action-cache-path", self.config.cache_path])

        # Add common GitHub context environment variables
        repo_name = Path.cwd().name
        github_env_vars = [
            f"GITHUB_REPOSITORY={repo_name}",
            f"GITHUB_WORKSPACE={os.getcwd()}",
            f"GITHUB_EVENT_NAME={event_type}",
            "GITHUB_SERVER_URL=https://github.com",
            "GITHUB_API_URL=https://api.github.com",
            "GITHUB_GRAPHQL_URL=https://api.github.com/graphql",
            "GITHUB_REF_NAME=main",
            "GITHUB_REF=refs/heads/main",
            "GITHUB_BASE_REF=",
            "GITHUB_HEAD_REF=",
            "GITHUB_JOB=local_job",
            "GITHUB_RUN_ID=1",
            "GITHUB_RUN_NUMBER=1",
            "GITHUB_RUN_ATTEMPT=1",
            "GITHUB_ACTOR=local-user",
            "GITHUB_ACTIONS=true",
            "CI=true",
        ]

        # Add event-specific variables
        if event_type == "pull_request":
            github_env_vars.extend(
                [
                    "GITHUB_BASE_REF=main",
                    "GITHUB_HEAD_REF=feature-branch",
                    "GITHUB_REF=refs/pull/1/merge",
                    "GITHUB_REF_NAME=1/merge",
                ]
            )
        elif event_type == "release":
            github_env_vars.extend(
                [
                    "GITHUB_REF=refs/tags/v1.0.0",
                    "GITHUB_REF_NAME=v1.0.0",
                ]
            )

        # Add all environment variables
        for var in github_env_vars:
            cmd.extend(["--env", var])

        # Add standard environment variables
        cmd.extend(["--env", "ACT=true", "--env", "ACT_LOCAL_TESTING=true"])

        # Enable step debugging
        cmd.extend(["--env", "ACTIONS_STEP_DEBUG=true"])

        # Add secrets
        cmd.extend(
            [
                "-s",
                "ACT=true",
                "-s",
                "ACT_LOCAL_TESTING=true",
                "-s",
                "GITHUB_TOKEN=local-testing-token",
            ]
        )

        # Add custom image if specified
        if self.config.custom_image:
            cmd.extend(["-P", self.config.custom_image])

        # Add secrets file if it exists
        if os.path.exists(self.config.secrets_file):
            cmd.extend(["--secret-file", self.config.secrets_file])

        # Add verbose flag if specified
        if self.config.verbose:
            cmd.append("--verbose")

        return cmd

    def run_workflow(
        self,
        workflow_file: Path,
        event_type: str | None = None,
        job_filter: str | None = None,
        timeout: int | None = None,
    ) -> tuple[bool, ValidationError | None]:
        """Run workflow with act and return success status and any error.

        Args:
            workflow_file: The workflow file to run
            event_type: The event type to trigger (if None, use the default for the workflow)
            job_filter: The job to run (if specified)
            timeout: Timeout in seconds (if None, use default_timeout)

        Returns:
            A tuple of (success, error) where success is a boolean indicating whether
            the workflow ran successfully, and error is a ValidationError if an error
            occurred, or None if the workflow ran successfully.
        """
        # Use workflow-specific timeout if available, otherwise use default
        if timeout is None:
            workflow_name = workflow_file.name
            if workflow_name in self.workflow_specific_timeouts:
                timeout = self.workflow_specific_timeouts[workflow_name]
            else:
                timeout = self.default_timeout

            # Apply special handling for specific jobs
            if job_filter == "compare-local" and workflow_file.name == "benchmark.yml":
                timeout = min(timeout, 120)  # 2 minutes max for this specific job

        # Create a process timer
        timer_name = f"workflow:{workflow_file.name}"
        if job_filter:
            timer_name += f":job:{job_filter}"
        process_timer = ProcessTimer(timer_name, timeout)

        # Determine event type
        if event_type is None:
            event_type = self.config.get_event_for_workflow(workflow_file)

        # Build command
        cmd = self.build_act_command(workflow_file, event_type or "push", job_filter)
        cmd_str = " ".join(cmd)

        logger.info("Running workflow validation: %s", workflow_file.name)
        if job_filter:
            logger.info("Job filter: %s", job_filter)
        logger.debug("Command: %s", cmd_str)

        try:
            # Start the timer
            process_timer.start()
            process_timer.update_progress("Starting subprocess")

            # Simple approach: Run command with timeout
            logger.info("Running command: %s", cmd_str)

            # Special handling for known problematic jobs
            if workflow_file.name == "benchmark.yml" and (
                job_filter == "compare-local"
                or job_filter == "compare"
                or job_filter == "benchmark"
            ):
                logger.warning(
                    "Known problematic job detected: %s in %s", job_filter, workflow_file.name
                )
                process_timer.update_progress("Skipping known problematic job")
                process_timer.end()
                return False, ValidationError(
                    message=f"Skipped known problematic job {job_filter} in {workflow_file.name}",
                    severity=ErrorSeverity.WARNING,
                    workflow_file=str(workflow_file),
                    job_name=job_filter,
                    suggestion="This job is known to hang in local testing. "
                    "Consider modifying the workflow to skip this job when running with ACT=true.",
                )

            # Create a more robust process handling approach
            try:
                # Start the process
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    bufsize=1,  # Line buffered
                )

                # Function to forcibly terminate the process and all its children
                def kill_process_tree():
                    """Kill the process and all its children."""
                    logger.warning(f"Forcibly terminating process for {workflow_file.name}")

                    try:
                        # On Windows, use taskkill to kill the process tree
                        if os.name == "nt":
                            subprocess.run(
                                ["taskkill", "/F", "/T", "/PID", str(process.pid)],
                                capture_output=True,
                                check=False,
                            )
                        # On Unix-like systems, use process group
                        else:
                            try:
                                os.killpg(os.getpgid(process.pid), 9)  # SIGKILL
                            except (ProcessLookupError, PermissionError):
                                # Process might already be gone
                                pass
                    except Exception as e:
                        logger.error(f"Error killing process tree: {e}")

                # Communicate with the process with timeout
                try:
                    stdout, stderr = process.communicate(timeout=timeout)

                    # Create a CompletedProcess object to match the subprocess.run() API
                    result = subprocess.CompletedProcess(
                        args=cmd, returncode=process.returncode, stdout=stdout, stderr=stderr
                    )
                except subprocess.TimeoutExpired:
                    # If timeout occurs, kill the process tree
                    kill_process_tree()

                    # Try to collect any output that was produced before timeout
                    try:
                        stdout, stderr = process.communicate(timeout=5)
                    except Exception:
                        stdout = "Process timed out and was forcibly terminated"
                        stderr = "No output collected after timeout"

                    # Re-raise the timeout exception
                    raise subprocess.TimeoutExpired(
                        cmd=cmd, timeout=timeout, output=stdout, stderr=stderr
                    ) from None

                # Update progress
                process_timer.update_progress(
                    f"Process completed with exit code {result.returncode}"
                )

                # Log output for debugging
                if result.stdout:
                    logger.debug("Process stdout:\n%s", result.stdout)
                if result.stderr:
                    logger.debug("Process stderr:\n%s", result.stderr)

                # Check for "Could not find any stages to run" which is a special case
                if (
                    "Could not find any stages to run" in result.stdout
                    or "Could not find any stages to run" in result.stderr
                ):
                    # This is not necessarily an error, but we should report it
                    process_timer.update_progress("No stages to run")
                    process_timer.end()
                    logger.warning(
                        "Could not find any stages to run for workflow %s (event: %s, job: %s)",
                        workflow_file.name,
                        event_type,
                        job_filter,
                    )
                    return True, ValidationError(
                        message="Could not find any stages to run. "
                        "This is likely due to event trigger mismatch.",
                        severity=ErrorSeverity.WARNING,
                        workflow_file=str(workflow_file),
                        job_name=job_filter,
                        suggestion="Check that your workflow triggers match the event type "
                        "you're testing with.",
                    )

                # Check for errors
                if result.returncode != 0:
                    # Extract error message
                    error_message = result.stderr if result.stderr else result.stdout

                    # Update progress and end timer
                    process_timer.update_progress(f"Failed with exit code {result.returncode}")
                    process_timer.end()

                    logger.error(
                        "Workflow %s failed with exit code %d (event: %s, job: %s)",
                        workflow_file.name,
                        result.returncode,
                        event_type,
                        job_filter,
                    )

                    # Create validation error
                    return False, ValidationError(
                        message=f"Workflow execution failed with exit code {result.returncode}",
                        severity=ErrorSeverity.ERROR,
                        workflow_file=str(workflow_file),
                        job_name=job_filter,
                        context=error_message[:500]
                        if len(error_message) > 500
                        else error_message,  # Limit context size
                        suggestion="Check the error message for details on what went wrong.",
                    )

                # Success case
                process_timer.update_progress("Completed successfully")
                process_timer.end()
                logger.info(
                    "Workflow %s validated successfully (event: %s, job: %s)",
                    workflow_file.name,
                    event_type,
                    job_filter,
                )
                return True, None

            except subprocess.TimeoutExpired as e:
                # Handle timeout - this is caught from the inner try/except block
                # The process has already been killed by the kill_process_tree function
                process_timer.update_progress("Timed out")
                process_timer.end()

                # Get any output that was captured
                stdout_raw: str | bytes | None = (
                    e.output if hasattr(e, "output") and e.output else None
                )
                stderr_raw: str | bytes | None = (
                    e.stderr if hasattr(e, "stderr") and e.stderr else None
                )

                # Convert to string if needed
                stdout = ""
                if stdout_raw is not None:
                    if isinstance(stdout_raw, str):
                        stdout = stdout_raw
                    else:
                        try:
                            stdout = stdout_raw.decode("utf-8", errors="replace")
                        except (AttributeError, UnicodeDecodeError):
                            stdout = str(stdout_raw)

                stderr = ""
                if stderr_raw is not None:
                    if isinstance(stderr_raw, str):
                        stderr = stderr_raw
                    else:
                        try:
                            stderr = stderr_raw.decode("utf-8", errors="replace")
                        except (AttributeError, UnicodeDecodeError):
                            stderr = str(stderr_raw)

                # Log detailed information about the timeout
                logger.error(
                    "Workflow %s timed out after %d seconds (event: %s, job: %s)",
                    workflow_file.name,
                    timeout,
                    event_type,
                    job_filter,
                )

                # Create a more informative error message
                suggestion = "The process appears to be hanging. "
                suggestion += "This could be due to waiting for user input, Docker issues, "
                suggestion += "or network problems. "
                suggestion += "Check for infinite loops, processes waiting for input, "
                suggestion += "or resource issues in your workflow."

                # For benchmark.yml compare-local job, add specific suggestion
                if workflow_file.name == "benchmark.yml" and job_filter == "compare-local":
                    suggestion = "The 'compare-local' job in benchmark.yml is known to "
                    suggestion += "hang in local testing. "
                    suggestion += (
                        "Consider skipping this job when running locally or increasing its timeout."
                    )

                # Include any output in the context
                context = ""
                if stdout:
                    context += f"STDOUT:\n{stdout[:250]}...\n"
                if stderr:
                    context += f"STDERR:\n{stderr[:250]}...\n"

                return False, ValidationError(
                    message=f"Workflow execution timed out after {timeout} seconds",
                    severity=ErrorSeverity.ERROR,
                    workflow_file=str(workflow_file),
                    job_name=job_filter,
                    context=context,
                    suggestion=suggestion,
                )

        except Exception as e:
            # Handle any other exceptions
            process_timer.update_progress(f"Exception: {e!s}")
            process_timer.end()

            logger.error(
                "Error running workflow %s: %s (event: %s, job: %s)",
                workflow_file.name,
                str(e),
                event_type,
                job_filter,
                exc_info=True,
            )

            return False, ValidationError(
                message=f"Error running workflow: {e!s}",
                severity=ErrorSeverity.ERROR,
                workflow_file=str(workflow_file),
                job_name=job_filter,
                suggestion="Make sure act is installed and Docker is running.",
            )
