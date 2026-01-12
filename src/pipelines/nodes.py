import logging, time
from ddgs import DDGS
from langchain_core.prompts import PromptTemplate
from langchain_core.messages import HumanMessage

from src.services.models import llm_model
from src.pipelines.pipeline_state import PipelineState

logger = logging.getLogger(__name__)


async def chat_node(state: PipelineState):
    response = await llm_model.ainvoke(state["llm_messages"])
    state["llm_response"] = response.content if hasattr(response, "content") else str(response) 
    return state


async def web_search_node(state: PipelineState):
    try: 
        web_search_result = DDGS().text(query=state["user_input"], region="in-en", max_results=5)

        # Extract body and links safely
        web_content = [item["body"] for item in web_search_result if "body" in item]
        links = [item["href"] for item in web_search_result if "href" in item]

        # Remove links containing "zhidao"
        links = [l for l in links if "zhidao" not in l.lower()]

        # Format links nicely with length check
        if links:
            filtered_links = [link for link in links if len(link) <= 200]
            if filtered_links:
                formatted_links = "\n".join(f"- {link}" for link in filtered_links)
                links_section = f"\n\n**Related Links:**\n{formatted_links}"
            else:
                links_section = ""
        else:
            links_section = ""

        # Prompt template
        prompt = PromptTemplate.from_template("""
        You are a helpful assistant that can answer questions based on the following web content:
        {web_content}

        Answer the following question:
        {user_input}
        """)

        # Format the prompt
        prompt = prompt.format(web_content=web_content, user_input=state["user_input"])

        # Invoke the LLM
        start_time = time.perf_counter()
        response = await llm_model.ainvoke([HumanMessage(content=prompt)])
        end_time = time.perf_counter()
        
        content = response.content if hasattr(response, "content") else str(response)
        state["response_time"] = round(end_time - start_time, 3)
        
        if hasattr(response, "usage_metadata") and response.usage_metadata:
            state["input_tokens"] = response.usage_metadata.get("input_tokens", 0)
            state["output_tokens"] = response.usage_metadata.get("output_tokens", 0)

        # Combine response and links
        final_response = content.strip() + links_section

        # Store the final response in the state
        state["llm_response"] = final_response
        return state

    except Exception as e:
        logger.error(f"Failed to fetch web search results: {e}")
        response = await llm_model.ainvoke([HumanMessage(content=state["user_input"])])
        state["llm_response"] = response.content if hasattr(response, "content") else str(response) 
        return state


