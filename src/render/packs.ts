// Runtime half of tools/build/packAssets.ts. Awaits the packed-asset file once (top-level await, so every module
// that imports a packed `?url` evaluates after it) and hands out blob: URLs for slices of it.
import { file } from 'virtual:asset-pack';

const blob: Blob | null = file ? await (await fetch(new URL(file, document.baseURI))).blob() : null;

export function slice(off: number, len: number, mime: string): string {
  return URL.createObjectURL(blob!.slice(off, off + len, mime));
}
