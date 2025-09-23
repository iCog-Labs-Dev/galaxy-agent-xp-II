# agents/routes/recommend.py
from fastapi import APIRouter, HTTPException
from agents.utils.response_models import SuggestionRequest, SuggestionResponse, WorkflowSuggestionResponse
from agents.suggesting_agent import ToolSuggestionAgent
from agents.workflow_suggestion_agent import WorkflowSuggestionAgent
from agents.services.classification_service import classify_query

# Router instance for /recommend endpoints
router = APIRouter(prefix="/recommend", tags=["Recommendation"])

# Initialize agents
tool_agent = ToolSuggestionAgent()
workflow_agent = WorkflowSuggestionAgent()

@router.post("/", response_model=dict)
async def recommend(request: SuggestionRequest):
    """
    Unified endpoint:
    - Gemini classifies the query as 'tool', 'workflow', or 'both'
    - Routes to the correct agent(s)
    - Returns structured JSON
    """
    try:
        # Step 1: Gemini classification
        category = classify_query(request.query)

        # Step 2: Route to appropriate agent(s)
        if category == "tool":
            tools = tool_agent.suggest_tools(request.query, request.top_k)
            return {"type": "tool", "results": tools}

        elif category == "workflow":
            workflows = workflow_agent.suggest_workflows(request.query, request.top_k)
            return {"type": "workflow", "results": workflows}

        else:  # "both"
            tools = tool_agent.suggest_tools(request.query, request.top_k)
            workflows = workflow_agent.suggest_workflows(request.query, request.top_k)
            return {"type": "both", "tool_results": tools, "workflow_results": workflows}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
