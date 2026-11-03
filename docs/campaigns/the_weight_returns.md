# Campaign 3: "The Weight Returns"

Campaign id: the_weight_returns · Faction: hadal_court · Mission prefix: hc_

Faction: Hadal Court (`hadal_court`). 8 missions. Escalation: assault with an escort, hold, siege and assassination, restraint, ambush escort, assault, breakthrough, finale. Relics are named by role with exact ids. Pearl rewards follow the bible (win, speed, losses, bonus). All times in turns; coordinates are (x, y) on the named map. Setting canon: `EBB_world_bible.md`, `bible/history_and_gazetteer.md`. Crossovers follow `campaign_1.md` and `campaigns/OUTLINE.md`. Herald Vhaal is pre-placed in every mission with tag `herald_vhaal`.

## Starting roster
- `hadal_court_herald_vhaal`
- `hadal_court_pit_thrall` x4
- `hadal_court_lantern_spitter` x2
- `hc_spell_pressure_spike`
- `hc_equip_brine_greaves`

## Recurring characters

**Herald Vhaal, the Third Bell** (player). Envoy of the Court of Depths in a bronze brine-bell, sent up the trench wall with one question: who lifted the sea? Formal, slow, unfailingly polite. She keeps a register of every answer she is given and marks each one true or false, and so far she has marked none of them true. She starts the climb as a magistrate looking for a thief. She ends it as a guard.

**Orrun Tessk, Bell-Knight.** Stood the night watch on the trench floor the night the weight went away, and was never relieved, because the officer who posted him did not survive the morning. His bell is cracked and still tolls. He speaks rarely and in the past tense, as if giving evidence. He wants an officer of the surface to stand in front of him and sign the order that ends his watch.

**Maelis Quell, Vent-Priest.** Eldest of the Vent-Priests, who has carried one flame up out of the trench for forty years, cupped against the cold. She keeps the giants alive and counts their cracks. She wants to see the Court reach the open sky alive, and to learn whether the sea above is mercy or theft. She is the first of the Court to laugh, which in a pressure-bell sounds like a kettle coming to the boil.

**Odo Brask, Compact fixer.** To the Court, a small loud man in three coats who answers every question with a price. Since Mother Hull he has read the Compact's copy of the Vigil Book, and he has not slept well. He will sell Vhaal the nearest thing to the truth he can bear to say, and then sell where she is standing.

**Prophet Imre Dunnock, "the Wet Saint".** The Tide's prophet, a former Concord tax clerk who audited the water ledgers and found they did not balance. He tells the Court they are fellow mourners of the same sea. He knows the sea will not be merciful when it comes home, and he says it will be anyway.

**Keeper Pell Auster.** Last Lanternkeeper of the Shoal, half-blind, never asleep. The Court has heard her name from the Concord, the Compact and the Tide, and all of them said it like a warning. She is the last person Vhaal asks, and the only one who answers.

---

## Mission 1: `hc_the_long_climb` — "The Long Climb"
- **Map:** `boiling_floor` (the Court rises onto the south plateau; Compact powder works on the north plateau; the vent island in the rift between, reached by the bone causeways. Maelis Quell pre-placed at (14,20) as a guest, unit `hadal_court_maelis_quell`, tag `maelis_quell`; two `hadal_court_bell_knight` at (12,20) and (14,22))
- **Enemy:** `salvage_compact`
- **Type:** assault / escort: keep the flame alive and break the powder works.
- **Briefing:**
  Register of the Third Bell, first entry above the dark. We have climbed for nineteen days, and the trench wall has finally ended in something the surface calls a floor. Maelis Quell carries the flame that has kept us warm since the cradle-pools, and it does not like the dry. I carry one question, and I have not yet met anyone worth asking.

  The vents of the Boiling Floor are ours. They were warm when the sea sat on them and they are warm now. Salvagers have built a powder works on the north plateau and are blasting our vents open to render the grease that gathers in them, which is like mining a hearth for its soot.

  We will cross the rift by the bone causeways and break the powder works. Maelis's flame must not go out; it is older than any lamp on the surface. I have asked the Bell-Knights to walk in front of her, and they have asked me to stop asking.
- **Victory:** destroy_keystone (team 1: the powder works on the north plateau, (12,2)).
- **Defeat:** unit_lost tag `maelis_quell`, unit_lost tag `herald_vhaal`, or turn_limit 16.
- **Events:**
  1. Turn 1: message from **Maelis Quell**: "Cold up here, Herald. Walk slowly. The flame and I are both old."
  2. Turn 3 (enemy turn): the Compact blasts the east vents. Terrain `scrap_field` at (14,11), radius 1, for the rest of the mission (duration 99). Spawn `salvage_compact_powder_monk` at (9,13) and `salvage_compact_wrecker` at (10,13). Message from **Brother Ashmaw** (from the powder works): "Nobody owns a hole in the ground, Herald! Salvage law. We were here first."
  3. Turn 6 (enemy turn): two `salvage_compact_bone_sled_rider` swing round the west causeway onto the south plateau at (3,18) and (4,18), riding for the flame. Message from **Herald Vhaal**: "Riders on the left. Bells, close on the priest. Thralls, be the floor."
- **Bonus objective:** Relight the flame at a living vent: reach_tile tag `maelis_quell` on any west-island vent, (10,10), (11,10), (11,11), (10,12) or (11,12). +Pearls.
- **Victory text:** The powder works go up in one long cough of grease-smoke, and the salvagers scatter north on their sleds, still shouting about law. Maelis kneels at a vent on the island and holds the flame to it until it burns blue. "There," she says. "Now it remembers where it came from." Vhaal enters the salvagers' claim in the register, and marks it false.
- **Defeat text:** The flame gutters in the dry wind and goes out. Maelis stands over the cold bowl for a long time, then starts back down the trench wall to relight it at the cradle-pools. It will take the Court a year. The surface does not notice.
- **Unlocks:** the bell line (Bell-Knight, `hadal_court_bell_knight`), the vent healer (Vent-Priest, `hadal_court_vent_priest`).

## Mission 2: `hc_deeplight_rising` — "Deeplight Rising"
- **Map:** `trench_deeplight` (the Court holds the middle and lower tiers from the lower bell-gate at the south; a Concord prospecting camp sits on the fallen lamp's terrace at the north. Pre-placed Concord: three `salt_concord_surveyor` at (8,4), (12,4) and (10,5), tag `salt_surveyor`; Survey-Chief Abel Marrish, a `salt_concord_tollkeeper`, at (10,4), tag `survey_chief`. Orrun Tessk pre-placed at (10,16) as a guest, unit `hadal_court_orrun_tessk`, tag `orrun_tessk`)
- **Enemy:** `salt_concord`
- **Type:** hold / defend.
- **Briefing:**
  Register of the Third Bell, entered at Deeplight. Six days ago a Concord company carried a Lanternkeeper across our bridges to the fallen lamp. I put my question to their commander, and she said she did not know. I have marked it as the first lie of the climb.

  Behind her company came prospectors, the way hagfish come behind a carcass. They have pitched a survey camp on the lamp terrace and are walking down the bridges with salt-markers in their packs, writing our city into their ledger one tier at a time. One salt-marker driven into the brood galleries below the lower bell-gate would kill a generation of thralls.

  We hold the middle and lower tiers until the camp loses heart. Orrun Tessk has come up from the floor to stand with us. He has not said why, and in three hundred years nobody has found the courage to ask him.
- **Victory:** survive 10 turns, or defeat_unit tag `salt_surveyor` (every surveyor dead).
- **Defeat:** reach_tile (team 1, tag `salt_surveyor`, any brood-gallery tile: x 6 to 15 on rows 19 and 20), unit_lost tag `herald_vhaal`, or destroy_keystone (team 0: the lower bell-gate, (10,18)).
- **Events:**
  1. Turn 1: message from **Orrun Tessk**: "They are standing on the lamp, Herald. They are measuring it."
  2. Turn 4 (enemy turn): two `salt_concord_causeway_outrider` gallop down the outer causeways, spawning at (3,13) and (18,13). Message from **Survey-Chief Abel Marrish**: "We're not taking anything, Herald. We're only writing down where it is."
  3. Turn 7 (enemy turn): the brine curtain thickens over the outer islets. Terrain `brine_pool` at (3,10) and at (18,10), radius 1, duration 4; status `soaked` on tag `salt_surveyor` for 2 turns. Message from **Herald Vhaal**: "The sky weeps on my city. It did not used to. Make a note of it."
- **Bonus objective:** Take the survey ledger: defeat_unit tag `survey_chief`. +Pearls.
- **Victory text:** The prospectors break on the middle bridges and run back up past the lamp, leaving their ledger in the brine. Vhaal reads it. Every tier of Deeplight is drawn, numbered and priced, and across the top someone has written "unclaimed". She enters it in the register, and marks it false.
- **Defeat text:** A surveyor reaches the brood galleries and drives his marker into the warm silt. The salt spreads in a white ring. By nightfall the pools are still, and the Court carries its young up the bridges in its arms.
- **Unlocks:** the lure (Lurecaller, `hadal_court_lurecaller`), the shadow scout (Murk Diver, `hadal_court_murk_diver`).

## Mission 3: `hc_the_unsigned_treaty` — "The Unsigned Treaty"
- **Map:** `saltpan_bastions` (the Court comes up the south road to the star fort; Verge-Captain Rook Saddler, a `salt_concord_rim_marshal`, holds the fort's inner ring at (14,13), tag `verge_commander`. Orrun Tessk pre-placed at (14,25) as a guest, unit `hadal_court_orrun_tessk`, tag `orrun_tessk`)
- **Enemy:** `salt_concord`
- **Type:** siege / assassinate.
- **Briefing:**
  Register of the Third Bell, entered at the Saltpan Verge. This is where the Concord's roads stop and their cairns say the surveyed world ends. Orrun Tessk asked to come here. It is the first thing he has asked for since the night the weight went away.

  Orrun stood the watch on the trench floor that night, and the officer who posted him did not survive the morning. He has never been relieved. He wants an officer of the surface to stand before him and sign for what was taken, and the nearest officer of the surface commands this fort.

  We take the fort through the south gate and bring the commander to Orrun. I would prefer the commander alive, and so would Orrun. The commander may hold a different view, and the Court has always respected a different view, briefly.
- **Victory:** defeat_unit tag `verge_commander`.
- **Defeat:** unit_lost tag `herald_vhaal`, unit_lost tag `orrun_tessk`, or turn_limit 16.
- **Events:**
  1. Turn 1: message from **Orrun Tessk**: "I have stood the watch three hundred and eleven years. I would like it signed for."
  2. Turn 3 (enemy turn): Saltwrights seal the inner south gate. Terrain `salt_wall` at (15,17), radius 0, duration 6. Message from **Verge-Captain Rook Saddler**: "Lay down your bells and the Concord will hear your claim at Harrowgate. You have my word."
  3. Turn 6 (enemy turn): Concord relief on both salt roads: `salt_concord_brineguard` at (0,14) and (1,14), `salt_concord_stair_warden` at (29,15). The Court's own straggler arrives: spawn team 0 `hadal_court_trench_crab` at (14,24). Message from **Herald Vhaal**: "The crab has caught up. It is late. So is the Concord. Take the gate."
- **Bonus objective:** Keep Orrun Tessk above half health (unit_hp_above tag `orrun_tessk`, 0.5). +Pearls.
- **Victory text:** Saddler, pinned against his own wall, offers to sign anything at all. Orrun hands him the paper and waits. Saddler signs it with a name that is not his, and dies before he can be asked for the right one. Orrun folds the paper into his cracked bell, where the brine eats the ink by morning. The watch goes on.
- **Defeat text:** Orrun Tessk falls in the south gate with his bell still tolling. The Concord's dispatch says a Court monster was slain at the Verge. Vhaal's register says a watchman died at his post, unrelieved.
- **Unlocks:** the artillery (Pressure Lancer, `hadal_court_pressure_lancer`), the pinning beast (Trench Crab, `hadal_court_trench_crab`).

## Mission 4: `hc_the_upper_kin` — "The Upper Kin"
- **Map:** `tide_steps` (the Court holds the south terraces; the basin below is wet shallows and brine pools, which keep the Overcurrent alive. Pre-placed Upper Kin in the basin: `overcurrent_weeping_sunfish` at (11,12), tag `upper_kin_sunfish`; `overcurrent_bellyeye_shoal` at (8,12) and (15,12); `overcurrent_hagwyrm` at (5,13). Maelis Quell pre-placed at (12,23), tag `maelis_quell`; Orrun Tessk at (11,23), tag `orrun_tessk`, both guests)
- **Enemy:** `overcurrent`
- **Type:** survive / restraint.
- **Briefing:**
  Register of the Third Bell. Deeplight is dark. A Murk Diver came up the Steps last night to say that a wet column came down our bridges singing, that keepers came behind it, and that between them the lamp went out. Over the city it is raining the sea, and the old ones stand in the galleries weeping, with their mouths open to it.

  Since then the sky over the Steps has gone thin, the colour of a bruise healing. This morning things began to fall through it: pale, wet, starving, lit from beneath. They are the Upper Kin, who were lifted with the sea and have lived in it upside down ever since, and the Court does not raise a hand to kin.

  We will not strike first. The Kin cannot live long in the dry, and Maelis's flame is the brightest thing on the terraces, so they will climb toward it and wither on the way. Hold the terraces, guard the flame, and wait. If one must be struck, strike it once, and do not enjoy it.
- **Victory:** survive 10 turns, or eliminate (team 1).
- **Defeat:** unit_lost tag `maelis_quell`, or unit_lost tag `herald_vhaal`.
- **Events:**
  1. Turn 1: message from **Maelis Quell**: "They are all looking at my flame, Herald. I have never been looked at like that."
  2. Turn 3 (enemy turn): the Kin fall onto the dry lower terrace: spawn `overcurrent_downward_shark` at (10,20) and `overcurrent_gulper` at (14,20). Message from **The Upper Kin**: "(a sound like a bell heard from under water, and then a sound like teeth)"
  3. Turn 6 (enemy turn): the thin sky weeps over the west basin. Terrain `brine_pool` at (6,14), radius 2, duration 3. Spawn `overcurrent_lure_mother` at (6,22), beside the terrace pool. Message from **Orrun Tessk**: "It is in my reach, Herald. I am not reaching."
- **Bonus objective:** Spare the weeper: the unit tagged `upper_kin_sunfish` is still alive at victory (negated defeat_unit tag `upper_kin_sunfish`). +Pearls.
- **Victory text:** By the tenth turn the Kin on the terraces have dried to pale husks, and the ones in the basin lie in the shallows breathing slowly, like things that have eaten too much. Maelis sits at the water's edge and keeps her flame low so as not to call them. "They fell out of our sea," she says. "Whatever lifted it lifted them too." Vhaal writes nothing in the register. The Kin gave no answer, and told no lie.
- **Defeat text:** The Kin reach the flame and swallow it, and then lie on the terrace drying in the light they have eaten. The Court carries what is left down to the basin. The water there is too shallow to hold anything up.
- **Unlocks:** the warm prayer (Vent Surge, `hc_spell_vent_surge`), the carried heat (Vent Flask, `hc_equip_vent_flask`).

## Mission 5: `hc_the_market_of_liars` — "The Market of Liars"
- **Map:** `the_kettle` (market day. Vhaal starts alone at Brask's stall in the sunk centre, (11,12); the rest of the Court waits at the south gate in the normal deploy zone. Odo Brask, `salvage_compact_odo_brask`, on team 1 at (12,9), tag `odo_brask`. Compact ambushers pre-placed in the gaps of the south hull ring: `salvage_compact_wrecker` at (6,17) and (16,17), `salvage_compact_rivet_slinger` at (9,17) and (13,17))
- **Enemy:** `salvage_compact`
- **Type:** escort / ambush.
- **Briefing:**
  Register of the Third Bell, entered in the Kettle. Every voice on the climb has said that if a thing is known on the Ebb, a broker named Odo Brask is selling it. So I have come to his market under the market code, with my bell polished and my Bell-Knights left at the gate as the code requires.

  Brask received me in a stall that smelled of lamp-oil and fear. He named his price, which was high, and I paid it, which surprised him. Then, sweating through three coats, he told me that the keepers of the lamps took our sea and hold it above the world like a purse.

  It has the weight of a true thing and the shape of a sale. I will consider it on the walk back to the gate, where my bells are waiting. Brask will not meet my eye, and the stalls between here and the gate have gone very quiet.
- **Victory:** reach_tile (team 0, tag `herald_vhaal`, tiles (9,18), (10,18), (11,18): the south gate road inside the Court's lines).
- **Defeat:** unit_lost tag `herald_vhaal`, or turn_limit 12.
- **Events:**
  1. Turn 1: message from **Odo Brask**: "Nothing personal, Herald. Somebody paid more for where you'd be standing than you paid for what I said. It's a market."
  2. Turn 3 (enemy turn): Brask kicks over the oil. Terrain `lamp_oil` at (11,11), radius 1, duration 3. Two `salvage_compact_bone_sled_rider` swing in through the east gap at (19,9) and (19,10). Message from **Maelis Quell** (from the gate): "Herald, the floor is on fire. I am told this is normal for a market."
  3. Turn 6 (enemy turn): `salvage_compact_hullbreaker` at (4,16) and `salvage_compact_snare_tinker` at (5,16) come over the west hulls. Message from **Orrun Tessk**: "Code or no code, Herald, I am coming in."
- **Bonus objective:** Protect the paid: Odo Brask is still alive at victory (negated defeat_unit tag `odo_brask`). The Herald paid for an answer, and a merchant who has been paid is under her protection, even when the answer was short. +Pearls.
- **Victory text:** Vhaal walks out through the south gate with three harpoons in her bell and the register under her arm, and the market closes behind her like water. At the gate she writes down Brask's answer and holds the pen over it for a long time. She does not mark it false. She writes: "Weighed. Short."
- **Defeat text:** The Herald falls in the aisles of the Kettle. The salvagers have her bell off its frame and onto a sled before the dust settles, and by nightfall it is sold to a buyer who will not say whom they are buying for.
- **Unlocks:** the drag (Undertow, `hc_spell_undertow`), the borrowed lure (Stalk-Lamp Lantern, `hc_equip_stalklamp`).

## Mission 6: `hc_the_rain_that_faces_upward` — "The Rain That Faces Upward"
- **Map:** `weeping_shelf` (rain active. The Court comes from the south half; the Tide shrine stands on the north half at (4,3), beyond the chasm. Two crossings: the short bone-road causeway at x 6 to 8, rows 10 and 11, and the long east flank at x 18 to 21. A `returning_tide_choirmaster` stands at the shrine and carries Dunnock's voice)
- **Enemy:** `returning_tide`
- **Type:** assault.
- **Briefing:**
  Register of the Third Bell, entered under the rain at the Weeping Shelf. The Tide sent word ahead that the Court would be welcome here, as fellow mourners. They have heard that Deeplight went dark. They say it proudly, because it was their column on our bridges.

  Their prophet speaks to us across the chasm through a choir of the drowned. He says we grieve the same sea, that the lamps keep it from both of us, and that if we help put out the lights it will come home to the Court and be merciful to everyone. He is the second voice to tell me the lamps are the thieves, and the first to say the thief should be killed for the sea's own good.

  We are not mourners. We are claimants, and a claimant does not drown the house to get it back. We will cross the chasm and break their shrine, and when the rain falls on us we will not open our mouths.
- **Victory:** destroy_keystone (team 1: the shrine, (4,3)).
- **Defeat:** unit_lost tag `herald_vhaal`, or turn_limit 15.
- **Events:**
  1. Turn 1: message from **Imre Dunnock** (through the Choirmaster's chant): "Welcome, cousins. We are all orphans of the same water."
  2. Turn 4 (enemy turn): a Rainsayer floods the causeway. Terrain `brine_pool` at (7,11), radius 1, duration 3; spawn `returning_tide_rainsayer` at (7,8). Message from **Maelis Quell**: "The rain is warm. It should not be warm. Somewhere a lamp is straining."
  3. Turn 7 (enemy turn): the drowned come up behind the Court on the south half: `returning_tide_drowned` at (18,12) and (20,12), `returning_tide_anchor_bearer` at (19,13). Message from **Orrun Tessk**: "The dead are behind us, Herald. They walk as if they have been told where to go."
- **Bonus objective:** Break the shrine before turn 11. +Pearls.
- **Victory text:** The shrine breaks, and the rain does not stop. The faithful stand in it with their mouths open and sing the Court out of the Shelf. One wringer stands apart and does not sing; she tastes the rain the way the old ones did in the galleries at Deeplight, and her face says she has understood something she would rather not have. Vhaal enters the prophet's offer in the register and marks it false. Under it, in smaller script, she adds: "He knows."
- **Defeat text:** The Court is driven back to the chasm's lip and stands there, soaked, while the choir sings it out of the rain. Dunnock's voice follows them all the way down the Shelf: "You will come back. Grief always comes back to the water."
- **Unlocks:** the waking tomb (Crushing Maw, `hadal_court_crushing_maw`), the held bell (Bellward, `hc_spell_bellward`).

## Mission 7: `hc_what_the_glass_remembers` — "What the Glass Remembers"
- **Map:** `glasswork_reach` (the Court enters by the south arm; the Lamplit hold the ruined lighthouse plateau and the north arm; the road to the Shoal leaves the map at the north edge, (12,0) to (16,0). Three `hadal_court_bell_knight` pre-placed at (13,26), (14,26) and (16,26), tag `bell_vanguard`. Captain Hollis Drenn, `lanternkeepers_captain_hollis_drenn`, at (14,10), tag `captain_drenn`; every pre-placed keeper unit also carries tag `keeper_line`)
- **Enemy:** `lanternkeepers`
- **Type:** breakthrough.
- **Briefing:**
  Register of the Third Bell, entered at the edge of the glass. Two voices have now told me that the lamps hold the sea, and that the keepers know who lifted it. The keepers' road to Lantern Shoal crosses this reach, where the old beam swept for three hundred years and turned the sand to glass.

  The keepers are waiting on the glass, and their captain is a drowned man bound to a lamp. He sent one message: that the lamps hold nothing, the keepers know nothing, and the Court should go home. It is the most frightened lie I have been told on the climb, and it was told by a man who is already dead.

  There is nowhere to hide on beam glass, so we will not hide. The Bell-Knights will walk into the beams in front of me, one step at a time, the way they walked out of the trench. I will walk behind them to the north road. We break no lamps.
- **Victory:** reach_tile (team 0, tag `herald_vhaal`, tiles (12,0) to (16,0): the north road to the Shoal), or eliminate (team 1).
- **Defeat:** unit_lost tag `herald_vhaal`, defeat_unit tag `bell_vanguard` (all three vanguard Bell-Knights dead), or turn_limit 18.
- **Events:**
  1. Turn 1: message from **Captain Hollis Drenn**: "Last week a bird stole a page from us. This week, bells. Turn round, Herald. There's nothing up that road but an old woman and a light."
  2. Turn 4 (enemy turn): the beams sweep the south arm. Status `lk_dazzled` on tag `bell_vanguard` for 2 turns; spawn `lanternkeepers_beamwright` at (14,5), tag `keeper_line`. Message from **Orrun Tessk**: "It is very bright, Herald. I have decided to walk into it anyway."
  3. Turn 8 (player turn): a Deep Herald climbs up behind the Court and sings the dark. Spawn team 0 `hadal_court_deep_herald` at (15,24); status `hc_darkened` on tag `keeper_line` for 2 turns. Message from **Maelis Quell**: "Now they know what it was like for us. Walk, Herald. Quickly."
- **Bonus objective:** Leave the lamp burning: the keepers' Beacon at (14,2) is still standing at victory (negated destroy_keystone team 1). +Pearls.
- **Victory text:** Vhaal steps off the glass onto the north road, and the beams behind her go still. Drenn does not follow. He stands among his drowned sailors and watches the bells go north, and he has noticed, as they all have, that the Court did not break a single lamp. "Tell Auster I'm sorry," he calls after them. Vhaal writes it down and, for the first time on the climb, does not know how to mark it.
- **Defeat text:** The last of the vanguard falls on the glass, blind in the beam. The keepers do not pursue. Drenn has the bells carried off the glass and laid in the shade, which is the kindest thing anyone on the surface has done for the Court, and changes nothing.
- **Unlocks:** the dark choir (Deep Herald, `hadal_court_deep_herald`), the title rite (The Weight Returns, `hc_spell_the_weight_returns`).

## Mission 8: `hc_the_third_bell` — "The Third Bell"
- **Map:** `lantern_shoal` (rain beginning. The Court climbs out of the flooded lower court at the south; the keepers' lamp stands at the north, (10,1) to (11,2), with Keeper Pell Auster, `lanternkeepers_keeper_pell_auster`, beside it at (11,3) on team 1, tag `keeper_auster`. Keepers tagged `keeper_line` hold the lamp-stone plateau. The Tide host is team 2 (hostile to everyone), tag `tide_host`, coming in from the east with Imre Dunnock, `returning_tide_imre_dunnock`, at (19,4), tag `prophet_dunnock`. Orrun Tessk at (9,18) and Maelis Quell at (12,18) are pre-placed guests, tags `orrun_tessk` and `maelis_quell`. The Concord company holds the tower wall offstage and appears only by voice)
- **Enemy:** `lanternkeepers` (team 1) + `returning_tide` (team 2)
- **Type:** race / restraint / finale.
- **Briefing:**
  Register of the Third Bell, last entry before the question. The sky over the Shoal is raining. Deeplight is dark, the floor of the air is thin, and the Tide are marching on the last lamp on the Shelf to finish what they began in our city.

  I have asked the question of salvagers, soldiers, a prophet, a broker and a drowned captain. I have marked every answer false, or short. One keeper is left who has not been asked, and every voice on the climb has said her name the way one says the name of a cliff.

  We go to the lamp. We do not break it, we do not let the Tide break it, and we do not lay a hand on the keeper, because if she falls the question falls with her. Orrun has polished his bell and Maelis has banked her flame. I have written the question out fair, so there can be no mistake about what was asked.
- **Victory:** reach_tile (team 0, tag `herald_vhaal`, tiles beside the lamp: (9,1), (9,2), (12,1), (12,2), (10,3), (12,3)).
- **Defeat:** unit_lost tag `herald_vhaal`, unit_lost tag `keeper_auster` (by any hand), destroy_keystone (team 1: the lamp goes out), or turn_limit 16.
- **Events:**
  1. Turn 2 (Tide turn, team 2): message from **Imre Dunnock**: "Look up, Herald. That is your sea, coming home. Stand aside and let it."
  2. Turn 6 (enemy turn): message from **Commander Tamsin Orrel** (from the tower wall): "Herald. I told you at Deeplight I didn't know. I still don't. I wasn't lying." Then message from **Herald Vhaal**: "We shall see, Commander. I am asking someone else."
  3. Turn 10 (enemy turn): the sky breaks. Terrain `brine_pool` at (4,10) and at (16,10), radius 2, and at (10,16), radius 1, all duration 6; status `soaked` on tags `keeper_line` and `tide_host` for 2 turns. Message from **Keeper Pell Auster**: "Hurry up, bell. If you want to ask me something, it had better be now."
- **Bonus objective:** Keep Keeper Auster above half health (unit_hp_above tag `keeper_auster`, 0.5). +Pearls.
- **Victory text:** Vhaal reaches the lamp and reads her question out, fair, as written. Auster puts her hand on the glass before she answers. "I don't know who lifted it. Nobody alive does. I know who holds it: me, and the ones before me, and whoever comes next. Put this out and the weight goes home to you, and everyone up here drowns under it. That's the truth. It's all I've got." Below, the Commander's company brings Dunnock down, and the rain slows, and stops. The Court does not go home. Orrun Tessk plants his cracked bell at the foot of the tower and turns to face outward, and Vhaal opens the register at its first page, finds the Commander's name, and strikes out the word "lie".
- **Defeat text:** The lamp goes dark with the question still unanswered. The sky opens, and the weight the Court has wanted back for three hundred years comes down on the Shoal all at once. Vhaal stands in it and finds that it is not mercy, and not justice, and not home.
- **Unlocks:** the unrelieved watch (Orrun Tessk, `hadal_court_orrun_tessk`) and the carried flame (Maelis Quell, `hadal_court_maelis_quell`).

## Campaign arc and secret
Missions 1 to 3 teach the Court's slow weight, its few enormous bodies, and its grievance: the surface treats the Court's vents, city and dead as unclaimed ground, and nobody will sign for the theft. Missions 4 to 6 break the frame: Deeplight goes dark behind them, the Upper Kin fall through the thinning sky, and two voices (Brask, then Dunnock) tell Vhaal the lamps are the thieves, one to sell her something and one to use her. Missions 7 and 8 reveal the secret from below: the Court was right that the lamps hold the sea and wrong that anyone took it on purpose, and the only honest answer on the Ebb is "I don't know who did it; I know who is carrying it." Putting out the last lamp would give the Court back everything it lost and drown everyone else, and the Court, which has always respected the weight of things, chooses to stand guard over the glass instead. The register's last entry reads, in Vhaal's fair hand: "Question answered. Watch begun. Relieve no one."
