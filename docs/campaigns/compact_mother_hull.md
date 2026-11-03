# Campaign 4: "Mother Hull"

Campaign id: compact_mother_hull · Faction: salvage_compact · Mission prefix: sv_

Faction: Salvage Compact (`salvage_compact`). 8 missions. Escalation: carcass skirmish, escort out, escort in, climb and steal back, siege, hunt, hold and extract, last stand. The year is 311 AE, the same year as Campaign 1, and the missions cross it: the Kettle after Varrow dies, the same Archive day seen from the ribs, and Mother Hull on the night the Shoal nearly goes dark. Briefings are Ketta Vane's sled-log, scratched with a nail into the rib-board of her sled. All times in turns. Setting canon: `EBB_world_bible.md`, `bible/history_and_gazetteer.md`.

## Starting roster
- `salvage_compact_ketta_vane`
- `salvage_compact_lamplighter`
- `salvage_compact_lamplighter`
- `salvage_compact_scrapper`
- `salvage_compact_scrapper`
- `salvage_compact_wrecker`
- `salvage_compact_wrecker`
- `salvage_compact_rivet_slinger`
- `sv_spell_cut_and_run_tonic`
- `sv_equip_scrap_vest`

## Recurring characters

**Ketta Vane, Sled-Queen of the Long Salt** (player). The fastest rider on the salt. She has outrun three debts, two wars and her own reputation, and wants exactly one thing: a stretch of open flat with nobody on it. Thinks the Compact is the only honest people on the Ebb because they admit everything is for sale. Short-tempered, generous with other people's money, keeps her goggles on indoors. She starts believing neutrality is just speed. She ends knowing the flat was never empty: something has been holding the sky off it the whole time.

**Odo Brask, Compact fixer.** The same Brask who sells Commander Orrel maps and warnings in Campaign 1. Three coats, one flask, a ledger for every side. He has spent the Compact's money for sixty years buying Lanternkeeper secrets nobody else wanted, and he is the only person in Mother Hull who suspects why the Charter was signed inside her. Calls Ketta "my best investment" and has never once paid her on time. Sells everyone out, always for a reason he will explain later.

**Brother Ashmaw, Fat-Cook of the Burning Chapel.** Head of the Powder-Monks. Broad, calm, ash on his shaven head, blesses every keg by name. He renders leviathan fat into blasting grease and wants the old hulls to burn bright enough to be seen from the Rim, so that someone up there finally asks what the Compact has been guarding. Nobody listens to him. He is right.

**Wren Halloway, the Rimfall Thief.** A Gyre roost-thief on a red-throated frigatebird. Robs the Compact in this campaign and the Lanternkeepers in her own. Cheerful, unrepentant, always one perch higher than you.

**Keeper Absalom Ruddle.** A Lanternkeeper of no fixed lamp, sent down the Hulks in the last week of the year with a pen, a seal and an offer. Grey, polite, exhausted. Has not slept properly since 276 AE and does not mention why. He does not ask the Compact to choose. He tells them they already have.

---

## Mission 1: `sv_breakers_yard` — "Breakers' Yard"
- **Map:** `breakers_yard` (fresh carcass on the wreck line, daylight)
- **Enemy:** `gyre`
- **Type:** skirmish / tutorial: take the carcass, break the camp.
- **Setup:** Ketta Vane pre-placed at (22,15), tag `ketta_vane`. Player keystone (22,16) is the Compact sled-camp lamp. Enemy keystone (9,3) is Torr Ashby's carrion-pole, planted on the old lamp-stone above the carcass. The carcass is the wreck line at (7,6) to (10,6), height 2. Pre-placed Gyre: `gyre_captain_torr_ashby` at (9,5) tag `torr_ashby`; `gyre_salt_crow` at (8,6) and (10,6); `gyre_gullwife` at (11,3); `gyre_roost_runner` at (12,4); `gyre_roostwarden` at (6,7). AI warband: roost_runner, salt_crow x2, gullwife, roostwarden, skua_lancer.
- **Briefing:**
  Sled-log, Ketta Vane. A fresh one came down in the yard three nights ago: a leviathan calf, still oily, ribs like a chapel. Fresh means the fat is good and the bone is soft enough to cut. Fresh also means every bird on the Rim smelled it before we did.

  Torr Ashby's Black Wheel is on it. Vultures on the ribs, roost-folk with hooks on the flats, and a carrion-pole planted on the old lamp-stone like he bought the place. He did not buy the place. Nobody buys the yard. That is the whole point of the yard.

  Lamp oil in every low place, so the kids go first and light it. Wreckers on the carcass, slingers on the hulks. Cut the pole down and the birds lose interest. Birds always lose interest.
- **Victory:** destroy_keystone team 1 (the carrion-pole).
- **Defeat:** destroy_keystone team 0 (the sled-camp lamp), or unit_lost tag `ketta_vane`, or turn_limit 14.
- **Events:**
  1. Turn 1: message from **Torr Ashby** (from the carcass): "Compact! You're late. We left you the smell."
  2. Turn 3: reinforcement, two `gyre_skua_lancer` drop out of the sun onto the east shelf at (27,7) and (28,8), behind the sled-camp (teaches that fliers ignore the trench).
  3. Turn 5: message from **Odo Brask** (signal-mirror from the north hulks): "Ketta, I've already sold the jaw. Try not to dent it."
- **Bonus objective:** End the battle with a Compact unit standing on the carcass (reach_tile team 0, tiles (7,6), (8,6), (9,6), (10,6)).
- **Salvage:** winPearls 30; bonus 20.
- **Victory text:** The pole comes down and the Black Wheel lifts off the ribs in one slow, offended spiral. Ashby circles once, low, and calls down that he will see her at the next one. Ketta waves him off. The calf's fat renders down clear as lamp-oil, and smells, for some reason, of rain.
- **Defeat text:** The birds strip the calf to the bone by dusk. Ketta's crew drags home one jawbone, which Brask had already sold, and an invoice for the dent.
- **Unlocks:** `salvage_compact_bone_sled_rider`, `salvage_compact_snare_tinker`.

## Mission 2: `sv_cut_and_run` — "Cut and Run"
- **Map:** `the_kettle` (market day, stalls standing, Concord toll-agents at the north rim)
- **Enemy:** `salt_concord`
- **Type:** escort out.
- **Setup:** Ketta Vane pre-placed at (10,18), tag `ketta_vane`. Three strongbox haulers, `salvage_compact_scrapper` on team 0, tag `strongbox_haul`, at (6,6), (11,6) and (15,6) under the north wreck wall. Pre-placed Concord: `salt_concord_tollkeeper` at (11,3) tag `toll_captain` (Toll-Captain Merrit Sax); `salt_concord_brineguard` at (9,4) and (13,4) (the gaps in the wreck wall); `salt_concord_salt_levy` x2 at (7,2) and (15,2); `salt_concord_surveyor` at (12,2). AI warband: salt_levy x3, brineguard x2, tollkeeper, causeway_outrider, brine_slinger.
- **Briefing:**
  Sled-log. The Concord killed Hesk Varrow on market day last week, in the aisles, in front of everybody. Varrow was a forger and nobody misses him. What they miss is the rule that said the Concord could not do that.

  Now the Concord has decided it likes the Kettle. Toll-agents at the north gaps with a ledger and a warrant for "contraband", which means anything in a strongbox. Our strongboxes are under the north wall, because the north wall is the shady side. Three haulers, three sleds, and the dogs ran.

  Get the boxes to the south road. Do not fight in the open aisles if you can help it, because the market will remember who started it. I would like the market to remember it was them.
- **Victory:** reach_tile tag `strongbox_haul` at the south road, tiles (9,19), (10,19), (11,19).
- **Defeat:** defeat_unit tag `strongbox_haul` (all three haulers lost), or unit_lost tag `ketta_vane`, or turn_limit 12.
- **Events:**
  1. Turn 1: message from **Toll-Captain Merrit Sax**: "By order of the Marshals' Office, this market is under audit. Please remain where you are. Please remain."
  2. Turn 3: reinforcement, two `salt_concord_causeway_outrider` come round the rim at (4,18) and (16,18), cutting at the south road.
  3. Turn 5: message from **Odo Brask** (from under a stall): "I've paid the south gate-ward. He's honest, so it may take him a turn to look away."
- **Bonus objective:** Lose no haulers (unit_lost tag `strongbox_haul`, negated).
- **Salvage:** winPearls 40; bonus 20.
- **Victory text:** The sleds go out the south road with the toll-agents shouting audit numbers after them. Brask counts the boxes twice, then a third time. His own box, the small iron one with the lock he never lets anyone see, is not among them. Somebody saw a red-throated bird over the north wall. Brask sits down very carefully.
- **Defeat text:** The boxes are sealed with Concord wax and carried up the Stair. Brask spends a month buying back his own receipts, one at a time, at Concord prices.
- **Unlocks:** `salvage_compact_tallow_mender`, `sv_spell_grease_the_deck`.

## Mission 3: `sv_grease_and_glory` — "Grease and Glory"
- **Map:** `boiling_floor` (vents active, powder works on the south plateau)
- **Enemy:** `hadal_court`
- **Type:** escort in / hold.
- **Setup:** Ketta Vane pre-placed at (13,19), tag `ketta_vane`. Brother Ashmaw (guest) `salvage_compact_brother_ashmaw` on team 0 at (12,20), tag `brother_ashmaw`. Player keystone (13,21) is the powder works kiln. Enemy keystone (12,2) is the Court's bell-anchor on the north plateau. Pre-placed Court: `hadal_court_maelis_quell` at (12,4) tag `maelis_quell` (carrying the flame); `hadal_court_bell_knight` at (11,3) and (13,3); `hadal_court_lantern_spitter` at (10,4). AI warband: pit_thrall x3, bell_knight, lurecaller, lantern_spitter, vent_priest. The mud-throat is the sinkmud at the heart of the vent island: (12,11), (13,11), (12,12), (13,12). The south plateau reaches the island by the bone causeway at column 9 (rows 14 to 17) or the causeway at columns 19 and 20.
- **Briefing:**
  Sled-log. Ashmaw wants the mud-throat. That is the big vent at the middle of the Boiling Floor, the one that never stops coughing. He says one charge down its neck will open a grease seam that will keep the kilns running for ten years, and he says it the way other people say grace.

  He goes himself. Powder-Monks do not let anyone else carry a blessed charge, and this one has a name. I asked what the name was. He said it was "Patience", which I think was a joke, but with Ashmaw you cannot tell.

  The scouts say something is walking up the far side of the rift, slow and bronze, carrying a light. Ashmaw says it is a pilgrim. I say a pilgrim does not need a ridge of Bell-Knights. Get him to the throat. Get him back if we can.
- **Victory:** reach_tile tag `brother_ashmaw` at the mud-throat, tiles (12,11), (13,11), (12,12), (13,12).
- **Defeat:** unit_lost tag `brother_ashmaw`, or unit_lost tag `ketta_vane`, or destroy_keystone team 0 (the kiln), or turn_limit 14.
- **Events:**
  1. Turn 1: message from **Brother Ashmaw**: "Mind the vents. They boil anyone not born under a mile of water. That is most of us. Ah. All of us."
  2. Turn 3: reinforcement, the Court comes up through the floor: `hadal_court_pit_thrall` at (11,11) and (14,12), `hadal_court_murk_diver` at (14,10), all on vent tiles.
  3. Turn 6: message from **Maelis Quell**: "We carry a flame to the open sky, small one. You are standing on its chimney." Then reinforcement, a `hadal_court_crushing_maw` heaves onto the east causeway at (16,8).
- **Bonus objective:** Let the flame pass: Maelis Quell survives (defeat_unit tag `maelis_quell`, negated).
- **Salvage:** winPearls 45; bonus 25.
- **Victory text:** Ashmaw kneels in the boiling mud, says the charge's name, and drops it down the throat. The floor heaves. Grease wells up black and sweet, and a column of fire stands over the rift for an hour. Across it, the bronze priest stops and watches, and lifts her small flame toward the column, as if greeting a relative. Then she walks on, up toward the sky.
- **Defeat text:** The Court closes over the throat like water over a dropped stone. Ashmaw is carried home on a sled, scalded and humming. "Next year," he says. Nobody argues. Nobody wants to go back.
- **Unlocks:** `salvage_compact_powder_monk`, `sv_spell_flash_fire`.

## Mission 4: `sv_the_roost_debt` — "The Roost Debt"
- **Map:** `gull_stacks` (nesting season, wind from the Rim)
- **Enemy:** `gyre`
- **Type:** climb / retrieve.
- **Setup:** Ketta Vane pre-placed at (14,24), tag `ketta_vane`. The strongbox sits on the high east stack, the scrap-field tiles (23,3) to (26,3), height 3, reached the long way round: the central stack, the bone road at row 10 (x17 to 22), the causeway at column 22 (rows 8 and 9), then up the east stack. Pre-placed Gyre: `gyre_wren_halloway` at (24,4) tag `wren_halloway`; `gyre_roostwarden` at (21,4) and (22,9); `gyre_gullwife` at (25,5); `gyre_frigate_thief` at (13,6); `gyre_salt_crow` at (12,12) and (16,13). AI warband: salt_crow x2, roost_runner x2, roostwarden, shrike_harrier, windreader.
- **Briefing:**
  Sled-log. Brask's iron box is on the high east stack at the Gull Stacks, sitting in a nest like an egg. We know because the thief sent us a letter saying so. The letter was written on the back of one of Brask's own receipts, which is the kind of joke I would admire if it were not my month's wages.

  Her name is Wren Halloway. She flies a frigatebird and she is very good. Birds do not need roads. We do. The stacks have bridges, but they go the long way, and the Gyre know every one of them.

  Brask says only that there is a page in that box he needs back, and that he would rather lose the gold. That is the first time in eleven years I have heard Brask prefer paper to gold. So we climb.
- **Victory:** reach_tile team 0 at the strongbox, tiles (23,3), (24,3), (25,3), (26,3).
- **Defeat:** unit_lost tag `ketta_vane`, or turn_limit 16.
- **Events:**
  1. Turn 1: message from **Wren Halloway** (from the east stack, feet dangling): "You walked? All this way? I'd have brought it down for a fee."
  2. Turn 3: reinforcement, two `gyre_salt_crow` and a `gyre_shrike_harrier` come off the west perch at (1,22), (2,21) and (3,22), harrying the climb from behind.
  3. Turn 6: message from **Odo Brask** (by Lamplighter flare-code, badly spelled): "If the box is open, don't read anything. If you read anything, don't tell me which page."
- **Bonus objectives:** Ketta opens the box herself (reach_tile tag `ketta_vane`, tiles (23,3) to (26,3)); finish before turn 10 (turn_limit 10, negated).
- **Salvage:** winPearls 45; bonus 20 and 15.
- **Victory text:** The box is open and the gold is all there. Wren is already a speck over the trench, waving. One page is missing from Brask's ledger of keeper receipts: the one that lists which Lanternkeeper carries the locked page of the Vigil Book, and where she sleeps. Ketta looks at the gap in the ledger for a long time. Then she shuts the box and does not ask.
- **Defeat text:** The crew climbs down in the dark. Wren drops the empty box on the sled-camp at dawn, with a feather in it and a note: "Thanks for the exercise."
- **Unlocks:** `salvage_compact_quartermaster`, `sv_spell_tripwire_alley`.

## Mission 5: `sv_embargo` — "Embargo"
- **Map:** `saltpan_bastions` (star fort on the flooded pan, Concord banners up)
- **Enemy:** `salt_concord`
- **Type:** siege.
- **Setup:** Ketta Vane pre-placed at (15,25), tag `ketta_vane`. Enemy keystone (14,2) is the Verge Gate, the toll-house where the salt roads close. Pre-placed Concord: `salt_concord_rim_marshal` at (14,4) tag `verge_marshal` (the Verge commander); `salt_concord_tollkeeper` at (14,13) tag `toll_clerk` (holding the embargo ledger, in the fort's centre court); `salt_concord_stair_warden` at (15,17); `salt_concord_brineguard` at (13,12) and (16,12); `salt_concord_brine_slinger` at (9,12) and (19,17); `salt_concord_saltwright` at (14,9). AI warband: salt_levy x3, brineguard x2, saltwright, caustic_lantern, surveyor.
- **Briefing:**
  Sled-log. The Concord has closed the salt roads. Every one. A notice nailed to every cairn on the Verge says the Compact is "a party to the Tide's insurrection" and may not trade on Concord ground until further notice. Further notice is Concord for never.

  Everything we eat comes up those roads or goes down them. The roads all run through one fort on the pan: a star of salt walls around a salt works, with a gate at the north end and a clerk in the middle who writes down every sled that passes. The clerk has the ledger. The ledger has the embargo. I have powder.

  Ashmaw has sent a cart of his best with a note: "Be generous." Brask has sent nothing, which means he has already sold the fort's water rights to somebody. Through the walls, through the court, break the gate. The salt roads were ribs before they were roads.
- **Victory:** destroy_keystone team 1 (the Verge Gate).
- **Defeat:** unit_lost tag `ketta_vane`, or destroy_keystone team 0, or turn_limit 18.
- **Events:**
  1. Turn 2: message from **the Verge-Marshal**: "Close the south gate." Then terrain: `salt_wall` at (15,19), radius 1, duration 4 (the Saltwrights seal the south causeway between the walls).
  2. Turn 5: message from **Odo Brask**: "West salt road's unwatched. I know because I'm the one who isn't watching it. That one's free. Don't get used to it."
  3. Turn 8: reinforcement, a relief column on the east road: `salt_concord_stair_warden` at (29,15) and `salt_concord_brineguard` at (28,15) and (27,15).
- **Bonus objective:** Take the ledger: defeat_unit tag `toll_clerk`.
- **Salvage:** winPearls 55; bonus 25.
- **Victory text:** The Verge Gate goes up in a sheet of white salt and orange fire. Ketta rides through before the dust settles, and for a quarter-mile there is nothing ahead of her but flat. She stops anyway. On the horizon to the north, very small, the Shoal's lamp is burning in broad daylight, and it is leaning, just slightly, toward the sky.
- **Defeat text:** The crew falls back across the pan with the salt wall at their heels. The embargo holds. By winter, Mother Hull is boiling leather.
- **Unlocks:** `salvage_compact_hullbreaker`, `salvage_compact_breach_gunner`.

## Mission 6: `sv_kelp_and_carcass` — "Kelp and Carcass"
- **Map:** `kelpmire` (wet, fog in the stalks, the channel running)
- **Enemy:** `overcurrent`
- **Type:** hunt / protect.
- **Setup:** Ketta Vane pre-placed at (10,21), tag `ketta_vane`. The thing that fell: `overcurrent_hagwyrm` on team 1 at (10,11), in the shallows of the channel, tag `slime_knot`. Three harvest cutters, `salvage_compact_scrapper` on team 0, tag `harvest_crew`, already at work at (8,14), (12,14) and (13,12). Pre-placed Overcurrent: `overcurrent_bellyeye_shoal` at (8,11) and (12,12); `overcurrent_tongue_louse` at (7,12). AI warband: bellyeye_shoal x2, gulper x2, tongue_louse, driftbell. Wet ground (shallows) covers most of the channel, rows 3 to 24; the Overcurrent dry out on the husk, silt and tangleweed banks.
- **Briefing:**
  Sled-log. Something fell out of the sky over the Kelpmire four nights ago. Not a bird. A knot of grey rope the length of a wagon, all mouth at one end, lying in the channel. Brask sold the first cut before anyone had looked at it properly, because the meat does not rot, and meat that does not rot is worth more than powder.

  The cutters went in yesterday. Today the cutters sent a runner to say the carcass is not a carcass. It is breathing through the slime. It ate a ladder. Things keep landing around it in the fog, pale and wet and wrong, and they all face the same way: toward the lamps.

  Brask says it is a fish. Ashmaw says it is a sign. Last week Brask sold a bronze Court herald an answer to a question, and he has been strange ever since, so I am not taking his word for fish. Kill it, cut it, get the crew home. In that order.
- **Victory:** defeat_unit tag `slime_knot`.
- **Defeat:** defeat_unit tag `harvest_crew` (all three cutters lost), or unit_lost tag `ketta_vane`, or turn_limit 14.
- **Events:**
  1. Turn 2: reinforcement, the sky thins: two `overcurrent_gulper` fall into the shallows at (5,5) and (12,6), and a `overcurrent_tongue_louse` at (6,15) beside the cutters.
  2. Turn 5: message from **Brother Ashmaw** (from the bank): "It needs the wet. Take the wet away." Then terrain: `silt` at (10,11), radius 1, duration 3 (the monks dig a drain under the knot; it starts to dry).
  3. Turn 8: message from **Hull cutter**: "It's raining. Ketta, it's raining up here. Where's it coming from?" Then reinforcement, a `overcurrent_downward_shark` falls onto the bank at (9,16), among the cutters.
- **Bonus objective:** Bring every cutter home (unit_lost tag `harvest_crew`, negated).
- **Salvage:** winPearls 55; bonus 25.
- **Victory text:** The knot stops moving at last. The cutters work by lamplight, and nobody speaks. Inside it they find a lighthouse lens-shard, grown over with slime like a pearl, still faintly warm. Brask buys it from the crew at four times its weight and does not sell it on. That night Ketta looks up, and for a moment she is sure the sky is looking back.
- **Defeat text:** The fog closes. The cutters do not come back, and neither do their sleds. In the spring, the Kelpmire is full of pale things lying in the channel, waiting, and none of them rot.
- **Unlocks:** `sv_equip_harpoon_gauntlet`, `sv_spell_black_market_cut`.

## Mission 7: `sv_the_archive` — "The Archive"
- **Map:** `mother_hull` (interior decks and ribs, the Archive day from Campaign 1, other side)
- **Enemy:** `salt_concord`
- **Type:** hold and extract.
- **Setup:** Ketta Vane pre-placed at (4,10), tag `ketta_vane`. Player keystone (3,10) is the skull gate of Mother Hull, the way into the Charter archive. Enemy keystone (18,10) is the Concord's rally standard at the tail. A Compact `salvage_compact_harpoon_engine` (guest, team 0) on the rib deck at (5,8), tag `harpoon_engine`. Pre-placed Concord (Tamsin Orrel's company; Orrel herself is not on the field, she is already inside): `salt_concord_caustic_lantern` at (19,9) and (19,12) tag `caustic_lantern`; `salt_concord_brineguard` at (16,10), (16,11) and (17,12); `salt_concord_stair_warden` at (15,10); `salt_concord_surveyor` at (17,9). AI warband: brineguard x2, salt_levy x2, surveyor, brine_slinger, saltwright, stair_warden. The jaw (the way out) is the silt at (0,20), (1,20), (0,21), (1,21).
- **Briefing:**
  Sled-log, Mother Hull. Brask sold the skull. Not the whole skull. The third hinge of the archive door, and the gas trap on it, to a Concord commander called Orrel, who is in the ribs right now with her company and two Caustic Lanterns. Brask sent me a note to say so. The note said, "Hold them as long as you can. I need ten minutes with the book."

  The book is the Compact's copy of the Vigil Book. The Lanternkeepers' book. We have had it in the skull for sixty years and nobody has read past the first page, because the Charter says the archive is for keeping, not reading. Brask has decided the Charter is wrong. I would argue, but he is inside the door and I am outside it.

  So: hold the skull gate, keep the Harpoon Engine firing, and when Brask comes out, get him down the jaw and onto the silt. If the door goes before he is out, he does not come out. I do not want to explain to Mother Hull that we lost her archive and her worst citizen on the same day.
- **Victory:** reach_tile tag `odo_brask` at the jaw, tiles (0,20), (1,20), (0,21), (1,21).
- **Defeat:** destroy_keystone team 0 (the skull gate falls before Brask is out), or unit_lost tag `odo_brask`, or unit_lost tag `ketta_vane`, or turn_limit 16.
- **Events:**
  1. Turn 1: message from **Commander Tamsin Orrel** (down the spine): "Lanterns on the Harpoon Engine first. Then the gate."
  2. Turn 5: message from **Odo Brask** (from inside the skull): "Ketta, the bit about the hand. I've got to the bit about the hand. Give me a minute." Then reinforcement, Concord sappers who came in by the third hinge: `salt_concord_brineguard` at (1,12) and `salt_concord_salt_levy` at (2,9), inside the skull end.
  3. Turn 8: Odo Brask (`salvage_compact_odo_brask`, team 0) appears at (1,10), tag `odo_brask`, with a message: "I've read it. I've read it, Ketta. We need to go, and then we need to talk about the heart."
- **Bonus objectives:** The skull gate still stands (destroy_keystone team 0, negated, checked at victory); bring the Harpoon Engine home (unit_lost tag `harpoon_engine`, negated).
- **Salvage:** winPearls 60; bonus 25 and 20.
- **Victory text:** Brask comes down the jaw on the seat of his three coats, white as salt. Behind them the archive door goes in at the third hinge, and Orrel's company pours into the skull to find the book open on the floor where Brask left it. Ketta waits for him to say something clever. He does not. He says, "She's not dead, you know. Mother Hull. She's holding something," and then he is sick on the silt.
- **Defeat text:** The skull gate goes, and the Concord carries out the archive in crates, with Brask in the last one. He is ransomed back a week later. He will not say what he read, and he will not go near the heart-chamber.
- **Unlocks:** `salvage_compact_odo_brask`, `sv_spell_compact_embargo`.

## Mission 8: `sv_the_warm_heart` — "The Warm Heart"
- **Map:** `mother_hull` (night, rain beginning, the heart-chamber unsealed)
- **Enemy:** `hadal_court` (team 1) + `returning_tide` (team 2, hostile to everyone)
- **Type:** last stand / hold.
- **Setup:** Ketta Vane pre-placed at (4,10), tag `ketta_vane`. Player keystone (3,10) is the heart-chamber: the lighthouse stone under the forward ribs, warm to the touch. Enemy keystone (18,10) is the Court's bell-anchor driven into the tail. Guests on team 0: `lanternkeepers_keeper_of_the_long_watch` at (2,11), tag `keeper_envoy` (Keeper Absalom Ruddle); `salvage_compact_brother_ashmaw` at (4,11), tag `brother_ashmaw`. Pre-placed Court, tag `court_vanguard` on each: `hadal_court_tollwarden` at (17,10) (the Fifth Bell); `hadal_court_bell_knight` at (16,10) and (16,11); `hadal_court_vent_priest` at (18,12); `hadal_court_lurecaller` at (17,9). Court AI warband: pit_thrall x3, bell_knight, pressure_lancer, deep_herald, trench_crab. Tide (team 2) arrives by event only. Wells: (10,5), (10,10), (10,16).
- **Briefing:**
  Sled-log, last page of the board. Deeplight is dark. Nobody here saw it, but everybody felt it: the sky over the Hulks went the colour of a bruise, and then it started to rain salt water out of nothing. Brask says the Court built their city around a fallen lamp, and somebody put the lamp out, and now they have come up the Brinks to find another.

  They have found ours. The heart-chamber has been sealed since the Charter. Brask opened it last night with Ashmaw and me holding the lamps, and the heart is not a heart. It is a lighthouse lamp, under the forward ribs, the size of a sled, burning. Mother Hull came ashore on a lighthouse on the night of the Ebb and died around it. Our grandparents signed the Charter inside her because it was the only warm room on the Hulks. Nobody told us why it was warm. Maybe nobody knew.

  The Court want to carry it down to Deeplight. The Tide want to put it out. A keeper called Ruddle walked in this morning with a pen and asked us to sign a second page to the Charter, under the first one. It says: "The Compact will keep the lamp." That is all it says. I signed it. Hold the heart until morning.
- **Victory:** survive 12 turns.
- **Defeat:** destroy_keystone team 0 (the heart goes out), or unit_lost tag `keeper_envoy`, or unit_lost tag `ketta_vane`.
- **Events:**
  1. Turn 1: message from **Keeper Absalom Ruddle**: "Nobody here has to understand it. You only have to stand in front of it. We have been doing the first part badly for three hundred years."
  2. Turn 4: the Tide come up out of the silt (team 2): `returning_tide_oswin_brack` at (10,1), tag `captain_brack`; `returning_tide_drowned` at (8,1), (12,1), (9,20) and (11,20); `returning_tide_rainsayer` at (10,21). Message from **Captain Oswin Brack**: "I sailed the Hulks before your Charter had a first line, girl. Let the light go. My crew is up there." Then terrain: `brine_pool` at (10,5), radius 1, duration 8, and at (10,16), radius 1, duration 8 (the rain fills the low decks).
  3. Turn 8: message from **Brother Ashmaw**: "Now, I think. Yes. Now." He strikes the heart-chamber's shutters open and the lamp shines through Mother Hull's ribs. Status `burning` on tag `court_vanguard`, duration 2.
- **Bonus objectives:** Ashmaw sees the morning (unit_hp_above tag `brother_ashmaw`, fraction 0.5); the Fifth Bell is driven off (defeat_unit tag `court_vanguard`).
- **Salvage:** winPearls 80; bonus 30 and 30.
- **Victory text:** At dawn the Court lifts its bells and goes back down the Brinks without a word; the Tide melt into the rain, singing. Mother Hull stands lit from inside, every rib a black bar across a white fire, and Ashmaw sits on the spine and weeps, because they can see it from the Rim. Brask checks the Charter's new page for spelling. Ketta rides out alone to the edge of the flat and looks back. For the first time in her life she does not want the flat to be empty. Someone ought to be awake on it.
- **Defeat text:** The heart goes out. For a long breath nothing happens. Then the rain stops being rain, and the sky over the Hulks comes down all at once, green and black and full of mouths.
- **Unlocks:** `salvage_compact_brother_ashmaw`, `salvage_compact_harpoon_engine`.

## Campaign arc and secret
Missions 1 to 3 teach the Compact's game: run, burn, sell, never hold. Missions 4 to 6 show the cost of neutrality: the Gyre robs it, the Concord starves it, and the Overcurrent fall on it, and each mission leaves Ketta a clue (the missing keeper page, the leaning lamp at the Shoal, the warm lens-shard inside the thing from the sky). Mission 7 is the Archive day from Campaign 1, seen from the ribs: Brask betrays the archive door to Orrel so that someone will finally read the Vigil Book. Mission 8 reveals the Compact's secret, kept even from itself: Mother Hull beached on a lighthouse on the night of the Ebb, her warm heart is a burning Beacon, and the Charter was signed in the one room on the Hulks that was holding the sea up. The Compact was never neutral; it was sitting on a lamp. It signs a second page, "The Compact will keep the lamp", and holds. The faction is right that nobody should own the Ebb, and wrong that anyone can stand on it without taking a side. The campaign ends with Ketta on the open flat at dawn, looking back at a city lit from the inside.
