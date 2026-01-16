"""
Usage:
    uv pip install ruff black isort mypy
    python3 scripts/lint_project.py

Runs all linters one by one:
    ruff → fast static analysis
    black --check → formatting validation
    isort --check-only → import order
    mypy → type checking
"""


import subprocess
import sys
from datetime import datetime
from pathlib import Path

# Output file
REPORT_FILE = Path("artifacts/lint_report.txt")
REPORT_FILE.parent.mkdir(exist_ok=True)

# Linters you want to run
LINTERS = {
    "ruff": ["ruff", "check", "."],
    "black": ["black", "--check", "."],
    "isort": ["isort", "--check-only", "."],
    "mypy": ["mypy", "."],
}


def write_report(text: str):
    with open(REPORT_FILE, "a") as f:
        f.write(text + "\n")


def run_linter(name, command):
    print(f"\nRunning {name}...")
    write_report(f"\nRunning {name}...")
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False
        )
        success = result.returncode == 0

        if success:
            msg = f"✅ {name} passed"
            print(msg)
            write_report(msg)
        else:
            msg = f"❌ {name} failed"
            print(msg)
            write_report(msg)

            if result.stdout:
                print(result.stdout)
                write_report("\nSTDOUT:\n" + result.stdout)

            if result.stderr:
                print(result.stderr)
                write_report("\nSTDERR:\n" + result.stderr)

        return success

    except FileNotFoundError:
        msg = f"⚠️  {name} is not installed"
        print(msg)
        write_report(msg)
        return None


def main():
    # Start fresh report
    with open(REPORT_FILE, "w") as f:
        header = f"LINT REPORT - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        f.write(header + "\n" + "=" * len(header) + "\n")

    print("Starting project linting...")
    write_report("Starting project linting...")

    results = {}

    for name, command in LINTERS.items():
        results[name] = run_linter(name, command)

    print("\n" + "=" * 40)
    write_report("\n" + "=" * 40)
    print("LINT SUMMARY")
    write_report("LINT SUMMARY")
    print("=" * 40)
    write_report("=" * 40)

    all_passed = True

    for name, status in results.items():
        if status is True:
            line = f"{name:10} : ✅ Passed"
        elif status is False:
            line = f"{name:10} : ❌ Failed"
            all_passed = False
        else:
            line = f"{name:10} : ⚠️  Not Installed"
            all_passed = False

        print(line)
        write_report(line)

    print("=" * 40)
    write_report("=" * 40)

    if not all_passed:
        msg = "\nLinting failed. Fix issues before proceeding."
        print(msg)
        write_report(msg)
        sys.exit(1)
    else:
        msg = "\nAll linters passed successfully!"
        print(msg)
        write_report(msg)


if __name__ == "__main__":
    main()
