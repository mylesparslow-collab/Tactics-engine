import './style.css';
import { loadBundledContent } from './engine/bundled';
import { validateContent } from './engine/content';
import { loadProgress, rosterFor } from './engine/campaign';
import { showBriefing, showMenu, type MissionChoice } from './ui/menu';
import { GameSession } from './ui/session';

const content = loadBundledContent();
const errors = validateContent(content);
const root = document.getElementById('app')!;
let session: GameSession | null = null;

function menu() {
  session?.destroy(); session = null;
  showMenu(root, content, errors, briefing);
}

function briefing(choice: MissionChoice) {
  showBriefing(root, content, choice, () => play(choice), menu);
}

function play(choice: MissionChoice) {
  session?.destroy();
  const roster = choice.campaign ? rosterFor(content, choice.campaign.id, loadProgress(choice.campaign.id)) : undefined;
  const c = choice.campaign;
  const next = c && content.campaigns[c.id].missions[c.index + 1];
  session = new GameSession(root, {
    content, missionId: choice.missionId, roster, campaign: c,
    onExit: menu,
    onRetry: () => play(choice),
    onNext: c && next ? () => briefing({ missionId: next.mission, campaign: { id: c.id, index: c.index + 1 } }) : undefined,
  });
}

menu();
