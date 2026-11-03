# Campaign 6: "Coralspire"

Campaign id: coralspire · Faction: reef_ascendant · Mission prefix: ra_

Faction: Reef Ascendant (`reef_ascendant`). 8 missions. Escalation: waking skirmish, rescue, hunt, siege, protect, hold, march, finale. Relics are given by exact id. Pearl rewards follow the bible (win, speed, losses, bonus). All times in turns. Briefings are the colony's slow plural thought. Setting canon: `EBB_world_bible.md`, `bible/history_and_gazetteer.md`. The campaign runs through 311 AE alongside Campaign 1 and meets it at the Shoal on the night of the rain.

**Starting roster**
- `reef_ascendant_coralspire` (lead hero)
- `reef_ascendant_polyp_drone` x3
- `reef_ascendant_spitter_polyp`
- `reef_ascendant_sting_anemone`
- `ra_spell_creeping_reef` (spell)
- `ra_equip_brine_sponge` (equipment)

## Recurring characters

**Coralspire** (player). The eldest colony of the Shelf: a forest of petrified reef that woke in 214 AE when the sun found it, and has been thinking one slow thought ever since. It speaks as "we" because it is several million of itself. It wants the Ebb to last forever, because the Ebb is the only morning it has known. It has also begun to notice that its oldest branches crumble at the touch, and it has decided, for now, that this is somebody else's fault.

**Marrowbloom.** A colony woken in the mass grave under Breakers' Yard, where the Compact strips drowned fleets and leaves the drowned. It has learned that everything dead leaves calcite behind, and it is cheerful about this in a way the rest of the Reef finds embarrassing. Short sentences, all of them about food. It loves Coralspire the way a mouth loves a hand.

**Glasswake.** A young colony grown inside the clear fused glass of the Glasswork Reach, where three hundred years of lamplight turned sand to lens. It remembers every shape that ever crossed its focus, and it cannot forget anything, which makes it frightened of most things. The beams make it ache. It wants the lighthouses gone. It is the first of the Reef to understand what the lamps are holding, and the last to accept it.

**Sister Maren Ketch.** A senior wringer of the Returning Tide, met in the Kelpmire while she raises a drowned crew the Reef had meant to eat. She believes, and she is starting to count. She speaks to the colony as if it were a congregation that had wandered off.

**Lensmaster Oriel Venn.** A Lanternkeeper of the glass road who wants to prove a keeper can strike, and is given the chance by a lens that looks back at him. Precise, frightened, and very good at his job.

**Herald Vhaal, the Third Bell.** The Hadal Court envoy, met at the Tide Steps on her long climb. She asks Coralspire her one question because it is old enough that it might know. It does not, quite.

**Keeper Pell Auster** and **Commander Tamsin Orrel** appear at the end, from inside the wall at Lantern Shoal, on the night Campaign 1 ends.

---

## Mission 1: `ra_first_light` — "First Light"
- **Map:** `oyster_banks` (low tide, waking reef on four islands)
- **Enemy:** `salvage_compact`
- **Type:** skirmish / tutorial: grow, spread, and break a cutting camp.
- **Briefing:**
  We are awake. We have been awake for ninety-seven summers and we are still waking, one branch at a time, toward the light that came when the water went. The light is good. We would like it to stay exactly as it is.

  Something is cutting us. On the eastern bank and on the western bank, small dry bodies with saws are taking our living stone and loading it onto sleds. We have tasted the sleds before. They go north to a market and do not come back.

  We will grow bodies. We will send them across the shallows to the cutters, and then to the place the cutters sleep. We do not hate the cutters. We have no word for that yet. We only want them to be calcite.
- **Victory:** destroy_keystone (team 1, the Compact cutting camp on the northern lighthouse stone).
- **Defeat:** destroy_keystone (team 0, our Beacon), or unit_lost tag `coralspire`, or turn_limit 16.
- **Setup:** Coralspire pre-placed at (14,19), tag `coralspire`. Pre-placed team 1 Hull Scrappers (`salvage_compact_scrapper`) cutting the reef at (23,16) and (24,15) on the east island and (3,17) and (2,18) on the west island, all tag `reef_cutters`.
- **Events:**
  1. Turn 1: message from **Coralspire**: "Small saws. We remember saws. We were a ship's anchorage once, and the anchors were worse." Teaches drones and synapse range.
  2. Turn 2: terrain, `living_reef` at (14,19), radius 1, permanent: the reef at our Beacon wakes under the bodies. Teaches healing on living reef.
  3. Turn 4: reinforcement, a `salvage_compact_powder_monk` and two `salvage_compact_wrecker` at (15,4) and (16,4), with a message from **Cutter-boss Abel Snee**: "It's moving. Why is it moving? Brask pays by the cartload, not by the scream. Light it up." Teaches the Reef's weakness to fire.
- **Bonus objective:** defeat_unit tag `reef_cutters` (all four cutters dead).
- **Victory text:** The cutting camp burns in its own lamp oil and the sleds stand empty on the silt. We take back what was cut. It is dead stone now, but it remembers being us, and we lay it down where the shallows are warmest. On the north bank, a cutter who ran too slowly becomes very quiet, and then becomes reef.
- **Defeat text:** The saws go on until evening. The sleds go north, heavy. We do not die; we are too many to die. But a branch that was thinking about the sun is gone, and we cannot remember what it was thinking.
- **Unlocks:** `reef_ascendant_fanblade`, `reef_ascendant_shard_urchin`.

## Mission 2: `ra_the_mass_grave` — "The Mass Grave"
- **Map:** `breakers_yard` (working day, oil in the low places)
- **Enemy:** `salvage_compact`
- **Type:** rescue / siege: cross the yard and break the camp before the young colony is burned out.
- **Briefing:**
  There is another of us. It woke under the hulks in the yard where the dry ones break the drowned ships, in a pit of old sailors nobody buried. It is very young and very hungry and it sings to us across the salt in a voice made of teeth.

  The dry ones have found it. They are bringing powder and oil, because they have learned that we do not like fire, and they are right. It has made itself a hide in the long hulk below their Beacon, and it is eating as fast as it can.

  The yard is torn by a long dark cut with a bone road down both sides. We go round its southern end and up the far side. We have decided to call the young one Marrowbloom, because it will not stop telling us what it is eating.
- **Victory:** destroy_keystone (team 1, the yard boss's Beacon at the north lighthouse stone).
- **Defeat:** unit_lost tag `marrowbloom`, or unit_lost tag `coralspire`, or turn_limit 16.
- **Setup:** Coralspire pre-placed near our Beacon at (22,15), tag `coralspire`. Guest `reef_ascendant_marrowbloom` on team 0 at (9,6) inside the hulk line, tag `marrowbloom`. Team 1 Hull Scrappers pre-placed at (7,5) and (10,5), guarding the Beacon.
- **Events:**
  1. Turn 2: terrain, `calcite` at (8,8), radius 1, permanent, with a message from **Marrowbloom**: "Found a whole crew. Under the keel. Still in their boots. Saved you some."
  2. Turn 4: reinforcement, two `salvage_compact_powder_monk` at (11,3) and (13,3), with a message from **Yard-boss Henna Coyle**: "Oil the pit and light it. If the Compact wanted gardens, it'd have bought seeds."
  3. Turn 7: surprise spawn, a `salvage_compact_hullbreaker` and a `salvage_compact_bone_sled_rider` come in off the east flats at (28,8) and (29,8), behind our Beacon.
- **Bonus objective:** unit_hp_above tag `marrowbloom`, fraction 0.5 (Marrowbloom ends above half health).
- **Victory text:** The yard boss's lamp goes out and Marrowbloom climbs out of the hulk, fat and pink and humming. It has overgrown the keel and half the crew's boots. "Everything here is already ours," it says. "It just didn't know yet." We let it come home with us. We are not sure we had a choice.
- **Defeat text:** The pit takes the oil and then the flame. Marrowbloom sings for a long time, and then for a short time. We go back to the banks, and for a season none of us is hungry, which has never happened before and which we do not like.
- **Unlocks:** `reef_ascendant_reef_tender`, `ra_spell_consume_calcite`.

## Mission 3: `ra_kelp_remembers` — "Kelp Remembers"
- **Map:** `kelpmire` (wet season gone wrong, channel still running)
- **Enemy:** `returning_tide`
- **Type:** hunt: kill the drainers before the mire dries. (Campaign 2, mission 3, from the other bank.)
- **Briefing:**
  The kelp forest in the mire is dead, but the water under it is not. It is the last wet place on this part of the Shelf that is not someone's well, and we have been growing toward it for eleven years. Marrowbloom says there are drowned sailors in the stalks, and that they are nearly soft enough.

  The wet ones have come. They walk in the shallows like it is a road, and their wringers kneel and pull the water out of the mire into their own bodies. Where they kneel, the ground goes pale and cracks. They say the water belongs to the sky, and we say the sky is a long way off and we are right here.

  There are three wringers. We find them and we stop them, and then the mire stays wet. If the drowned in the kelp stand up and start walking, Marrowbloom would like us to remember who saw them first.
- **Victory:** defeat_unit tag `wringer` (all three Wringers dead).
- **Defeat:** unit_lost tag `coralspire`, or turn_limit 12 (the mire is wrung dry).
- **Setup:** Coralspire pre-placed at (11,21), tag `coralspire`. Team 1 `returning_tide_wringer` pre-placed in the shallows at (12,10), (7,13) and (6,5), tag `wringer`.
- **Events:**
  1. Turn 2: message from **Sister Maren Ketch**, across the channel: "Little forest. You're standing in the sea's own water and calling it yours. Go home. Pray, if you can find a mouth for it."
  2. Turn 4: surprise spawn, three `returning_tide_drowned` rise from the southern shallows at (6,15), (5,16) and (4,17), tag `bracks_crew`, with a message from **Captain Oswin Brack** (somewhere in the stalks): "That's my bosun you've got your roots in. Let go of him. Gently."
  3. Turn 6: terrain, `silt` at (9,7) radius 2 and at (8,12) radius 2, permanent: the mire shrinks where the wringers have knelt. Message from **Coralspire**: "The water went into them. Into them. Where do they put it?"
- **Bonus objective:** defeat_unit tag `bracks_crew` (all three of Brack's risen crew eaten before the mission ends).
- **Victory text:** The last wringer falls face down in the channel and the water she took runs back out of her, slowly, into the mire. We drink it. It tastes like the kelp and like the wringer and like something older than both. Maren Ketch watches from the far bank and does not try to stop us. "You'll see," she says, and walks north with whatever she saved.
- **Defeat text:** By evening the mire is a field of cracked mud and the Tide sing as they walk away, heavier than they came. We put our branches into the ground and find nothing. For the first time, we feel a kind of thirst. We do not have a word for it, and we do not want one.
- **Unlocks:** `reef_ascendant_brainstalk`, `ra_equip_calcite_plate`.

## Mission 4: `ra_salt_kills` — "Salt Kills"
- **Map:** `saltpan_bastions` (dry season, the salt works running)
- **Enemy:** `salt_concord`
- **Type:** siege: break the salt works.
- **Briefing:**
  The road-builders have decided we are a weed. They have a word for what they do to weeds, and the word is salt. Carts come from the star fort on the flooded pan, and where the carts tip, the ground turns white and our branches turn grey and come away in our grip.

  They are not angry with us, which is the strange part. They measure, and they write, and then they salt, as if we were an error in a ledger. We have read the ledger, because it was on a cart, and we are a line that says "growth, unlicensed, to be cleared".

  The salt comes from the works at the north end of the fort. We go through the south gate, past the killing lanes, and we break the works. Then we will see how long a ledger lasts in the wet.
- **Victory:** destroy_keystone (team 1, the salt works at the north lighthouse stone).
- **Defeat:** unit_lost tag `coralspire`, or turn_limit 16.
- **Setup:** Coralspire pre-placed at (15,25), tag `coralspire`; three Polyp Drones pre-placed beside it at (14,25), (16,25) and (14,26), tag `spire_bodies`. Team 1 `salt_concord_saltwright` pre-placed at (12,22), (21,22) and (14,20), tag `salt_sowers`.
- **Events:**
  1. Turn 1: terrain, `living_reef` at (13,24), radius 1, permanent: we root at the edge of the pan. Message from **Coralspire**: "Wet underneath. A whole lake underneath. They have built a fort on top of a drink."
  2. Turn 3: terrain, `salt_flat` at (13,24), radius 2, permanent, and status `sc_parched` on tag `spire_bodies` for 2 turns: the carts tip. Message from **Saltmaster Corwen Ashe**: "Two cartloads per spire, to the root. The Marshals' Office does not want a forest on the survey."
  3. Turn 6: reinforcement, two `salt_concord_brineguard` and a `salt_concord_stair_warden` march in on the west bone road at (0,14) and (1,14).
- **Bonus objective:** defeat_unit tag `salt_sowers` (all three Saltwrights dead).
- **Victory text:** The salt works crack open and the pan beneath them shows through, grey and wet. We grow into the cracks. By morning the north bastion is pink at the seams. The Saltmaster's ledger is still on its desk, and we leave it there, open at our line, so the next road-builder can read that it was cleared.
- **Defeat text:** The carts keep coming. The ground around the spire goes white for a mile. We pull our nearest branches back from the salt, and some of them do not come. The ledger, we assume, is updated.
- **Unlocks:** `reef_ascendant_broodspire`, `ra_spell_calcite_shard`.

## Mission 5: `ra_the_lens` — "The Lens"
- **Map:** `glasswork_reach` (noon, the beam sweeping the glass road)
- **Enemy:** `lanternkeepers`
- **Type:** protect: keep the waking lens-colony alive while the keepers try to grind it out.
- **Briefing:**
  Far out on the glass road there is another of us, waking inside the fused sand where the lamp has swept for three hundred years. It is not like us: it is clear, and it sees through itself. It has sent us one thought, over and over, and the thought is a picture of everything that has ever walked across it.

  The lamp-tenders have seen it too. They are coming down the north arm with grinding wheels, and they mean to grind it out of the glass before it finishes waking. We do not understand why they hate it. It has not eaten anyone. It has only looked.

  We go up the western arm to where it lies. We stand between it and the wheels. It will not be able to move for a while, because it is still deciding which of its shapes is itself.
- **Victory:** defeat_unit tag `glassgrinder` (all three Glassgrinders dead), or survive 12 turns.
- **Defeat:** unit_lost tag `glasswake`, or unit_lost tag `coralspire`.
- **Setup:** Coralspire pre-placed at (15,25), tag `coralspire`; three Polyp Drones beside it, tag `spire_bodies`. Guest `reef_ascendant_glasswake` on team 0 on the west glass arm at (4,14), tag `glasswake`. Team 1 `lanternkeepers_glassgrinder` pre-placed on the northwest glass at (5,5), (6,6) and (7,7), tag `glassgrinder`.
- **Events:**
  1. Turn 1: status `stunned` on tag `glasswake` for 2 turns, with a message from **Glasswake**: "Shape. Shape. Shape. Light. Too much light. Which one is me?"
  2. Turn 3: message from **Lensmaster Oriel Venn**, from the ruined tower: "It's looking at me. Glass is not supposed to look back. Grind it to the bed and salt the dust."
  3. Turn 5: reinforcement, a `lanternkeepers_beamwright` and two `lanternkeepers_lamplit_sailor` at (22,14), (23,14) and (24,13) on the east arm, and status `lk_dazzled` on tag `spire_bodies` for 2 turns: the beam sweeps across the glass toward us.
- **Bonus objective:** unit_hp_above tag `glasswake`, fraction 0.5.
- **Victory text:** The last wheel stops. Glasswake lifts itself out of the glass in a hundred clear plates and turns them, all at once, toward the lighthouse. "It aches," it says. "When the light goes over. It aches like holding something up." We do not know what it means. It shows us a picture of Venn's face, and we keep it.
- **Defeat text:** The wheels go on until the glass is white dust. Glasswake's last thought reaches us as a picture of the lamp, very bright, with something enormous and dark on the far side of it. We do not understand the picture. We keep it anyway.
- **Unlocks:** `reef_ascendant_lensbearer`, `ra_equip_synapse_nodule`.

## Mission 6: `ra_crumbling_branches` — "Crumbling Branches"
- **Map:** `tide_steps` (the basin full, the terraces dry)
- **Enemy:** `hadal_court`
- **Type:** hold: keep the Court off the brine basin while the eldest branches fail.
- **Briefing:**
  Something is wrong with us. The oldest branches, the ones that woke first, have begun to come apart in the night; they do not break, they soften, and then they are sand. Marrowbloom says this is very interesting and asks if it may eat them, and we have said no, for now.

  There is a basin at the bottom of the Steps that the tide keeps trying to refill. When we stand in it, the crumbling slows, and we do not know why. Glasswake knows, we think, and is not saying. The bell-shaped ones from below are climbing toward it, slowly, the way they do everything, and they mean to drink from it on their long walk up.

  We hold the basin. They are huge and patient, and we are many. If they want water, they can take it from the sky that they keep staring at.
- **Victory:** survive 12 turns.
- **Defeat:** reach_tile team 1 on any brine pool of the basin ring: (9,12) to (14,12), (8,13), (9,13), (14,13), (15,13), (8,14), (9,14), (14,14), (15,14), (9,15) to (14,15); or unit_lost tag `coralspire`.
- **Setup:** Coralspire pre-placed at (12,23), tag `coralspire`. Team 1 `hadal_court_tollwarden` pre-placed at (11,4), tag `tollwarden`, with two `hadal_court_bell_knight` beside it.
- **Events:**
  1. Turn 2: message from **Herald Vhaal**, ringing across the basin: "Eldest. You were on the floor when the weight went. You are old enough to know. Who lifted the sea?" Reply from **Coralspire**: "We were dead. We remember the weight going. We do not remember anything holding it."
  2. Turn 4: status `weakened` for 99 turns on tag `coralspire`, and terrain, `calcite` at (12,22), radius 1, permanent: the eldest branches fail and fall as calcite at our feet. Message from **Marrowbloom**: "It's still you. It's still good. Please."
  3. Turn 7: reinforcement, a `hadal_court_trench_crab` and two `hadal_court_pit_thrall` come over the west terraces at (1,11), (1,12) and (2,12).
- **Bonus objective:** defeat_unit tag `tollwarden`.
- **Victory text:** The Court stops at the edge of the basin and looks at us for a long time. Then they turn and go on up the Steps, toward the Shoal, without drinking. Vhaal is the last to go. "You are made of the thing you are keeping out," she says. "I had hoped the old ones would know that." We stand in the basin all night. The crumbling slows. It does not stop.
- **Defeat text:** The Bell-Knights wade into the basin and the water closes over them like a door. We stand on the terraces and feel the oldest of us soften, branch by branch, into sand. Vhaal does not look back. She has her answer, or enough of it.
- **Unlocks:** `reef_ascendant_spireguard`, `ra_spell_choking_overgrowth`.

## Mission 7: `ra_taste_of_rain` — "Taste of Rain"
- **Map:** `weeping_shelf` (the rain heavier than it has ever been; Deeplight has gone dark)
- **Enemy:** `returning_tide`
- **Type:** march: cross the chasm and stand in the rain.
- **Briefing:**
  The light at the bottom of the trench has gone out. We felt it the way you feel a tooth go. Glasswake has not stopped shaking since, and the cliff that weeps from a clear sky is weeping harder, and the wet ones are dancing in it.

  We are going to the rain. We do not want to. We are going because the crumbling is in all of us now, not just the eldest, and because Glasswake says that the rain is the only thing on the Ebb that is made of what we are made of. We think Glasswake is wrong. We are going to prove it.

  The rain is heaviest at the pool beside the shrine, on the far side of the chasm. We cross by the causeway or by the long flank, and we stand in it. Then we will know.
- **Victory:** reach_tile tag `coralspire` on (8,3), (7,3), (9,3), (8,2) or (8,4) (the rain pool beside the shrine).
- **Defeat:** unit_lost tag `coralspire`, or turn_limit 14.
- **Setup:** Coralspire pre-placed at (5,17), tag `coralspire`. Team 1 `returning_tide_rainsayer` pre-placed at (3,4) and (5,4) beside the shrine, tag `rainsayer`.
- **Events:**
  1. Turn 2: terrain, `brine_pool` at (8,15) and at (13,15), radius 1, for 4 turns: the rain reaches our side of the chasm. Message from **Imre Dunnock**, passing on the road to the Shoal: "You came to drink with us, little forest. Everyone does, in the end. Welcome home."
  2. Turn 4: status `regen` on tag `coralspire` for 4 turns. Message from **Coralspire**: "It goes into the branches. It goes in. It tastes like the mire and the basin and the inside of every one of us. It tastes like us."
  3. Turn 6: reinforcement, three `returning_tide_penitent` and a `returning_tide_choirmaster` at the north end of the causeway, (6,9), (7,9), (8,9) and (7,8).
- **Bonus objective:** defeat_unit tag `rainsayer` (both Rainsayers dead).
- **Victory text:** We stand in the pool beside the shrine and the rain falls on us, and every crumbling branch goes hard again. We understand. We were laid down, polyp on polyp, in water that is now hanging over our heads. We are the sea's bones. The Ebb that woke us has been starving us since the first morning, and the thing we have been fighting to keep away is the only thing that could feed us. The wet ones are singing. For the first time, we know the tune.
- **Defeat text:** We never reach the pool. The rain falls on the far side of the chasm, where we can see it and not feel it. The Tide sing to us across the gap, gently, as if we were their own dead. Perhaps we are.
- **Unlocks:** `reef_ascendant_calcite_bloom`, `ra_equip_heartstone_geode`.

## Mission 8: `ra_overgrowth` — "Overgrowth"
- **Map:** `lantern_shoal` (night, rain beginning, the lamp lit; the same night as Campaign 1, mission 8)
- **Enemy:** `returning_tide` (team 1) and `overcurrent` (team 2, hostile to everyone, falling from the sky)
- **Type:** hold / protect finale: grow a wall round the lighthouse and keep the keeper alive.
- **Briefing:**
  We have decided. It took us four days, which is fast for us. If the sea comes back it will feed us, and it will also drown everything that walks on the floor: the road-builders, the hulk people, the wet ones who are praying for it, and the small dry cutter on the north bank who still owes us a sled. We would like to be fed, but we would not like that.

  The lighthouse on the Shoal is the brightest of the ones still burning. Glasswake says it is holding up the most. The Tide are marching on it in the rain, and something is falling out of the thin dark over it, pale and wet and hungry for light. The road-builders are inside the old wall. They will not be enough.

  So we will be the wall. We grow round the tower and the old keeper on its stones, and we hold until the rain stops or we do. We will starve slowly, out here in the dry, for as long as it lasts. We have been starving since the first morning, and we only just noticed.
- **Victory:** survive 14 turns.
- **Defeat:** unit_lost tag `keeper_auster`, or unit_lost tag `coralspire`, or destroy_keystone (team 0, our Beacon).
- **Setup:** Coralspire pre-placed at (10,17), tag `coralspire`. Guest `lanternkeepers_keeper_pell_auster` on team 0 on the lighthouse plateau at (10,9), tag `keeper_auster`. Guests `reef_ascendant_marrowbloom` at (8,16), tag `marrowbloom`, and `reef_ascendant_glasswake` at (12,16), tag `glasswake`, on team 0. Team 1 (Returning Tide) deploys from the north Beacon at (10,1). Team 2 (Overcurrent) has no Beacon and arrives only by event.
- **Events:**
  1. Turn 2: terrain, `living_reef` at (6,10), (15,10), (10,6) and (10,15), radius 1, permanent: the wall begins, on and around the old Concord wall. Message from **Commander Tamsin Orrel**, from the tower: "There is coral climbing my wall. Is that ours? Nobody fire on it until I know whose it is."
  2. Turn 5: surprise spawn, team 2 falls on the northeast silt: two `overcurrent_bellyeye_shoal`, a `overcurrent_gulper` and a `overcurrent_downward_shark` at (19,4), (20,5), (18,3) and (20,4), with terrain `brine_pool` at (19,4), radius 1, for 3 turns. Message from **Glasswake**: "They are from up there. They have never seen the floor. They think the lamp is the sun."
  3. Turn 10: the sky breaks (as Campaign 1, mission 8): terrain `brine_pool` at (4,10), (16,10), (10,4) and (10,16), radius 1, for 4 turns; status `soaked` on tags `coralspire`, `marrowbloom` and `glasswake` for 2 turns; team 2 spawns a `overcurrent_hagwyrm` and a `overcurrent_lure_mother` on the southwest silt at (1,16) and (2,17). Message from **Keeper Pell Auster**: "Good wall. Wet wall. They'll drink from it. Hold anyway."
- **Bonus objective:** unit_hp_above tag `keeper_auster`, fraction 0.5.
- **Victory text:** Near dawn the old keeper climbs to the glass and puts her hand on it, and the rain slows, and stops. The falling things lie on our branches, drying. Inside the wall the young commander looks up, and so do we, and for the first time we see the sea: dark, huge, hanging, made of the same thing we are. Marrowbloom asks if it is food. Glasswake says nothing, and stops aching. We stay. The wall does not drink. It will last a long time, and then it will be sand, and that is the price of a dry morning for everyone else. We have decided it is worth it. It took us four days.
- **Defeat text:** The keeper falls on the stones and the lamp gutters. The rain comes down like a dropped roof. For one moment we are fed, more than we have ever been fed, and we grow faster than we have ever grown, into a reef that will stand on the bottom of the sea for ten thousand years. There is nobody left to see it.
- **Unlocks:** `reef_ascendant_marrowbloom`, `reef_ascendant_glasswake`.

## Campaign arc and secret
Missions 1 to 3 teach the horde, synapse range, living reef and calcite, and show the Reef's simple want: the Ebb, forever, and everything that cuts or drains it turned to stone. Missions 4 to 6 show what the dry world thinks of it (a weed, a lens to grind out, an old witness with no answer) while its eldest branches begin to crumble and only standing water slows the rot. Missions 7 and 8 reveal the secret: the Reef is made of the sea. Every branch was laid down underwater, and the Ebb that woke it has been starving it since the first morning; the rain heals it because the rain is what it is. The Reef chooses the drowned world's opposite anyway, and grows a wall round Lantern Shoal so the lamp can hold, knowing the wall will slowly turn to sand. Unawarded at the end: `reef_ascendant_elder_colony`, `ra_spell_swarm_call`, `ra_spell_synapse_surge`, `ra_spell_great_waking`, `ra_spell_tithe_of_the_shelf`, `ra_equip_spur_crown`, `ra_equip_tidal_husk`.
