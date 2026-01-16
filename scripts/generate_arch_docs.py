from pathlib import Path
from datetime import datetime
import subprocess


ARTIFACTS_DIR = Path("artifacts")
ARTIFACTS_DIR.mkdir(exist_ok=True)

TREE_FILE = ARTIFACTS_DIR / "project_tree.txt"
ARCH_DOC = ARTIFACTS_DIR / "ARCHITECTURE.md"
PIPELINE_DIR = ARTIFACTS_DIR  # where your pipeline PNGs already go


IGNORE_PATTERN = "*.pyc|__pycache__|.venv|venv|env|.env*"


def generate_tree():
    print("Generating project tree...")
    with open(TREE_FILE, "w") as f:
        subprocess.run(
            ["tree", "-I", IGNORE_PATTERN],
            stdout=f,
            stderr=subprocess.PIPE,
            text=True,
        )


def collect_pipeline_graphs():
    print("Collecting pipeline graphs...")
    images = sorted(PIPELINE_DIR.glob("*.png"))
    return images


def generate_metadata():
    return {
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "repo": Path(".").resolve().name,
        "author": "Akash Gaur",
    }


def build_arch_doc(tree_text: str, images: list[Path], metadata: dict):
    lines = []

    # Header
    lines.append("# Architecture Documentation\n")
    lines.append("## Metadata")
    lines.append(f"- Repository: `{metadata['repo']}`")
    lines.append(f"- Generated at: `{metadata['generated_at']}`")
    lines.append(f"- Author: `{metadata['author']}`")
    lines.append("\n---\n")

    # Tree
    lines.append("## Project Structure")
    lines.append("```text")
    lines.append(tree_text)
    lines.append("```")
    lines.append("\n---\n")

    # Pipelines
    lines.append("## Pipeline Graphs\n")
    if not images:
        lines.append("_No pipeline graphs found._\n")
    else:
        for img in images:
            lines.append(f"### {img.stem}")
            lines.append(f"![{img.stem}]({img.name})\n")

    return "\n".join(lines)


def main():
    generate_tree()

    tree_text = TREE_FILE.read_text()
    images = collect_pipeline_graphs()
    metadata = generate_metadata()

    doc = build_arch_doc(tree_text, images, metadata)

    ARCH_DOC.write_text(doc)
    print(f"Architecture documentation generated: {ARCH_DOC}")


if __name__ == "__main__":
    main()
