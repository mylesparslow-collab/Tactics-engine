# Tactics Engine (prototype)

An original, data-driven, turn-based tactics game engine for the browser: isometric grid with height,
AP-based movement and abilities, essence-funded deployment, missions with scripted objectives, and campaigns.
All units, abilities, statuses, terrain, maps, missions and campaigns are JSON in `content/`; see
[CONTENT_SCHEMA.md](CONTENT_SCHEMA.md). Art is placeholder (procedural shapes) until real sprites are supplied
via `sprite.image`.

```
npm install
npm run dev        # play at http://localhost:5173
npm test           # rules tests, real-content validation, AI-vs-AI battles for every faction
npm run build      # static build in dist/ (works offline / any static host)
```

## Layout
- `src/engine/` — rules only, no DOM. `game.ts` (state + actions), `ai.ts` (greedy opponent), `content.ts`
  (validation, defaults, labels), `campaign.ts` (progress + roster), `bundled.ts` (loads `content/`).
- `src/render/`, `src/ui/`, `src/main.ts` — canvas isometric renderer, sprites, HUD, menus.
- `content/` — all game data. Drop new maps in `content/maps/` and missions in `content/missions/`; they load automatically.
- `tests/` — vitest suite. Rules tests use the small placeholder set in `tests/fixtures/content/`, so real content
  can change freely; `tests/content.test.ts` validates the real `content/` and plays every faction.

## Modes
- **Campaign**: missions in order, unlocks carry forward, progress saved in the browser.
- **Skirmish missions**: any mission file.
- **Quick battle**: pick your faction, the opponent's faction and a map; decks are built from each faction's cards.

## Controls
Click a unit to select it (blue = where it can walk), pick an ability, click a target. Click a card in your
warband, then a green tile to deploy. `E`/`Enter` ends the turn, `Esc` or right-click cancels, `1-9` pick abilities, `Q`/`R` rotate the camera.
In the browser console, `__tactics.game` is the live game state (handy for debugging content).

## Hosting (Cloudflare Pages)

`.github/workflows/deploy.yml` tests, builds, and deploys `dist/` to the Cloudflare Pages project `ebb` on every push to
`main` (production) and on every pull request (a preview URL). It needs two repository secrets, set under
Settings, Secrets and variables, Actions: `CLOUDFLARE_API_TOKEN` (a token with the "Cloudflare Pages: Edit" permission)
and `CLOUDFLARE_ACCOUNT_ID`. Without them the workflow still builds and tests, and skips the deploy.
