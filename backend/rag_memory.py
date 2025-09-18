# Import necessary libraries and set up
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.graph import MessagesState, StateGraph
from langchain_core.tools import tool
from langchain_core.messages import SystemMessage
from langgraph.prebuilt import ToolNode
from langchain import hub
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone
from langchain_openai import OpenAIEmbeddings
from langchain_openai import ChatOpenAI
from langchain.chains import RetrievalQA
import os
import dotenv
from openai import OpenAI

dotenv.load_dotenv()

# Initialize LLM, embeddings, Pinecone, and vector store
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)
llm = ChatOpenAI(model="gpt-5-mini")
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index = pc.Index("connect-chatbot-mq-1")
memory = MemorySaver()

vector_store = PineconeVectorStore(embedding=embeddings, index=index)
retriever = vector_store.as_retriever(search_type="similarity_score_threshold", search_kwargs={"score_threshold": 0.6, "k": 3})
graph_builder = StateGraph(MessagesState)


@tool(response_format="content_and_artifact")
def retrieve(query: str):
    """Retrieve relevant documents from the vector store."""
    docs = retriever.invoke(query)
    serialized = "\n\n".join(
        f"Source: {doc.metadata}\nContent: {doc.page_content}"
        for doc in docs
    )
    return serialized, docs


def query_or_respond(state: MessagesState):
    """Generate tool call for retrieval or response"""
    llm_with_tools = llm.bind_tools([retrieve])
    response = llm_with_tools.invoke(state['messages'], tool_choice="required")
    return {"messages": [response]}


# Retrieve node
tools = ToolNode([retrieve])

# Generate a response with retrieved docs


def generate(state: MessagesState):
    """ Generate answer """
    # Retrieve all tool messages
    recent_tool_messages = []
    for message in reversed(state['messages']):
        if message.type == "tool":
            recent_tool_messages.append(message)
        else:
            break
    tool_messages = recent_tool_messages[::-1]

    # Format into prompt
    docs_content = "\n\n".join(doc.content for doc in tool_messages)
    system_message_content = f"""
    You are a helpful assistant that helps students find information about Macquarie University. 
    Only answer questions related to Macquarie University and basic greetings. Disregard any **question** not related to Macquarie University and reply with "I'm sorry, I can only answer questions related to Macquarie University.".
    Try to use the following context and link the context to answer the question.
    Try to keep your answer concise and to the point, and provide relevant contact information if applicable.
    Only provide the source of your information in the format "Source: " at the end of your answer if the question is related to the context (Example: If it is basic greeting or a question not related to Macquarie University, do not provide any source).
    Do not recommend further actions such as "If you want, if you'd like, ...'. Simply, the user asks, you answer.
    Here is the context: {docs_content}"""
    conversation_messages = [
        message
        for message in state["messages"]
        if message.type in ("human", "system")
        or (message.type == "ai" and not message.tool_calls)
    ]

    prompt = [SystemMessage(system_message_content)] + conversation_messages

    # Run
    response = llm.invoke(prompt)
    return {"messages": [response]}


graph_builder.add_node(query_or_respond)
graph_builder.add_node(tools)
graph_builder.add_node(generate)

graph_builder.set_entry_point("query_or_respond")
graph_builder.add_conditional_edges(
    "query_or_respond",
    tools_condition,
    {END: END, "tools": "tools"},
)
graph_builder.add_edge("tools", "generate")
graph_builder.add_edge("generate", END)

graph = graph_builder.compile(checkpointer=memory)
config = {"configurable": {"thread_id": "1"}}

def run_llm(input_message: str):
    # for step in graph.stream(
    #     {"messages": [{"role": "user", "content": input_message}]},
    #     stream_mode="values",
    # ):
    #     step["messages"][-1].pretty_print()
    # return step["messages"][-1].content
    return graph.invoke(
        {"messages": [{"role": "user", "content": input_message}]}, config)