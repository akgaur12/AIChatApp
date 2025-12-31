from langgraph.graph import StateGraph
from langgraph.constants import END, START

from src.pipelines.nodes import chat_node, web_search_node
from src.pipelines.pipeline_state import PipelineState

# create state graph
builder = StateGraph(PipelineState)

# add nodes
builder.add_node("chat_node", chat_node)
builder.add_node("web_search_node", web_search_node)

# add edges
builder.add_conditional_edges(START,
    lambda state: state["service_name"],
    {
        "chat": "chat_node",
        "web_search": "web_search_node"
    }
)

builder.add_edge("chat_node", END)
builder.add_edge("web_search_node", END)

# build pipeline
pipeline = builder.compile()

