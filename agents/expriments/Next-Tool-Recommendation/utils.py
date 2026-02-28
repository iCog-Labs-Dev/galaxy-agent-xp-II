import numpy as np
import tensorflow as tf

from config import settings


def parse_sequence(sequence_str):
    tools = sequence_str.split(",")
    return [t.strip() for t in tools if t.strip()]


def generate_tool_aliases(tool_name):
    aliases = []

    def add(value):
        if value and value not in aliases:
            aliases.append(value)

    add(tool_name)
    add(tool_name.lower())

    parts = tool_name.split("/")
    if len(parts) >= 2:
        last = parts[-1]
        second_last = parts[-2]

        add(last)
        add(last.lower())
        add(second_last)
        add(second_last.lower())

        if "+" in last:
            base_last = last.split("+", 1)[0]
            add(base_last)
            add(base_last.lower())

        if "+" in second_last:
            base_second_last = second_last.split("+", 1)[0]
            add(base_second_last)
            add(base_second_last.lower())

    return aliases


def resolve_tool_id(tool_name, model_dict):
    for alias in generate_tool_aliases(tool_name):
        if alias in model_dict:
            return model_dict[alias]
    return None


def convert_tools_to_ids(tool_list, model_dict):
    ids = []
    for tool_name in tool_list:
        tool_id = resolve_tool_id(tool_name, model_dict)
        if tool_id is not None:
            ids.append(tool_id)
    return ids


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
