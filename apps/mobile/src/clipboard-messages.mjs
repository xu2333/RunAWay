// Compare the inert clipboard markup to the plain text the browser actually pasted.
// If its numbered message boundaries cannot reproduce that text, keep the normal text path.
export function clipboardMessages(plain, html) {
  if (!plain || plain.length > 64000 || !html || html.length > 1000000) return null;
  const template = document.createElement('template');
  template.innerHTML = html;
  const articles = [...template.content.querySelectorAll('[role="article"]')];
  if (articles.length < 2 || articles.length > 300) return null;
  const start = Number(articles[0].getAttribute('aria-posinset'));
  const total = Number(articles[0].getAttribute('aria-setsize'));
  if (!Number.isSafeInteger(start) || !Number.isSafeInteger(total) ||
      start < 1 || start + articles.length - 1 > total) return null;

  const texts = [];
  for (const [i, article] of articles.entries()) {
    if (Number(article.getAttribute('aria-posinset')) !== start + i ||
        Number(article.getAttribute('aria-setsize')) !== total) return null;
    const paragraphs = [...article.querySelectorAll('p')];
    const text = paragraphs.map(p => p.textContent).join('\n\n');
    if (!text.trim()) return null;
    texts.push(text);
  }
  return texts.join('\n\n') === plain ? texts : null;
}

// Without numbered messages the visitor supplies the roles. Preserve the literal
// separators for neighbouring paragraphs they confirm belong to the same speaker.
export function plainParagraphs(raw) {
  if (raw.length > 64000 || /^\s*[[{<#❯⏺]/.test(raw)) return null;
  if (/^\s*(?:用户|我|助手|工具|user|assistant|tool|你说|you said|chatgpt\s*(?:说|said))\s*(?:[:：]|$)/im.test(raw)) return null;
  const pieces = raw.split(/(\n[ \t]*\n(?:[ \t]*\n)*)/);
  const paragraphs = pieces.filter((_, index) => index % 2 === 0);
  if (paragraphs.length < 3 || paragraphs.length > 100 || paragraphs.some(p=>!p.trim())) return null;
  return paragraphs.map((text,i)=>({text, separator:i ? pieces[i*2-1] : ''}));
}

export function groupParagraphs(paragraphs, selected) {
  const turns=[];
  for(const [i,{text,separator}] of paragraphs.entries()){
    const role=selected[i] ? 'user' : 'assistant';
    const last=turns.at(-1);
    if(last?.role===role) last.text+=separator+text;
    else turns.push({role,text});
  }
  return turns;
}
