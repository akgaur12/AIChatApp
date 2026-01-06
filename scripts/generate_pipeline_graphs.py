from src.pipelines.builder import pipeline

from langchain_core.runnables.graph import MermaidDrawMethod
from pathlib import Path


FIG_DIR = Path("reports")
FIG_DIR.mkdir(exist_ok=True)

pipeline_names = ["main_pipeline"]
pipelines = [pipeline]

for p, name in zip(pipelines, pipeline_names):
    pipeline_graph = p.get_graph().draw_mermaid_png(
        draw_method=MermaidDrawMethod.API,
        background_color="white",
        padding=8
    )
    with open(FIG_DIR / f"{name}.png", "wb") as f:
        f.write(pipeline_graph)
        print(f"{name}.png is created")


