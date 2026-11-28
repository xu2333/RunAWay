// The desktop selection can contain a clock label between message bodies. Match
// every paragraph and label against the plain selection before excluding any label.
const clockLabel = /^(?:(?:0?[1-9]|1[0-2]):[0-5]\d[ \u00a0\u202f][ap]m|(?:[01]?\d|2[0-3]):[0-5]\d|(?:上午|下午)\s*(?:0?[1-9]|1[0-2]):[0-5]\d)$/i;

function timestampedMessages(plain, fragment) {
  const parts = plainParagraphs(plain);
  if (!parts || fragment.querySelector('br, img, pre, table, ul, ol, hr')) return null;
  const walker = document.createTreeWalker(fragment, NodeFilter.SHOW_TEXT);
  const messages = [];
  let index = 0, body = null, previousParagraph = null;
  for (let node = walker.nextNode(); node; node = walker.nextNode()) {
    if (!node.textContent.trim()) continue;
    const parent = node.parentElement;
    const paragraph = parent?.closest('p');
    if (paragraph && paragraph === previousParagraph) continue; // Inline formatting in one paragraph.
    previousParagraph = paragraph;
    const part = parts[index++];
    if (!part) return null;
    if (paragraph) {
      if (part.text !== paragraph.textContent) return null;
      if (!body) {
        body = paragraph.parentElement;
        messages.push(part.text);
      } else if (body === paragraph.parentElement) {
        messages[messages.length - 1] += part.separator + part.text;
      } else return null; // Missing separator between two different message bodies.
    } else {
      if (!body || parent?.tagName !== 'SPAN' || body.contains(parent) ||
          part.text !== node.textContent || !clockLabel.test(part.text)) return null;
      body = null;
    }
  }
  return index === parts.length && messages.length >= 2 ? messages : null;
}

export function clipboardMessages(plain, html) {
  if (!plain || plain.length > 64000 || !html || html.length > 1000000) return null;
  const template = document.createElement('template');
  template.innerHTML = html;
  const articles = [...template.content.querySelectorAll('[role="article"]')];
  if (!articles.length) return timestampedMessages(plain, template.content);
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

export function groupParagraphs(paragraphs, roles) {
  const turns=[];
  for(const [i,{text,separator}] of paragraphs.entries()){
    const role=roles[i];
    if(role==='exclude') continue;
    const last=turns.at(-1);
    if(last?.role===role) last.text+=separator+text;
    else turns.push({role,text});
  }
  return turns;
}
