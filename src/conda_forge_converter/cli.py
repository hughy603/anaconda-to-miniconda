"""Command-line interface for the conda-forge-converter package."""

import argparse
import os
import sys
from typing import Sequence

from .core import (
    convert_environment,
    convert_multiple_environments,
    environment_exists,
    is_conda_environment,
    list_all_conda_environments
)
from .utils import logger, setup_logging, PathLike


def parse_args(args: Sequence[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments.
    
    Args:
        args: Command-line arguments to parse. If None, sys.argv[1:] is used.
        
    Returns:
        Parsed arguments as a Namespace object.
    """
    parser = argparse.ArgumentParser(
        description="Convert Anaconda environments to conda-forge environments",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    # Single environment options
    parser.add_argument("-s", "--source-env", help="Name of the source Anaconda environment")
    parser.add_argument("-t", "--target-env", help="Name for the new conda-forge environment")
    
    # Batch conversion options
    parser.add_argument("--batch", action="store_true", help="Convert multiple environments")
    parser.add_argument("--pattern", help="Pattern for matching environment names (e.g., 'data*')")
    parser.add_argument("--exclude", help="Comma-separated list of environments to exclude")
    parser.add_argument("--target-suffix", default="_forge", 
                      help="Suffix to add to target environment names in batch mode (default: _forge)")
    
    # Environment search paths
    parser.add_argument("--search-path", action="append", metavar="PATH",
                      help="Path to search for conda environments (can be specified multiple times)")
    parser.add_argument("--search-depth", type=int, default=3,
                      help="Maximum directory depth when searching for environments (default: 3)")
    
    # Performance and resource options
    parser.add_argument("--max-parallel", type=int, default=1, 
                      help="Maximum number of parallel conversions (default: 1)")
    parser.add_argument("--no-backup", action="store_true", 
                      help="Skip backing up environment specifications")
    
    # Python version
    parser.add_argument("--python", help="Specify Python version for the new environment")
    
    # Output control
    parser.add_argument("--dry-run", action="store_true", 
                      help="Show what would be installed without creating environments")
    parser.add_argument("--verbose", "-v", action="store_true", 
                      help="Show detailed output of conda commands")
    parser.add_argument("--log-file", 
                      help="Path to log file for detailed logging")
    
    return parser.parse_args(args)


def main(args: Sequence[str] | None = None) -> int:
    """Main entry point for the command-line interface.
    
    Args:
        args: Command-line arguments to parse. If None, sys.argv[1:] is used.
        
    Returns:
        Exit code (0 for success, 1 for failure)
    """
    parsed_args = parse_args(args)
    
    # Setup logging with global logger
    setup_logging(parsed_args.log_file, parsed_args.verbose)
    
    if parsed_args.batch:
        # Batch mode - convert multiple environments
        success = convert_multiple_environments(
            parsed_args.pattern,
            parsed_args.target_suffix,
            parsed_args.dry_run,
            parsed_args.verbose,
            parsed_args.exclude,
            parsed_args.max_parallel,
            not parsed_args.no_backup,
            parsed_args.search_path
        )
    else:
        # Single environment mode
        if not parsed_args.source_env:
            logger.error("In single environment mode, --source-env is required")
            return 1
        
        # Check if the source environment exists or is a path
        env_dict = list_all_conda_environments(
            search_paths=parsed_args.search_path, 
            verbose=parsed_args.verbose
        )
        
        env_path: PathLike | None = None
        if parsed_args.source_env in env_dict:
            env_path = env_dict[parsed_args.source_env]
            if parsed_args.verbose:
                logger.debug(f"Found source environment: {parsed_args.source_env} at {env_path}")
        elif os.path.isdir(parsed_args.source_env) and is_conda_environment(parsed_args.source_env):
            # If the source_env is a path and is a conda environment
            env_path = parsed_args.source_env
            parsed_args.source_env = os.path.basename(parsed_args.source_env)
            if parsed_args.verbose:
                logger.debug(f"Using environment at path: {env_path}")
        elif parsed_args.search_path:
            logger.error(f"Environment '{parsed_args.source_env}' not found in registered environments or search paths")
            return 1
        
        success = convert_environment(
            parsed_args.source_env,
            parsed_args.target_env,
            parsed_args.python,
            parsed_args.dry_run,
            parsed_args.verbose,
            env_path
        )
    
    return 0 if success or parsed_args.dry_run else 1


if __name__ == "__main__":
    sys.exit(main())
