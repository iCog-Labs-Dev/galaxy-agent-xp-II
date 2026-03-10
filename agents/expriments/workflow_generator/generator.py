import numpy as np
import tensorflow as tf
import os


def _normalize_probs(values):
    values = np.asarray(values, dtype=np.float64)
    values = np.maximum(values, 0.0)
    s_val = values.sum()
    if s_val <= 0:
        return np.ones_like(values) / len(values)
    return values / s_val


def _temperature_scale(values, temperature):
    if temperature <= 0:
        return values
    clipped = np.maximum(values, 1e-12)
    return np.power(clipped, 1.0 / temperature)


def _top_p_filter(sorted_pairs, top_p):
    if top_p >= 1.0:
        return sorted_pairs
    running = 0.0
    keep = []
    for pair in sorted_pairs:
        keep.append(pair)
        running += pair[1]
        if running >= top_p:
            break
    return keep


def _build_input_tensor(current_sequence_ids, max_input_len=25):
    input_tensor = np.zeros((1, max_input_len))
    for idx, tid in enumerate(current_sequence_ids):
        if idx < max_input_len:
            input_tensor[0, idx] = tid
    return input_tensor


def _predict_candidates(
    model,
    current_sequence_ids,
    reverse_dict,
    max_input_len=25,
    top_k=8,
    top_p=0.9,
    temperature=1.0,
    repetition_penalty=1.1,
):
    input_tensor = _build_input_tensor(current_sequence_ids, max_input_len=max_input_len)
    predictions, _ = model.predict(input_tensor, verbose=0)
    probs = np.asarray(predictions[0], dtype=np.float64)
    probs = _temperature_scale(probs, temperature)

    for tool_id in current_sequence_ids:
        if 0 <= tool_id < len(probs):
            probs[tool_id] = probs[tool_id] / max(repetition_penalty, 1e-6)

    probs = _normalize_probs(probs)

    sorted_ids = np.argsort(probs)[::-1]
    sorted_pairs = [(int(tool_id), float(probs[tool_id])) for tool_id in sorted_ids if int(tool_id) != 0]
    sorted_pairs = _top_p_filter(sorted_pairs, top_p)
    sorted_pairs = sorted_pairs[:top_k]

    candidates = []
    for cand_id, cand_prob in sorted_pairs:
        cand_name = reverse_dict.get(str(cand_id), "")
        if not cand_name:
            continue
        if "upload" in cand_name.lower():
            continue
        candidates.append(
            {
                "id": cand_id,
                "name": cand_name,
                "prob": cand_prob,
            }
        )

    return candidates


def _heuristic_rerank(candidates, selected_names):
    reranked = []
    selected_set = set([name.lower() for name in selected_names])
    for item in candidates:
        name = item["name"]
        score = item["prob"]
        if name.lower() in selected_set:
            score *= 0.2
        if "report" in name.lower() or "multiqc" in name.lower():
            score *= 0.95
        reranked.append((item, score))
    reranked = sorted(reranked, key=lambda x: x[1], reverse=True)
    return [item for item, _ in reranked]


def _heuristic_scored(candidates, selected_names):
    selected_set = set([name.lower() for name in selected_names])
    scored = []
    for item in candidates:
        score = float(item["prob"])
        if item["name"].lower() in selected_set:
            score *= 0.2
        if "report" in item["name"].lower() or "multiqc" in item["name"].lower():
            score *= 0.95
        scored.append({
            "id": int(item["id"]),
            "name": item["name"],
            "prob": float(item["prob"]),
            "heuristic_score": float(score),
        })
    scored = sorted(scored, key=lambda x: x["heuristic_score"], reverse=True)
    return scored


def _rank_with_pick(candidates, picked_name):
    exact = [item for item in candidates if item["name"] == picked_name]
    if exact:
        rest = [item for item in candidates if item["name"] != picked_name]
        return exact + rest

    lowered = picked_name.lower().strip()
    fuzzy = [item for item in candidates if item["name"].lower() == lowered]
    if fuzzy:
        rest = [item for item in candidates if item["name"].lower() != lowered]
        return fuzzy + rest

    return None


def _llm_rerank_candidates(candidates, selected_names, llm_model="gpt-4o-mini", llm_provider="auto"):
    if llm_provider not in ["auto", "openai", "gemini"]:
        return _heuristic_rerank(candidates, selected_names), {
            "provider_requested": llm_provider,
            "provider_used": "heuristic",
            "model": llm_model,
            "picked": None,
            "status": "unsupported_provider",
            "error": None,
        }

    openai_key = os.getenv("OPENAI_API_KEY")
    gemini_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

    if llm_provider == "openai" and not openai_key:
        return _heuristic_rerank(candidates, selected_names), {
            "provider_requested": llm_provider,
            "provider_used": "heuristic",
            "model": llm_model,
            "picked": None,
            "status": "missing_openai_key",
            "error": "OPENAI_API_KEY is not set",
        }
    if llm_provider == "gemini" and not gemini_key:
        return _heuristic_rerank(candidates, selected_names), {
            "provider_requested": llm_provider,
            "provider_used": "heuristic",
            "model": llm_model,
            "picked": None,
            "status": "missing_gemini_key",
            "error": "GEMINI_API_KEY/GOOGLE_API_KEY is not set",
        }
    if llm_provider == "auto" and not openai_key and not gemini_key:
        return _heuristic_rerank(candidates, selected_names), {
            "provider_requested": llm_provider,
            "provider_used": "heuristic",
            "model": llm_model,
            "picked": None,
            "status": "missing_all_keys",
            "error": "No LLM API keys found",
        }

    names = [item["name"] for item in candidates]
    prompt = (
        "You are selecting the next Galaxy tool in a workflow. "
        "Prioritize compatibility, diversity (avoid repeated tools), and realistic sequencing. "
        "Return ONLY one tool name from the provided candidates.\n\n"
        "Current chain:\n"
        + " -> ".join(selected_names)
        + "\n\nCandidates:\n"
        + "\n".join(names)
    )

    use_openai_first = llm_provider == "openai" or (llm_provider == "auto" and openai_key is not None)

    if use_openai_first:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=openai_key)
            response = client.chat.completions.create(
                model=llm_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
            )
            picked = response.choices[0].message.content.strip()
            ranked = _rank_with_pick(candidates, picked)
            if ranked is not None:
                return ranked, {
                    "provider_requested": llm_provider,
                    "provider_used": "openai",
                    "model": llm_model,
                    "picked": picked,
                    "status": "ok",
                    "error": None,
                }
        except Exception as exc:
            if llm_provider == "openai":
                return _heuristic_rerank(candidates, selected_names), {
                    "provider_requested": llm_provider,
                    "provider_used": "heuristic",
                    "model": llm_model,
                    "picked": None,
                    "status": "openai_error",
                    "error": str(exc),
                }

    use_gemini = llm_provider == "gemini" or (llm_provider == "auto" and gemini_key is not None)
    if use_gemini:
        try:
            import google.generativeai as genai
            genai.configure(api_key=gemini_key)
            gm = genai.GenerativeModel(llm_model)
            response = gm.generate_content(prompt)
            picked = (response.text or "").strip()
            ranked = _rank_with_pick(candidates, picked)
            if ranked is not None:
                return ranked, {
                    "provider_requested": llm_provider,
                    "provider_used": "gemini",
                    "model": llm_model,
                    "picked": picked,
                    "status": "ok",
                    "error": None,
                }
        except Exception as exc:
            return _heuristic_rerank(candidates, selected_names), {
                "provider_requested": llm_provider,
                "provider_used": "heuristic",
                "model": llm_model,
                "picked": None,
                "status": "gemini_error",
                "error": str(exc),
            }

    return _heuristic_rerank(candidates, selected_names), {
        "provider_requested": llm_provider,
        "provider_used": "heuristic",
        "model": llm_model,
        "picked": None,
        "status": "fallback",
        "error": None,
    }

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

    return [reverse_dict[str(tid)] for tid in current_sequence_ids if str(tid) in reverse_dict]


def hybrid_generate_tool_sequence(
    model,
    forward_dict,
    reverse_dict,
    seed_tool_name,
    max_len=10,
    top_k=8,
    top_p=0.9,
    temperature=1.0,
    repetition_penalty=1.1,
    use_llm=True,
    llm_model="gpt-4o-mini",
    llm_provider="auto",
    validator=None,
    return_trace=False,
):
    clean_seed = seed_tool_name.split("/")[-2] if "/" in seed_tool_name else seed_tool_name
    seed_id = forward_dict.get(clean_seed, 1)

    current_sequence_ids = [seed_id]
    selected_names = [reverse_dict.get(str(seed_id), clean_seed)]
    terminals = ["multiqc", "plot", "visualize", "report"]
    trace = []

    for step_idx in range(max_len):
        candidates = _predict_candidates(
            model=model,
            current_sequence_ids=current_sequence_ids,
            reverse_dict=reverse_dict,
            top_k=top_k,
            top_p=top_p,
            temperature=temperature,
            repetition_penalty=repetition_penalty,
        )

        if validator is not None and hasattr(validator, "installed_tools"):
            installed = validator.installed_tools
            candidates = [item for item in candidates if item["name"] in installed]

        heuristic_scores = _heuristic_scored(candidates, selected_names)
        heuristic_map = {item["id"]: item["heuristic_score"] for item in heuristic_scores}

        if not candidates:
            print("Stopping: no valid candidates available.")
            trace.append({
                "step": step_idx + 1,
                "chain": list(selected_names),
                "candidates": [],
                "llm": {
                    "provider_requested": llm_provider,
                    "provider_used": "heuristic",
                    "model": llm_model,
                    "picked": None,
                    "status": "no_candidates",
                },
                "chosen": None,
                "stop_reason": "no_valid_candidates",
            })
            break

        if use_llm:
            ranked = _llm_rerank_candidates(
                candidates,
                selected_names,
                llm_model=llm_model,
                llm_provider=llm_provider,
            )
            ranked, llm_info = ranked
        else:
            ranked = _heuristic_rerank(candidates, selected_names)
            llm_info = {
                "provider_requested": llm_provider,
                "provider_used": "heuristic",
                "model": llm_model,
                "picked": None,
                "status": "disabled",
                "error": None,
            }

        chosen = ranked[0]
        step_candidates = []
        for rank_idx, item in enumerate(ranked, start=1):
            step_candidates.append({
                "rank": rank_idx,
                "id": int(item["id"]),
                "name": item["name"],
                "prob": float(item["prob"]),
                "heuristic_score": float(heuristic_map.get(item["id"], item["prob"])),
                "selected_by_llm": bool(llm_info.get("picked") == item["name"]),
            })

        trace.append({
            "step": step_idx + 1,
            "chain": list(selected_names),
            "candidates": step_candidates,
            "llm": llm_info,
            "chosen": {
                "id": int(chosen["id"]),
                "name": chosen["name"],
                "prob": float(chosen["prob"]),
                "heuristic_score": float(heuristic_map.get(chosen["id"], chosen["prob"])),
            },
            "stop_reason": None,
        })

        if chosen["prob"] < 0.0005:
            print("Stopping: candidate probability too low.")
            trace[-1]["stop_reason"] = "probability_too_low"
            break

        next_tool_id = chosen["id"]
        next_tool_name = chosen["name"]

        if next_tool_id in current_sequence_ids:
            print("Stopping: repetition guard triggered.")
            trace[-1]["stop_reason"] = "repetition_guard"
            break

        current_sequence_ids.append(next_tool_id)
        selected_names.append(next_tool_name)

        if any(term in next_tool_name.lower() for term in terminals):
            print("Stopping: terminal tool detected ({}).".format(next_tool_name))
            trace[-1]["stop_reason"] = "terminal_tool_detected"
            break

    chain = [reverse_dict[str(tid)] for tid in current_sequence_ids if str(tid) in reverse_dict]
    if return_trace:
        return chain, trace
    return chain