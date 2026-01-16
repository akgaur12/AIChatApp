from src.pipelines.builder import pipeline


PIPELINES = [
    ("main", pipeline, "main_pipeline"),
]


def summarize_pipeline(pipeline, name):
    g = pipeline.get_graph()

    # LangChain graph exposes nodes and edges internally
    # Usually available as:
    nodes = len(g.nodes)
    edges = len(g.edges)

    complexity = nodes + edges

    return {
        "name": name,
        "nodes": nodes,
        "edges": edges,
        "complexity": complexity,
    }


def main():
    print("\nPIPELINE SUMMARY")
    print("=" * 60)
    print(f"{'Pipeline':30} {'Nodes':>8} {'Edges':>8} {'Complexity':>12}")
    print("-" * 60)

    for _, pipeline, name in PIPELINES:
        try:
            stats = summarize_pipeline(pipeline, name)
            print(
                f"{stats['name']:30} "
                f"{stats['nodes']:8} "
                f"{stats['edges']:8} "
                f"{stats['complexity']:12}"
            )
        except Exception as e:
            print(f"{name:30} ERROR: {e}")

    print("=" * 60)
    print("\nComplexity = Nodes + Edges (simple structural metric)")


if __name__ == "__main__":
    main()
