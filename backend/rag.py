# Import necessary libraries and set up
from langchain.prompts import PromptTemplate
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains import create_retrieval_chain
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

vector_store = PineconeVectorStore(embedding=embeddings, index=index)
retriever = vector_store.as_retriever(search_kwargs={"k": 3})


retrieval_qa_chat_prompt_template = PromptTemplate(
    input_variables=["input", "context"],
    template="""
You are a helpful assistant that helps students find information about Macquarie University. 
Only answer questions related to Macquarie University. Assume the user is asking about Macquarie University's policy.
Answer any use questions based solely on the context below:

<context>
{context}
</context>

Question: {input}
Answer concisely and provide relevant contact info if applicable. If you don't know the answer, just say "Please contact Service Connect for further assistance". Do not try to make up an answer.
"""
)

combine_docs_chain = create_stuff_documents_chain(
    llm, retrieval_qa_chat_prompt_template
)
rag_chain = create_retrieval_chain(
    retriever, combine_docs_chain)

def rag_chain_invoke(question):
    return rag_chain.invoke({"input": question})

