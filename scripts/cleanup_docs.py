#!/usr/bin/env python
"""Script to clean up duplicate documentation directories."""
import os
import shutil
from pathlib import Path

def main():
    docs_dir = Path("docs")
    
    # Directories to keep and their duplicates
    keep_dirs = {
        "user": ["user-guide", "guide"],
        "dev": ["contributing"],
        "user/getting-started.md": ["getting-started"],
    }
    
    # Move files from duplicate directories to their proper locations
    for keep, duplicates in keep_dirs.items():
        keep_path = docs_dir / keep
        for duplicate in duplicates:
            duplicate_path = docs_dir / duplicate
            if duplicate_path.exists():
                if keep_path.is_file():
                    # If keeping a file, move the duplicate directory's contents
                    for item in duplicate_path.iterdir():
                        if item.is_file():
                            shutil.move(str(item), str(keep_path.parent))
                        elif item.is_dir():
                            shutil.move(str(item), str(keep_path.parent))
                else:
                    # If keeping a directory, move contents into it
                    for item in duplicate_path.iterdir():
                        if item.is_file():
                            shutil.move(str(item), str(keep_path))
                        elif item.is_dir():
                            shutil.move(str(item), str(keep_path))
                # Remove the duplicate directory
                shutil.rmtree(duplicate_path)
                print(f"Moved contents from {duplicate} to {keep}")

if __name__ == "__main__":
    main() 