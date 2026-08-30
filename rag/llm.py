from langchain_openai import AzureChatOpenAI
from config import AZURE_OPENAI_GPT_DEPLOYMENT, AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_KEY, AZURE_OPENAI_API_VERSION

llm = AzureChatOpenAI(
    azure_deployment=AZURE_OPENAI_GPT_DEPLOYMENT,
    azure_endpoint=AZURE_OPENAI_ENDPOINT,
    api_key=AZURE_OPENAI_KEY,
    api_version=AZURE_OPENAI_API_VERSION,
    temperature=0.2,
    max_tokens=512,
)
