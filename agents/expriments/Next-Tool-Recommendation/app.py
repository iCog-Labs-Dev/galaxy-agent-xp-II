from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from model import model_manager
from utils import predict
from config import settings


app = FastAPI(title="Next Tool Recommendation API")


@app.get("/")
def health_check():
    return {"status": "ok", "service": "Tool Recommendation API"}


class PredictionRequest(BaseModel):
    tool_sequence: str
    topk: int = settings.TOP_K_DEFAULT


@app.on_event("startup")
def startup():
    model_manager.load()


@app.post("/Next Tool Recommendation")
def predict_tools(request: PredictionRequest):
    try:
        results = predict(model_manager, request.tool_sequence, request.topk)
        return {"Input Sequence Of Tools": request.tool_sequence, "Next Tool Recommendations": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))