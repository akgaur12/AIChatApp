import subprocess
import argparse
from pathlib import Path

ARTIFACTS_DIR = Path("artifacts")
ARTIFACTS_DIR.mkdir(exist_ok=True)

DEFAULT_OUTPUT_FILE = ARTIFACTS_DIR / "project_tree.txt"
DEFAULT_IGNORE_PATTERN = "*.pyc|__pycache__"


def main():
    parser = argparse.ArgumentParser(
        description="Generate a directory tree and save it to a file"
    )
    parser.add_argument(
        "-o", "--output",
        default=DEFAULT_OUTPUT_FILE,
        help="Output file name (default: project_tree.txt)"
    )
    parser.add_argument(
        "-i", "--ignore",
        default=DEFAULT_IGNORE_PATTERN,
        help='Ignore pattern for tree (default: "*.pyc|__pycache__")'
    )
    parser.add_argument(
        "-a", "--all",
        action="store_true",
        help="Include hidden files (-a flag for tree)"
    )
    parser.add_argument(
        "-L", "--level",
        type=int,
        help="Limit directory depth (tree -L)"
    )

    args = parser.parse_args()

    # Build the tree command dynamically
    command = ["tree"]

    if args.all:
        command.append("-a")

    if args.level:
        command.extend(["-L", str(args.level)])

    command.extend(["-I", args.ignore])

    # Run and write output
    with open(args.output, "w") as f:
        subprocess.run(command, stdout=f, stderr=subprocess.PIPE, text=True)

    print(f"Tree saved to {args.output}")
    print(f"Command used: {' '.join(command)}")


if __name__ == "__main__":
    main()

# Default (same as your original):
# python3 generate_tree.py

# Custom output file:
# python3 generate_tree.py -o my_tree.txt

# Ignore more things:
# python3 generate_tree.py -i "*.pyc|__pycache__|.venv|venv|env|.env*"

# Include hidden files:
# python3 generate_tree.py -a

# Limit depth: 
# python3 generate_tree.py -L 4