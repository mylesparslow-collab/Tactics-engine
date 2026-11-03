# Campaign 8: "What Feeds Below the Beam"

Campaign id: what_feeds_below · Faction: overcurrent · Mission prefix: oc_

Faction: The Overcurrent (`overcurrent`). 8 missions. Escalation: first fall, find water, eat the hunters, a saint is fed, strike the kin, toward the light, the hooked arms, the brightest light in the world. A short, brutal campaign where the player is the monster. The Overcurrent have no language, so every briefing is an entry from the Vigil Book's locked page, written by the keeper who follows them; their event lines are the animals' drives (Hunger, Light, Dry) and the hum of the Undersinging (The Choir). Every mission offers wet ground or brine events, because every Overcurrent champion `dries`. The player's own keystone is "the thin place" (where the sky is open above them). Pearl rewards follow the bible (win, speed, losses, bonus). All times in turns. Setting canon: `EBB_world_bible.md`, `bible/history_and_gazetteer.md`.

Timeline: the campaign runs in the weeks between Deeplight going dark (Tide mission 8) and the last night at Lantern Shoal (Concord mission 8, Lanternkeepers mission 8, Reef mission 8). The rain is falling across the Shelf throughout, and stops at the end.

## Starting roster
- `overcurrent_the_undersinging` (lead hero)
- `overcurrent_bellyeye_shoal`
- `overcurrent_bellyeye_shoal`
- `overcurrent_gulper`
- `overcurrent_gulper`
- `overcurrent_tongue_louse`
- `overcurrent_tongue_louse`
- `oc_spell_brine_squall` (spell: the starting answer to drying)
- `oc_equip_gill_bladder` (equipment)

## Recurring characters

**The Undersinging** (player). A siphonophore choir a hundred bodies long, every body a small lamp-coloured bell, humming at the frequency of the lighthouses. It is not a leader. The others follow its sound the way moths follow a lit window. It has no name for itself; Wenna Cray named it after the noise it makes through the floor of a lamp gallery. It begins hungry. It ends at the glass.

**Keeper Wenna Cray, the page's hand.** Nineteen, keeper of the small lamp at the Tide Steps, three years into a vow she took because her mother took it. The locked page has one rule: whoever sees them fall writes down what they do. She is the only one who saw. She follows the fall across the Ebb with two water skins, a borrowed sled and a pen, frightened the whole time, writing anyway. Dry, precise, and much braver on paper than she thinks she is.

**Mother Mantle, the Hook-Armed Deep.** A colossal squid with hooks turning in her suckers and an eye the size of a door. The people of Mother Hull named her after the hull because she came down beside it and would not leave. She is patient in a way nothing on the Ebb is any more. The small ones stay wet as long as they stay near her.

**Saint Rictus, the Jaw That Prays.** A goblin shark whose jaw slings out on a ligament, kept in a brine pool below the Weeping Shelf shrine by a Tide splinter that feeds it. The splinter is led by **Brother Ansel Tey**, a former Rainwatch tower-man who decided the sea had finally answered and that it was hungry. Tey is the only person in this campaign who is glad.

**The voices.** The animals do not speak. Their event lines are labelled by drive, and the JSON speaker is the drive's name: **Hunger** (food, warmth, wounds), **Light** (the beams, any glow), **Dry** (the air, the salt, the dying), and **The Choir** (the Undersinging's hum, the closest thing they have to a plan). Lines are lowercase fragments.

Also appearing: Prophet Imre Dunnock (M4, by chant), Coralspire (M2), Odo Brask and Brother Ashmaw (M7), Captain Hollis Drenn (M6), Lensmaster Oriel Venn and Keeper Pell Auster (M8). Tamsin Orrel's company holds the Shoal's outer wall in M8 and is never named as a unit.

---

## Mission 1: `oc_the_floor_thins` — "The Floor Thins"
- **Map:** `tide_steps` (dusk, the Steps lamp flickering; player on the south terraces, dry stone; the basin shallows below)
- **Enemy:** `salt_concord`
- **Type:** skirmish / tutorial: skyfall, drying, and the wet basin.
- **Setup:** player `overcurrent_the_undersinging` at (12,24), tag `undersinging`. Team 1 patrol in the basin shallows, tag `concord_patrol`: `salt_concord_surveyor` (12,16), `salt_concord_brineguard` (8,16), `salt_concord_brineguard` (15,16), `salt_concord_salt_levy` (5,15), `salt_concord_salt_levy` (18,15), `salt_concord_brine_slinger` (12,11). Small warband: 2 Salt Levy, 1 Brine Slinger. Wet ground: the whole basin (shallows rows 10 to 17, brine pools round the central lake).
- **Briefing:**
  Locked page, the first new entry in ninety years. Keeper Wenna Cray, the Steps lamp. Our lamp flickered three times at dusk, the evening the word came that Deeplight had gone dark. The page says that whoever sees what comes next must write it down, and nobody else saw it, so this is me.

  The sky over the basin went the colour of the inside of a shell. Then it sagged, the way canvas sags under rain, and things came through it. They were pale and wet and lit from underneath, and they hit the terraces like dropped fish, and they did not die.

  There is a Concord patrol in the basin, six of them, standing in the shallows to fill their skins. The things have smelled them. I am on the lamp gallery with the shutters closed, and I can hear them humming.
- **Victory:** defeat_unit tag `concord_patrol` (all six).
- **Defeat:** unit_lost tag `undersinging`, or turn_limit 12.
- **Events:**
  1. Turn 1: message from **Dry**: "air. too much air. it bites." Then message from **Hunger**: "warm ones. standing in our water. down."
  2. Turn 3: terrain `brine_pool` at (12,22), radius 1, duration 3 (the thin place drips on the terrace road). Message from **The Choir**: "mmmmm. the floor above is open. it weeps for us."
  3. Turn 5 (enemy turn): the Rainwatch relief comes down the terrace roads. Spawn team 1 `salt_concord_brineguard` (11,8) and (12,8), `salt_concord_causeway_outrider` (5,8), tag `concord_relief`. Message from **Sergeant Abel Corrie, Rainwatch**: "Form on the road! Shields up. And nobody look up, do you hear me? Nobody look up."
- **Bonus objective:** Feed before the relief reaches the basin: win before turn 6 (turn_limit 6, negated). Pearls: win 30, bonus 20.
- **Victory text:** The basin goes quiet. Six water skins float in the shallows, still full. On the terraces, two of the fallen have already gone grey and stiff in the air, and the rest have learned something: down, toward the wet. Wenna writes "they learn fast" and then crosses out "fast".
- **Defeat text:** The long one dries on the terrace in a ring of white salt, still humming, then not. The sky closes over the basin like a healed cut. Wenna writes the date, and nothing else, and does not sleep.
- **Unlocks:** `overcurrent_driftbell`, `oc_spell_something_heavy`.

## Mission 2: `oc_wet_ground` — "Wet Ground"
- **Map:** `oyster_banks` (islands of silt and waking reef, shallows between; a long drop on every side)
- **Enemy:** `reef_ascendant`
- **Type:** hunt / race against drying: kill the minds, take the wet.
- **Setup:** player `overcurrent_the_undersinging` at (14,20), tag `undersinging`. Team 1, three minds rooted on living reef, tag `reef_mind`: `reef_ascendant_brainstalk` at (3,7), (24,5), (24,16). Drones beside each mind, tag `reef_body`: `reef_ascendant_polyp_drone` at (2,7), (4,7), (23,5), (25,5), (23,16), (25,16). `reef_ascendant_spireguard` (13,9) on the central shallows, tag `reef_body`. Warband: Sting Anemone, Spitter Polyp x2, Fanblade, Reef Tender. Wet ground: the central shallows spine (cols 13 and 14), the oyster beds (wet, but they cut), the reef itself.
- **Briefing:**
  Entry the third. They are dying. Half of what fell at the Steps lay on the terraces by noon the next day, gone grey and stiff, with the salt drawing a white line around each one like a coroner's chalk.

  The rest went west in a long pale string toward the Oyster Banks, where the ground is wet. I followed with two water skins and a borrowed sled. The birds that used to sit on the Steps lamp have gone, and they have not come back.

  The Banks are not empty. The coral there is awake, it has noticed them, and it does not share. The long one, which I have started calling the Undersinging because of the sound, went straight for the shallows as if it remembered them.
- **Victory:** defeat_unit tag `reef_mind` (all three Brainstalks).
- **Defeat:** unit_lost tag `undersinging`, or turn_limit 14.
- **Events:**
  1. Turn 1: message from **Dry**: "the air is eating us. find the wet. find the wet."
  2. Turn 3 (enemy turn): terrain `calcite` at (13,11), radius 1, duration 5 (the colony seals its central oyster bed into dry stone). Message from **Coralspire**: "We close our wet. You are the sea. You are what we grew to keep out."
  3. Turn 6 (enemy turn): spawn team 1 `reef_ascendant_fanblade` (3,17) and (4,17), `reef_ascendant_spireguard` (2,18), tag `reef_body`, on the south-west reef behind the player. Message from **Hunger**: "more. sweet. bone that grows. more."
- **Bonus objective:** The Undersinging ends above half strength (unit_hp_above tag `undersinging`, 0.5). Pearls: win 35, bonus 15.
- **Victory text:** The minds go dark one by one, and the drones around them stop, mid-step, like toys run down. The Overcurrent lie in the shallows and do not dry. Wenna watches the Undersinging drift over the dead reef, humming, and writes: "It is not cruel. It is thirsty. I keep wanting those to be different things."
- **Defeat text:** The coral closes over the shallows and the fallen dry on its edge, one by one, facing the water they cannot reach. The reef grows over them by morning. Coralspire does not gloat. It simply goes on growing.
- **Unlocks:** `overcurrent_weeping_sunfish`, `oc_spell_spawning_water`.

## Mission 3: `oc_the_slime_knot` — "The Slime Knot"
- **Map:** `kelpmire` (husk forest and sinkmud, the cold channel of shallows winding through it)
- **Enemy:** `salvage_compact`
- **Type:** rescue / assassinate: eat the hunters before the kin is cut apart.
- **Setup:** player `overcurrent_the_undersinging` at (10,22), tag `undersinging`. Guest on the player's team: `overcurrent_hagwyrm` at (8,12) in the channel, tag `hagwyrm_kin` (the carcass that is not dead yet). Team 1 hunters, tag `harpoon_crew`: `salvage_compact_harpoon_engine` on the wreck at (3,6), `salvage_compact_breach_gunner` (12,9) and (15,8), `salvage_compact_quartermaster` (8,3). Cutters on the carcass, tag `carcass_cutters`: `salvage_compact_scrapper` (9,12) and (7,13), `salvage_compact_snare_tinker` (10,11). Warband: Wrecker x2, Rivet-Slinger, Tallow-Mender. Wet ground: the whole channel.
- **Briefing:**
  Entry the sixth. One of the big ones did not make it to the Banks. It came down in the Kelpmire instead, a hagfish the length of a wagon, and the Compact found it before it had finished dying.

  They are cutting it while it lives. Harpoons through the gill slits, a winch on a wreck, men with saws walking on its back. I am told the meat does not rot, and sells by the pound to a fat man in the Kettle who asks no questions.

  The others have heard it. I did not know they could hear each other. They are coming down the channel now, and the Compact has not noticed, because the Compact is counting.
- **Victory:** defeat_unit tag `harpoon_crew` (the engine, both gunners and the quartermaster).
- **Defeat:** unit_lost tag `undersinging`, or turn_limit 14.
- **Events:**
  1. Turn 1: status `sv_harpooned` on tag `hagwyrm_kin`, duration 3. Message from **Hunger**: "kin. pinned. it bleeds the good smell."
  2. Turn 4 (enemy turn): spawn team 1 `salvage_compact_bone_sled_rider` (13,18) and (15,18), tag `sled_riders`, behind the player. Message from **Cutter Mags Ollery**: "Keep sawing! Brask pays by the pound, and he don't pay for what crawls off."
  3. When the tag `hagwyrm_kin` dies: message from **Hunger**: "kin is meat now. good. good." Then message from **The Choir**: "mmm. mmmmm."
- **Bonus objective:** The hagwyrm survives (unit_lost tag `hagwyrm_kin`, negated). Pearls: win 40, bonus 25.
- **Victory text:** The Harpoon Engine goes over in the mud with its crew still on the winch. The hagwyrm pulls the last harpoon out of itself by knotting around it, and floods the channel with slime so thick the sleds will not come back for a season. Somewhere in the Kettle, a fat man in three coats raises the price of carcass.
- **Defeat text:** The sleds take the hagwyrm in pieces and the long one in a net. Wenna sees it a week later, dried and coiled in a Kettle stall, labelled "sky eel, does not rot, ask inside".
- **Unlocks:** `overcurrent_hagwyrm`, `oc_equip_hookskin`.

## Mission 4: `oc_a_saint_is_fed` — "A Saint Is Fed"
- **Map:** `weeping_shelf` (rain heavier than it has ever been; the chasm, the bone causeway, the long east flank)
- **Enemy:** `returning_tide`
- **Type:** escort / hold: keep the Saint alive until the censor dies or the choir gives up.
- **Setup:** player `overcurrent_the_undersinging` at (4,17), tag `undersinging`. Guests on the player's team: `overcurrent_saint_rictus` in the shrine pool at (8,18), tag `saint_rictus`; the splinter faithful, tag `splinter`: `returning_tide_penitent` (7,17) and (9,17), `returning_tide_shroud_mender` (8,19). Team 1: `returning_tide_choirmaster` at (4,5), tag `tide_censor` (Choirmaster Oda Vell, sent from Dunnock's camp). Warband: Penitent x3, Drowned x2, Tear-Slinger x2, Wringer, Undertow Singer. Wet ground: the shelf's brine pools (3,14), (13,15), (16,17), (8,18), plus the events.
- **Briefing:**
  Entry the ninth. There is a Tide splinter on the Weeping Shelf that has stopped waiting for the sea and started serving what comes out of it. They keep a goblin-jawed shark in the pool below the shrine. They call it Saint Rictus, and they feed it.

  I watched a man walk into the pool with his arms open. He was singing. I am writing this down because the page says to, and because I would rather nobody ever believed me.

  The main Tide does not approve. Dunnock's choir is coming over the causeway to put the Saint down, and the Undersinging has gone to the Shelf as if it had been called by name.
- **Victory:** defeat_unit tag `tide_censor`, or survive 10 turns.
- **Defeat:** unit_lost tag `saint_rictus`, or unit_lost tag `undersinging`.
- **Events:**
  1. Turn 1: message from **Brother Ansel Tey**: "Eat, Saint. Eat, and remember us to the sea when it comes home." Then message from **Hunger**: "they come to us. they come to us singing."
  2. Turn 3 (enemy turn): message from **Imre Dunnock** (through the Choirmaster's chant): "That is not the sea's mercy, children. That is its appetite. Come home." Spawn team 1 `returning_tide_drowned` out of the pools behind the player at (3,14) and (13,15), tag `tide_host`.
  3. Turn 6: terrain `brine_pool` at (8,13), radius 1, duration 4, and at (6,15), radius 1, duration 4 (the rain thickens where the Saint is fed). Message from **The Choir**: "mmmm. the sky leans down to listen."
- **Bonus objective:** Keep the splinter alive (unit_lost tag `splinter`, negated). Pearls: win 45, bonus 20.
- **Victory text:** The Choirmaster falls into the chasm still singing Dunnock's hymn, and the choir behind her breaks and goes home in the rain. Brother Tey kneels at the pool's edge and the Saint takes the offering from his hands, gently, which is worse. Wenna writes: "Dunnock was right. I did not expect to agree with him about anything."
- **Defeat text:** The choir sings the Saint down into the pool and holds it under the shallow brine until it stops moving. Brother Tey sits beside the water all night. In the morning he walks into the rain toward the Shoal, alone, and nobody follows him.
- **Unlocks:** `overcurrent_siphon_chain`, `oc_equip_parasite_crown`.

## Mission 5: `oc_the_upper_kin` — "The Upper Kin"
- **Map:** `boiling_floor` (scalding vents on the central island, bone causeways, shallows at the island's edges)
- **Enemy:** `hadal_court`
- **Type:** assault: break the vent-bell of a host that will not raise its hand first.
- **Setup:** player `overcurrent_the_undersinging` at (13,20), tag `undersinging`. Team 1 keystone at (12,2) is the vent-bell. Court host, tag `court_host`: `hadal_court_tollwarden` (12,3), `hadal_court_bell_knight` on the causeway heads at (6,6), (16,6) and (22,5), `hadal_court_vent_priest` (11,11), `hadal_court_pit_thrall` (10,10) and (13,10), `hadal_court_trench_crab` (14,12), `hadal_court_lantern_spitter` (11,4). Warband: Pit Thrall x2, Lurecaller, Pressure Lancer. Wet ground: shallows at (8,9) to (9,10) and (16,13) to (17,14) on the island's edges, plus the events. The vents burn the Overcurrent and heal the Court.
- **Briefing:**
  Entry the twelfth. At the Steps the bell-people from the trench stood among the fallen and would not strike them. They waited for them to dry out, the way you wait out a fever, and they called them the Upper Kin.

  The Kin have followed the Court's road down to the Boiling Floor. The vents scald them and heal the Court in the same steam. There is a bell on the north rim with a vent-flame burning inside it, and to anything raised under the beams it must look like a lamp.

  The Court will not strike first. I have watched them stand with their hands open for a whole turn of the glass. The Kin do not know what an open hand is.
- **Victory:** destroy_keystone team 1 (the vent-bell).
- **Defeat:** unit_lost tag `undersinging`, or turn_limit 14.
- **Events:**
  1. Turn 1: status `stunned` on tag `court_host`, duration 1 (the Court holds its hand). Message from **A Court Tollwarden**: "Upper Kin. The Court does not raise a hand to you. Pass by, and go back up."
  2. Turn 3: terrain `brine_pool` at (13,19), radius 1, duration 4 (the thin place follows them). Message from **The Choir**: "mmmm. a lamp in a bell. a lamp in a bell."
  3. When a unit with tag `court_host` first dies: message from **A Court Tollwarden**: "So. You struck first. The Court will remember it was you." Spawn team 1 `hadal_court_crushing_maw` at (12,13) out of the vents, tag `court_host`.
- **Bonus objective:** Break the vent-bell before turn 10 (turn_limit 10, negated). Pearls: win 50, bonus 25.
- **Victory text:** The bell cracks and the flame inside it goes out, and the Overcurrent lose interest in it at once. The Court does not pursue. The Tollwarden stands on the rim and watches them go, and Wenna, who is close enough to hear, swears the bronze helm is weeping brine.
- **Defeat text:** The Court never strikes first. It does not have to. The Kin cook on the vents, one by one, while the Bell-Knights stand with their hands open and wait, as patiently as they waited at the Steps.
- **Unlocks:** `overcurrent_barrelgaze`, `overcurrent_downward_shark`.

## Mission 6: `oc_brightest_prey` — "Brightest Prey"
- **Map:** `glasswork_reach` (four arms of beam glass meeting at the ruined lighthouse; glowmoss at its heart)
- **Enemy:** `lanternkeepers`
- **Type:** breakthrough / race: go toward the light.
- **Setup:** player `overcurrent_the_undersinging` at (15,26), tag `undersinging`. Team 1 on the ruin, tag `keepers_watch`: `lanternkeepers_keeper_of_the_long_watch` (14,13), `lanternkeepers_beamwright` (12,12) and (17,12), `lanternkeepers_stairkeeper` (14,17) and (15,17), `lanternkeepers_glassgrinder` (11,15), `lanternkeepers_signalman` (18,15). Warband: Oilbearer x2, Wick x2, Lantern Warden, Beaconrunner. Captain Hollis Drenn is present in voice only. Wet ground: razor oyster beds on the south-west arm, around (7,20) to (8,21), and the north-east arm, plus the event pool.
- **Briefing:**
  Entry the fifteenth. I have to write this one as a keeper, not as a witness. They have turned toward the Glasswork Reach, where the Shoal's beam swept for three hundred years and fused the sand into glass. The glass still holds a little of the light, and to them it must look like the floor of heaven.

  Captain Drenn has the beams out on all four arms. My own house stands between the Undersinging and the old lamp-ruin, and I am on the wrong side of the line, with a book instead of a lens.

  The old entries say they come toward the light because it is the only light they have ever had. The old entries do not say what to do about it. I think the keepers who wrote them did not know either.
- **Victory:** reach_tile team 0, tag `undersinging`, tiles (14,14), (15,14), (14,15), (15,15) (the glowmoss heart of the ruin).
- **Defeat:** unit_lost tag `undersinging`, or turn_limit 15.
- **Events:**
  1. Turn 1: message from **Light**: "bright. bright. there. there. THERE."
  2. Turn 3 (enemy turn): message from **Captain Hollis Drenn**: "Beams down every arm. Keep it on the glass, where it can't hide." Status `lk_dazzled` on tag `undersinging`, duration 1.
  3. Turn 6: terrain `brine_pool` at (15,22), radius 1, duration 4 (the sky drips on the south arm). Message from **Keeper Wenna Cray**: "Hold the south beam. No. Let it come. I need to see what it does at the glass."
- **Bonus objective:** Reach the heart before turn 10 (turn_limit 10, negated). Pearls: win 55, bonus 25.
- **Victory text:** The Undersinging coils into the glowmoss at the heart of the ruin and stops. It does not attack the keepers on the stair. It lies in the old lamp-room with every body lit, humming, as close to the light as it can get. Captain Drenn lowers his lens. "It isn't hunting," he says. "It's homesick."
- **Defeat text:** The beams pin the long one on the open glass and it dries there, lit from every side, the brightest thing on the Reach for one long minute. Drenn has the carcass burned. Wenna keeps a single bell-body in a jar, and it hums whenever the Shoal lamp turns.
- **Unlocks:** `overcurrent_lure_mother`, `oc_equip_belly_lantern`.

## Mission 7: `oc_the_hooked_arms` — "The Hooked Arms"
- **Map:** `mother_hull` (the bone-road spine at height 2, wreck ribs arching off it, lamp oil spilled on the decks)
- **Enemy:** `salvage_compact`
- **Type:** siege / escort: Mother Mantle tears the harpoon engines off the ribs.
- **Setup:** player `overcurrent_the_undersinging` at (3,9), tag `undersinging`. Guest on the player's team: `overcurrent_mother_mantle` at (2,11), tag `mother_mantle`. Team 1 engines on the ribs, tag `harpoon_battery`: `salvage_compact_harpoon_engine` at (16,5) and (16,16). Hull militia, tag `hull_militia`: `salvage_compact_quartermaster` (17,10), `salvage_compact_hullbreaker` (14,10), `salvage_compact_powder_monk` (13,9) and (13,12), `salvage_compact_rivet_slinger` (10,5) and (10,16), `salvage_compact_bone_sled_rider` (12,3). Warband: Hull Scrapper x3, Wrecker x2, Tallow-Mender. Wet ground: none on the map; only the event pools and Mother Mantle (allies adjacent to her do not dry). The lamp-oil tiles burn.
- **Briefing:**
  Entry the nineteenth. Something came down on the flats beside Mother Hull last night that was larger than the hulks. A squid, I think, with hooks turning in its suckers and an eye like a door left open. The hull-folk are already calling her Mother Mantle, the way you name a storm so you can curse it.

  The Compact keep two harpoon engines on the ribs, and they have been shooting the fallen all week for the price of the meat. She has come for the engines. She does not seem angry. She seems patient, the way the tide was patient, when there was a tide.

  I am inside the hull with three thousand people and a fat man in three coats who keeps trying to sell me a better seat. There is no water in a dead leviathan. Whatever comes in here will be dying the whole time it eats.
- **Victory:** defeat_unit tag `harpoon_battery` (both engines).
- **Defeat:** unit_lost tag `mother_mantle`, unit_lost tag `undersinging`, or turn_limit 14.
- **Events:**
  1. Turn 1: terrain `brine_pool` at (6,7), radius 1, duration 4, and at (6,15), radius 1, duration 4 (brine runs off Mother Mantle onto the flats). Message from **Dry**: "no water in the bone. none. stay by the big one. stay."
  2. Turn 3: message from **Odo Brask** (from the skull): "Madam, whatever you are, I want it known that the Compact has always been neutral. I can also offer you a very good price on the Concord."
  3. Turn 6 (enemy turn): terrain `lamp_oil` at (10,10), radius 1, duration 3 (the militia fires the spine). Spawn team 1 `salvage_compact_powder_monk` at (19,6) and (19,14), tag `hull_militia`. Message from **Brother Ashmaw**: "Burn it! They're all water and no skin. Burn it bright enough the Rim can see!"
- **Bonus objective:** Mother Mantle ends above half strength (unit_hp_above tag `mother_mantle`, 0.5). Pearls: win 60, bonus 25.
- **Victory text:** Mother Mantle takes the second engine in four arms and pulls, and two hulks that have leaned on each other for a century come apart with a sound like a held breath let go. She does not go further in. Three thousand people listen to her drag herself back out onto the flats, toward the Shoal. Brask, in the skull, asks Wenna if she is selling the page.
- **Defeat text:** The harpoons hold. Mother Mantle dries on the flats beside the hull that named her, hooks still turning, and the Compact cut her for a month. The meat does not rot. Nobody in the Hulks will eat it.
- **Unlocks:** `overcurrent_ribbon_king`, `oc_spell_hunger`.

## Mission 8: `oc_below_the_beam` — "Below the Beam"
- **Map:** `lantern_shoal` (night, rain falling from a sky so thin shapes move in it; the lamp lit; keepers on the tower plateau, the Concord company on the outer ground)
- **Enemy:** `lanternkeepers` (team 1) + `salt_concord` (team 2, hostile to everyone)
- **Type:** finale / breakthrough: reach the glass, and do not let the keeper die.
- **Setup:** player `overcurrent_the_undersinging` at (10,18), tag `undersinging`. Guests on the player's team: `overcurrent_mother_mantle` (9,19), tag `mother_mantle`; `overcurrent_saint_rictus` (12,19), tag `saint_rictus`. Team 1 on the tower plateau, tag `shoal_keepers`: `lanternkeepers_first_flame` (10,8), `lanternkeepers_keeper_of_the_long_watch` (11,8), `lanternkeepers_beamwright` (8,9) and (13,9), `lanternkeepers_stairkeeper` (9,12) and (12,12), `lanternkeepers_lantern_warden` (10,13). `lanternkeepers_keeper_pell_auster` at (11,9), tag `keeper_auster` (her hand on the glass). Team 2, Tamsin Orrel's company on the outer ground, tag `shoal_company`: `salt_concord_stair_warden` (7,16), `salt_concord_brineguard` (5,16) and (6,17), `salt_concord_caustic_lantern` (4,18), `salt_concord_salt_levy` (3,16), `salt_concord_rim_marshal` (16,16), `salt_concord_brineguard` (15,17). Team 1 warband: Signalman, Oilbearer x2, Bellringer, Beaconrunner. Team 2 warband: Salt Levy x2, Brine Slinger x2. Wet ground: none on the map; the rain events make it.
- **Briefing:**
  Entry the last, if I am lucky. The page came back to me today. A bird-girl dropped it on the Shoal stair and flew off without a word, and I have bound my loose leaves into it, so it is whole again.

  Everything that fell is coming here. The Shoal lamp is the brightest light in the world, and the sky above it is so thin I can see shapes moving in it. Keeper Auster has her hand on the glass, my house is on the stair, and the Concord company is on the wall. None of us has ever faced anything that wanted the lamp more than we do.

  I have read the whole page now, every keeper's hand back to the Oaths. There is one line at the bottom in the oldest ink, with a space under it for someone to write whether it was true. I think tonight I find out.
- **Victory:** reach_tile team 0, tag `undersinging`, tiles (10,10), (11,10), (10,11), (11,11) (the glass).
- **Defeat:** unit_lost tag `undersinging`; unit_lost tag `keeper_auster` (the lamp goes out with her, and the sea comes down on everything, the Overcurrent included); or turn_limit 16.
- **Events:**
  1. Turn 1: terrain `brine_pool` at (10,16), radius 2, duration 4 (the rain pools at the foot of the Shoal). Message from **The Choir**: "mmmmmmmm. the brightest. the brightest. the brightest."
  2. Turn 4 (enemy turn): message from **Lensmaster Oriel Venn**: "Keepers don't speak. I'm speaking. Every lens on the stair, now. It does not touch the glass." Status `lk_dazzled` on tag `undersinging`, duration 1.
  3. Turn 7: the sky breaks over the Shoal. Spawn team 0 `overcurrent_the_thinning` at (10,15), tag `the_thinning` (its shadow lands first). Terrain `brine_pool` at (4,10), radius 2, duration 5, and at (16,10), radius 2, duration 5. Message from **Keeper Pell Auster**: "Shutters open. All of them. Let it look. Nobody touches the glass but me."
- **Bonus objective:** Mother Mantle survives (unit_lost tag `mother_mantle`, negated); Saint Rictus survives (unit_lost tag `saint_rictus`, negated). Pearls: win 80, bonus 25 each.
- **Victory text:** The Undersinging climbs the tower and lays its hundred bodies against the glass, and does not break it. It hums at the lamp's own pitch, and the lamp hums back. Inside, Keeper Auster keeps her hand where it is. Above, the floor of the sky knits shut; below, a Concord commander looks up and sees the sea for the first time, and the sea looks back. By morning everything that fell lies grey on the salt around the Shoal, dried in rings, every one of them facing the lamp. The locked page's last line, in the oldest ink, reads: "What feeds below the beam does not want the lamp out. It has never had another sun. Keep it lit for them too." Under it, in fresh ink, Wenna Cray writes one word: "True."
- **Defeat text:** The lamp gutters. For one breath the sky is open all the way up, and the Undersinging sees past the light the whole dark weight of its own sea, coming down after it. Then there is no above or below, only water, and the hum goes on under it for a while.
- **Unlocks:** `overcurrent_mother_mantle`, `overcurrent_saint_rictus`, `overcurrent_the_thinning` (per the outline; this is the one mission that unlocks three).

## Campaign arc and secret
Missions 1 to 3 teach the Overcurrent's whole problem: they fall, they burst, they dry, and everything on the Ebb either eats them, sells them or seals the wet away from them. Missions 4 and 5 show how the floor's peoples answer them (the Tide splinter worships, Dunnock refuses, the Court will not strike first and is struck anyway), and missions 6 to 8 turn the hunt toward the light. The secret is the locked page's: the Overcurrent are the life of the lifted sea, lit for three hundred years only from below, and the lamps are their sun as well as the hand that holds them up. They never wanted a lamp out. They wanted to be near one. The campaign ends with the swarm dead on the salt around the Shoal, the lamp still burning, and the line under the Vigil Oaths finally answered: "We keep it for what is above the roof" means them too.

Unlock count note: missions 1 to 7 unlock 2 relics each and mission 8 unlocks the 3 the outline names, so 17 distinct unlocks. Never awarded: `oc_spell_rain_of_fish`, `oc_spell_ink_bloom`, `oc_spell_undertow_from_above`, `oc_spell_the_sky_opens`, `oc_equip_lure_stalk`, `oc_equip_drowned_heart`.
