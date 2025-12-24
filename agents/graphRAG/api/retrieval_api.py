"""
FastAPI endpoints for GraphRAG retrieval with intent detection and LLM synthesis.
"""
import os
import logging
from typing import Optional, List, Dict
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

from agents.graphRAG.pipeline.workflow_retrival_pipeline import WorkflowRetrievalPipeline
from agents.graphRAG.pipeline.tool_retrieval_pipeline import ToolRetrievalPipeline
from agents.graphRAG.utils.intent_detection import IntentDetector
from agents.graphRAG.retrieval.gemini_llm import GeminiLLM
from agents.ingestion.Load.neo4j_client import Neo4jClient

# ---------------- CONFIGURATION ---------------- #
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()
# Support both GEMINI_API_KEY and GOOGLE_API_KEY
if "GOOGLE_API_KEY" not in os.environ and "GEMINI_API_KEY" in os.environ:
    os.environ["GOOGLE_API_KEY"] = os.environ["GEMINI_API_KEY"]
os.environ.setdefault("GOOGLE_API_KEY", "dummy_key")

# ---------------- FASTAPI SETUP ---------------- #
app = FastAPI(title="Galaxy GraphRAG Retrieval API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------- INITIALIZATION ---------------- #
try:
    neo4j_client = Neo4jClient()
    workflow_pipeline = WorkflowRetrievalPipeline(neo4j_client)
    tool_pipeline = ToolRetrievalPipeline(neo4j_client)
    intent_detector = IntentDetector()
    logger.info("✅ Retrieval pipelines initialized successfully")
except Exception as e:
    logger.error(f"❌ Pipeline initialization failed: {e}")
    neo4j_client = None
    workflow_pipeline = None
    tool_pipeline = None
    intent_detector = None

# Initialize LLM separately (may fail if API key not set)
try:
    if os.environ.get("GOOGLE_API_KEY") and os.environ.get("GOOGLE_API_KEY") != "dummy_key":
        llm = GeminiLLM()
        logger.info("✅ LLM initialized successfully")
    else:
        logger.warning("⚠️ GOOGLE_API_KEY not set, LLM synthesis will be disabled")
        llm = None
except Exception as e:
    logger.warning(f"⚠️ LLM initialization failed: {e}. Answer synthesis will be disabled.")
    llm = None

# ---------------- REQUEST/RESPONSE MODELS ---------------- #
class QueryRequest(BaseModel):
    query: str
    top_k: int = 5
    synthesize: bool = True  # Whether to use LLM to synthesize final answer

class QueryResponse(BaseModel):
    intent: str
    intent_confidence: float
    workflows: Optional[List[Dict]] = None
    tools: Optional[List[Dict]] = None
    synthesized_answer: Optional[str] = None

# ---------------- HELPER FUNCTIONS ---------------- #
def synthesize_answer(
    query: str,
    workflows: List[Dict],
    tools: List[Dict],
    intent: str
) -> str:
    """
    Use LLM to synthesize a final answer from retrieved workflows and tools.
    """
    if not llm:
        return "LLM not available for answer synthesis."
    
    # Build context for LLM
    context_parts = []
    
    if workflows:
        context_parts.append("## Workflows Found:\n")
        for i, wf in enumerate(workflows[:3], 1):  # Limit to top 3
            wf_data = wf.get("workflow", {})
            category = wf.get("category", {})
            steps = wf.get("steps", [])
            
            # Extract tools from steps
            all_tools = set()
            for step in steps:
                for tool in step.get("tools", []):
                    if tool.get("name"):
                        all_tools.add(tool["name"])
            
            context_parts.append(
                f"{i}. {wf_data.get('name', 'Unknown')} "
                f"(Category: {category.get('name', 'Unknown')}, "
                f"Score: {wf.get('similarity_score', 0):.3f})\n"
                f"   Tools used: {', '.join(sorted(all_tools)[:10])}\n"
            )
    
    if tools:
        context_parts.append("\n## Tools Found:\n")
        for i, tool in enumerate(tools[:3], 1):  # Limit to top 3
            tool_data = tool.get("tool", {})
            category = tool.get("category", {})
            context_parts.append(
                f"{i}. {tool_data.get('name', 'Unknown')} "
                f"(Category: {category.get('name', 'Unknown')}, "
                f"Score: {tool.get('similarity_score', 0):.3f})\n"
                f"   Description: {tool_data.get('description', '')[:100]}...\n"
            )
    
    context = "\n".join(context_parts)
    
    # Create prompt for LLM
    prompt = f"""Based on the user's query and the retrieved information, provide a helpful answer.

User Query: {query}

Retrieved Information:
{context}

Please provide a concise, helpful answer that:
1. Directly addresses the user's query
2. Mentions the most relevant workflows/tools found
3. Explains how they might be useful
4. Is written in a natural, conversational tone

Answer:"""
    
    try:
        answer = llm.generate(prompt)
        return answer
    except Exception as e:
        logger.error(f"LLM synthesis failed: {e}")
        return f"Found {len(workflows)} workflows and {len(tools)} tools, but LLM synthesis failed."

# ---------------- ENDPOINTS ---------------- #
@app.get("/")
def root():
    return {
        "message": "Galaxy GraphRAG Retrieval API",
        "endpoints": {
            "/query": "Main endpoint with intent detection",
            "/query-workflows": "Query workflows only",
            "/query-tools": "Query tools only",
            "/detect-intent": "Detect query intent only"
        }
    }

@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "pipelines_initialized": {
            "workflow": workflow_pipeline is not None,
            "tool": tool_pipeline is not None,
            "intent_detector": intent_detector is not None,
            "llm": llm is not None
        }
    }

@app.post("/detect-intent")
def detect_intent(request: QueryRequest):
    """Detect user intent without retrieving data."""
    if not intent_detector:
        raise HTTPException(status_code=500, detail="Intent detector not initialized")
    
    intent_info = intent_detector.detect_intent(request.query)
    return intent_info

@app.post("/query-workflows")
def query_workflows(request: QueryRequest):
    """Query workflows only."""
    if not workflow_pipeline:
        raise HTTPException(status_code=500, detail="Workflow pipeline not initialized")
    
    try:
        workflows = workflow_pipeline.retrieve_workflows(request.query, request.top_k)
        return {
            "intent": "workflow",
            "workflows": workflows,
            "count": len(workflows)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Workflow query failed: {e}")

@app.post("/query-tools")
def query_tools(request: QueryRequest):
    """Query tools only."""
    if not tool_pipeline:
        raise HTTPException(status_code=500, detail="Tool pipeline not initialized")
    
    try:
        tools = tool_pipeline.retrieve_tools(request.query, request.top_k)
        return {
            "intent": "tool",
            "tools": tools,
            "count": len(tools)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Tool query failed: {e}")

@app.post("/query", response_model=QueryResponse)
def query(request: QueryRequest):
    """
    Main endpoint: Detects intent, retrieves workflows/tools, and optionally synthesizes answer.
    """
    if not intent_detector:
        raise HTTPException(status_code=500, detail="Intent detector not initialized")
    
    # Detect intent
    intent_info = intent_detector.detect_intent(request.query)
    intent = intent_info["intent"]
    
    workflows = None
    tools = None
    
    # Retrieve based on intent
    try:
        if intent_detector.should_retrieve_workflows(request.query):
            if workflow_pipeline:
                workflows = workflow_pipeline.retrieve_workflows(request.query, request.top_k)
            else:
                logger.warning("Workflow pipeline not available")
        
        if intent_detector.should_retrieve_tools(request.query):
            if tool_pipeline:
                tools = tool_pipeline.retrieve_tools(request.query, request.top_k)
            else:
                logger.warning("Tool pipeline not available")
    except Exception as e:
        logger.error(f"Retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=f"Retrieval failed: {e}")
    
    # Synthesize answer if requested
    synthesized_answer = None
    if request.synthesize and (workflows or tools):
        try:
            synthesized_answer = synthesize_answer(
                request.query,
                workflows or [],
                tools or [],
                intent
            )
        except Exception as e:
            logger.error(f"Answer synthesis failed: {e}")
            synthesized_answer = "Answer synthesis failed, but results are available."
    
    return QueryResponse(
        intent=intent,
        intent_confidence=intent_info["confidence"],
        workflows=workflows,
        tools=tools,
        synthesized_answer=synthesized_answer
    )

# ---------------- ENTRYPOINT ---------------- #
if __name__ == "__main__":
    import uvicorn
    logger.info("🚀 Starting GraphRAG Retrieval API on http://localhost:8001")
    uvicorn.run(app, host="0.0.0.0", port=8001)

