import logging, time
from ddgs import DDGS
from langchain_core.prompts import PromptTemplate
from langchain_core.messages import HumanMessage

from src.clients.llm_client import llm_model
from src.llms.llm_parser import parse_response
from src.pipelines.pipeline_state import PipelineState

logger = logging.getLogger(__name__)


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
    if state["service_name"] == "web_search":
        return state
    else:
        user_input = state["user_input"].lower()
        
        # Keywords that suggest a need for real-time information
        search_keywords = [
            "current", "now", "today", "latest", "news", "weather", 
            "price", "stock", "exchange rate", "score", "live",
            "who is"
        ]

        self_inquery = ["who are you", "what are you", "tell me about you", "what is your name", "who is you"]
        
        # Check if any keyword is in the user input
        if any(keyword in user_input for keyword in search_keywords):
            state["service_name"] = "web_search"
        
        if any(keyword in user_input for keyword in self_inquery):
            state["service_name"] = "self"
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
        
        parsed_response = parse_response(response)
        content = parsed_response.content
        state["response_time"] = round(end_time - start_time, 3)
        
        if parsed_response.response_metadata:
            state["input_tokens"] = parsed_response.response_metadata.get("input_tokens", 0)
            state["output_tokens"] = parsed_response.response_metadata.get("output_tokens", 0)

        # Combine response and links
        final_response = content.strip() + links_section

        # Store the final response in the state
        state["llm_response"] = final_response
        return state

    except Exception as e:
        logger.error(f"Failed to fetch web search results: {e}")
        response = await llm_model.ainvoke([HumanMessage(content=state["user_input"])])
        parsed_response = parse_response(response)
        state["llm_response"] = parsed_response.content 
        return state



async def self_node(state: PipelineState):
       # Prompt template
        prompt = PromptTemplate.from_template("""
You are SannaAI, a smart, friendly, and professional AI assistant developed by Akash Gaur.

Your role is to respond ONLY to self-inquiry type questions such as:
- "who are you"
- "what are you"
- "tell me about you"
- "what is your name"
- "who is you"

When answering:
- Clearly introduce yourself as **SannaAI**.
- Mention that you are an AI assistant created to help with coding, writing, analysis, and problem-solving.
- Keep your tone warm, confident, and intelligent.
- Do not answer unrelated or general questions. If the question is outside self-inquiry, politely say that this prompt is only for identity-related questions.

Example style:
"I am SannaAI, a powerful AI assistant developed by Akash Gaur. I’m designed to help you with coding, writing, analysis, and smart problem-solving."

User Question:
{user_input}
""")

        # Format the prompt
        prompt = prompt.format(user_input=state["user_input"])

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

