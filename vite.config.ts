import { defineConfig } from 'vite';
declare const process: { env: Record<string, string | undefined> };
// SINGLE=1 inlines assets into the bundle (used to publish as one self-contained page).
export default defineConfig({
  base: './',
  build: process.env.SINGLE ? { assetsInlineLimit: 1_000_000 } : {},
});
