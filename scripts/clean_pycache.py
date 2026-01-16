import os
import shutil
from pathlib import Path


def clean_pycache(root: Path):
    removed_dirs = 0
    removed_files = 0

    for dirpath, dirnames, filenames in os.walk(root):
        # Remove __pycache__ directories
        if "__pycache__" in dirnames:
            pycache_path = Path(dirpath) / "__pycache__"
            shutil.rmtree(pycache_path, ignore_errors=True)
            removed_dirs += 1
            print(f"Removed directory: {pycache_path}")

        # Remove .pyc files
        for file in filenames:
            if file.endswith(".pyc"):
                pyc_file = Path(dirpath) / file
                try:
                    pyc_file.unlink()
                    removed_files += 1
                    print(f"Removed file: {pyc_file}")
                except Exception as e:
                    print(f"Failed to remove {pyc_file}: {e}")

    print("\nCleanup complete!")
    print(f"Total __pycache__ directories removed: {removed_dirs}")
    print(f"Total .pyc files removed: {removed_files}")


if __name__ == "__main__":
    repo_root = Path(".").resolve()
    print(f"Cleaning Python cache files from: {repo_root}\n")
    clean_pycache(repo_root)

# python3 scripts/clean_pycache.py
