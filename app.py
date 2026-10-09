from fastapi import FastAPI, Request
from pydantic import BaseModel
from fastapi.responses import HTMLResponse, JSONResponse
import uvicorn
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from backend import run_workflow
from pathlib import Path
import traceback

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(title="tripMate ai", version="1.0.0")

app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


class planRequest(BaseModel):
    message: str
    thread_id: str | None = None


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse(request=request, name="index.html", context={})


@app.post("/api/travel")
def travel_planner(travelrequest: planRequest):
    try:
        user_query = travelrequest.message.strip()
        if not user_query:
            return JSONResponse(
                content={"success": False, "error": "message cannot be empty "},
                status_code=400,
            )
        result = run_workflow(user_input=user_query, thread_id=travelrequest.thread_id)

        return JSONResponse(
            content={
                "success": True,
                "thread_id": result["thread_id"],
                "answer": result["final_answer"],
                "flight_agent_response": result["flight_agent_response"],
                "hotel_agent_response": result["hotel_agent_response"],
                "itinerary_agent_response": result["itinerary_agent_response"],
                "llm_calls": result["llm_calls"],
            },
            status_code=200,
        )
    except Exception as e:
        print("ERROR:", e)
        traceback.print_exc()

        return JSONResponse(
            status_code=500, content={"success": False, "error": str(e)}
        )


if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
    )
