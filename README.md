# Tactics Engine (prototype)

An original, data-driven, turn-based tactics game engine for the browser: isometric grid with height,
AP-based movement and abilities, essence-funded deployment, missions with scripted objectives, and campaigns.
All units, abilities, statuses, terrain, maps, missions and campaigns are JSON in `content/`; see
[CONTENT_SCHEMA.md](CONTENT_SCHEMA.md). Art is placeholder (procedural shapes) until real sprites are supplied
via `sprite.image`.

```
npm install
npm run dev        # play at http://localhost:5173
npm test           # rules + content validation + AI-vs-AI smoke tests
npm run build      # static build in dist/ (works offline / any static host)
```

## Layout
- `src/engine/` — rules only, no DOM. `game.ts` (state + actions), `ai.ts` (greedy opponent), `content.ts`
  (validation, defaults, labels), `campaign.ts` (progress + roster), `bundled.ts` (loads `content/`).
- `src/render/`, `src/ui/`, `src/main.ts` — canvas isometric renderer, sprites, HUD, menus.
- `content/` — all game data. Drop new maps in `content/maps/` and missions in `content/missions/`; they load automatically.
- `tests/` — vitest suite.

## Controls
Click a unit to select it (blue = where it can walk), pick an ability, click a target. Click a card in your
warband, then a green tile to deploy. `E`/`Enter` ends the turn, `Esc` cancels.
