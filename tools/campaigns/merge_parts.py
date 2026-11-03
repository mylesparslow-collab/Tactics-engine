#!/usr/bin/env python3
"""Merge tools/campaigns/parts/<campaignId>.json into content/campaigns.json (Concord's campaign stays first).
Each part file is one CampaignDef: {"id", "name", "description", "faction", "startingRoster", "missions"}."""
import json
from pathlib import Path

here = Path(__file__).resolve().parent
out = here.parents[1] / 'content' / 'campaigns.json'
camps = json.loads(out.read_text())
ORDER = ['light_at_lantern_shoal', 'the_weeping_shelf', 'the_weight_returns', 'compact_mother_hull',
         'the_long_watch', 'coralspire', 'the_carrion_wheel', 'what_feeds_below']
for p in sorted((here / 'parts').glob('*.json')):
    d = json.loads(p.read_text())
    cid = d.pop('id', p.stem)
    camps[cid] = d
camps = {k: camps[k] for k in sorted(camps, key=lambda k: ORDER.index(k) if k in ORDER else 99)}
out.write_text(json.dumps(camps, indent=2, ensure_ascii=False) + '\n')
print('campaigns:', ', '.join(camps))
