"""Serial-only diagnostic decorator for a separately authorized, single invocation.

No CLI entry point, service backend, retries or authorization. The caller retains
its pinned runtime, per-child guard and finite call gate. Never wrap concurrent
users of generation.run_bounded. This is not used by any sealed experiment.
"""
import time
from unittest.mock import patch
from runaway import generation


class CapturedGenerationFailure(ValueError):
    def __init__(self, provenance):
        super().__init__('Generation failed; sanitized completion metadata retained; no card produced')
        self.provenance = provenance


def capture_once(invoke, *, model):
    """Call invoke exactly once and preserve safe metadata if its parser fails.

    observe forwards all arguments unchanged. Existing timeout/provenance errors
    pass through unchanged; partial messages never become a successful result.
    Return status and event counts do not establish an upstream failure cause.
    """
    completed = []
    original = generation.run_bounded

    def observe(*args, **kwargs):
        start = time.monotonic()
        result = original(*args, **kwargs)
        progress = generation.progress_metadata(result.stdout, result.stderr)
        progress.pop('observed_cli_thread_ids', None)
        completed.append({'returncode': result.returncode,
                          'elapsed_seconds': round(time.monotonic()-start, 3),
                          'progress': progress})
        return result

    try:
        with patch.object(generation, 'run_bounded', observe):
            return invoke()
    except Exception as exc:
        if getattr(exc, 'provenance', None) is not None or not completed:
            raise
        # A one-child guard belongs to the caller. Reject accidental multi-child
        # use here rather than interpreting any completion as a repaired answer.
        progress = completed[-1]['progress']
        raise CapturedGenerationFailure({
            'backend': 'codex', 'model_requested': model, 'resolved_model': None,
            'usage': progress['usage'], 'observed_completed_children': len(completed),
            'completion': completed[-1], 'cause_established': False,
            'partial_answer_accepted': False, 'automatic_retry': False}) from None
