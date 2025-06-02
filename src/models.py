# src/models.py
import os
from src.common.utils import logger  # Cập nhật import
from src.prompts import PROMT_HEADER
from langchain_groq import ChatGroq

def using_llm_groq(api_key: str = None, model_name: str = "llama3-8b-8192") -> ChatGroq:
    try:
        if api_key:
            os.environ['GROQ_API_KEY'] = api_key
            groq_llm = ChatGroq(
                api_key=api_key,
                model=model_name,
                temperature=0.2,
                max_tokens=512,
            )
            return groq_llm
        else:
            logger.warning("Please enter api key Groq")
    except Exception as e:
        logger.error(f"Error occurred: {e}")