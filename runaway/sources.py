"""Explicit ingestion and UTF-8 bounded, traceable source chunks."""
import json
from pathlib import Path

from .card import canonical, digest
from .profile import validate_sources


def load_sources(path):
    path = Path(path)
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".json":
        return validate_sources(json.loads(text))
    return validate_sources({"schema_version": 1, "sources": [
        {"id": "narrative", "episode_id": "provided_narrative", "role": "user", "text": text}]})


def chunks(sources, limit=16000):
    """Preserve order/roles; split long messages with 128-character overlap.

    Chunks stop at episode boundaries. Quotes remain substrings of original sources.
    Fragment offsets count Unicode characters, while the call limit counts UTF-8 bytes.
    """
    validate_sources(sources)
    if type(limit) is not int or not 2000 <= limit <= 128000:
        raise ValueError("chunk-bytes must be between 2000 and 128000")
    result, current, segments = [], [], []

    def size(items):
        return len(canonical({"schema_version": 1, "sources": items}).encode())

    def flush():
        if current:
            result.append({"sources": {"schema_version": 1, "sources": list(current)},
                           "segments": list(segments)})
            current.clear()
            segments.clear()

    for source in sources["sources"]:
        if current and current[-1]["episode_id"] != source["episode_id"]:
            flush()
        if size([source]) <= limit:
            if size(current + [source]) > limit:
                flush()
            current.append(source)
            segments.append({"source_id": source["id"], "start": 0, "end": len(source["text"])})
            continue
        flush()
        start, text = 0, source["text"]
        while start < len(text):
            lo, hi = start + 1, len(text)
            end = start
            while lo <= hi:
                mid = (lo + hi) // 2
                if size([{**source, "text": text[start:mid]}]) <= limit:
                    end, lo = mid, mid + 1
                else:
                    hi = mid - 1
            if end <= start:
                raise ValueError("Source metadata cannot fit into a chunk")
            if end < len(text):
                boundary = text.rfind("\n\n", start + (end - start) // 2, end)
                if boundary != -1:
                    end = boundary + 2
            fragment = {**source, "text": text[start:end]}
            result.append({"sources": {"schema_version": 1, "sources": [fragment]},
                           "segments": [{"source_id": source["id"], "start": start, "end": end}]})
            if end == len(text):
                break
            start = end - min(128, (end - start) // 4)
    flush()
    return result


def plan(sources, limit=16000, budget=2400):
    if type(budget) is not int or budget <= 0:
        raise ValueError("budget-chars must be positive")
    parts = chunks(sources, limit)
    return {"source_sha256": digest(canonical(sources)), "source_count": len(sources["sources"]),
            "chunk_bytes": limit, "budget_characters": budget, "chunks": [
                {"index": i, "bytes": len(canonical(p["sources"]).encode()), "segments": p["segments"]}
                for i, p in enumerate(parts)],
            "model_calls_upper_bound": len(parts) * 2 + (1 if len(parts) > 1 else 0) + 2,
            "note": "Extraction and support review per chunk, cross-chunk linking if needed, compact generation and review. No automatic retries. Not a token or price estimate."}
