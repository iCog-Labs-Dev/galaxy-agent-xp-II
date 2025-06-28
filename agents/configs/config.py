from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    embeddings_path: str = "embeddings/galaxy_embeddings.npy"
    metadata_path: str = "embeddings/galaxy_metadata.json"
    data_to_encode_path: str ="data/galaxy_tools_may_3_2025_v1.json"
    workflow_embeddings_path: str = "agents/embeddings/iwc_workflow_embeddings.npy"
    workflow_metadata_path: str = "agents/embeddings/iwc_workflow_metadata.json"
    allowed_origins: str = "*"

settings = Settings()