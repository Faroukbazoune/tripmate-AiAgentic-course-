from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel
from langgraph.graph import START, StateGraph, END
from langgraph.checkpoint.postgres import PostgresSaver
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage, AIMessage
from langchain_groq import ChatGroq
import certifi
import os
import uuid
from langgraph.graph.message import add_messages
from typing import Annotated
import psycopg
from psycopg.rows import dict_row
from dotenv import load_dotenv, find_dotenv

from tools.flight_tool import search_flights
from tools.tavily_tool import tavily_serach

load_dotenv(find_dotenv())


os.environ["SSL_CERT_FILE"] = certifi.where()
os.environ["REQUESTS_CA_BUNDLE"] = certifi.where()


def get_db_url():
    url = os.getenv("DATABASE_URL")

    if not url:
        raise ValueError("DATABASE URL not found")

    if "sslmode" not in url:
        seperator = "&" if "?" in url else "?"
        url = f"{url}{seperator}sslmode=require"

    return url


class GraphState(BaseModel):
    messages: Annotated[list[BaseMessage], add_messages]
    User_query: str
    flight_agent_response: str
    hotel_agent_response: str
    itinerary_agent_response: str
    llm_calls: int
    final_response: str


if not os.getenv("GEMINI_API_KEY"):
    raise ValueError("GEMINI KEY NOT FOUND . please add it ")

google_llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash")


def flight_agent(state: GraphState):
    flight_data = search_flights(state.User_query)

    return {
        "llm_calls": state.llm_calls + 1,
        "messages": [AIMessage(content="flight data fetched")],
        "flight_agent_response": flight_data,
    }


def hotel_agent(state: GraphState):
    query = f"best hotels for {state.User_query}"
    hotels = search_flights(query)
    return {
        "messages": [AIMessage(content="hotels informations found")],
        "hotel_agent_response": hotels,
        "llm_calls": state.llm_calls + 1,
    }


def itinerary_agent(state: GraphState):
    prompt = f"""create a complete travel itinerary.
     User query :
      {state.User_query}
fight results:
{state.flight_agent_response}

hotels result :
{state.hotel_agent_response}

make the itinerary budget-aware , easy to follow and fun.  """
    response = google_llm.invoke(
        [
            SystemMessage(content="you are a helpful and professional travel planner"),
            HumanMessage(content=prompt),
        ]
    )

    return {
        "itinerary_agent_response": response.content,
        "llm_calls": state.llm_calls + 1,
        "messages": [response],
    }


def final_response_agent(state: GraphState):
    prompt = f"""generate a final travel response using this infos:
    user query : {state.User_query}.
    
    flight results:{state.flight_agent_response}.
    
    hotels result:{state.hotel_agent_response}.
    
    itinerary results:{state.itinerary_agent_response}.
    
    format the final answer beautifully using this structure :
    1.trip summary
    2.flight information
    3.hotels informations
    4.day by day itinerary 
    5.estimated budget
    6.final recommendations
     
    important:
    be clear and practical 
    keep the response useful for travel plannig
    mention the flight api may not provide tickets prices if its unavailable  """

    response = google_llm.invoke(
        [
            SystemMessage(
                content="you are a helpful and professional ai travel booking assistant "
            ),
            HumanMessage(content=prompt),
        ]
    )

    return {
        "messages": [response],
        "llm_calls": state.llm_calls + 1,
        "final_response": response.content,
    }


graph = StateGraph(GraphState)
graph.add_node("flight_agent", flight_agent)
graph.add_node("hotels_agent", hotel_agent)
graph.add_node("final_response_agent", final_response_agent)
graph.add_node("itinerary_agent", itinerary_agent)


graph.add_edge(START, "flight_agent")
graph.add_edge("flight_agent", "hotels_agent")
graph.add_edge("hotels_agent", "itinerary_agent")
graph.add_edge("itinerary_agent", "final_response_agent")
graph.add_edge("final_response_agent", END)


DATABASE_URL = get_db_url()

conn = psycopg.connect(DATABASE_URL, autocommit=True, row_factory=dict_row)
checkpointer = PostgresSaver(conn)
checkpointer.setup()

workflow = graph.compile(checkpointer=checkpointer)


##for fastapi
def run_workflow(user_input: str, thread_id: str | None = None):

    if not thread_id:
        thread_id = f"user_{uuid.uuid4().hex}"

    config = {
        "configurable": {
            "thread_id": thread_id,
        },
    }

    response = workflow.invoke(
        {
            "messages": [HumanMessage(content=user_input)],
            "User_query": user_input,
            "flight_agent_response": "",
            "hotel_agent_response": "",
            "itinerary_agent_response": "",
            "llm_calls": 0,
            "final_response": "",
        },
        config=config,
    )

    result = response["messages"][-1].content

    return {
        "thread_id": thread_id,
        "final_answer": result,
        "flight_agent_response": response["flight_agent_response"],
        "hotel_agent_response": response["hotel_agent_response"],
        "itinerary_agent_response": response["itinerary_agent_response"],
        "llm_calls": response["llm_calls"],
    }
