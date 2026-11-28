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
