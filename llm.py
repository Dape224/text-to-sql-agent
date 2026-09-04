import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()
api_key= os.getenv("GEMINI_API_KEY")


def brain():
    llm = ChatGoogleGenerativeAI(
        model= "gemini-2.5-flash",
        api_key= api_key
    )
    return llm