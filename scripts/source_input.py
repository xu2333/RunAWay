"""Explicit source normalization;role labels are annotations,not authenticated origin."""
import copy
import json
import re

from runaway.constraint_extract import parse_answer
from runaway.profile import validate_sources
from runaway.text_integrity import require_intact

FORMATS = ('auto', 'narrative', 'role-text', 'sources-json')
ROLES = {'用户': 'user', '我': 'user', 'user': 'user',
         '助手': 'assistant', 'assistant': 'assistant', '工具': 'tool', 'tool': 'tool',
         '上下文': 'context', 'context': 'context', '系统': 'context', 'system': 'context',
         'developer': 'context'}
LABEL = re.compile(r'^(用户|我|user|助手|assistant|工具|tool|上下文|context|系统|system|developer)[ \t]*[:：][ \t]?', re.I)
FENCE = re.compile(r'^[ \t]{0,3}(`{3,}|~{3,})([^\r\n]*)')
CONTROL = re.compile(r'^\ufeff?\s*<(heartbeat|automation|subagent_notification|goal_continuation|'
                     r'send_user_message_question_reply|external_codex_apps_open_page|'
                     r'in-app-browser-context|environment_context|turn_aborted)(?:[\s/>]|$)', re.I)
MESSAGES = {
    'explicit_roles_required': 'Role-labelled text needs --input-format role-text; choose narrative explicitly only for your own prose.',
    'invalid_source_json': 'Use RunAWay source JSON with schema_version and sources, or select another explicit input format.',
    'ambiguous_transcript': 'Role text needs column-zero speaker labels, nonempty messages and closed code fences.',
    'automated_user_source': 'A runtime/control block cannot be user evidence; annotate it as context or review the source manually.',
    'source_too_large': 'Selected text and normalized source JSON must each fit 64 KB; select a smaller complete episode.',
    'invalid_source_text': 'Source text must be intact, nonempty Unicode; no repair or truncation was made.',
    'invalid_input_format': 'Choose auto, narrative, role-text or sources-json.',
}


class SourceInputError(ValueError):
    def __init__(self, code):
        super().__init__(MESSAGES[code])
        self.code = code


def selected_sources(value):
    """Validate the normalized payload before preparation or importing a packet."""
    try:
        validate_sources(value)
    except (ValueError, TypeError, KeyError):
        raise SourceInputError('invalid_source_text') from None
    for item in value['sources']:
        if item['role'] == 'user' and CONTROL.match(item['text']):
            raise SourceInputError('automated_user_source')
    # Match the actual prepared source file's encoding,including formatting.
    if len((json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode()) > 64000:
        raise SourceInputError('source_too_large')
    return copy.deepcopy(value)


def role_text(raw):
    sources, current, fence = [], None, None
    for index, line in enumerate(raw.splitlines(keepends=True)):
        # A UTF-8 BOM is a file marker,not message text or a speaker label.
        if index == 0 and line.startswith('\ufeff'):
            line = line[1:]
        label = LABEL.match(line) if fence is None else None
        if label:
            if current is not None:
                sources.append(current)
            current = {'id': 'message-%d' % (len(sources) + 1), 'episode_id': 'submitted',
                       'role': ROLES[label.group(1).lower()], 'text': line[label.end():]}
            body = current['text']
        elif current is not None:
            current['text'] += line
            body = line
        elif line.strip():
            raise SourceInputError('ambiguous_transcript')
        else:
            continue
        mark = FENCE.match(body)
        if fence is None and mark:
            fence = (mark.group(1)[0], len(mark.group(1)))
        elif fence is not None and mark and mark.group(1)[0] == fence[0] and len(mark.group(1)) >= fence[1] and not mark.group(2).strip():
            fence = None
    if fence is not None or current is None:
        raise SourceInputError('ambiguous_transcript')
    sources.append(current)
    if any(not message['text'].strip() for message in sources):
        raise SourceInputError('ambiguous_transcript')
    return selected_sources({'schema_version': 1, 'sources': sources})


def normalize(raw, input_format='auto', *, json_filename=False):
    if input_format not in FORMATS:
        raise SourceInputError('invalid_input_format')
    try:
        require_intact(raw, 'selected source')
    except ValueError:
        raise SourceInputError('invalid_source_text') from None
    if not raw.strip():
        raise SourceInputError('invalid_source_text')
    if len(raw.encode()) > 64000:
        raise SourceInputError('source_too_large')
    without_bom = raw[1:] if raw.startswith('\ufeff') else raw
    if input_format == 'auto':
        if json_filename or without_bom.lstrip().startswith(('{', '[')):
            input_format = 'sources-json'
        elif any(LABEL.match(line) for line in without_bom.splitlines()):
            raise SourceInputError('explicit_roles_required')
        else:
            input_format = 'narrative'
    if input_format == 'sources-json':
        try:
            value = parse_answer(without_bom)
            validate_sources(value)
        except (ValueError, TypeError, KeyError, RecursionError):
            raise SourceInputError('invalid_source_json') from None
        return selected_sources(value)
    if input_format == 'role-text':
        return role_text(raw)
    return selected_sources({'schema_version': 1, 'sources': [
        {'id': 'narrative', 'episode_id': 'provided_narrative', 'role': 'user', 'text': raw}]})


def role_counts(sources):
    return {role: sum(item['role'] == role for item in sources['sources'])
            for role in ('user', 'assistant', 'tool', 'context')}
