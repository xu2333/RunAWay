"""Reject damaged text; never guess what a replacement character used to mean."""


def require_intact(text, label='text'):
    if not isinstance(text, str):
        raise ValueError(label + ' must be text')
    for index, char in enumerate(text):
        if char == '\ufffd' or 0xD800 <= ord(char) <= 0xDFFF:
            raise ValueError(f'Text integrity error in {label} at codepoint {index}: replacement character or unpaired surrogate; restore the original text, do not guess a repair')
    return text
