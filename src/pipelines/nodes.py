import logging, time, re
from ddgs import DDGS
from langchain_core.prompts import PromptTemplate
from langchain_core.messages import HumanMessage

from src.clients.llm_client import llm_model
from src.llms.llm_parser import parse_response
from src.pipelines.pipeline_state import PipelineState
import src.prompts.prompts as prompts


logger = logging.getLogger(__name__)



SEARCH_PATTERN = re.compile(
    r"\b(current|now|today|latest|news|weather|price|stock|exchange rate|score|live|who is)\b",
    re.IGNORECASE,
)

SELF_PATTERN = re.compile(
    r"\b(who are you|what are you|tell me about you|what is your name|who is you)\b",
    re.IGNORECASE,
)


# async def select_tool_node(state: PipelineState):
#     if state["service_name"] == "web_search":
#         return state
#     else:
#         user_input = state["user_input"]
#         prompt = f"Does this query require real-time web search for an accurate answer? Query: {user_input}. Answer 'yes' or 'no'."
#         response = await llm_model.ainvoke(prompt)

#         state["service_name"] = "web_search" if "yes" in response.content.lower() else "chat"
#         logger.info(f"Selected service: {state['service_name']}")

#     return state


async def select_tool_node(state: PipelineState):
    # Early return if already routed
    if state.get("service_name") in {"web_search", "image_search", "news_search"}:
        return state

    user_input = state["user_input"]

    if SELF_PATTERN.search(user_input):
        state["service_name"] = "self"
        return state

    if SEARCH_PATTERN.search(user_input):
        state["service_name"] = "web_search"

    return state



async def chat_node(state: PipelineState):
    start_time = time.perf_counter()
    response = await llm_model.ainvoke(state["llm_messages"])
    end_time = time.perf_counter()

    parsed_response = parse_response(response)

    # with open("artifacts/response.txt", "a") as f:
    #     f.write(str(parsed_response))
    #     f.write("\n\n")
    
    state["llm_response"] = parsed_response.content
    state["response_time"] = round(end_time - start_time, 3)
    
    if parsed_response.response_metadata:
        state["input_tokens"] = parsed_response.response_metadata.get("input_tokens", 0)
        state["output_tokens"] = parsed_response.response_metadata.get("output_tokens", 0)

    return state



async def search_node(state: PipelineState):
    service_name = state.get("service_name")
    user_input = state["user_input"]
    
    try:
        start_time = time.perf_counter()
        links_section = ""
        prompt = None

        if service_name == "web_search":
            results = list(DDGS().text(query=user_input, region="in-en", max_results=5))
            if not results:
                logger.warning(f"No web search results found for query: {user_input}")
                response = await llm_model.ainvoke([HumanMessage(content=user_input)])
                parsed_response = parse_response(response)
                state["llm_response"] = parsed_response.content
                state["response_time"] = round(time.perf_counter() - start_time, 3)
                return state

            web_content = "\n\n".join([it.get("body", it.get("title", "")) for it in results if it.get("body") or it.get("title")])
            links = [it.get("href", it.get("url", "")) for it in results if it.get("href") or it.get("url")]
            if links:
                formatted_links = "\n".join([f"- {l}" for l in links if len(l) <= 300][:5])
                links_section = f"\n\n**Sources:**\n{formatted_links}"
            
            prompt = prompts.WEB_SEARCH_PROMPT.format(web_content=web_content, user_input=user_input)

        elif service_name == "image_search":
            results = DDGS().images(query=user_input, region="in-en", safesearch="off", timelimit="m", max_results=4)
            img_url = [i["image"] for i in results if "zhidao" not in i["image"].lower()]
            img_title = [i["title"] for i in results]
            thumbnail_url = [i["thumbnail"] for i in results]

            if img_url:
                formatted_links = "\n".join(f"- {l}" for l in img_url if len(l) <= 200)
                links_section = f"\n\n**Related Images Links:**\n{formatted_links}" if formatted_links else ""

            prompt = prompts.IMAGE_SEARCH_PROMPT.format(img_title=img_title, thumbnail_url=thumbnail_url, user_input=user_input)

        elif service_name == "news_search":
            results = DDGS().news(query=user_input, region="in-en", safesearch="off", timelimit="m", max_results=5)
            news_url = [i["url"] for i in results if "zhidao" not in i["url"].lower()]
            
            if news_url:
                formatted_links = "\n".join(f"- {l}" for l in news_url if len(l) <= 200)
                links_section = f"\n\n**Sources:**\n{formatted_links}" if formatted_links else ""

            prompt = prompts.NEWS_SEARCH_PROMPT.format(
                news_title=[i["title"] for i in results],
                image=[i["image"] for i in results],
                news_date=[i["date"] for i in results],
                news_source=[i["source"] for i in results],
                user_input=user_input
            )

        if prompt:
            response = await llm_model.ainvoke([HumanMessage(content=prompt)])
            end_time = time.perf_counter()
            parsed_response = parse_response(response)
            state["response_time"] = round(end_time - start_time, 3)
            
            if parsed_response.response_metadata:
                state["input_tokens"] = parsed_response.response_metadata.get("input_tokens", 0)
                state["output_tokens"] = parsed_response.response_metadata.get("output_tokens", 0)

            state["llm_response"] = parsed_response.content.strip() + links_section
            return state

    except Exception as e:
        logger.error(f"Search node failed for {service_name}: {e}")
        start_time = time.perf_counter()
        response = await llm_model.ainvoke([HumanMessage(content=user_input)])
        end_time = time.perf_counter()
        parsed_response = parse_response(response)
        state["llm_response"] = parsed_response.content 
        state["response_time"] = round(end_time - start_time, 3)
        return state

    return state




async def self_node(state: PipelineState):
       # Prompt
        prompt = prompts.SELF_PROMPT.format(user_input=state["user_input"])

        # Invoke the LLM
        start_time = time.perf_counter()
        response = await llm_model.ainvoke([HumanMessage(content=prompt)])
        end_time = time.perf_counter()
        
        parsed_response = parse_response(response)
        content = parsed_response.content
        state["response_time"] = round(end_time - start_time, 3)
        
        if parsed_response.response_metadata:
            state["input_tokens"] = parsed_response.response_metadata.get("input_tokens", 0)
            state["output_tokens"] = parsed_response.response_metadata.get("output_tokens", 0)

        # Store the final response in the state
        state["llm_response"] = content
        return state

