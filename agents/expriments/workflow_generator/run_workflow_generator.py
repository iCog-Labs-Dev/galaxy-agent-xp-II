

import os
import sys
import json
import argparse
import numpy as np
import tensorflow as tf
import h5py

# --- PATH FIX ---
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "..", "..", ".."))
expriments_root = os.path.abspath(os.path.join(current_dir, ".."))
from dotenv import load_dotenv
scripts_path = os.path.join(expriments_root, "scripts")


if project_root not in sys.path:
    sys.path.insert(0, project_root)
if expriments_root not in sys.path:
    sys.path.insert(0, expriments_root)
if scripts_path not in sys.path:
    sys.path.insert(0, scripts_path)


# --- IMPORTS ---
from agents.expriments.Next_Tool_Recommendation.model import build_transformer_model, ModelManager
try:
    from .generator import generate_tool_sequence, hybrid_generate_tool_sequence
    from .generate_ga_file import create_galaxy_workflow
    from .validator import GalaxyValidator
except ImportError:
    from generator import generate_tool_sequence, hybrid_generate_tool_sequence
    from generate_ga_file import create_galaxy_workflow
    from validator import GalaxyValidator

load_dotenv(os.path.join(project_root, '.env'))

# --- CONFIGURATION ---
MODEL_PATH = os.getenv(
    "WORKFLOW_GENERATOR_MODEL_PATH",
    os.path.join(expriments_root, "transformer_model", "model_feb_28_26.h5")
)
BRIDGE_DICT_PATH = os.getenv(
    "WORKFLOW_GENERATOR_BRIDGE_DICT_PATH",
    os.path.join(expriments_root, "data", "tool_id_dict.txt")
)
TOOLS_CACHE_PATH = os.getenv(
    "WORKFLOW_GENERATOR_TOOLS_CACHE_PATH",
    os.path.join(expriments_root, "reports", "workflow_generator", "installed_tools_cache.json")
)

SEED_TOOL = "Grep1"
MAX_STEPS = 15

# Tools that usually require extra/manual parameterization or multi-input wiring
# and often break on raw auto-generated .ga imports.
UNSAFE_AUTO_TOOLS = {
    "join1",
    "tp_easyjoin_tool",
    "bedtools_intersectbed",
    "grouping1",
    "addvalue",
    "tab2fasta",
    "datamash_ops",
}


def _parse_args():
    parser = argparse.ArgumentParser(description="Generate Galaxy workflow from transformer or hybrid generator")
    parser.add_argument("--mode", choices=["transformer", "hybrid"], default="hybrid")
    parser.add_argument("--seed_tool", default=SEED_TOOL)
    parser.add_argument("--max_steps", type=int, default=MAX_STEPS)
    parser.add_argument("--top_k", type=int, default=8)
    parser.add_argument("--top_p", type=float, default=0.9)
    parser.add_argument("--temperature", type=float, default=1.0)
    parser.add_argument("--repetition_penalty", type=float, default=1.1)
    parser.add_argument("--llm_provider", choices=["auto", "openai", "gemini"], default="auto")
    parser.add_argument("--llm_model", default="gpt-4o-mini")
    parser.add_argument("--disable_llm", action="store_true")
    parser.add_argument("--skip_validation", action="store_true")
    parser.add_argument("--galaxy_timeout", type=int, default=15)
    parser.add_argument("--tools_cache_file", default=TOOLS_CACHE_PATH)
    parser.add_argument("--tools_cache_ttl", type=int, default=1800)
    parser.add_argument("--workflow_name", default="AI_Validated_Workflow")
    parser.add_argument("--output_file", default="ai_generated_workflow.ga")
    parser.add_argument("--llm_trace_file", default="", help="Optional JSON file path to save step-by-step LLM/score trace")
    parser.add_argument("--console_trace", action="store_true", help="Print full hybrid trace (all steps/candidates) to console")
    parser.add_argument("--safe_mode", action="store_true", help="Filter out tools likely to fail import due to complex inputs/params")
    return parser.parse_args()


def _sanitize_chain_for_import(chain, validator, safe_mode=False):
    if not safe_mode:
        return chain, []

    dropped = []
    sanitized = []
    for tool_name in chain:
        t_lower = tool_name.lower()
        if t_lower in UNSAFE_AUTO_TOOLS:
            dropped.append((tool_name, "unsafe_auto_tool"))
            continue
        if validator.validation_ready and tool_name not in validator.installed_tools:
            dropped.append((tool_name, "not_installed"))
            continue
        sanitized.append(tool_name)

    return sanitized, dropped


def _print_console_trace(generation_trace):
    print("\n📋 Hybrid generation trace:")
    for step in generation_trace:
        step_no = step.get("step")
        chain = " -> ".join(step.get("chain", []))
        llm = step.get("llm", {})
        chosen = step.get("chosen")
        stop_reason = step.get("stop_reason")

        print(f"\n--- Step {step_no} ---")
        print(f"Chain: {chain}")
        print(
            "LLM: provider_requested={provider_requested}, provider_used={provider_used}, model={model}, status={status}, picked={picked}".format(
                provider_requested=llm.get("provider_requested"),
                provider_used=llm.get("provider_used"),
                model=llm.get("model"),
                status=llm.get("status"),
                picked=llm.get("picked"),
            )
        )
        if llm.get("error"):
            print(f"LLM error: {llm.get('error')}")

        print("Candidates:")
        for cand in step.get("candidates", []):
            print(
                "  #{rank} id={id} name={name} prob={prob:.6f} heuristic_score={heuristic_score:.6f} selected_by_llm={selected_by_llm}".format(
                    rank=cand.get("rank"),
                    id=cand.get("id"),
                    name=cand.get("name"),
                    prob=float(cand.get("prob", 0.0)),
                    heuristic_score=float(cand.get("heuristic_score", 0.0)),
                    selected_by_llm=cand.get("selected_by_llm"),
                )
            )

        if chosen:
            print(
                "Chosen: id={id} name={name} prob={prob:.6f} heuristic_score={heuristic_score:.6f}".format(
                    id=chosen.get("id"),
                    name=chosen.get("name"),
                    prob=float(chosen.get("prob", 0.0)),
                    heuristic_score=float(chosen.get("heuristic_score", 0.0)),
                )
            )
        if stop_reason:
            print(f"Stop reason: {stop_reason}")


def main():
    args = _parse_args()
    print("🚀 Initializing Workflow Generator...")

    # 1. Load the Bridge Dictionary (Local Source of Truth)
    tool_map = {}
    if os.path.exists(BRIDGE_DICT_PATH):
        with open(BRIDGE_DICT_PATH, 'r') as f:
            tool_map = json.load(f)
        print(f"✅ Loaded bridge dictionary from {BRIDGE_DICT_PATH}")
    else:
        print(f"⚠️ Warning: Bridge dictionary not found at {BRIDGE_DICT_PATH}. IDs may be incomplete.")

    # 2. Load Model and Metadata
    model_manager = ModelManager(MODEL_PATH)
    model_manager.load()

    model = model_manager.get_model()
    reverse_dict, forward_dict, class_weights = model_manager.get_metadata()

    # 3. Predict Sequence
    print(f"AI is dreaming up a workflow starting from '{args.seed_tool}' using mode '{args.mode}'...")

    # --- NEW: VALIDATION LAYER ---
    GALAXY_URL = os.getenv("GALAXY_URL", "http://localhost:8080")
    API_KEY = os.getenv("GALAXY_API_KEY")

    validator = GalaxyValidator(
        GALAXY_URL,
        API_KEY,
        timeout=args.galaxy_timeout,
        skip_validation=args.skip_validation,
        cache_file=args.tools_cache_file,
        cache_ttl=args.tools_cache_ttl,
    )
    generation_trace = None
    if args.mode == "hybrid":
        predicted_chain, generation_trace = hybrid_generate_tool_sequence(
            model=model,
            forward_dict=forward_dict,
            reverse_dict=reverse_dict,
            seed_tool_name=args.seed_tool,
            max_len=args.max_steps,
            top_k=args.top_k,
            top_p=args.top_p,
            temperature=args.temperature,
            repetition_penalty=args.repetition_penalty,
            use_llm=not args.disable_llm,
            llm_model=args.llm_model,
            llm_provider=args.llm_provider,
            validator=validator,
            return_trace=True,
        )
    else:
        predicted_chain = generate_tool_sequence(
            model,
            forward_dict,
            reverse_dict,
            args.seed_tool,
            max_len=args.max_steps,
        )

    if args.llm_trace_file and generation_trace is not None:
        trace_payload = {
            "mode": args.mode,
            "seed_tool": args.seed_tool,
            "llm_provider": args.llm_provider,
            "llm_model": args.llm_model,
            "predicted_chain": predicted_chain,
            "steps": generation_trace,
        }
        trace_dir = os.path.dirname(args.llm_trace_file)
        if trace_dir:
            os.makedirs(trace_dir, exist_ok=True)
        with open(args.llm_trace_file, "w") as trace_file:
            json.dump(trace_payload, trace_file, indent=2)
        print(f"🧾 Saved LLM trace to: {args.llm_trace_file}")

    if args.console_trace and generation_trace is not None:
        _print_console_trace(generation_trace)

    if generation_trace is not None:
        statuses = []
        for step in generation_trace:
            llm_meta = step.get("llm", {})
            status = llm_meta.get("status")
            if status and status != "ok" and status != "disabled":
                statuses.append((status, llm_meta.get("error")))
        if statuses:
            uniq = []
            for item in statuses:
                if item not in uniq:
                    uniq.append(item)
            print("⚠️ LLM fallback statuses detected:")
            for status, err in uniq:
                if err:
                    print(f"   - {status}: {err}")
                else:
                    print(f"   - {status}")

    final_chain = validator.validate_and_fix_chain(predicted_chain, tool_map)

    sanitized_chain, dropped = _sanitize_chain_for_import(final_chain, validator, safe_mode=args.safe_mode)
    if dropped:
        print("⚠️ Safe-mode removed tools before .ga export:")
        for tool_name, reason in dropped:
            print(f"   - {tool_name} ({reason})")
    if sanitized_chain:
        final_chain = sanitized_chain
    else:
        print("⚠️ Safe-mode removed all predicted tools; falling back to original validated chain.")

    if validator.validation_ready:
        for name in final_chain:
            tool_map[name] = validator.installed_tools[name]['full_id']

    print("\n✅ Validated Sequence (Exists on Instance):")
    print(" -> ".join(final_chain))

    print("\n✅ AI Predicted Sequence:")
    print(" -> ".join(predicted_chain))

    # 4. Assemble .ga (Pass only installed tools!)
    print("Assembling .ga file using installed tools only...")
    workflow_json = create_galaxy_workflow(
        final_chain,
        tool_mapping=tool_map,
        workflow_name=args.workflow_name
    )

    with open(args.output_file, "w") as f:
        json.dump(workflow_json, f, indent=4)

    print(f"\n✨ Done! File saved as: {args.output_file}")
    print("Action: Import this file into your Galaxy 'Workflows' menu.")

if __name__ == "__main__":
    main()