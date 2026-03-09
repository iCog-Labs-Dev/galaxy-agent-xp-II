import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

MODULE_DIR = Path(__file__).resolve().parents[1]
if str(MODULE_DIR) not in sys.path:
    sys.path.insert(0, str(MODULE_DIR))

from agents.expriments.Next_Tool_Recommendation import app as app_module


@pytest.fixture
def real_requests():
    data_path = Path(__file__).parent / "data" / "test_data.json"
    return json.loads(data_path.read_text())


@pytest.fixture
def client():
    with patch.object(app_module.model_manager, "load", return_value=None):
        with TestClient(app_module.app) as test_client:
            yield test_client


def test_health_check(client):
    response = client.get("/")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_predict_endpoint_with_real_request_payload(client, real_requests):
    request_payload = real_requests["requests"][0]
    mocked_result = [
        {"Tool_Name": "multiqc", "Tool_Score": 0.913},
        {"Tool_Name": "kraken2", "Tool_Score": 0.721},
    ]

    with patch.object(app_module, "predict", return_value=mocked_result) as mock_predict:
        response = client.post("/Next Tool Recommendation", json=request_payload)

    assert response.status_code == 200
    body = response.json()
    assert body["Input Sequence Of Tools"] == request_payload["tool_sequence"]
    assert body["Next Tool Recommendations"] == mocked_result
    mock_predict.assert_called_once()


def test_predict_endpoint_returns_500_on_predict_error(client, real_requests):
    request_payload = real_requests["requests"][1]

    with patch.object(app_module, "predict", side_effect=RuntimeError("model failure")):
        response = client.post("/Next Tool Recommendation", json=request_payload)

    assert response.status_code == 500
    assert "model failure" in response.json()["detail"]
