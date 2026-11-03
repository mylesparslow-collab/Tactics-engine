# Campaign 1: "The Light at Lantern Shoal"

Faction: Salt Concord (`salt_concord`). 8 missions. Escalation: Tide skirmish, escort, bargain, hold, assassination, infiltration, race, finale. Relics are named by role; ids come from the unit thread. Pearl rewards follow the bible (win, speed, losses, bonus). All times in turns. Setting canon: `EBB_world_bible.md`, `bible/history_and_gazetteer.md`.

## Recurring characters

**Commander Tamsin Orrel** (player). A Rim Marshal's daughter and the Concord's youngest survey-company commander, promoted after the Broken Toll because nobody senior wanted to go. Dry, methodical, measures everything twice, and privately keeps a Rim-style night lamp in her tent. She starts believing in the Concord. She ends believing in the work, not the paper.

**Odo Brask, Compact fixer.** Sells maps, grain, rumours and, when it pays, silence. Fat, cheerful, wearing three coats in desert heat. He knows exactly why the Shoal matters because the Compact has been buying Lanternkeeper secrets for sixty years. Plays every side and is quietly terrified of all of them. Will betray Tamsin once, correctly.

**Prophet Imre Dunnock, "the Wet Saint".** Tide prophet, once a Concord tax clerk who audited the water ledgers and found they did not balance. Gentle voice, soaked cloak, a following of thousands. He is the only antagonist who has read the numbers. He wants the lamps out because he believes the sea above will be merciful. He is wrong, and he knows it.

**Keeper Pell Auster.** Last Lanternkeeper of the Shoal. Elderly, blind in one eye, always awake. Speaks in short instructions and half-sentences. Refuses to carry a weapon but will stand in front of one. Gives the company the Vigil Book, a page at a time, as she decides they are ready.

**Herald Vhaal, the Third Bell.** Hadal Court envoy in a bronze brine-bell. Formal, slow, unfailingly polite, horrifying. Speaks of the Concord as a house guest who has been eating the host's furniture for three hundred years. She wants an answer to one question, and will accept only the truth.

---

## Mission 1: `lamp_and_wall` — "Lamp and Wall"
- **Map:** `lantern_shoal` (standard setup, daylight, lamp lit)
- **Enemy:** `returning_tide`
- **Type:** skirmish / tutorial: defend a position and break out.
- **Briefing:**
  Commander Orrel's log, day 9. The Shoal stands where the survey said it would, which is more than I can say for the garrison. Forty men were posted here fifty years ago and the wall they built is still standing; the men are not. The lamp is lit. I have been told the lamp is not our business, and I have been told this by three different officers, which makes me curious about it.

  We have a Beacon to hold: Concord regulations say a lighthouse is a Beacon whether or not anyone wishes to hold it. Our scouts report a wet, silent column coming in from the east: Tide penitents with a Wringer behind them. They want the lamp. We will not give it.

  Hold the wall, use the ruins, bring up the Brineguard. Once their Wringer breaks, they will fall back. I would like them to fall back as far as possible.
- **Victory:** destroy_keystone (enemy forward shrine at the east edge); alternative `eliminate` after turn 8.
- **Defeat:** unit_lost tag `beacon_garrison` (the lighthouse Beacon falls), or turn_limit 14.
- **Events:**
  1. Turn 1: message from **Keeper Pell Auster** (hail from the tower): "Don't touch the lamp. Don't let them near the lamp. That's all." Introduces the Beacon as sacred.
  2. Turn 3: reinforcements, four Penitents from the east flank.
  3. Turn 5: surprise spawn, a Wringer emerges from a brine pool near the player's rear (teaches the pool tile).
- **Bonus objective:** Lose no units. +Pearls.
- **Victory text:** The column breaks and flows back into the haze, leaving wet footprints that dry too fast. The lamp does not so much as flicker. Keeper Auster walks out of the tower for the first time in three years and says, "Good. They'll be back."
- **Defeat text:** The Wringer reaches the tower stair. The lamp gutters, and for a moment the air tastes of brine. The company withdraws in disorder. Somewhere above, someone has begun to cry.
- **Unlocks:** the line infantry core (Brineguard), the ranged marker (Surveyor).

## Mission 2: `down_the_stair` — "Down the Stair"
- **Map:** `greywater_stair` (convoy setup, switchback)
- **Enemy:** `returning_tide`
- **Type:** escort.
- **Briefing:**
  Our supplies sit at the top of the Stair. Our company sits at the bottom. Between us are nine landings, a thousand feet of cliff, and a Tide host that has apparently read the Concord road manual and found the weak bend.

  Three supply wagons come down at dawn. I need them all at the Shelf landing, and I need the Stair-Wardens to hold each switchback long enough to let them pass. The Tide want to tip the wagons off the edge. I would prefer they did not.

  I'll be honest: this is the first time I've used the Stair in anger. It was built to be walked down by conscripts and marched up by armies. Nobody planned for it to be a shooting gallery.
- **Victory:** reach_tile (all three wagons, tag `supply_wagon`, at the lower landing).
- **Defeat:** unit_lost tag `supply_wagon` (any two lost), or turn_limit 16.
- **Events:**
  1. Turn 2: surprise spawn, Penitents drop from the cliff face onto the third landing.
  2. Turn 5: message from **Odo Brask**, signalling from a bone-sled below: "Commander! Ambush at the fifth landing. You never heard this from me. Wait, you did. I'm sending the bill."
  3. Turn 7: reinforcement, a Rainsayer floods the lower landing tiles into brine pools, slowing the wagons.
- **Bonus objective:** Deliver all three wagons undamaged.
- **Victory text:** The last wagon rolls onto the Shelf at dusk. Odo Brask is waiting with a flask and an invoice. "Free sample," he says, grinning. The invoice is for the flask.
- **Defeat text:** The wagons go over the edge in a long, slow fall. The company will have to make do with what is in their packs, which is mostly salt.
- **Unlocks:** the wall-maker (Saltwright), the heavy tank (Stair-Warden).

## Mission 3: `bargain_in_the_kettle` — "A Bargain in the Kettle"
- **Map:** `the_kettle` (market day, neutral stalls)
- **Enemy:** `salvage_compact`
- **Type:** assassinate / infiltrate.
- **Briefing:**
  Brask says the Tide's raiders were armed by the Compact. I did not believe him until he showed me the receipts, which were in my own handwriting. Someone has been forging Concord requisitions and selling them to the Tide's quartermasters, and that someone is a broker named Hesk Varrow, who has a stall in the Kettle and thirty hired knives.

  The Compact does not hand over its own. They do, however, tolerate a quiet word. I have a quiet word ready, and four Brineguard to deliver it.

  We will go in disguised as traders, find Varrow and remove him. The Compact militia will not interfere if we do not break the market code. That means no fighting in the open aisles. Make it look like trade.
- **Victory:** defeat_unit tag `broker_varrow`.
- **Defeat:** unit_lost tag `commander_orrel`, or turn_limit 12.
- **Events:**
  1. Turn 1: message from **Odo Brask**: "Varrow keeps his gold under the third hull. His guards change at the bell. Don't ask how I know."
  2. Turn 4: surprise spawn, Compact bone-sleds ring the market (an ambush, not a trap).
  3. Turn 7: Varrow tries to flee on a sled. A reinforcement Wrecker squad covers him.
- **Bonus objective:** Kill Varrow without destroying any market stalls.
- **Victory text:** Varrow goes quietly. The market closes around the space where he stood like water around a dropped stone. Brask presses a map into Tamsin's hand: "That's the way to the Weeping Shelf. It's free. Next one's not."
- **Defeat text:** Orrel is dragged out of the market in a sack. The Compact will ransom her to the Concord, for a fee she will be reminded of for years.
- **Unlocks:** the skirmish duellist (Surveyor's Mark: a long-range marked-target specialist), the salt-ward medic.

## Mission 4: `hold_the_wall` — "Hold the Wall"
- **Map:** `lantern_shoal` (night, fog, garrison wall damaged)
- **Enemy:** `returning_tide`
- **Type:** hold / survive.
- **Briefing:**
  The Tide have found what we are protecting. They are coming in force. Brask says three thousand, which means perhaps eight hundred. Dunnock leads them, and for the first time we know the man's name and his old trade: tax clerk, Rim-born, brilliant. He has taken a hundred wells in the north and never lost a battle he chose to fight.

  The relief column will arrive in nine turns. Until then we hold the wall, the tower, and the lamp. We have the Saltwright and her barricades. We have the Stair-Wardens. And we have a blind old woman who says she will talk to the sea.

  I know what the regulations say about hopeless defences. I also know what the regulations say about retreat: that it is worse.
- **Victory:** survive 9 turns.
- **Defeat:** unit_lost tag `beacon_garrison`, or unit_lost tag `keeper_auster`.
- **Events:**
  1. Turn 2: message from **Imre Dunnock** (across the fog, via a Choirmaster's chant): "We are not here to take the lamp, Commander. Only to ask it to stop."
  2. Turn 5: reinforcement, a wave of Drowned climbs out of the brine pools (they return once).
  3. Turn 8: Keeper Auster lights a second, hidden lamp on the tower roof, a light-damage flare that burns every Drowned adjacent to the tower.
- **Bonus objective:** Keep the wall's north section standing.
- **Victory text:** The relief bugle sounds across the dunes and the Tide fade back into the fog. Dunnock's last words reach the tower on the wind: "You hold it up for them. You do not even know." Auster closes the shutters. "He's right about that part."
- **Defeat text:** The lamp goes dark for the length of a breath. Then Auster relights it with her bare hands. The Tide fall back, horrified at what they almost did, and Dunnock does not give the order to advance again.
- **Unlocks:** the siege engine (Caustic Lantern), the aura commander (Rim Marshal).

## Mission 5: `rain_on_clear_sky` — "Rain on Clear Sky"
- **Map:** `weeping_shelf` (rain active, slick tiles)
- **Enemy:** `returning_tide`
- **Type:** assassinate / race against reinforcement.
- **Briefing:**
  We go to the Weeping Shelf. The Tide cannot be pinned at the Shoal while their holy ground feeds them. Take away the Rainsayers and the faith loses its voice. There are four of them, working a shrine on a ledge above a fall of rain that comes from nowhere.

  Brask warns that the rain gets heavier when we are loud. I have decided not to think about why. The rain soaks our troops and flows into the pools, so we must hit the Rainsayers before they flood the ledge. Quick, brutal, over by turn ten.

  We will not touch Dunnock. He is not here. If he were, I might have to listen to him.
- **Victory:** defeat_unit tag `rainsayer` (all four).
- **Defeat:** unit_lost tag `commander_orrel`, or turn_limit 10.
- **Events:**
  1. Turn 3: reinforcement, Penitents surge from the lower terrace.
  2. Turn 5: message from **Keeper Pell Auster**: "That rain is the lamp's breath, Commander. It leaks when something pulls on it. Be quick."
  3. Turn 7: surprise spawn, a Choirmaster rises from the pool at the shrine, buffing every Penitent in sight.
- **Bonus objective:** Eliminate all four Rainsayers before turn 8.
- **Victory text:** The last Rainsayer falls and the drizzle thins to a mist. Tamsin holds out her hand and catches a drop. It is warm. It tastes of salt, and of somewhere very far above.
- **Defeat text:** The rain thickens until the ledge is a lake. The company retreats through brine up to their knees, and the Tide sing the whole way.
- **Unlocks:** the pool-walking skirmisher (Brine-Stalker, a captured-doctrine Concord counter), the heavy marker (Cartographer).

## Mission 6: `mother_hull_archive` — "The Archive at Mother Hull"
- **Map:** `mother_hull` (interior decks and ribs)
- **Enemy:** `salvage_compact`
- **Type:** siege / infiltrate.
- **Briefing:**
  Brask has betrayed us. Not in a dramatic way. He sold the Shoal's location to the Compact so they can sell it back to whoever pays most, and now the Compact's militia has sealed Mother Hull. That is fine. Brask also told me where the real prize is: the Charter archive, in the leviathan's skull, which holds the Compact's copy of the Vigil Book.

  We go in through the ribs. The Compact militia is scattered and overconfident. The Harpoon Engine on the third deck will pin anything that moves, so the Caustic Lanterns need to take it out first.

  We break the main gate, secure the skull, and leave. We do not stay for tea.
- **Victory:** destroy_keystone (the archive door).
- **Defeat:** unit_lost tag `caustic_lantern` (both siege engines), or turn_limit 15.
- **Events:**
  1. Turn 2: message from **Odo Brask**: "Commander, I did the thing. Please don't hit me. The archive door has a gas trap. It's the third hinge. You're welcome."
  2. Turn 6: reinforcement, a Harpoon Engine crew and Bone-Sled Riders arrive from the rear.
  3. Turn 9: surprise spawn, Herald Vhaal's scout appears inside the skull, watching.
- **Bonus objective:** Capture the archive door with no allied losses.
- **Victory text:** Inside, Tamsin finds the Vigil Book copy. Odo Brask is already reading it. "I always wondered," he whispers. Then he reads the page about the hand held up, and sits down on the floor.
- **Defeat text:** The Harpoon Engine pins the last Lantern. The company is held for three days and sent home with a polite bill and a longer reading list.
- **Unlocks:** the powder-defying bulwark (Salt-Ward Bulwark) and a Concord Relic of the Court-slayer role (Pressure-Breaker).

## Mission 7: `race_to_deeplight` — "Race to Deeplight"
- **Map:** `trench_deeplight` (cliff ledges, narrow bridges)
- **Enemy:** `hadal_court`
- **Type:** race / escort.
- **Briefing:**
  The Vigil Book tells us a lamp fell into the trench at Deeplight, and burns still. The Court built a city around it. The Book also says a Beacon elsewhere is about to fail, and that Keeper Auster must reach the fallen lamp to relight the chain before it does.

  We are racing a clock I do not understand and an enemy that does not hurry. The Court's Bell-Knights are slow. Slow is not the same as stoppable. Their Lurecallers will pull us off the bridges. Their Deep Herald will darken the ledge.

  We escort Auster across three bridges to the lamp. If we lose her, we lose the chain. I do not want to find out what that means.
- **Victory:** reach_tile (tag `keeper_auster` at the fallen lamp).
- **Defeat:** unit_lost tag `keeper_auster`, or turn_limit 14.
- **Events:**
  1. Turn 3: message from **Herald Vhaal**: "Concord. You carry the Keeper. Answer me one question and I will let her pass: who lifted the sea?"
  2. Turn 7: reinforcement, a Crushing Maw heaves up from the trench and blocks the second bridge.
  3. Turn 10: surprise spawn, the whole level goes dark (Deep Herald), and the player must navigate by the lamp's light alone.
- **Bonus objective:** Keep Auster above half health.
- **Victory text:** Auster puts her hand on the fallen lamp, and the glass sings. Far above, a column of grey brine begins to fall, slowly, from a cloudless sky. "It's started," she says. "Go home. Defend the Shoal."
- **Defeat text:** Auster falls from the bridge and the lamp below flares once. The company retreats, and the Court does not pursue. They already know what comes next.
- **Unlocks:** the light-forged aura (Lamp-Bearer) and the commander's second aura (Rim Marshal's Banner).

## Mission 8: `the_light_goes_out` — "The Light Goes Out"
- **Map:** `lantern_shoal` (interior and summit, rain beginning, heights altered)
- **Enemy:** `returning_tide` (with a Hadal Court surprise spawn)
- **Type:** siege / assassinate / hold.
- **Briefing:**
  The Beacon at Deeplight is out, and we are still here. The rain has started: first drizzle, then a downpour of seawater falling from a clear sky. The Tide march on the Shoal through it, singing, and they are not alone. The Court has come up the Brinks to witness.

  Dunnock leads from the summit. He wants the lamp dark. He believes the sea will be kind. I have the Vigil Book, a company of tired Brineguard, and a Keeper's last instruction in my coat: "If all else fails, put your hand on the glass."

  We hold the lighthouse. We kill Dunnock. Then, if we can, we keep the sea where it is. I would like to say I understand how. I do not.
- **Victory:** defeat_unit tag `prophet_dunnock`; the lamp must still burn.
- **Defeat:** unit_lost tag `beacon_garrison` (the lamp), or turn_limit 16.
- **Events:**
  1. Turn 2: message from **Imre Dunnock**: "Look up, Commander. That is not weather. That is everything you ever took for granted, coming home."
  2. Turn 6: surprise spawn, Herald Vhaal and two Bell-Knights climb out of the flooded lower court, neutral until the lamp falls or Dunnock dies.
  3. Turn 10: the sky breaks. Seawater rains on every tile: all units are soaked, and brine pools spread across the map.
- **Bonus objective:** Keep the lamp's top floor free of brine.
- **Victory text:** Dunnock dies with the tower's light on his face. Auster, last of her house, stands at the glass and puts her hand on it. The rain slows, and stops. "That's it," she says. "That's all it ever was. Someone has to stay awake." Tamsin looks up. For the first time, she can see the sea.
- **Defeat text:** The lamp goes dark. The sky opens. The last thing Tamsin sees is a wall of green water, a mile high, folding over the horizon.
- **Unlocks:** the Lanternkeeper's champion (Vigil-Warden, a rare Concord-allied Relic) and the exotic commander (the Beacon-Marshal).

## Campaign arc and secret
Missions 1 to 3 teach the Tide, the Concord's own road network, and the Compact's market. Missions 4 to 6 show the Tide's real intent, the stakes of the lamp, and the Vigil Book. Missions 7 and 8 reveal the secret: the sea was lifted, not lost, and each lighthouse holds it up. The campaign ends with Tamsin holding a hand on the glass beside Auster, and the Concord's survey maps marked, in her hand: "Do not pave the Ebb. It is not ours."
