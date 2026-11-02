import './style.css';
import { loadBundledContent } from './engine/bundled';
import { validateContent } from './engine/content';
import { loadProgress, rosterFor } from './engine/campaign';
import { showBriefing, showMenu, type MissionChoice } from './ui/menu';
import { GameSession } from './ui/session';
import { installAudioUnlock, playBattleStart, preloadBanks, preloadBattleBanks } from './audio/sfx';
import { enterBattle, enterMenu, seedOf } from './audio/scenes';
import { installUiSounds } from './audio/ui';
import { soundButton } from './ui/soundpanel';

installAudioUnlock();
installUiSounds();
preloadBanks();

const content = loadBundledContent();
const errors = validateContent(content);
const root = document.getElementById('app')!;
let session: GameSession | null = null;

// The title screen is rebuilt by several flows (back buttons, sub-menus); keep its speaker button there without touching them.
let sbRaf = 0;
new MutationObserver(() => {
  if (sbRaf) return;
  sbRaf = requestAnimationFrame(() => { sbRaf = 0; const t = root.querySelector('.title-scr'); if (t && !t.querySelector('.menu-sound')) t.append(soundButton()); });
}).observe(root, { childList: true, subtree: true });

function menu() {
  session?.destroy(); session = null;
  showMenu(root, content, errors, briefing);
  enterMenu();
}

function briefing(choice: MissionChoice) {
  preloadBattleBanks(); // the player is about to fight
  showBriefing(root, content, choice, () => play(choice), menu);
}

function play(choice: MissionChoice) {
  session?.destroy();
  const roster = choice.campaign ? rosterFor(content, choice.campaign.id, loadProgress(choice.campaign.id)) : undefined;
  const c = choice.campaign;
  const next = c && content.campaigns[c.id].missions[c.index + 1];
  enterBattle(content.missions[choice.missionId]?.map ?? '', seedOf(choice.missionId));
  preloadBattleBanks();
  playBattleStart();
  session = new GameSession(root, {
    content, missionId: choice.missionId, roster, campaign: c,
    onExit: menu,
    onRetry: () => play(choice),
    onNext: c && next ? () => briefing({ missionId: next.mission, campaign: { id: c.id, index: c.index + 1 } }) : undefined,
  });
}

menu();
// Dev-only handle for automated playtests.
if (import.meta.env.DEV) {
  (window as unknown as { brinewake: () => GameSession | null }).brinewake = () => session;
  (window as unknown as { ebbPlay: (id: string) => void }).ebbPlay = id => play({ missionId: id }); // perf/playtest harness
}
