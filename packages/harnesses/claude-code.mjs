// Unscoped rules load at session start without taking over the user's CLAUDE.md.
export default Object.freeze({
  id: 'claude-code', label: 'Claude Code', path: '.claude/rules/runaway.md',
  preamble: '', append: false,
  documentation: 'https://code.claude.com/docs/en/memory#organize-rules-with-clauderules',
  note: 'Start a fresh session with project rules enabled. Check /context for loaded memory files.',
  maxBytes: 24000,
});
