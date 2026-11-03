# Campaign 2: "The Weeping Shelf"

Campaign id: the_weeping_shelf · Faction: returning_tide · Mission prefix: rt_

Faction: Returning Tide (`returning_tide`). 8 missions. Escalation: hold, ambush, escort, bargain, take-and-hold, test-and-withdraw, breakthrough, finale. A prequel that runs into Campaign 1: it starts before Tamsin Orrel reaches the Shoal and ends between Concord missions 7 and 8, when Deeplight goes dark. Briefings are leaves from Sister Maren Ketch's tally, the private ledger in which she counts what she wrings. Coordinates are (x, y) = (column, row) on the map's tile grid. Setting canon: `EBB_world_bible.md`, `bible/history_and_gazetteer.md`, `campaign_1.md`.

## Starting roster
- `returning_tide_maren_ketch` (hero, lead; pre-placed every mission with tag `maren_ketch`)
- `returning_tide_penitent` ×3
- `returning_tide_drowned` ×2
- `rt_spell_brine_lash`
- `rt_equip_oilskin_cloak`

## Recurring characters

**Sister Maren Ketch** (player). Senior wringer of the Weeping Shelf, forty-odd, big-handed, soft-spoken, soaked to the elbow at all times. She has drawn the water out of more living things than she will admit to, and believes in every one of them. This year she has started counting. She starts out keeping the tally as a witness for the faithful. She ends it knowing exactly what the sea above is, because she is the one who opened the door.

**Prophet Imre Dunnock, "the Wet Saint".** The same man Tamsin will meet across the fog: former Concord tax clerk, Rim-born, gentle, terrifying with a column of figures. To his own people he is warm, funny and always right. He sends Maren to do every hard thing and thanks her properly each time. He knows the sea will not be merciful, and Maren slowly works out that he knows.

**Captain Oswin Brack.** A Hulk captain who went down with the hulk *Patience* on the night of the Long Ebb and got up again in the year of the First Wringing. Twenty-two hands under him, and he will say every name if you let him. Loud, bluff, polite to the dead. The Tide has promised him the sea will bring his crew home, and he has decided to believe it.

**Watch-Lieutenant Ansel Treave.** Concord Rainwatch officer, the man whose job is to watch for clouds that do not exist. Neat, tired, scrupulously polite in writing. He writes the Tide letters before he attacks them. He is not cruel; he is thorough, which on the Shelf is worse.

**Tobin Seck.** Sixteen, a Penitent from the Rim's poorest ward, who walked to the Shelf barefoot because someone told him the rain was free. Wants to be first into everything. Maren did not mean to become fond of him.

**Hesk Varrow** (Compact broker, one mission) and **Odo Brask** (Compact fixer, one line) cross over from Campaign 1, as does **Keeper Pell Auster** (one line, heard from the other side of the wall) and **Herald Vhaal** (one question).

---

## Mission 1: `rt_rain_on_the_faithful` — "Rain on the Faithful"
- **Map:** `weeping_shelf` (rain active; the shrine is our Beacon at the south end; the chasm splits the shelf at rows 10 to 11, crossed by the bone-road causeway at x 6 to 8 and the long east route at x 18 to 21)
- **Enemy:** `salt_concord` (the Rainwatch)
- **Type:** hold / survive.
- **Setup:** Player: Maren (4,16). Three pilgrims, `returning_tide_penitent` tag `shrine_pilgrim`, standing in and beside the shrine pool at (8,18), (7,17), (9,18). Enemy pre-placed: Brineguard at (3,5) and (5,5), Salt Levy at (7,7) and (9,6), Surveyor at (4,6). Enemy warband: Brineguard ×2, Salt Levy ×3, Brine Slinger, Saltwright, Surveyor.
- **Briefing:**
  Tally of Sister Maren Ketch, senior wringer, first leaf. Wrung this season: nine. Six were dying already and asked; two were Concord deserters who did not ask but did not argue; one was a goat, and I am not proud of the goat. The Prophet once kept the Concord's ledgers, and he says a number written down is the only honest witness left on the Ebb.

  The Rainwatch are coming up the north ledge to clear the shrine. Watch-Lieutenant Treave has sent a letter, beautifully spelled, informing us that the rain is a public nuisance and the pool a hazard to health. They mean to salt the pool and pull down the hut Ysolde Marrow built under the first drop.

  We do not need to win. We need to still be standing in the rain when they run out of daylight. The pilgrims at the pool will not move, and I will not ask them to.
- **Victory:** survive 8 turns.
- **Defeat:** destroy_keystone team 0 (the shrine pool), or unit_lost tag `maren_ketch`.
- **Events:**
  1. Turn 1: message from **Watch-Lieutenant Ansel Treave** (speaking-trumpet, across the chasm): "By order of the Marshals' Office, this ledge is closed. Disperse, and take your dead with you. Both kinds."
  2. Turn 3 (Concord turn): reinforcement, two Causeway Outriders (`salt_concord_causeway_outrider`) at the east crossing, (18,10) and (21,11). Message from **Imre Dunnock** (from the hut): "Let them come the long way round, Sister. The long way is wet."
  3. Turn 5 (our turn): the rain thickens on the causeway: terrain `brine_pool` at (7,10), radius 2, 4 turns. Message from **Maren Ketch**: "Hear that? It comes down harder when they shout. So shout back."
- **Bonus objective:** No pilgrim dies (unit_lost tag `shrine_pilgrim`, negated). +20 Pearls. Second: Maren above half strength (unit_hp_above `maren_ketch` 0.5). +10 Pearls. Win: 40 Pearls.
- **Victory text:** The Rainwatch fall back across the causeway with their salt sacks still full. Tobin Seck, the youngest pilgrim, stands in the pool with his mouth open and his eyes shut, laughing. That night Maren writes the day's number in the tally and finds she has written it twice.
- **Defeat text:** Salt hisses into the shrine pool and, for one terrible afternoon, the rain stops. The faithful kneel in the dry and weep instead. Treave's men take down Marrow's hut plank by plank, and number every plank.
- **Unlocks:** `returning_tide_wringer`, `returning_tide_tear_slinger`.

## Mission 2: `rt_the_broken_toll` — "The Broken Toll"
- **Map:** `greywater_stair` (dawn; we hold the top landing at the Rim, the Concord toll-house is at the foot)
- **Enemy:** `salt_concord` (salt convoy and escort)
- **Type:** ambush / interdiction.
- **Setup:** Player: Maren (11,3). Enemy pre-placed: three salt wagons, `salt_concord_salt_levy` tag `salt_wagon`, at (8,16), (10,16), (12,16). Escort: Stair-Warden (10,15), Brineguard (8,15) and (12,15), Tollkeeper tag `toll_sergeant` (10,17), Surveyor (11,18). Enemy warband: Brineguard ×2, Salt Levy ×2, Brine Slinger ×2, Stair-Warden.
- **Briefing:**
  Tally, second leaf. Wrung since the shrine: four, all Concord, all at night. I broke the toll on this Stair once before, in my novice year, and the Concord made some girl a commander for cleaning up after us. I have wondered since what became of her.

  Three salt wagons climb at dawn from the toll-house at the foot. The faithful came down the cliff on ropes in the dark and hold the top landing, which the Concord road manual does not cover, because nobody who wrote it ever wanted to come down a cliff. No wagon reaches the top: if they cannot get salt up, they cannot pay for spears to come down.

  Odo Brask sold us the convoy schedule for a barrel of kelp wine. I would not trust him with the barrel.
- **Victory:** defeat_unit tag `salt_wagon` (all three wagons destroyed).
- **Defeat:** reach_tile team 1, tag `salt_wagon`, tiles (4,4), (5,4), (6,4), (15,4), (16,4), (17,4) (a wagon tops the last stair); or unit_lost tag `maren_ketch`; or turn_limit 14.
- **Events:**
  1. Turn 1: message from **Odo Brask** (on a bone-sled at the foot, waving): "Three wagons, upper road, dawn. You never heard it from me. If anyone asks, you got it from the Gyre. Everyone believes the Gyre."
  2. Turn 3 (Concord turn): reinforcement, two Causeway Outriders at the side gaps, (1,11) and (20,11). Message from **Convoy Sergeant**: "Outriders up the side gaps! Keep the wagons off the middle stair!"
  3. Turn 5 (our turn): seep-water floods the central gap: terrain `brine_pool` at (10,11), radius 1, 4 turns; spawn two `returning_tide_drowned` (team 0) at (9,8) and (12,8). Message from **Maren Ketch**: "The cliff is weeping again. No engineer ever found where it comes from. I have a guess who's crying."
- **Bonus objective:** Kill the toll sergeant (defeat_unit tag `toll_sergeant`). +20 Pearls. Win: 40 Pearls.
- **Victory text:** The last wagon tips at the third switchback and pours a year of salt down the cliff in a long white fan. The Concord will call this the second Broken Toll, and promote someone. Maren counts the drivers and stops at seven, because the eighth is still moving and she has not decided.
- **Defeat text:** A wagon crests the top landing and the toll-bell rings the whole length of the Stair. The faithful climb back up their ropes in the dark. One rope is cut halfway, and nobody sees by whom.
- **Unlocks:** `returning_tide_tideskulker`, `returning_tide_rainsayer`.

## Mission 3: `rt_bracks_crew` — "Brack's Crew"
- **Map:** `kelpmire` (low mist; the hulk *Patience* is the wreck at (3,6), north-west, close under the Reef's growth)
- **Enemy:** `reef_ascendant`
- **Type:** escort / rescue.
- **Setup:** Player: Maren (10,21); guest Captain Oswin Brack, `returning_tide_oswin_brack` tag `captain_brack`, at (12,22). Enemy pre-placed: Spireguard (4,4) guarding the wreck, Brainstalk (9,5), Sting Anemone (5,7), Polyp Drone ×4 at (7,8), (8,8), (11,9), (12,10). Enemy warband: Polyp Drone ×4, Fanblade ×2, Spitter Polyp ×2, Reef Tender, Broodspire.
- **Briefing:**
  Tally, third leaf. The Prophet has given me a captain. Oswin Brack went down with the hulk *Patience* on the night of the Long Ebb and has refused to stay down since, and he has been asking for his crew for a hundred and ninety years with the patience of a man who named his ship after it.

  The *Patience* lies in the Kelpmire, where the mud keeps her dead wet enough to wake. Twenty-two hands, Brack says, and he will say every name if you let him. This year the Reef has grown into the mire, and the Reef eats whatever lies still.

  We go in, we wake the crew, and Brack walks to his ship to call the rest. I have promised him all twenty-two. I know how many I can wring awake in a day, and it is not twenty-two.
- **Victory:** reach_tile team 0, tag `captain_brack`, tiles (2,5), (3,5), (2,6), (3,6), (4,6) (Brack stands on the *Patience*).
- **Defeat:** unit_lost tag `captain_brack`, or unit_lost tag `maren_ketch`, or turn_limit 14.
- **Events:**
  1. Turn 2 (our turn): two of the crew rise from the west kelp: spawn `returning_tide_drowned` (team 0, tag `brack_crew`) at (1,10) and (2,11). Message from **Captain Oswin Brack**: "Haddow! Jory Fenn! Up, you idle sods. Three hundred years is not shore leave."
  2. Turn 4 (Reef turn): reinforcement, two Fanblades (`reef_ascendant_fanblade`) at (14,12) and (16,11). Message from **The Reef** (a pressure behind the eyes, not a sound): "still things are ours. still things become us. why do yours not stay still."
  3. Turn 6 (our turn): two more of the crew rise from the east kelp: spawn `returning_tide_drowned` (team 0, tag `brack_crew`) at (15,13) and (16,14). Message from **Maren Ketch**: "Four, Captain. That's four. Count them with me."
- **Bonus objective:** Lose none of Brack's crew (unit_lost tag `brack_crew`, negated). +25 Pearls. Win: 45 Pearls.
- **Victory text:** Brack reaches the *Patience* and stands at her rail, which is now at ankle height, and calls the roll. Four answer. He calls it again, all twenty-two names, slower, and waits a long time after each. "The sea will bring the rest," he says. "The Prophet promised." Maren writes four in the tally and, underneath, small: eighteen.
- **Defeat text:** The Reef closes over the wreck like a hand. Six Penitents drag Brack out of the mire, still calling names. The coral holds the rest of his crew very gently, and does not let go.
- **Unlocks:** `returning_tide_shroud_mender`, `rt_spell_drowned_rise`.

## Mission 4: `rt_paper_swords` — "Paper Swords"
- **Map:** `the_kettle` (market day, noon; the deal is struck in the centre bowl, the way out is the south gate on the bone road)
- **Enemy:** `salvage_compact` (Kettle militia)
- **Type:** bargain gone wrong / escort.
- **Setup:** Player: Maren (11,12). Two hired sleds carrying the crates, `salvage_compact_bone_sled_rider` on team 0, tag `paper_sled`, at (9,11) and (12,11). Enemy pre-placed: Hesk Varrow, `salvage_compact_quartermaster` tag `broker_varrow`, at (11,8); Hull Scrapper at (8,9) and (13,9); Rivet-Slinger at (10,6). Enemy warband: Hull Scrapper ×2, Wrecker ×2, Rivet-Slinger, Snare-Tinker, Powder-Monk, Bone-Sled Rider.
- **Briefing:**
  Tally, fourth leaf. We are buying swords. A broker in the Kettle named Hesk Varrow sells us Concord arms with Concord requisitions attached, seals and all, so that when the Concord finds its own spears in our hands it will spend a season arresting its own clerks. The Prophet laughed when he read the receipts and said he used to write receipts like that, only honest ones.

  The Kettle has a code: no blades drawn in the aisles on market day. Varrow wants the coin in the centre bowl at noon, and two hired bone-sleds will carry the crates out by the south gate. I have been told to trust the code, and I have also been told that Varrow once sold the same powder cart to both ends of a feud.

  Get the sleds to the south gate. Do not kill the broker. The faithful have nobody else who can spell "requisition".
- **Victory:** reach_tile team 0, tag `paper_sled`, tiles (10,17), (10,18), (10,19) (a sled reaches the south gate).
- **Defeat:** defeat_unit tag `paper_sled` (both sleds destroyed), or unit_lost tag `maren_ketch`, or turn_limit 12.
- **Events:**
  1. Turn 1: message from **Hesk Varrow**: "Sixty spears, forty helms, every seal genuine. The Concord isn't, but the seals are. A pleasure, Sister."
  2. Turn 2 (Compact turn): the double-cross. Reinforcement, two Wreckers (`salvage_compact_wrecker`) at (3,9) and (18,9). Message from **Kettle Militia Captain**: "Contraband seizure, under the market code! Drop the crates and nobody gets harpooned. Probably."
  3. Turn 5 (Compact turn): reinforcement, two Bone-Sled Riders at (6,18) and (14,18) to close the gate. Message from **Hesk Varrow**: "Nothing personal. I sold the crates twice. It's a very good crate."
- **Bonus objective:** Varrow lives (unit_lost tag `broker_varrow`, negated). +20 Pearls. Win: 40 Pearls.
- **Victory text:** The sleds clatter out through the south gate with half the Kettle chasing them and the other half taking bets. Varrow is already gone, paid twice, whistling. Someone will kill him for this eventually; Maren hopes it is someone with a receipt.
- **Defeat text:** The militia take the crates, the coin and Maren's good boots. Varrow sells her the boots back an hour later, at a very reasonable price.
- **Unlocks:** `returning_tide_anchor_bearer`, `rt_equip_drowners_gaff`.

## Mission 5: `rt_wringing_the_wells` — "Wringing the Wells"
- **Map:** `tide_steps` (dry season; four Concord tide wells at (4,9), (17,11), (6,16) and (19,18); the relief column comes down from the north rim)
- **Enemy:** `salt_concord` (well wardens, then the Rainwatch relief)
- **Type:** take-and-hold / race against relief.
- **Setup:** Player: Maren (12,23). Enemy pre-placed: four wardens tagged `well_warden`, each standing on a well: Stair-Warden (4,9), Stair-Warden (17,11), Brineguard (6,16), Brineguard (19,18). Also Saltwright (11,8), Brine Slinger (14,9), Surveyor (13,4). Enemy warband: Brineguard ×2, Salt Levy ×2, Brine Slinger, Brine Chirurgeon, Tollkeeper.
- **Briefing:**
  Tally, fifth leaf. The Prophet has audited the wells. Four Concord tide wells on the Steps draw more than the basin gives back, he says, and for ninety years the difference has been written off as evaporation. He wants them wrung dry and the water poured into the basin where it belongs, as a correction.

  Each well has a warden standing in the damp like a man guarding a purse. Kill the wardens and the wells are ours to empty. A Rainwatch relief column is coming down from the north rim, and once it reaches the basin the Steps are closed to us for good.

  I have never wrung a man standing on water before. The Prophet says it is easier. I think he is guessing, and he never guesses.
- **Victory:** defeat_unit tag `well_warden` (all four wardens).
- **Defeat:** unit_lost tag `maren_ketch`, or destroy_keystone team 0, or turn_limit 12 (the relief column seals the basin).
- **Events:**
  1. Turn 1: message from **Concord Well-Sergeant**: "Tide wells are Concord property under the Seventh Water Ordinance. Drink, and you'll be billed. Die, and your family will be billed."
  2. When the first unit tagged `well_warden` dies: message from **Maren Ketch**: "One. I'm counting them now. I don't remember deciding to."
  3. Turn 6 (Concord turn): the relief vanguard arrives: spawn `salt_concord_rim_marshal` tag `lt_treave` at (11,4), and two Causeway Outriders at (10,4) and (12,4). Message from **Watch-Lieutenant Ansel Treave**: "Sister Ketch. I remember you from the shrine. I have brought more salt."
- **Bonus objective:** Kill Watch-Lieutenant Treave (defeat_unit tag `lt_treave`). +25 Pearls. Win: 45 Pearls.
- **Victory text:** The fourth warden goes down in the shallows and the Penitents carry the water to the basin in their hands, in their hats, in their mouths. It takes until dark. The basin does not rise by so much as a finger, and Maren notices, and writes that down too.
- **Defeat text:** The relief column fills the Steps with salt and Rainwatch blue. The faithful withdraw across the terraces, leaving the wells full and the basin as empty as it has been for three hundred years.
- **Unlocks:** `returning_tide_undertow_singer`, `rt_spell_wringing_rite`.

## Mission 6: `rt_lamp_and_wall_other_side` — "Lamp and Wall, the Other Side"
- **Map:** `lantern_shoal` (daylight, lamp lit; the Concord garrison holds the walled lamp-stone plateau in the centre; our forward shrine is the south Beacon)
- **Enemy:** `salt_concord` (Tamsin Orrel's newly arrived company; she is not on the field)
- **Type:** probing assault / survive and withdraw. This is Concord mission 1, `lamp_and_wall`, seen from the column.
- **Setup:** Player: Maren (10,17); Tobin Seck, `returning_tide_penitent` tag `tobin_seck`, at (9,17). Enemy pre-placed on the plateau: Brineguard tag `shoal_sergeant` (10,14), Brineguard (8,14) and (12,14), Stair-Warden (6,12), Saltwright (11,11), Surveyor (9,9) and (12,9), Brine Slinger (10,7). Enemy warband: Brineguard ×2, Salt Levy ×2, Surveyor, Stair-Warden.
- **Briefing:**
  Tally, sixth leaf. The Prophet sends us to Lantern Shoal and has told us plainly that we will not take it. A new Concord company is digging in around the old wall, under a commander who measures everything twice; the scouts say she keeps a night lamp in her tent like a Rim child. We are to walk up to the wall, test it, and come home.

  "Test the wall," he said, and then said it again, the way he repeats a number he does not like. I asked what we are testing for. He said: whether the light flinches when the faithful come near, and how long the soldiers stand before they look up at it for help.

  I lead the column in, wet and silent, from the east road. Hold for eight turns, keep the shrine-cart standing, and bring home as many as the wall allows. Tobin Seck asked to walk at the front, and I said yes, and I have written his name in the tally before the battle, which I have never done.
- **Victory:** survive 8 turns.
- **Defeat:** unit_lost tag `maren_ketch`, or destroy_keystone team 0 (the forward shrine).
- **Events:**
  1. Turn 1: message from **Keeper Pell Auster** (from the tower, to the garrison; the wind carries it to the column): "Don't touch the lamp. Don't let them near the lamp. That's all."
  2. Turn 5 (our turn): a pool opens behind the garrison: terrain `brine_pool` at (10,4), radius 1, 3 turns; spawn `returning_tide_wringer` (team 0) at (10,4). Message from **Imre Dunnock** (through a Choirmaster's chant): "Up out of the pool, Brother, behind them. Now watch which way the soldiers turn. Not at you. At the lamp."
  3. Turn 7: message from **Imre Dunnock**: "Enough. Sister, bring them home. The wall holds, the lamp holds, and now I know which one to ask."
- **Bonus objective:** Tobin comes home (unit_lost tag `tobin_seck`, negated). +20 Pearls. Second: kill the wall sergeant (defeat_unit tag `shoal_sergeant`). +10 Pearls. Win: 40 Pearls.
- **Victory text:** The column breaks and flows back into the haze as ordered, leaving wet footprints that dry too fast. Looking back, Maren sees an old woman walk out of the tower and hears her say, "Good. They'll be back." Dunnock does not look back at all. He is already looking toward the Brinks, where a fallen lamp burns at the bottom of a trench.
- **Defeat text:** The wall does not break, and neither does the column, until it does. Maren carries Tobin out across the salt on her back. The tally that night has a column of names and no total, because she cannot make herself add them up.
- **Unlocks:** `returning_tide_choirmaster`, `rt_equip_second_tide_shroud`.

## Mission 7: `rt_the_glass_road` — "The Glass Road"
- **Map:** `glasswork_reach` (clear night, every beam lane lit; the way to the Brinks is off the north edge past the keepers' Beacon)
- **Enemy:** `lanternkeepers`
- **Type:** breakthrough.
- **Setup:** Player: Maren (15,25). Enemy pre-placed: Keeper of the Long Watch tag `glass_warden` at (13,4); Beamwright at (14,8) and (15,21); Stairkeeper (14,19); Signalman (12,14); Lantern Warden (17,13); Wick (21,14). Enemy warband: Wick ×2, Oilbearer ×2, Beamwright, Glassgrinder, Lantern Warden, Bellringer.
- **Briefing:**
  Tally, seventh leaf. The Prophet has told us at last. The Shoal is too strong and too watched, but a lamp fell into a trench at Deeplight fifty years ago and burns still, and the Court that built a city round it only stares at it. Put that one out, he says, and the sea will hear us knock.

  Between us and the Brinks lies the Glasswork Reach, where the Shoal's beam swept so long the sand turned to glass. The Lanternkeepers hold it. They have hunted the faithful for three centuries without once explaining why, and their beams run down the glass lanes like a ruler across a page.

  We cross the glass and come out the north side, or we break their Beacon and walk out over it. Keep off the bright lanes when you can. Wet them when you cannot.
- **Victory:** reach_tile team 0, tag `maren_ketch`, tiles (12,0), (13,0), (14,0), (15,0), (16,0) (Maren steps off the north edge onto the Brinks road); or destroy_keystone team 1.
- **Defeat:** unit_lost tag `maren_ketch`, or destroy_keystone team 0, or turn_limit 16.
- **Events:**
  1. Turn 1: message from **Keeper of the Long Watch**: "Tide on the reach. Beams down every lane. Do not speak to them. They listen too well."
  2. Turn 3 (our turn): Rainsayers wet the south lane: terrain `brine_pool` at (15,22), radius 2, 4 turns. Message from **Tideskulker scout**: "A big bird went over low before dawn, Sister, north, with a rider on it. The keepers have been shouting at the sky ever since."
  3. Turn 5 (keepers' turn): reinforcement, two Lamplit Sailors (`lanternkeepers_lamplit_sailor`) step out of the beam on the lamp-stone at (11,13) and (18,13). Message from **Maren Ketch**: "Those are drowned men. Those are ours. Why are they standing in the light?"
- **Bonus objective:** Kill the Keeper of the Long Watch (defeat_unit tag `glass_warden`). +20 Pearls. Win: 45 Pearls.
- **Victory text:** Maren comes off the north end of the glass with her shadow running ahead of her, long and thin, thrown by a beam that has stopped sweeping and is pointing at her back. Below lie the Brinks, and the trench, and very far down, a cold white light. She does not write a number in the tally that night. She writes a question, and crosses it out.
- **Defeat text:** The beams find every wet foot on the reach. The faithful retreat south over glass still warm to the touch, and the keepers do not follow, and do not say a word.
- **Unlocks:** `returning_tide_bloat_drowned`, `rt_spell_the_sea_remembers`.

## Mission 8: `rt_the_light_goes_out_at_deeplight` — "The Light Goes Out at Deeplight"
- **Map:** `trench_deeplight` (grey brine already falling in a column over the trench; the fallen lamp is the keepers' Beacon at the north end of the causeways)
- **Enemy:** `lanternkeepers` (team 1, the tenders Auster left at the lamp) and `hadal_court` (team 2, hostile to everyone)
- **Type:** siege / finale. Takes place between Concord missions 7 and 8.
- **Setup:** Player: Maren (10,16); guests Prophet Imre Dunnock, `returning_tide_imre_dunnock` tag `prophet_dunnock`, at (11,17), and Captain Oswin Brack, `returning_tide_oswin_brack` tag `captain_brack`, at (9,17). Team 1 pre-placed: Keeper Ilse Tarrow, `lanternkeepers_keeper_of_the_long_watch` tag `deeplight_tender`, at (11,2); Stairkeeper at (10,5) and (11,5); Beamwright (8,4); Lantern Warden (12,3); Signalman (14,2). Team 1 warband: Lamplit Sailor ×2, Oilbearer ×2, Beamwright, Lantern Warden, Glassgrinder. Team 2 pre-placed on the side islets: Bell-Knight (3,10), Lurecaller (2,11), Bell-Knight (18,10), Lantern Spitter (19,11); no warband.
- **Briefing:**
  Tally, last leaf. Three days ago the old keeper from the Shoal came down to Deeplight with Concord soldiers, put her hand on the fallen lamp and went home, and since then a column of grey brine has been falling out of a clear sky over the trench. The Prophet says that is the sea leaning on the door. He says one more push.

  The lamp hangs in the Court's city at the far end of the causeways. The keepers she left behind are tending it, and the Court stand round it in their bells, watching, and will thank nobody. Dunnock walks with us, and Captain Brack, who has been promised his eighteen.

  Reach the lamp and put it out. I have done every terrible thing I was asked to do and counted every one, and the numbers have stopped adding up, the way the Prophet's did once. This is the last line on the list, and after it the sea will tell me whether I was right.
- **Victory:** destroy_keystone team 1 (the fallen lamp goes out).
- **Defeat:** unit_lost tag `maren_ketch`, or unit_lost tag `prophet_dunnock`, or destroy_keystone team 0, or turn_limit 18.
- **Events:**
  1. Turn 2 (Court turn): a Crushing Maw (`hadal_court_crushing_maw`, team 2) heaves up onto the centre islet at (10,10). Message from **Herald Vhaal** (from behind the brine curtain): "Small wet ones. You walk into my city to put out its sun. First, answer me one question. Who lifted the sea?"
  2. Turn 6 (keepers' turn): reinforcement, two Lamplit Sailors on the centre bridge at (10,7) and (11,8). Message from **Keeper Ilse Tarrow**: "Don't. You don't know what it's holding. Sister, you of all of them have tasted the rain. Think."
  3. Turn 10 (our turn): the column of brine widens: terrain `brine_pool` at (10,10), radius 2, 6 turns. Message from **Captain Oswin Brack**: "Hear that, Sister? That's the sea on the roof. My lads are up there. Open the door."
- **Bonus objective:** Brack lives (unit_lost tag `captain_brack`, negated). +25 Pearls. Second: Maren above half strength (unit_hp_above `maren_ketch` 0.5). +15 Pearls. Win: 60 Pearls.
- **Victory text:** The lamp goes out the way a held breath goes out, and for a moment nothing happens at all, and the Court in their bells turn their great heads upward together. Then the rain starts: not the drizzle of the Shelf but the sea, coming down in ropes. Maren opens her mouth to it as she has every day of her life, and it tastes of salt and cold and enormous distance, and she understands that it is not mercy and not judgement, only weight, and that it will not stop for anyone. Beside her, Dunnock is weeping. He knew.
- **Defeat text:** The keepers hold the glass and the lamp burns on, a cold white sun below the world. The faithful retreat over the causeways under a rain that thins, and thins, and stops. Dunnock says nothing on the long walk home, and Maren is almost grateful.
- **Unlocks:** `returning_tide_imre_dunnock`, `returning_tide_oswin_brack`.

## Campaign arc and secret
Missions 1 to 3 teach the Tide on its own ground: holding wet terrain, ambushing on the Concord's roads, and waking the Drowned, while Maren's tally starts as a witness for the faithful. Missions 4 to 6 cross Campaign 1 directly (Brask's schedule and the girl promoted after the Broken Toll, Varrow and his forged receipts before Tamsin finds them, and the first assault on the Shoal seen from the column) and show that Dunnock is not trying to take the Shoal but measuring it, and that the numbers in Maren's tally no longer balance. Missions 7 and 8 turn the faith into its act: the keepers' glass, then the fallen lamp at Deeplight, put out by Maren's hand in the gap between Auster's visit and Tamsin's last stand. The Tide were right about where the sea went and wrong about what it would be. The rain that falls in the Concord's mission 8 is the rain Maren starts, and the sky it thins is the one the Overcurrent will fall through. The campaign ends with the last line of her tally, written in the rain with the ink running: "Wrung: everyone."

Unawarded Tide relics (earned elsewhere or by Pearls): `returning_tide_tide_prophet`, `rt_spell_wet_blessing`, `rt_spell_pool_of_the_faithful`, `rt_spell_hymn_of_the_deep`, `rt_spell_tithe_of_water`, `rt_equip_knotted_cord`, `rt_equip_barnacle_mail`, `rt_equip_lungful_of_sea`.
