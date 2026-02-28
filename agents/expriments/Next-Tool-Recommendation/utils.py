import numpy as np
import tensorflow as tf

from config import settings


def parse_sequence(sequence_str):
    tools = sequence_str.split(",")
    return [t.strip() for t in tools if t.strip()]


def convert_tools_to_ids(tool_list, model_dict):
    return [model_dict[t] for t in tool_list if t in model_dict]


def pad_or_truncate(sequence_ids):
    seq = sequence_ids[: settings.MAX_SEQ_LEN]
    seq.extend([0] * (settings.MAX_SEQ_LEN - len(seq)))
    return np.array(seq)


def create_model_input(sequence_ids):
    return np.reshape(sequence_ids, (1, settings.MAX_SEQ_LEN))


def flatten_predictions(prediction):
    return np.reshape(prediction, (prediction.shape[1],))


def apply_class_weights(prediction, class_weights):
    weights = np.array([class_weights.get(i, 1.0) for i in range(len(prediction))])
    return prediction * weights


def remove_last_tool(prediction, last_tool_id):
    if last_tool_id < len(prediction):
        prediction[last_tool_id] = 0
    return prediction


def select_top_k(prediction, topk):
    indices = np.argsort(prediction)[-topk:][::-1]
    scores = prediction[indices]
    return indices, scores


def convert_ids_to_names(indices, reverse_dict):
    return [reverse_dict[str(i)] for i in indices]


def predict(model_manager, sequence_str, topk=settings.TOP_K_DEFAULT):
    model = model_manager.get_model()
    reverse_dict, model_dict, class_weights = model_manager.get_metadata()
    tools = parse_sequence(sequence_str)
    ids = convert_tools_to_ids(tools, model_dict)
    if not ids:
        return []
    last_tool_id = ids[-1]
    padded = pad_or_truncate(ids)
    sample = create_model_input(padded)
    sample = tf.convert_to_tensor(sample, dtype=tf.int64)

    prediction, _ = model(sample, training=False)
    prediction = flatten_predictions(prediction)
    prediction = apply_class_weights(prediction, class_weights)
    prediction = remove_last_tool(prediction, last_tool_id)

    indices, scores = select_top_k(prediction, topk)
    tool_names = convert_ids_to_names(indices, reverse_dict)
    return [{"tool": name, "score": float(score)} for name, score in zip(tool_names, scores)]
