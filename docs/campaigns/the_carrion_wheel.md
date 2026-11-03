# Campaign 7: "The Carrion Wheel"

Campaign id: the_carrion_wheel · Faction: gyre · Mission prefix: gy_

Faction: The Gyre (`gyre`). 8 missions. Escalation: nest defence, aerial escort, carcass race, heist, the famous robbery, retreat, rescue, last stand. Set in 311 AE alongside Campaign 1. Relics are named by exact id. Pearl rewards follow the bible (win, speed, losses, bonus). All times in turns. Setting canon: `EBB_world_bible.md`, `bible/history_and_gazetteer.md`.

Note on the finale: the outline gives mission 8 three unlocks (Oskeline, Torr Ashby, Mother of the Wheel). The brief allows exactly two per mission, so Captain Torr Ashby unlocks in mission 7, the mission where he finally fights for no pay. Mission 8 unlocks Oskeline and Mother of the Wheel.

## Starting roster
- `gyre_wren_halloway` (lead hero)
- `gyre_roost_runner`, `gyre_roost_runner`
- `gyre_salt_crow`, `gyre_salt_crow`
- `gyre_gullwife`
- `gyre_roostwarden`
- `gy_spell_dive_signal` (spell)
- `gy_equip_beak_mask` (equipment)

## Recurring characters

**Wren Halloway, the Rimfall Thief** (player). Nineteen, roost-born on the Gull Stacks, never once allowed onto the Greywater Stair. Rides a red-throated frigatebird called Pocket. Taught herself to read from Concord maps she was paid to carry and kept a copy of. Keeps a tally of every score in a stolen Concord ledger, in her own spelling. She wants one theft so big the whole Rim has to say her name. She gets it, and it is the wrong kind of famous.

**Roost-Mother Oskeline, Keeper of the High Nests.** Ancient, earthbound, louder than the birds. Has raised every great bird on the Stacks and calls them by the crack of her knees. Thinks Wren is an idiot, and would set the Rim on fire for her. Cannot read and says this is why she still sleeps at night.

**Captain Torr Ashby, of the Black Wheel.** A mercenary on a bald vulture the size of a cart, who follows armies and sells the battles their own cleanup. Cheerful, well fed, honest in the way only a man with no loyalties can be. He wants every fight to last a little longer. He meets the one fight there is nothing left after.

**Odo Brask, Compact fixer.** The same three coats and the same smile as in Campaign 1. Owns a strongbox that holds sixty years of the Compact's dealings with the Lanternkeepers, mostly failed. Robbed by Wren in the middle of market day, and more upset about the ledger than the money.

**Keeper Sabine Lusk.** The road-keeper of the Glasswork Reach, who walks the glass between lamps carrying the master of the Vigil Book's one locked page. Smoked spectacles, a soft voice, polite to birds. She has paid Gyre riders to carry letters for twenty years and never told one of them what was in them. Wren carried her letters as a child.

**Herald Vhaal, the Third Bell.** Hadal Court envoy, as in Campaign 1. She hears a thief on the Ebb has read something no surface-dweller is meant to read, and comes up out of the kelp to ask it her one question.

---

## Mission 1: `gy_the_cliff_shoot` — "The Cliff Shoot"
- **Map:** `gull_stacks` (dawn, nesting season, chicks still on the high perches)
- **Enemy:** `salt_concord`
- **Type:** skirmish / tutorial: protect the nests and break the shooters' camp.
- **Setup:** Wren (`gyre_wren_halloway`, tag `wren_halloway`) at (14,22). Three nestlings (`gyre_salt_crow`, team 0, tag `nestling`) on the perches with no road: north-west plateau (3,7), east oyster perch (23,12), west calcite perch (4,13). Concord shooters (Surveyors, Brine Slingers, Salt Levies) deploy around their camp on the north stack.
- **Briefing:**
  Wren Halloway's tally, Concord ledger, page one. The Concord has put a bounty on birds again: a shilling a beak, two for the big ones. Their shooters came down the north stack in the night with long guns and a tent. Oskeline says they have shot eleven gulls and a crow that was not even ours.

  Three of the chicks are still up on the high perches, the ones with no bridge to them. The Concord can't reach them on foot. They don't need to: they have guns that reach further than a bridge.

  We go up, we put the shooters off the stack, and we knock their camp into the sinkhole. Nobody on the Stair will hear about it. That is the problem with the Stacks. Nobody ever hears about anything that happens here.
- **Victory:** destroy_keystone (the shooters' camp on the north stack, team 1); alternative `eliminate` team 1.
- **Defeat:** unit_lost tag `wren_halloway`, or turn_limit 14.
- **Events:**
  1. Turn 1: message from **Roost-Mother Oskeline** (shouting up from the roost-lamp): "Three chicks on the high perches. They don't know what a gun is. Go and teach the Concord what a beak is."
  2. Turn 3: reinforcement, two Surveyors (`salt_concord_surveyor`) climb onto the eastern bridge at (19,10) and (20,10), in range of the oyster perch.
  3. Turn 5: message from a **Concord bounty sergeant**: "Shilling a beak, lads! Two for the ones with riders!" Then spawn a Saltwright (`salt_concord_saltwright`) at (13,8) and a Brine Slinger at (13,9), walling the middle bridge.
- **Bonus objective:** Lose no nestlings (unit_lost tag `nestling`, negated). Salvage: winPearls 30.
- **Victory text:** The camp goes over the edge, tent and all, and the last shooter runs up the north road holding his hat on. Oskeline counts the chicks with her finger, twice. "Three," she says. "Good. Now go and steal something useful."
- **Defeat text:** Wren comes down hard on the shallows with a ball through Pocket's wing. The shooters sit on the north stack for a week and send the beaks up the Stair in a sack.
- **Unlocks:** `gyre_skua_lancer`, `gyre_windreader`.

## Mission 2: `gy_maps_for_sale` — "Maps for Sale"
- **Map:** `greywater_stair` (morning, Tide ambush set on the lower landings)
- **Enemy:** `returning_tide`
- **Type:** aerial escort.
- **Setup:** Wren (tag `wren_halloway`) at (11,3). The map pelican, Bucket (`gyre_pelican_hauler`, team 0, tag `map_pouch`), at (12,2). Goal: the Shelf landing, bottom-right corner, tiles (19,20), (20,20), (21,20), (19,21), (20,21), (21,21).
- **Briefing:**
  Tally, page four. A Concord surveyor named Edda Pilling paid us in salt to fly a satchel of survey maps down the Stair to a company at the bottom. She called us vermin while she counted it out. It was good salt.

  The satchel rides in Bucket's pouch, because Bucket is the only bird on the Stacks who will carry paper without eating it. The Tide are sitting on the lower landings waiting for Concord wagons. They have slingers. Slingers do not care whether you are a wagon.

  I read the maps on the roost last night, all of them, slowly. Every lighthouse on the Shelf is marked in red ink. Next to one of them someone has written "Lantern Shoal: do not touch the lamp", and I would very much like to know why a map needs to be told that.
- **Victory:** reach_tile (tag `map_pouch` at the Shelf landing tiles above).
- **Defeat:** unit_lost tag `map_pouch`, or unit_lost tag `wren_halloway`, or turn_limit 14.
- **Events:**
  1. Turn 2: surprise spawn, two Tear Slingers (`returning_tide_tear_slinger`) stand up out of the third landing at (3,11) and (18,11), covering both sides of the drop.
  2. Turn 4: message from **Cartographer Edda Pilling**, leaning over the top rail: "Those maps are signed and sealed! If one sheet arrives wet I am docking you by the sheet!"
  3. Turn 6: a Rainsayer (`returning_tide_rainsayer`) appears at (15,17) and floods the landing: terrain `brine_pool` at (17,19), radius 1, duration 4.
- **Bonus objective:** Keep Bucket above half health (unit_hp_above tag `map_pouch`, 0.5). Salvage: winPearls 35.
- **Victory text:** Bucket lands on the Shelf, opens her beak, and produces the satchel only slightly damp. The Concord quartermaster signs for it without looking up. The address on the flap says "Commander T. Orrel, Shoal expedition". Wren reads it upside down and remembers it.
- **Defeat text:** Bucket goes down on the fifth landing in a cloud of loose paper. The maps blow out over the Shelf, and for a week the Tide wrap their dead in them.
- **Unlocks:** `gyre_pelican_hauler`, `gy_spell_updraft`.

## Mission 3: `gy_first_on_the_carcass` — "First on the Carcass"
- **Map:** `breakers_yard` (noon, a dead leviathan fresh on the western ribs, Compact cutters already there)
- **Enemy:** `salvage_compact`
- **Type:** race.
- **Setup:** Wren (tag `wren_halloway`) at (22,14). Captain Torr Ashby (`gyre_captain_torr_ashby`, team 0 guest, tag `torr_ashby`) at (21,13). The carcass lies across the bone-road ribs on the western rise: tiles (5,9), (6,9), (7,9), (5,10), (6,10), (7,10), (8,10). A Compact flense-master (`salvage_compact_hullbreaker`, tag `flense_master`) stands on (6,10) with cutters (Scrappers, Wreckers) around it.
- **Briefing:**
  A handbill, nailed to the roost-post, signed with a vulture's foot. "The Black Wheel offers terms. One leviathan, two days dead, lying on the ribs in the Breakers' Yard. Whoever stands on it first eats it. Captain Torr Ashby will provide the vulture, the appetite and the reputation; the Stacks will provide wings and a thief, and take a third."

  Wren's note under it: a third of a leviathan is more meat than the Stacks have seen in a year. The Compact's cutters got there at dawn and they are already flensing. Torr says that is fine, because a cut carcass is a carcass someone else has done the work on.

  The yard is torn in half by a trench, and the ribs are the only road over. Birds will get there first. Birds cannot keep it. Someone has to walk.
- **Victory:** reach_tile (team 0, any unit on the carcass tiles above).
- **Defeat:** unit_lost tag `wren_halloway`, or turn_limit 10 (the Compact strips the carcass to the bone and sleds it home).
- **Events:**
  1. Turn 1: message from **Captain Torr Ashby**: "Lovely. Nobody's dead yet. That's the best time to arrive. Plenty of choice later."
  2. Turn 3: reinforcement, two Bone-Sled Riders (`salvage_compact_bone_sled_rider`) come up the bone road at (13,8) and (17,9) to cut off the ribs.
  3. Turn 6: surprise spawn, **Ketta Vane** (`salvage_compact_ketta_vane`, tag `ketta_vane`) skids in at (13,8): "Torr Ashby. I told you last time. Find your own dead."
- **Bonus objective:** Kill the flense-master (defeat_unit tag `flense_master`). Salvage: winPearls 40.
- **Victory text:** Wren's Roostwarden plants a nest-pike in the leviathan's jaw and the Compact cutters back off, swearing in three languages. Torr lands on the ribcage like a man sitting down to dinner. "A third," he says. "Of what's left after I've eaten. That's how thirds work."
- **Defeat text:** The Compact sleds the last of the carcass out at dusk. Torr shrugs and goes to look for a battle. The Stacks eat lichen for another month.
- **Unlocks:** `gyre_shrike_harrier`, `gy_spell_carrion_call`.

## Mission 4: `gy_rob_the_broker` — "Rob the Broker"
- **Map:** `the_kettle` (market day, the bowl packed, militia at both gates)
- **Enemy:** `salvage_compact`
- **Type:** heist.
- **Setup:** Wren (tag `wren_halloway`) at (10,19). **Odo Brask** (`salvage_compact_odo_brask`, team 1, tag `odo_brask`) at (12,3), beside his counting-hull. The strongbox is in the wreck at (12,4). Compact militia (Wreckers, Rivet Slingers, a Quartermaster) hold the north rim.
- **Briefing:**
  Tally, page nine. Everyone on the Ebb knows Odo Brask keeps a strongbox in the hull by the north gate of the Kettle, and everyone knows nobody has ever got near it. So everyone will know who did.

  It has to be my hands on the box. Not a crow, not Bucket, not one of the runners: me. A theft nobody saw you make is just something that went missing. I go in over the stalls, Pocket drops me on the hull, and the rest of you make enough noise that the militia looks the wrong way.

  One rule. Brask lives. A dead broker cannot be robbed again, and the Compact would close every market on the Ebb to the Stacks for a hundred years, which is longer than even Oskeline plans to hold a grudge.
- **Victory:** reach_tile (tag `wren_halloway` at (12,4), the strongbox).
- **Defeat:** unit_lost tag `wren_halloway`; or defeat_unit tag `odo_brask` (Brask is killed); or turn_limit 12.
- **Events:**
  1. Turn 1: message from **Odo Brask**: "Lovely morning for it. Whoever's on the frigatebird, I can see you, and I'd like to discuss a commission."
  2. Turn 4: the market bell rings. Reinforcement, two Wreckers (`salvage_compact_wrecker`) at the west and east gaps, (3,9) and (19,9).
  3. Turn 7: message from **Odo Brask**: "Take the money! Take it! Leave the ledger, the ledger is sentimental!" Then two Bone-Sled Riders (`salvage_compact_bone_sled_rider`) sweep in from (0,10) and (21,10).
- **Bonus objective:** Wren above half strength at the end (unit_hp_above tag `wren_halloway`, 0.5). Salvage: winPearls 45.
- **Victory text:** The box is mostly promissory notes. Under them is the ledger: sixty years of the Compact buying Lanternkeeper secrets, page after page. One line is underlined twice. "Locked page. Master copy carried by the road-keeper of the Glasswork Reach. Not for sale. Asked forty-one times." Wren reads it in the air, and Pocket has to correct for her.
- **Defeat text:** The militia net Pocket over the north gate. Brask sells Wren back to the Stacks for a price Oskeline will never stop mentioning.
- **Unlocks:** `gyre_frigate_thief`, `gy_equip_hooded_lure`.

## Mission 5: `gy_a_lanterns_pocket` — "A Lantern's Pocket"
- **Map:** `glasswork_reach` (night, the beams sweeping the glass arms, the ruined lighthouse at the centre)
- **Enemy:** `lanternkeepers`
- **Type:** infiltrate / the famous robbery.
- **Setup:** Wren (tag `wren_halloway`) at (15,26). **Keeper Sabine Lusk** (`lanternkeepers_keeper_of_the_long_watch`, team 1, tag `keeper_lusk`) sleeps in the lamp-room on (14,14). The page is in the lamp-room: goal tiles are the four glowmoss tiles (14,14), (15,14), (14,15), (15,15). Lamplit Sailors, Wicks and a Lantern Warden hold the lighthouse ring.
- **Briefing:**
  Tally, page twelve, written on the north stack while Ketta Vane's sleds were still climbing it. The Compact came for Brask's box. We let them have it. I kept the ledger.

  Keeper Lusk sleeps one night a month in the ruined lamp-room on the Reach, with the locked page under her pillow. I know because I carried her letters there when I was eleven, and she gave me a biscuit and told me nothing. Forty-one people have tried to buy that page. Nobody has tried to take it, because nobody robs a keeper.

  The glass is open and bright, and the beams light up anything that crosses it. So we cross it fast and we do not stop. I touch nothing but the page, and I do not hurt the keeper. Robbing her is one thing. The Rim would never forgive the other.
- **Victory:** reach_tile (tag `wren_halloway` on any of the four lamp-room tiles).
- **Defeat:** unit_lost tag `wren_halloway`; or defeat_unit tag `keeper_lusk` (Wren will not be the one who killed a keeper); or turn_limit 12.
- **Events:**
  1. Turn 1: message from **Keeper Sabine Lusk** (half asleep, from the lamp-room): "Is that a frigatebird? Tell your captain the letters go to the Shoal tonight, not here."
  2. Turn 3: surprise spawn, three Lamplit Sailors (`lanternkeepers_lamplit_sailor`) step out of the beam on the south glass arm at (14,22), (15,22) and (15,21), behind the player.
  3. Turn 8: reinforcement, **Captain Hollis Drenn** (`lanternkeepers_captain_hollis_drenn`, tag `captain_drenn`) arrives on the north road at (14,9): "Nobody robs a keeper. Who would even think of it?"
- **Bonus objective:** Leave Keeper Lusk above half strength (unit_hp_above tag `keeper_lusk`, 0.5). Salvage: winPearls 50.
- **Victory text:** Wren comes out of the lamp-room with a single page in an iron clasp, still locked. She picks the lock on the wing, a thousand feet up, by beam-light. She reads the first line. Pocket feels her go very still, and banks for home without being told.
- **Defeat text:** The beam finds Pocket over the glass and holds her there, white and blind. Lusk takes the page back from Wren's coat with a polite apology, and gives her a biscuit.
- **Unlocks:** `gyre_stormkite_gunner`, `gy_spell_black_sky`.

## Mission 6: `gy_every_bird_comes_home` — "Every Bird Comes Home"
- **Map:** `kelpmire` (dusk, fog in the stalks, the Court coming up the channel)
- **Enemy:** `hadal_court`
- **Type:** rescue / retreat.
- **Setup:** Wren (tag `wren_halloway`) hiding in the kelp at (15,4), far from home, close to the Court. Roost-Mother Oskeline (`gyre_roost_mother_oskeline`, team 0 guest, tag `roost_mother`) at (10,22). Goal: the roost-lamp, tiles (9,23), (11,23), (9,24), (10,24), (11,24). Court Bell-Knights, Lurecallers and a Deep Herald deploy in the north mire.
- **Briefing:**
  Tally, page fourteen. I have read the page four times now. It says the sky is a floor, and above the floor there is a sea, and the lamps are what hold it up. It says where a lamp flickers the floor goes thin, and the things that feed on the underside of the beam come down toward the light. "They do not come down for us. We are only in the way."

  I have stopped looking up. Pocket has not. Something followed us out of the Reach, and it is not a keeper: it is big, it is slow, it rings when it walks, and it has been asking the kelp for me by name.

  I am in the stalks north of the channel with a hook through Pocket's wing. Oskeline says she is coming with every bird on the Stacks. Oskeline cannot fly. I have decided not to argue.
- **Victory:** reach_tile (tag `wren_halloway` on any roost-lamp tile above).
- **Defeat:** unit_lost tag `wren_halloway`, or unit_lost tag `roost_mother`, or turn_limit 14.
- **Events:**
  1. Turn 1: message from **Herald Vhaal** (from the fog, her bell ringing under every word): "Thief. You carry a page that was not yours. Neither was the sea. Give me the one, and I will not ask about the other." Status `rooted` on tag `wren_halloway` for 3 turns (Pocket's wing is hooked).
  2. Turn 3: message from **Roost-Mother Oskeline**: "Up, all of you. Bring me back my idiot." Spawn three Salt Crows (`gyre_salt_crow`, team 0, tag `homing_crow`) around Wren at (14,5), (16,5) and (15,6).
  3. Turn 6: surprise spawn, a Crushing Maw (`hadal_court_crushing_maw`) heaves up out of the channel at (10,13), with a Lurecaller (`hadal_court_lurecaller`) at (12,11), across the only short way home.
- **Bonus objective:** Bring every homing crow back (unit_lost tag `homing_crow`, negated). Salvage: winPearls 55.
- **Victory text:** Pocket comes down on the roost-lamp in a heap of feathers, and Wren falls off her. Oskeline hits her with a crook, then holds on to her for a long time. Out in the fog, Vhaal's bell stops ringing. "She'll be back," says Oskeline. "Bells always come back. That's what they're for."
- **Defeat text:** The Lurecaller's light pulls Pocket down into the channel. Vhaal lifts the page out of the mud, reads it in silence, and goes back down without a word.
- **Unlocks:** `gyre_wheel_captain`, `gy_equip_oilskin_flight_coat`.

## Mission 7: `gy_the_wrong_sky` — "The Wrong Sky"
- **Map:** `tide_steps` (after Deeplight, a sky the colour of a bruise, the basin full and rising)
- **Enemy:** `overcurrent`
- **Type:** rescue / hold.
- **Setup:** Captain Torr Ashby (`gyre_captain_torr_ashby`, team 0 guest, tag `torr_ashby`) at (12,19), grounded on the lower terrace with two of his Black Wheel Skua Lancers (`gyre_skua_lancer`, tag `black_wheel`) at (11,19) and (13,19). Wren (tag `wren_halloway`) deploys with the company on the south rim. The Overcurrent start in the basin water: the shallows and brine pools are theirs; the dry terraces and salt walls are where they die slowly.
- **Briefing:**
  Oskeline's words, written down by Wren because the old woman said someone had better. Three nights ago a lamp went out somewhere down in the trenches. The next morning it rained salt water out of a clear sky, and not one bird on the Stacks would leave the roost. They sit with their heads all turned the same way, looking up.

  Torr Ashby took the Black Wheel to the Tide Steps anyway, because a Concord patrol died there and nobody had cleaned it up. His riders came back without him. They say there was nothing on the bones to clean, and that the birds would not lift, and then something came down out of the sky onto the basin.

  He is a vulture and a liar and he owes us a third of a leviathan. Go and get him. Stay on the dry steps. Whatever is falling out of that sky drowns in the air, so make it come to you.
- **Victory:** survive 9 turns.
- **Defeat:** unit_lost tag `torr_ashby`, or unit_lost tag `wren_halloway`.
- **Events:**
  1. Turn 1: message from **Captain Torr Ashby**: "Wren! Don't land. The birds won't fly, which means they know something, which means I'd like to be somewhere else." Status `rooted` on tag `black_wheel` and on tag `torr_ashby` for 4 turns.
  2. Turn 4: skyfall, two Downward Sharks (`overcurrent_downward_shark`) drop onto the south rim behind the company at (6,23) and (17,23), drawn by the player's Beacon.
  3. Turn 7: the rain comes. Terrain `brine_pool` at (12,22), radius 1, duration 3, at the foot of the player's lamp; spawn a Ribbon King (`overcurrent_ribbon_king`) out of the basin at (12,16).
- **Bonus objective:** Keep Torr above half strength (unit_hp_above tag `torr_ashby`, 0.5). Salvage: winPearls 60.
- **Victory text:** By dusk the things in the basin have stopped moving, pale and split on the dry steps. Torr walks among them and does not pick anything up. "First battle I've seen with nothing left after," he says. "They eat everything. Even the cleanup." He flies home with the Stacks, and does not mention money once.
- **Defeat text:** The Ribbon King passes over the terrace and Torr's vulture is simply not there any more. The Black Wheel scatters across the Rim, and for a year the cliff-towns have no one to sell their dead to.
- **Unlocks:** `gyre_captain_torr_ashby`, `gy_spell_wrong_sky_gale`.

## Mission 8: `gy_the_wheel_comes_down` — "The Wheel Comes Down"
- **Map:** `gull_stacks` (night, rain from a clear sky, every bird on the Rim crowded into the cliffs)
- **Enemy:** `overcurrent`
- **Type:** last stand.
- **Setup:** Wren (tag `wren_halloway`) at (14,22). Roost-Mother Oskeline (`gyre_roost_mother_oskeline`, team 0 guest, tag `roost_mother`) at (14,23), beside the roost-lamp. **Keeper Sabine Lusk** (`lanternkeepers_keeper_of_the_long_watch`, team 0 guest, tag `keeper_lusk`) at (15,24). Nestlings (`gyre_salt_crow`, team 0, tag `nestling`) on the same high perches as mission 1: (3,7), (23,12), (4,13). Wet ground on the map: the shallows at the roost (13 to 15, 21 to 22) and at the north stack (13 to 14, 5 to 6), the oyster beds on the east and west perches.
- **Briefing:**
  Tally, last page. There is a lamp on the Stacks. It has always been there, on the stone under the roost, and the birds have nested on its gallery for three hundred years. Nobody ever tended it, and it has never once gone out. Keeper Lusk climbed up here last night with her spectacles fogged by the rain, and looked at it, and sat down.

  She did not ask for the page. She said the things on the underside of the beam go toward light, and that tonight ours is the brightest light between here and the Shoal. Every bird on the Rim is in these cliffs because they know it too. The sky I thought nobody could take is where the sea is. It was always where the sea is.

  So nobody flies out, and nothing comes in. We hold the roost until morning, and we keep the old woman, the keeper and the chicks alive. After that I have something to give back.
- **Victory:** survive 12 turns.
- **Defeat:** unit_lost tag `roost_mother`, or unit_lost tag `wren_halloway`.
- **Events:**
  1. Turn 1: message from **Keeper Sabine Lusk**: "Keep the page until morning. You'll want to know what you are looking at."
  2. Turn 4: the rain reaches the Stacks: terrain `brine_pool` at (14,13), radius 2, duration 4, on the middle stack. Skyfall, two Downward Sharks (`overcurrent_downward_shark`) land on the nest perches at (4,7) and (22,12).
  3. Turn 8: message from **Roost-Mother Oskeline**: "Its shadow's here. It isn't." Spawn The Thinning (`overcurrent_the_thinning`) at (14,17), on the bridge above the roost.
- **Bonus objective:** Lose no nestlings (unit_lost tag `nestling`, negated); Keeper Lusk above half strength (unit_hp_above tag `keeper_lusk`, 0.5). Salvage: winPearls 70.
- **Victory text:** Toward dawn the rain stops. Lusk looks south toward the Shoal and says one word, "Pell", and nothing else. Wren takes the iron clasp out of her coat and puts it into the keeper's hand, lock broken, page folded once. "I read it," she says. "I'd like you to know it was me." Lusk nods. "Everyone will," she says. "That's the trouble with you, Wren Halloway. Everyone always will."
- **Defeat text:** The Thinning's shadow covers the roost and does not lift. In the morning the Stacks are quiet, and every bird on the Rim is flying inland, away from the sky.
- **Unlocks:** `gyre_roost_mother_oskeline`, `gyre_mother_of_the_wheel`.

## Campaign arc and secret
Missions 1 to 3 teach the Gyre's world: the Concord shoots them and pays them, the Tide do not care what flies, and every carcass is a race against the Compact. Missions 4 and 5 are the score: Brask's ledger points at the one thing on the Ebb nobody has ever managed to buy, and Wren takes it with her own hands. Missions 6 to 8 are what the page says coming true: the Court hunts the reader, Deeplight goes dark, and the things that feed on the underside of the beam fall onto the Tide Steps and then onto the nests. The Gyre are right that the dead belong to whoever comes for them, and that nobody on the Stair ever looked up. They are wrong that the sky is theirs: it is the floor of the sea, and their nests have been sheltering under a lamp all along. The campaign ends with the page returned and a new line in Wren's tally, in her own spelling: "Biggest score on the Rim. Gave it back. Look up."
