import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
class Settings:
    MODEL_PATH = os.path.join(BASE_DIR, "../transformer_model/model_feb_28_26.h5")
    MAX_SEQ_LEN = 25
    TOP_K_DEFAULT = 5


settings = Settings()