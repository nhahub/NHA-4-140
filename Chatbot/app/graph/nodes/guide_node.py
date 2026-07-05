from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.runnables import RunnableConfig
from app.graph.state import CarsChatState
from app.data.website_guide import format_website_guide


TOPIC_DETECT_SYSTEM = """Classify the user's website help question into one of these topics:
post_ad | filter_search | save_car | compare | contact_seller |
delete_ad | edit_ad | view_favorites | account_settings | other

Respond with ONLY the topic string.
User message: "{message}"
"""

GUIDE_SYSTEM = """You are a friendly website guide for a car marketplace.
Help the user with their question about how to use the website.

Website features reference:
{website_guide}

Detected topic: {detected_topic}
User message: "{message}"

Answer helpfully and concisely. If the question is about a feature not listed
above, be honest that you are not sure and suggest they contact support.
Always respond in the same language as the user (Arabic or English).
"""


async def guide_node(state: CarsChatState, config: RunnableConfig) -> dict:
    llm_router = config["configurable"].get("llm_router")
    llm_fast = config["configurable"]["llm_fast"]
    llm_stream = config["configurable"]["llm_stream"]

    last_message = state["messages"][-1].content if state.get("messages") else ""

    # Step 1: Topic detection
    topic_msgs = [
        SystemMessage(content=TOPIC_DETECT_SYSTEM.format(message=last_message)),
        HumanMessage(content=last_message),
    ]
    if llm_router:
        topic_response = await llm_router.ainvoke_task("guide_topic", topic_msgs)
    else:
        topic_response = await llm_fast.ainvoke(topic_msgs)
    detected_topic = topic_response.content.strip().lower() if topic_response.content else "other"

    # Step 2: Guide response (streaming)
    streamed_text = ""
    response_msgs = [
        SystemMessage(content=GUIDE_SYSTEM.format(
            detected_topic=detected_topic,
            message=last_message,
            website_guide=format_website_guide(),
        )),
        HumanMessage(content=last_message),
    ]
    if llm_router:
        async for chunk in llm_router.astream_task("guide", response_msgs):
            content = chunk.content if hasattr(chunk, "content") else str(chunk)
            streamed_text += content
    else:
        async for chunk in llm_stream.astream(response_msgs):
            content = chunk.content if hasattr(chunk, "content") else str(chunk)
            streamed_text += content

    return {
        "node_response": streamed_text,
    }
