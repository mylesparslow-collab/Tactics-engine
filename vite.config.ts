import { defineConfig } from 'vite';
import { packAssets } from './tools/build/packAssets.ts';
declare const process: { env: Record<string, string | undefined> };
// SINGLE=1 builds for publishing as an artifact: everything is inlined into the bundle except unit sprites
// (sheets + stills) and any asset over 32 KB, which ship as separate files so the JS stays under the 16 MB per-file cap.
export default defineConfig({
  base: './',
  // Production builds pack stills, tiles and UI kit art into one file (see tools/build/packAssets.ts); SINGLE keeps them loose.
  plugins: process.env.SINGLE ? [] : [packAssets()],
  build: process.env.SINGLE
    ? { assetsInlineLimit: (file: string, content: { length: number }) => !/[\\/]content[\\/]sprites[\\/]/.test(file) && content.length < 32_000, chunkSizeWarningLimit: 20_000 }
    : {},
});
