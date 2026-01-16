
import argparse
from pathlib import Path
from src.pipelines.builder import pipeline

from langchain_core.runnables.graph import MermaidDrawMethod


FIG_DIR = Path("artifacts")
FIG_DIR.mkdir(exist_ok=True)


def main(args):
    # Tag each pipeline with its app
    PIPELINES = [
        ("main", pipeline, "main_pipeline"),
    ]

    # Select based on CLI arg
    selected = [
        (p, name)
        for app, p, name in PIPELINES
        if args.app == "both" or args.app == app
    ]

    # Unzip into your original variables
    pipelines, pipeline_names = zip(*selected)

    for p, name in zip(pipelines, pipeline_names):
        pipeline_graph = p.get_graph().draw_mermaid_png(
            draw_method=MermaidDrawMethod.API,
            background_color="white",
            padding=8
        )
        with open(FIG_DIR / f"{name}.png", "wb") as f:
            f.write(pipeline_graph)
            print(f"{name}.png is created")



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate pipeline graphs")
    parser.add_argument(
        "--app",
        choices=["main", "both"],
        default="both",
        help="Which app pipelines to generate (default: both)"
    )
    args = parser.parse_args()

    # Run main
    main(args)


    # python generate_pipeline_graphs.py --app main
    # python generate_pipeline_graphs.py --app both




