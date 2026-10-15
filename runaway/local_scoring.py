"""Optional local Qwen3 GGUF teacher forcing. No network or model downloads."""
import importlib.metadata
import json
import math
from pathlib import Path
import time

from .card import canonical, digest
from .evaluation import CONDITIONS, file_digest, prefix, summarize, validate_dataset
from .pipeline import write_once


def log_probability(logits, token):
    import numpy as np
    values = np.asarray(logits, dtype=np.float64)
    maximum = values.max()
    result = float(values[token] - maximum - np.log(np.exp(values - maximum).sum()))
    if not math.isfinite(result):
        raise ValueError("Nonfinite token probability")
    return result


def last_logits(model):
    import numpy as np
    return np.ctypeslib.as_array(model._ctx.get_logits_ith(-1), shape=(model.n_vocab(),))


def teacher_force(model, prefix_ids, target_ids, logits_reader=last_logits):
    if not prefix_ids or not target_ids:
        raise ValueError("Empty prefix or target")
    model.reset()
    model.eval(prefix_ids)
    result = []
    for index, token in enumerate(target_ids):
        result.append(log_probability(logits_reader(model), token))
        if index + 1 < len(target_ids):
            model.eval([token])
    return result


def validate_backend(model):
    p = model.tokenize(b"The capital of France is", add_bos=False)
    t = model.tokenize(b" Paris.", add_bos=False)
    streamed = teacher_force(model, p, t)
    try:
        model.reset()
        model._logits_all = True
        model.eval(p + t)
        batched = [log_probability(model.scores[len(p) + i - 1], token) for i, token in enumerate(t)]
    finally:
        model._logits_all = False
        model.reset()
    error = max(abs(a - b) for a, b in zip(streamed, batched))
    if error > .01:
        raise ValueError("Streaming and batched causal backend checks disagree")
    return {"max_logprob_error": error, "streamed_logprobs": streamed, "batched_logprobs": batched,
            "note": "Short backend check only; not a bound on long-context numerical error."}


def encode_prefix(model, snapshot, memory, context):
    tok = lambda text, special: model.tokenize(text.encode(), add_bos=False, special=special)
    # Only trusted delimiters are special; user content uses ordinary tokens.
    return (tok("<|im_start|>system\n", True) + tok(snapshot["system"], False) +
            tok("<|im_end|>\n<|im_start|>user\n", True) + tok(prefix(memory, context), False) +
            tok("<|im_end|>\n<|im_start|>assistant\n<think>\n\n</think>\n\n", True))


def run(snapshot, dataset, destination, progress=lambda message: None):
    readiness = validate_dataset(dataset, snapshot)
    try:
        import llama_cpp
        version = importlib.metadata.version("llama-cpp-python")
    except ImportError:
        raise ValueError("Local scoring requires optional llama-cpp-python==0.3.36 and numpy; no download was attempted")
    if version != "0.3.36":
        raise ValueError("Scorer's low-level logits access was validated with llama-cpp-python==0.3.36 only")
    for model in snapshot["models"]:
        if file_digest(model["path"]) != model["sha256"]:
            raise ValueError("Local model changed since freezing")
    out = Path(destination)
    out.mkdir(mode=0o700, parents=True, exist_ok=False)
    write_once(out / "snapshot.private.json", snapshot)
    write_once(out / "dataset.private.json", dataset)
    write_once(out / "readiness.private.json", readiness)
    rows = []
    try:
        for index, record in enumerate(snapshot["models"]):
            progress(f"model-{index}: loading frozen local GGUF")
            model = llama_cpp.Llama(model_path=record["path"], n_ctx=snapshot["n_ctx"], n_batch=512,
                                    n_gpu_layers=snapshot["gpu_layers"], logits_all=False, verbose=False, seed=0)
            try:
                if model.metadata.get("general.architecture") != "qwen3" or model.metadata.get("tokenizer.ggml.pre") != "qwen2":
                    raise ValueError("This evaluator supports the validated Qwen3 chat template only")
                check = validate_backend(model)
                write_once(out / f"model-{index}.backend.private.json", {
                    "model_sha256": record["sha256"], "llama_cpp_python": version,
                    "backend_check": check, "metadata": model.metadata,
                    "system_info": llama_cpp.llama_print_system_info().decode(errors="replace")})
                # Tokenize and check every case/condition before any dataset score.
                prepared = []
                for case in dataset["cases"]:
                    raw = case["target"]["text"].encode()
                    target_ids = model.tokenize(raw, add_bos=False, special=False)
                    if not target_ids or model.detokenize(target_ids) != raw:
                        raise ValueError("Target byte round-trip failed")
                    for condition in CONDITIONS:
                        memory = snapshot["memories"][condition]
                        ids = encode_prefix(model, snapshot, memory, case["context"])
                        if len(ids) + len(target_ids) > model.n_ctx():
                            raise ValueError("Context exceeds frozen limit; no text was truncated")
                        prepared.append((case, condition, ids, target_ids))
                for case, condition, ids, target_ids in prepared:
                    progress(f"model-{index}: {case['id']} / {condition}")
                    start = time.monotonic()
                    logs = teacher_force(model, ids, target_ids)
                    memory = snapshot["memories"][condition]
                    row = {"model_sha256": record["sha256"], "case_id": case["id"], "condition": condition,
                           "target_sha256": digest(case["target"]["text"]), "target_ids": target_ids,
                           "target_logprobs": logs, "prefix_ids_sha256": digest(canonical(ids)),
                           "prefix_tokens": len(ids), "memory_tokens": len(model.tokenize(memory.encode(), add_bos=False, special=False)),
                           "elapsed_seconds": time.monotonic() - start}
                    rows.append(row)
                    write_once(out / f"model-{index}.{case['id']}.{condition}.private.json", row)
            finally:
                model.close()
        report = summarize(snapshot, dataset, rows)
        write_once(out / "summary.private.json", report)
        return report
    except Exception as exc:
        write_once(out / "failure.private.json", {"status": "incomplete", "completed_scores": len(rows),
                   "error_type": type(exc).__name__, "note": "Partial rows are diagnostics, not a complete comparison. No automatic retries."})
        raise
