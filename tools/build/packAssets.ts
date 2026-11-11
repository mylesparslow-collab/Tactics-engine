// Build-time asset packing (production build only; `vite dev` serves the loose files as before).
// Small images that are loaded through `import.meta.glob(..., { query: '?url' })` are concatenated into ONE pack
// file instead of being emitted individually (itch.io caps a build at 1,000 files). At startup src/render/packs.ts
// fetches the pack once and turns each entry into a blob: URL, so every consumer still receives a plain URL string.
// New files matching RULES are picked up automatically; nothing has to be registered.
import { createHash } from 'node:crypto';
import { readdirSync, readFileSync, statSync } from 'node:fs';
import { extname, join, resolve, sep } from 'node:path';

/** Which files get packed, as POSIX paths relative to the project root. */
const RULES: RegExp[] = [
  /^content\/sprites\/[^/]+_still\.png$/, // unit stills (the sheets stay loose: big, and loaded lazily per unit)
  /^content\/tiles\//,                    // terrain tiles and props
  /^src\/ui\/kit\//,                      // UI kit art
];
const MIME: Record<string, string> = { '.png': 'image/png', '.webp': 'image/webp', '.svg': 'image/svg+xml', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.gif': 'image/gif' };
const VIRTUAL = 'virtual:asset-pack', RESOLVED = '\0' + VIRTUAL;
const RUNTIME = '/src/render/packs.ts';

function walk(dir: string, out: string[] = []): string[] {
  for (const e of readdirSync(dir, { withFileTypes: true })) {
    const p = join(dir, e.name);
    if (e.isDirectory()) walk(p, out); else out.push(p);
  }
  return out;
}

export function packAssets() {
  let root = '';
  const entries = new Map<string, { off: number; len: number; mime: string }>(); // abs path -> slice of the pack
  let packName = '', packData: Buffer = Buffer.alloc(0);
  return {
    name: 'brinewake-pack-assets',
    apply: 'build' as const,
    enforce: 'pre' as const,
    configResolved(c: { root: string }) { root = resolve(c.root); },
    buildStart(this: { emitFile(f: unknown): void }) {
      entries.clear();
      const parts: Buffer[] = []; let off = 0;
      const files = ['content', 'src/ui/kit'].flatMap(d => { try { return walk(join(root, d)); } catch { return []; } }).sort();
      for (const abs of files) {
        const rel = abs.slice(root.length + 1).split(sep).join('/');
        const mime = MIME[extname(abs).toLowerCase()];
        if (!mime || !RULES.some(r => r.test(rel)) || !statSync(abs).isFile()) continue;
        const buf = readFileSync(abs);
        entries.set(abs, { off, len: buf.length, mime }); parts.push(buf); off += buf.length;
      }
      packData = Buffer.concat(parts);
      packName = `assets/pack-${createHash('sha1').update(packData).digest('hex').slice(0, 8)}.bin`;
      if (entries.size) this.emitFile({ type: 'asset', fileName: packName, source: packData });
    },
    resolveId(id: string) { return id === VIRTUAL ? RESOLVED : null; },
    load(id: string) {
      if (id === RESOLVED) return `export const file = ${JSON.stringify(entries.size ? packName : '')};`;
      // `<file>?url` of a packed file: export its blob: URL (the pack is awaited before any module that imports it runs)
      const [path, query] = id.split('?');
      const e = query === 'url' ? entries.get(resolve(path)) : undefined;
      if (!e) return null;
      return `import { slice } from ${JSON.stringify(RUNTIME)};\nexport default slice(${e.off}, ${e.len}, ${JSON.stringify(e.mime)});`;
    },
  };
}
