import json
import logging
from pathlib import Path
from typing import Any, Dict, List

from neo4j_graphrag.retrievers import Text2CypherRetriever

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def load_json(file_path: str) -> Any:
    """
    Load a JSON file and return its content.

    Raises:
        FileNotFoundError: If file does not exist.
        json.JSONDecodeError: If JSON is invalid.
    """
    path = Path(file_path).resolve()
    if not path.exists():
        logger.error(f"JSON file not found: {file_path}")
        raise FileNotFoundError(f"JSON file not found: {file_path}")

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        logger.info(f"Loaded JSON file successfully: {file_path}")
        return data
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON file {file_path}: {e}")
        raise


def init_retriever(driver, llm) -> Text2CypherRetriever:
    """
    Initialize Text2CypherRetriever using JSON schema and examples.

    Args:
        driver: Neo4j driver/session object
        llm: GeminiLLM or compatible LLM wrapper

    Returns:
        Text2CypherRetriever instance
    """
    # Compute project root and retrieval folder
    retrieval_folder = Path(__file__).parent.resolve()
    schema_file = retrieval_folder / "neo4j_schema.json"
    examples_file = retrieval_folder / "examples.json"


    # Load schema and examples
    schema_json: Dict[str, Any] = load_json(schema_file)
    examples_list: List[Dict[str, Any]] = load_json(examples_file)

    # Convert schema dict to JSON string for retriever
    neo4j_schema_str = json.dumps(schema_json, indent=2)

    retriever = Text2CypherRetriever(
        driver=driver,
        llm=llm,
        neo4j_schema=neo4j_schema_str,
        examples=examples_list
    )

    logger.info("Text2CypherRetriever initialized successfully.")
    return retriever
