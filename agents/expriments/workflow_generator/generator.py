import numpy as np
import tensorflow as tf

def generate_tool_sequence(model, f_dict, rev_dict, seed_tool_name, max_len=10):
    # Clean the seed name (in case it's a full path)
    clean_seed = seed_tool_name.split("/")[-2] if "/" in seed_tool_name else seed_tool_name
    seed_id = f_dict.get(clean_seed, 1) 
    
    current_sequence_ids = [seed_id]
    
    for _ in range(max_len):
        input_tensor = np.zeros((1, 25))
        for i, tid in enumerate(current_sequence_ids):
            if i < 25: input_tensor[0, i] = tid
        
        predictions, _, _ = model.predict(input_tensor, verbose=0)
        best_candidates = np.argsort(predictions[0])[::-1]
        
        next_tool_id = None
        for cand_id in best_candidates:
            if cand_id == 0 or cand_id in current_sequence_ids:
                continue
            
            cand_name = rev_dict.get(cand_id, "")
            # Don't suggest uploading in the middle of a chain
            if "upload" in cand_name.lower():
                continue
                
            next_tool_id = cand_id
            break

        if next_tool_id is None or predictions[0][next_tool_id] < 0.001:
            break
            
        current_sequence_ids.append(next_tool_id)
        
        # Stop if we hit a terminal tool
        terminals = ['multiqc', 'plot', 'visualize', 'report']
        if any(t in rev_dict[next_tool_id].lower() for t in terminals):
            break

    return [rev_dict[tid] for tid in current_sequence_ids]