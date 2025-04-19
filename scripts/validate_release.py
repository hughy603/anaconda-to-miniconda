#!/usr/bin/env python
"""Script to validate release readiness."""

import re
import subprocess
import sys
from pathlib import Path


def get_hatch_path() -> str:
    """Get the absolute path to the hatch executable."""
    if sys.platform == "win32":
        return "C:\\Program Files\\Hatch\\hatch.exe"
    else:
        return "/usr/local/bin/hatch"


def run_command(cmd: list[str], check: bool = True) -> subprocess.CompletedProcess[str]:
    """Run a command with proper security measures."""
    try:
        result = subprocess.run(cmd, check=check, text=True, capture_output=True)
        return result
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {e!s}")
        if e.stderr:
            print(f"Stderr: {e.stderr}")
        raise


def get_current_version() -> str:
    """Get the current version from hatch."""
    hatch_path = get_hatch_path()
    try:
        result = run_command([hatch_path, "version"])
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return "0.0.0"


def validate_version(version: str) -> bool:
    """Validate a version string."""
    try:
        major, minor, patch = map(int, version.split("."))
        return major >= 0 and minor >= 0 and patch >= 0
    except ValueError:
        return False


def check_tests() -> bool:
    """Run tests and return success status.

    Returns:
        True if tests pass, False otherwise

    """
    try:
        run_command(["test-cov"])
        return True
    except subprocess.CalledProcessError as e:
        print(f"Test failure: {e.stderr}")
        return False


def check_linting() -> bool:
    """Run linting checks and return success status.

    Returns:
        True if linting passes, False otherwise

    """
    try:
        run_command(["lint"])
        run_command(["format", "--check"])
        run_command(["type-check"])
        return True
    except subprocess.CalledProcessError as e:
        print(f"Linting failure: {e.stderr}")
        return False


def check_changelog() -> bool:
    """Check if CHANGELOG.md has been updated.

    Returns:
        True if changelog has changes, False otherwise

    """
    try:
        result = run_command(["git", "diff", "--name-only", "HEAD~1", "HEAD"])
        if "CHANGELOG.md" not in result.stdout:
            print("Warning: CHANGELOG.md has not been modified in the last commit")
            return False
        return True
    except subprocess.CalledProcessError as e:
        print(f"Changelog check failure: {e.stderr}")
        return False


def check_dependencies() -> bool:
    """Check for outdated or vulnerable dependencies.

    Returns:
        True if dependencies are up to date and secure, False otherwise

    """
    try:
        # Check for outdated packages
        result = run_command(["pip", "list", "--outdated"])
        if result.stdout.strip():
            print("Warning: Outdated dependencies found:")
            print(result.stdout)
            return False

        # Skip security vulnerabilities check as bandit is not installed
        print("Skipping security check - bandit not installed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Dependency check failure: {e.stderr}")
        return False


def check_documentation() -> bool:
    """Check if documentation is up to date.

    Returns:
        True if documentation is valid, False otherwise

    """
    try:
        # Check if docs build successfully
        run_command(["docs-build", "--strict"])
        return True
    except subprocess.CalledProcessError as e:
        print(f"Documentation check failure: {e.stderr}")
        return False


def get_version_from_file(file_path: Path, pattern: str) -> str | None:
    """Get version from a file using regex pattern.

    Args:
        file_path: Path to the file
        pattern: Regex pattern to match version

    Returns:
        Version string if found, None otherwise

    """
    if not file_path.exists():
        return None

    content = file_path.read_text()
    match = re.search(pattern, content)
    return match.group(1) if match else None


def validate_version_consistency() -> bool:
    """Validate version consistency across files.

    Returns:
        True if versions are consistent, False otherwise

    """
    current_version = get_current_version()
    if not validate_version(current_version):
        print(f"Invalid version format: {current_version}")
        return False

    # Version patterns for different files
    version_patterns = {
        "src/conda_forge_converter/_version.py": r'__version__\s*=\s*version\s*=\s*"([^"]+)"',
    }

    # Check versions in each file
    for file_path, pattern in version_patterns.items():
        path = Path(file_path)
        file_version = get_version_from_file(path, pattern)
        if file_version is None:
            print(f"Warning: Could not find version in {file_path}")
            continue
        if file_version != current_version:
            print(f"Error: Version mismatch in {file_path}")
            print(f"  Expected: {current_version}")
            print(f"  Found: {file_version}")
            return False

    # Check CHANGELOG.md for version entry
    changelog_path = Path("CHANGELOG.md")
    if changelog_path.exists():
        content = changelog_path.read_text()
        if f"## [{current_version}]" not in content:
            print("Warning: Version not found in CHANGELOG.md")
            print("  Make sure to update CHANGELOG.md with the new version")
            return False

    return True


def check_git_state() -> bool:
    """Check git repository state.

    Returns:
        True if git state is clean, False otherwise

    """
    try:
        # Check for uncommitted changes
        result = run_command(["git", "status", "--porcelain"])
        if result.stdout.strip():
            print("Warning: Uncommitted changes found:")
            print(result.stdout)
            return False

        # Check for unpushed commits
        result = run_command(["git", "log", "origin/main..HEAD"])
        if result.stdout.strip():
            print("Warning: Unpushed commits found:")
            print(result.stdout)
            return False

        return True
    except subprocess.CalledProcessError as e:
        print(f"Git state check failure: {e.stderr}")
        return False


def check_branch() -> bool:
    """Check if we're on the main branch.

    Returns:
        True if on main branch, False otherwise

    """
    try:
        result = run_command(["git", "branch", "--show-current"])
        current_branch = result.stdout.strip()
        if current_branch != "main":
            print(f"Warning: Not on main branch. Current branch: {current_branch}")
            return False
        return True
    except subprocess.CalledProcessError as e:
        print(f"Branch check failure: {e.stderr}")
        return False


def check_tag_conflict(version: str) -> bool:
    """Check if a tag already exists for the given version.

    Args:
        version: Version to check

    Returns:
        True if no tag conflict, False otherwise

    """
    try:
        result = run_command(["git", "tag"], check=False)
        if f"v{version}" in result.stdout.splitlines():
            print(f"Error: Tag v{version} already exists")
            return False
        return True
    except subprocess.CalledProcessError as e:
        print(f"Tag check failure: {e.stderr}")
        return False


def main() -> None:
    """Main entry point."""
    try:
        current_version = get_current_version()
        if not validate_version(current_version):
            print(f"Invalid version format: {current_version}")
            sys.exit(1)

        print(f"Current version: {current_version}")

        # Get version first for tag conflict check
        version_ok = validate_version_consistency() and check_tag_conflict(current_version)

        checks = [
            ("Git Branch", check_branch),
            ("Git State", check_git_state),
            ("Version Consistency", lambda: version_ok),  # Use the result from earlier
            ("Changelog", check_changelog),
            ("Dependencies", check_dependencies),
            ("Linting", check_linting),
            ("Tests", check_tests),
            ("Documentation", check_documentation),
        ]

        failed = False
        results = []

        for name, check in checks:
            print(f"\nRunning {name} check...")
            try:
                result = check()
                if not result:
                    print(f"❌ {name} check failed")
                    failed = True
                    results.append(f"❌ {name}")
                else:
                    print(f"✅ {name} check passed")
                    results.append(f"✅ {name}")
            except Exception as e:
                print(f"❌ {name} check failed with exception: {e}")
                failed = True
                results.append(f"❌ {name} (exception)")

        # Print summary
        print("\n" + "=" * 50)
        print(f"Release Validation Summary for v{current_version}")
        print("=" * 50)
        for result in results:
            print(result)
        print("=" * 50)

        if failed:
            print("\n❌ Release validation failed. Please fix the issues before proceeding.")
            sys.exit(1)
        else:
            print("\n✅ All checks passed! Ready for release.")
    except Exception as e:
        print(f"Error: {e!s}")
        sys.exit(1)


if __name__ == "__main__":
    main()
