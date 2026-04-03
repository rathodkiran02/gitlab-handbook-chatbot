from google import genai
from google.genai import types
import os
from dotenv import load_dotenv

load_dotenv()
client = genai.Client(
    api_key=os.getenv('GEMINI_API_KEY'),
    http_options=types.HttpOptions(api_version='v1beta')
)

r = client.models.embed_content(
    model='gemini-embedding-001',
    contents='hello world'
)
print('Works! Dims:', len(r.embeddings[0].values))