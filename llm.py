import os
from dotenv import load_dotenv
from langchain_mistralai import ChatMistralAI

load_dotenv()
api_key= os.getenv("MISTRAL_API_KEY")


def brain():
    llm = ChatMistralAI(
        model= "mistral-medium-latest",
        api_key= api_key
    )
    return llm