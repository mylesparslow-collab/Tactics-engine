type Kid = Node | string | null | undefined | false;
export function h<K extends keyof HTMLElementTagNameMap>(
  tag: K, props?: Record<string, unknown> | null, ...kids: Kid[]
): HTMLElementTagNameMap[K] {
  const el = document.createElement(tag);
  for (const [k, v] of Object.entries(props ?? {})) {
    if (v === undefined || v === null || v === false) continue;
    if (k === 'class') el.className = String(v);
    else if (k.startsWith('on') && typeof v === 'function') (el as unknown as Record<string, unknown>)[k] = v;
    else if (k === 'disabled') (el as HTMLButtonElement).disabled = !!v;
    else el.setAttribute(k, String(v));
  }
  for (const kid of kids) if (kid !== null && kid !== undefined && kid !== false) el.append(kid);
  return el;
}
export function clear(el: HTMLElement) { while (el.firstChild) el.removeChild(el.firstChild); }
