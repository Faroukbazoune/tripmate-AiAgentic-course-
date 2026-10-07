from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel
from langgraph.graph import START, StateGraph, END
from langgraph.checkpoint.postgres import PostgresSaver
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage, AIMessage
from langchain_groq import ChatGroq
import certifi
import os
import uuid
import operator
from langgraph.graph.message import add_messages
from typing import Annotated
import psycopg
from psycopg.rows import dict_row
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())


os.environ["SSL_CERT_FILE"] = certifi.where()
os.environ["REQUESTS_CA_BUNDLE"] = certifi.where()


class GraphState(BaseModel):
    messages: Annotated[list[BaseMessage], add_messages]
    User_query: str
    flight_agent_response: str
    hotel_agent_response: str
    reseach_agent_response: str
    Final_response: str


google_llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash")
