// A dedicated rule avoids changing the project's shared AGENTS.md.
export default Object.freeze({
  id: 'antigravity', label: 'Antigravity', path: '.agents/rules/runaway.md',
  preamble: '---\ntrigger: always_on\ndescription: "RunAWay personal judgment preferences"\n---\n\n',
  append: false,
  documentation: 'https://antigravity.google/docs/rules',
  note: 'Start a fresh workspace session. This rule uses trigger: always_on; other active rules still apply.',
  maxBytes: 24000,
});
