from langgraph.constants import END, START
from langgraph.graph import StateGraph

from src.pipelines.nodes import chat_node, search_node, select_tool_node, self_node
from src.pipelines.pipeline_state import PipelineState

# create state graph
builder = StateGraph(PipelineState)

# add nodes
builder.add_node("select_tool_node", select_tool_node)
builder.add_node("chat_node", chat_node)
builder.add_node("search_node", search_node)
builder.add_node("self_node_", self_node)

# add edges
builder.add_edge(START, "select_tool_node")
builder.add_conditional_edges("select_tool_node",
    lambda state: state["service_name"],
    {
        "self": "self_node_",
        "chat": "chat_node",
        "web_search": "search_node",
        "thinking": "chat_node",
        "image_search": "search_node",
        "news_search": "search_node"
    }
)

builder.add_edge("self_node_", END)
builder.add_edge("chat_node", END)
builder.add_edge("search_node", END)

# build pipeline
pipeline = builder.compile()

