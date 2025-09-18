# Set up and embed documents, then upsert to Pinecone
from pinecone import Pinecone
from openai import OpenAI
import os
import json
from tqdm import tqdm
import dotenv

dotenv.load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)
pc = Pinecone(
    api_key=os.getenv("PINECONE_API_KEY")
)

index = pc.Index("connect-chatbot-mq-1")

with open("mq_connect_data_1.json", "r", encoding="utf-8") as f:
    data = json.load(f)

#Embed and upsert
for i, item in tqdm(enumerate(data), total=len(data), desc="Embedding & upserting"):
    text = item['text']
    url = item['url']

    resp = client.embeddings.create(
        model = 'text-embedding-3-small',
        input=text
    )
    vector = resp.data[0].embedding

    index.upsert([
        {
            "id": f"doc-{i}",
            "values": vector,
            "metadata": {"url": url, "text": text}
        }
    ])
