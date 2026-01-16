import tomllib
from pathlib import Path


PYPROJECT_FILE = Path("pyproject.toml")
OUTPUT_FILE = Path("artifacts/requirements.txt")


def load_dependencies(pyproject_path: Path):
    with open(pyproject_path, "rb") as f:
        data = tomllib.load(f)

    deps = []

    # PEP 621 style
    if "project" in data and "dependencies" in data["project"]:
        deps.extend(data["project"]["dependencies"])

    # Poetry style
    if "tool" in data and "poetry" in data["tool"]:
        poetry = data["tool"]["poetry"]
        if "dependencies" in poetry:
            for name, spec in poetry["dependencies"].items():
                if name.lower() == "python":
                    continue
                if isinstance(spec, str):
                    deps.append(f"{name}{spec}")
                elif isinstance(spec, dict):
                    version = spec.get("version", "")
                    deps.append(f"{name}{version}")

    return deps


def main():
    if not PYPROJECT_FILE.exists():
        print("❌ pyproject.toml not found")
        return

    deps = load_dependencies(PYPROJECT_FILE)

    if not deps:
        print("⚠️ No dependencies found in pyproject.toml")
        return

    with open(OUTPUT_FILE, "w") as f:
        for dep in deps:
            f.write(dep + "\n")

    print(f"requirements.txt generated successfully → {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
