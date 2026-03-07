import numpy as np
import tensorflow as tf

def generate_tool_sequence(model, forward_dict, reverse_dict, seed_tool_name, max_len=10):
    # Clean the seed name (in case it's a full path)
    clean_seed = seed_tool_name.split("/")[-2] if "/" in seed_tool_name else seed_tool_name
    seed_id = forward_dict.get(clean_seed, 1)

    current_sequence_ids = [seed_id]

    for step in range(max_len):
        input_tensor = np.zeros((1, 25))
        for i, tid in enumerate(current_sequence_ids):
            if i < 25:
                input_tensor[0, i] = tid

        predictions, _ = model.predict(input_tensor, verbose=0)
        best_candidates = np.argsort(predictions[0])[::-1]

        print(f"\nStep {step+1}:")
        print("Current sequence IDs:", current_sequence_ids)
        print("Top 5 candidates:")
        for idx in best_candidates[:5]:
            name = reverse_dict.get(str(idx), "?")
            prob = predictions[0][idx]
            print(f"  ID {idx}: {name} (prob={prob:.4f})")

        next_tool_id = None
        for cand_id in best_candidates:
            if cand_id == 0 or cand_id in current_sequence_ids:
                continue

            cand_name = reverse_dict.get(str(cand_id), "")
            # Don't suggest uploading in the middle of a chain
            if "upload" in cand_name.lower():
                continue

            next_tool_id = cand_id
            break

        if next_tool_id is None or predictions[0][next_tool_id] < 0.001:
            print(f"Stopping: next_tool_id is None or probability too low.")
            break

        print(f"Selected next tool: ID {next_tool_id}, Name: {reverse_dict.get(str(next_tool_id), '?')}, Prob: {predictions[0][next_tool_id]:.4f}")
        current_sequence_ids.append(next_tool_id)

        # Stop if we hit a terminal tool
        terminals = ['multiqc', 'plot', 'visualize', 'report']
        tool_name = reverse_dict.get(str(next_tool_id), None)
        if tool_name is not None:
            if any(t in tool_name.lower() for t in terminals):
                print(f"Stopping: terminal tool detected ({tool_name}).")
                break
        else:
            # If tool_name is missing, break to avoid KeyError
            print(f"⚠️ Warning: Tool ID {next_tool_id} not found in reverse_dict. Skipping.")
            break

    # Only return tool names that exist in reverse_dict
    return [reverse_dict[str(tid)] for tid in current_sequence_ids if str(tid) in reverse_dict]