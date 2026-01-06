import importlib.util
import os
import sys
import json
import argparse
import pkgutil
from pathlib import Path
import importlib.metadata as md
from tqdm import tqdm


REPORT_DIR = Path("reports") # artifacts, reports, 
REPORT_DIR.mkdir(exist_ok=True)

OUTPUT_TEXT_FILE = REPORT_DIR / "package_sizes.txt"
OUTPUT_JSON_FILE = REPORT_DIR / "package_sizes.json"


def get_package_folder(package_name: str):
    """Return the folder path where the package is installed."""
    try:
        spec = importlib.util.find_spec(package_name)
        if spec is None or spec.origin is None:
            return None

        if spec.submodule_search_locations:
            return list(spec.submodule_search_locations)[0]

        return os.path.dirname(spec.origin)
    except Exception:
        return None


def get_folder_size_mb(folder: str) -> float:
    """Calculate folder size in MB."""
    total = 0
    for root, _, files in os.walk(folder):
        for f in files:
            try:
                total += os.path.getsize(os.path.join(root, f))
            except FileNotFoundError:
                continue
    return total / (1024 * 1024)


def is_stdlib_module(name: str) -> bool:
    """Check if package is part of stdlib."""
    try:
        spec = importlib.util.find_spec(name)
        return spec and "site-packages" not in (spec.origin or "")
    except Exception:
        return False


def list_installed_packages():
    """Return list of top-level installed packages."""
    return sorted({mod.name for mod in pkgutil.iter_modules()})


def main():
    parser = argparse.ArgumentParser(description="Check installed Python package sizes.")
    parser.add_argument("--sort", choices=["size", "name"], default="name")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--exclude-stdlib", action="store_true")
    parser.add_argument("--only-big", type=float, default=0)
    args = parser.parse_args()

    packages = list_installed_packages()
    results = []
    total_size = 0.0

    # --- Progress Bar ---
    print(f"Scanning {len(packages)} packages...")
    for pkg in tqdm(packages, desc="Processing", ncols=80):
        if args.exclude_stdlib and is_stdlib_module(pkg):
            continue

        folder = get_package_folder(pkg)
        if not folder:
            continue

        size_mb = get_folder_size_mb(folder)
        if size_mb < args.only_big:
            continue

        try:
            version = md.version(pkg)
        except md.PackageNotFoundError:
            version = "unknown"

        total_size += size_mb

        results.append({
            "package": pkg,
            "version": version,
            "size_mb": round(size_mb, 2),
            "path": folder
        })

    # Sorting
    if args.sort == "size":
        results.sort(key=lambda x: x["size_mb"], reverse=True)
    else:
        results.sort(key=lambda x: x["package"].lower())

    # Save text output
    out_path = Path(OUTPUT_TEXT_FILE)
    with out_path.open("w") as f:
        f.write(f"{'Package Name':25s} {'Version':15s} {'Size (MB)':10s}\n")
        f.write("-" * 60 + "\n")

        for r in results:
            f.write(f"{r['package']:25s} {r['version']:15s} {r['size_mb']:10.2f}\n")

        f.write("\nTOTAL SIZE: {:.2f} MB\n".format(total_size))

    print(f"\nText report saved → {OUTPUT_TEXT_FILE}")

    # Save JSON output
    if args.json:
        json_path = Path(OUTPUT_JSON_FILE)
        json_path.write_text(json.dumps({
            "total_size_mb": round(total_size, 2),
            "packages": results
        }, indent=4))
        print(f"JSON report saved → {OUTPUT_JSON_FILE}")


if __name__ == "__main__":
    main()

    # python3 scripts/check_package_sizes.py --sort size
    # python3 scripts/check_package_sizes.py --json
    # python3 scripts/check_package_sizes.py --exclude-stdlib
    # python3 scripts/check_package_sizes.py --only-big 10
    # python3 scripts/check_package_sizes.py --sort size --json --exclude-stdlib --only-big 5




