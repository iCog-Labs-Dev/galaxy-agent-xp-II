import numpy as np
import pytest


class DummyModel:
    def __init__(self, prediction_sequences):
        """
        prediction_sequences: list of 1D numpy arrays, one per predict() call.
        """
        self._seq = prediction_sequences
        self.calls = 0

    def predict(self, input_tensor, verbose=0):
        # Return predictions with expected (1, n_classes) shape and a dummy second value.
        if not self._seq:
            raise RuntimeError("No prediction sequences configured")
        # Safely handle extra calls by reusing the last sequence
        index = min(self.calls, len(self._seq) - 1)
        preds = self._seq[index]
        self.calls += 1
        return np.array([preds]), None


@pytest.fixture
def basic_dicts():
    # Simple mapping: tool ids 1..4 map to names
    forward = {"tool_a": 1, "tool_b": 2, "upload_data": 3, "multiqc": 4}
    reverse = {str(v): k for k, v in forward.items()}
    return forward, reverse


def test_generate_tool_sequence_basic_happy_path(basic_dicts):
    # Arrange
    forward_dict, reverse_dict = basic_dicts
    # Model will always prefer id 2 then 4 (terminal)
    predictions = [
        np.array([0.0, 0.1, 0.9, 0.0, 0.0]),  # from seed -> tool_b
        np.array([0.0, 0.0, 0.0, 0.0, 1.0]),  # from tool_b -> multiqc (terminal)
    ]
    model = DummyModel(predictions)

    from agents.expriments.workflow_generator.generator import generate_tool_sequence

    # Act
    result = generate_tool_sequence(
        model, forward_dict, reverse_dict, seed_tool_name="tool_a", max_len=5
    )

    # Assert
    # Sequence should include the seed tool and then tool_b and multiqc (terminal) once
    assert result == ["tool_a", "tool_b", "multiqc"]


def test_generate_tool_sequence_skips_upload_tools(basic_dicts):
    # Arrange
    forward_dict, reverse_dict = basic_dicts
    # First candidate is upload_data but should be skipped in the middle of the chain.
    predictions = [
        np.array([0.0, 0.1, 0.05, 0.8, 0.0]),
        np.array([0.0, 0.1, 0.05, 0.8, 0.0]),
    ]
    model = DummyModel(predictions)

    from agents.expriments.workflow_generator.generator import generate_tool_sequence

    # Act
    result = generate_tool_sequence(
        model, forward_dict, reverse_dict, seed_tool_name="tool_a", max_len=2
    )

    # Assert
    # upload_data must never appear; we should move from seed to a non-upload tool
    assert "upload_data" not in result
    assert result[0] == "tool_a"
    # Depending on ranking, the next tool should be a valid non-upload tool
    assert result[1] in {"tool_b", "multiqc"}


def test_generate_tool_sequence_stops_when_probability_too_low(basic_dicts, capsys):
    # Arrange
    forward_dict, reverse_dict = basic_dicts
    # First step chooses tool_b, second step probability for next candidate is below threshold (0.001)
    predictions = [
        np.array([0.0, 0.1, 0.9, 0.0, 0.0]),  # from seed -> tool_b
        np.array([0.0, 0.0005, 0.0, 0.0, 0.0]),
    ]
    model = DummyModel(predictions)

    from agents.expriments.workflow_generator.generator import generate_tool_sequence

    # Act
    result = generate_tool_sequence(
        model, forward_dict, reverse_dict, seed_tool_name="tool_a", max_len=10
    )
    captured = capsys.readouterr()

    # Assert
    # Should only add the high-probability tool_b and then stop
    assert result == ["tool_a", "tool_b"]
    assert "probability too low" in captured.out


def test_generate_tool_sequence_breaks_on_missing_reverse_dict_entry(basic_dicts, capsys):
    # Arrange
    forward_dict, reverse_dict = basic_dicts
    # Prediction selects an id that doesn't exist in reverse_dict (e.g., 99)
    predictions = [
        np.array([0.0, 0.9, 0.0, 0.0, 0.0]),
        np.array([0.0, 0.0, 0.0, 0.0, 0.0]),  # dummy, won't be used
    ]

    class MissingIdDummyModel(DummyModel):
        def predict(self, input_tensor, verbose=0):
            preds, _ = super().predict(input_tensor, verbose)
            # Overwrite predictions so that best candidate is index 99
            extended = np.zeros(100)
            extended[1] = 0.9  # existing id
            extended[99] = 0.95  # higher score but missing in reverse_dict
            return np.array([extended]), None

    model = MissingIdDummyModel(predictions)

    from agents.expriments.workflow_generator.generator import generate_tool_sequence

    # Act
    result = generate_tool_sequence(
        model, forward_dict, reverse_dict, seed_tool_name="tool_a", max_len=10
    )
    captured = capsys.readouterr()

    # Assert
    # It should warn and stop without including the missing-id tool
    assert result == ["tool_a"]
    assert "not found in reverse_dict" in captured.out

