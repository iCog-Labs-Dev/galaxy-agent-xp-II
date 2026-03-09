import json
import sys
from pathlib import Path
from unittest.mock import Mock

import numpy as np
import pytest

MODULE_DIR = Path(__file__).resolve().parents[1]
if str(MODULE_DIR) not in sys.path:
    sys.path.insert(0, str(MODULE_DIR))

import utils
from config import settings


@pytest.fixture
def real_requests():
    data_path = Path(__file__).parent / "data" / "test_data.json"
    return json.loads(data_path.read_text())


def test_parse_sequence_uses_real_data(real_requests):
    sequence = real_requests["requests"][1]["tool_sequence"]
    parsed = utils.parse_sequence(sequence)

    assert parsed[0] == "Input"
    assert "toolshed.g2.bx.psu.edu/repos/devteam/fastqc/fastqc/0.74+galaxy1" in parsed


def test_generate_tool_aliases_for_toolshed_id():
    tool_id = "toolshed.g2.bx.psu.edu/repos/devteam/fastqc/fastqc/0.74+galaxy1"
    aliases = utils.generate_tool_aliases(tool_id)

    assert tool_id in aliases
    assert "fastqc" in aliases
    assert "0.74" in aliases


def test_convert_tools_to_ids_resolves_aliases():
    tool_list = [
        "Input",
        "toolshed.g2.bx.psu.edu/repos/devteam/fastqc/fastqc/0.74+galaxy1",
        "toolshed.g2.bx.psu.edu/repos/iuc/porechop/porechop/0.2.4+galaxy1",
    ]
    model_dict = {"Input": 1, "fastqc": 2, "porechop": 3}

    ids = utils.convert_tools_to_ids(tool_list, model_dict)

    assert ids == [1, 2, 3]


def test_pad_or_truncate_respects_max_seq_len():
    seq = list(range(settings.MAX_SEQ_LEN + 10))
    padded = utils.pad_or_truncate(seq)

    assert len(padded) == settings.MAX_SEQ_LEN
    assert padded[-1] == settings.MAX_SEQ_LEN - 1

def test_predict_returns_ranked_rounded_scores(monkeypatch):
    monkeypatch.setattr(utils.tf, "convert_to_tensor", lambda x, dtype=None: x)
    model = Mock()
    model.return_value = (np.array([[0.11, 0.91, 0.52, 0.77]], dtype=float), None)

    manager = Mock()
    manager.get_model.return_value = model
    manager.get_metadata.return_value = (
        {
            "0": "Input",
            "1": "fastqc",
            "2": "multiqc",
            "3": "kraken2",
        },
        {"Input": 0, "fastqc": 1, "multiqc": 2, "kraken2": 3},
        {0: 1.0, 1: 1.0, 2: 1.0, 3: 1.0},
    )

    result = utils.predict(manager, "Input,fastqc", topk=2)

    assert len(result) == 2
    assert result[0]["Tool_Score"] >= result[1]["Tool_Score"]
    assert isinstance(result[0]["Tool_Name"], str)
    assert isinstance(result[0]["Tool_Score"], float)
    assert result[0]["Tool_Score"] == round(result[0]["Tool_Score"], 3)
