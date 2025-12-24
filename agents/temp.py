from agents.summary_agent import summarize_tool_suggestions, summarize_workflow_suggestions
from agents.tool_suggesting_agent import ToolSuggestionAgentPipeline
from agents.workflow_suggestion_agent import WorkflowSuggestionAgentPipeline
from agents.ingestion.Load.neo4j_client import Neo4jClient

# Initialize Neo4j client
neo_client = Neo4jClient("agents/graphRAG/config/graph_db_config.yml")

# Initialize pipeline agents
tool_agent = ToolSuggestionAgentPipeline(neo_client)
workflow_agent = WorkflowSuggestionAgentPipeline(neo_client)

query = "I want a workflow to filter and sort rDock docking results"

# Get raw suggestions from the pipelines
tool_results = tool_agent.suggest_tools(query, top_k=5)
workflow_results = workflow_agent.suggest_workflows(query, top_k=5)

# Pass the raw results directly to the summary agent
tool_summary = summarize_tool_suggestions(tool_results, query)
workflow_summary = summarize_workflow_suggestions(workflow_results, query)

print("=== Tool Summary ===")
print(tool_summary)
print("\n=== Workflow Summary ===")
print(workflow_summary)
