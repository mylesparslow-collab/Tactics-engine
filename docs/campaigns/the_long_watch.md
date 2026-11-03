# Campaign 5: "The Long Watch"

Campaign id: the_long_watch · Faction: lanternkeepers · Mission prefix: lk_

Faction: Lanternkeepers (`lanternkeepers`). 8 missions. Escalation: lane defence, rescue, interception, chase, pilgrimage, survival, hunt, finale. Set in 311 AE across the same crisis as Campaign 1; it runs alongside "The Light at Lantern Shoal" and ends on the same night. Pearl rewards follow the bible (win, speed, losses, bonus). All times in turns. Coordinates are (x, y) on the named map. Setting canon: `EBB_world_bible.md`, `bible/history_and_gazetteer.md`.

## Starting roster
- `lanternkeepers_captain_hollis_drenn` (lead hero)
- `lanternkeepers_wick`
- `lanternkeepers_wick`
- `lanternkeepers_lamplit_sailor`
- `lanternkeepers_lamplit_sailor`
- `lanternkeepers_oilbearer`
- `lanternkeepers_oilbearer`
- `lanternkeepers_signalman`
- `lk_spell_lamp_flash` (spell)
- `lk_equip_wick_trimmers` (equipment)

## Recurring characters

**Captain Hollis Drenn** (player). Master of the *Gannet's Due*, the last ship to founder off the Rim, which struck the bar at Lantern Shoal an hour before the Long Ebb. He woke on the sand at dawn, dry and dead, bound to the lamp whose light he had been steering by. He has commanded the Lamplit for three hundred and eleven years, keeps ship's time by the lamp's sweep, and goes wherever its beam can reach. Courteous, patient, and very good at counting. He starts believing that silence is a kind of mercy. He ends holding the lens steady while someone else breaks it.

**Lensmaster Oriel Venn.** The Shoal's lens-grinder, forty, burn-scarred on both hands, and the only keeper in living memory to ask in chapter why the order is not allowed to fight. She can fold a beam into a blade a mile long and is tired of being told to point it at the floor. She wants to prove a keeper can strike. What she proves, in the end, is that a keeper can speak.

**Keeper Pell Auster.** Last Lanternkeeper of the Shoal, as in Campaign 1. She has not left the tower in three years and does not leave it now; she talks to Drenn by shutter-lamp from the gallery, in half-sentences. She knows the locked page by heart and has never once said it aloud. Will not carry a weapon. Will stand in front of one.

**Prophet Imre Dunnock, "the Wet Saint".** The Tide's prophet, as in Campaign 1. The keepers have hunted him for eleven years and never seen his face. He is the one man on the Ebb who has guessed what they know, and he guessed it alone, because they would not tell him.

**Odo Brask, Compact fixer.** As in Campaign 1. Has been buying keeper secrets for sixty years and is frightened of every one he owns. Sells the keepers back their own book, twice.

**Herald Vhaal, the Third Bell.** Hadal Court envoy, as in Campaign 1. Carries one question up from the trench. The keepers are the first people she meets who refuse to answer it, which she finds more honest than lying and much ruder.

---

## Mission 1: `lk_counting_the_lamps` "Counting the Lamps"
- **Map:** `glasswork_reach` (daylight, the Shoal's beam sweeping the four glass arms)
- **Enemy:** `returning_tide` (a splinter, not Dunnock's host)
- **Type:** lane defence / skirmish.
- **Setup:** Player: Captain Drenn (tag `captain_drenn`) at (15,25); Oilbearer (14,26), Oilbearer (16,26), Wick (15,24) (tag `watch`). Tide: Wringer (14,5), Penitent (13,5), Penitent (16,5), Tear Slinger (12,6), Tear Slinger (16,6), Rainsayer (15,3). Tide warband: Penitent x3, Drowned x2, Tear Slinger x2, Tideskulker x2, Wringer, Shroud Mender, Rainsayer.
- **Briefing:**
  The Count, 311 AE, Lantern Shoal, entered by Captain H. Drenn for Keeper Auster, whose eye is worse. Lamps seen burning from the gallery on the clear nights of the spring: forty-one. Last year, forty-three. The year before that, forty-four, and I have stopped writing down the year I first counted.

  The Shoal's beam swept the Reach for three hundred years and fused the sand to glass, four long arms of it meeting at the old dead tower. The Tide have sent a splinter of penitents onto the glass to wet it. Wet glass scatters the beam, and a scattered beam does not reach the Brinks.

  We keep the lanes clear and the old lamp-room dry. Lensmaster Venn asks permission to burn them off the glass. I have told her she may, provided she does not enjoy it.
- **Victory:** destroy_keystone team 1 (the splinter's shrine at the north end); or `eliminate` team 1.
- **Defeat:** reach_tile team 1 on the old lamp-room tiles (14,14), (15,14), (14,15), (15,15); unit_lost tag `captain_drenn`; destroy_keystone team 0.
- **Events:**
  1. Turn 1: message from **Captain Drenn**: "Forty-one. Keep them off the glass and we stay at forty-one."
  2. Turn 3: the Rainsayer's cloudburst: terrain `brine_pool` at (15,21), radius 1, 3 turns. Message from **Lensmaster Venn** (by shutter from the Shoal): "They've wet the south arm. I can't see you through it."
  3. Turn 5: reinforcement, two Tideskulkers (team 1) slide out along the west arm at (2,14) and (2,15).
- **Bonus objective:** Win before turn 10.
- **Victory text:** The splinter breaks and runs north, and the beam comes down the glass clean and white, all the way to the Brinks. Drenn enters the count again in the evening, as if it might change. Forty-one.
- **Defeat text:** A penitent kneels in the old lamp-room and pours a skin of brine over the glass. The beam scatters into a hundred weak lights. Far off on the Brinks, something that was waiting for it stops waiting.
- **Unlocks:** `lanternkeepers_lantern_warden`, `lanternkeepers_glassgrinder`.

## Mission 2: `lk_signal_fire` "Signal Fire"
- **Map:** `gull_stacks` (wind, the nesting stacks, thin bone bridges)
- **Enemy:** `gyre`
- **Type:** rescue / escort.
- **Setup:** Player: Captain Drenn (tag `captain_drenn`) at (14,23); Wick (13,24), Wick (15,24), Signalman (14,22). Escort: the messenger Linnet Garr, a Gyre Roost-Runner on the player's team (tag `messenger`) at (25,5), on the high north-east stack. Gyre: Wheel-Captain (13,3), Roost-Runner (12,4), Roost-Runner (15,4), Skua Lancer (22,3), Frigate Thief (23,4), Gullwife (11,2), Roostwarden (14,5). Gyre warband: Salt Crow x3, Roost-Runner x2, Skua Lancer x2, Gullwife, Shrike Harrier x2, Windreader.
- **Briefing:**
  Captain's log. We pay the Gyre to carry our letters between lamps, and in return we say nothing else to them. It is the oldest bargain on the Rim and the only one the Gyre have never broken. Three days ago a rider named Linnet Garr left the Brinks with the keepers' count sealed in oilcloth, and did not arrive.

  She came down on the Gull Stacks with a shrike-spike through her bird's wing. The Wheel there has guessed that a letter worth sealing twice is a letter worth reading. They are circling her stack now and making up their minds.

  We bring her home with the seal unbroken. The Wheel will ask what is in it. The answer is nothing, and we will keep giving it until they stop asking.
- **Victory:** reach_tile team 0, tag `messenger`, on (14,23), (13,24), (14,24), (15,24) beside the Beacon.
- **Defeat:** unit_lost tag `messenger`; unit_lost tag `captain_drenn`; turn_limit 14.
- **Events:**
  1. Turn 1: status `gy_pinned` on tag `messenger`, 2 turns. Message from **Linnet Garr**: "Bird's down, I'm not. Whoever's coming, come quicker."
  2. Turn 3: message from **the Wheel-Captain**: "Lamp-ghost! Tell us what's in the letter and you can have the girl. Fair trade." Reply from **Captain Drenn**: "Weather."
  3. Turn 6: the Wheel lights a signal fire on the west stacks: reinforcement, two Shrike Harriers (team 1) at (4,6) and (5,7). Message from **Linnet Garr**: "I flew it four hundred miles. I'd like to know what I nearly died for." **Captain Drenn**: "So would I, mostly."
- **Bonus objective:** Bring Linnet Garr home above half health (unit_hp_above tag `messenger`, 0.5).
- **Victory text:** Linnet lands by the Beacon and hands over the oilcloth without a word, which is the most professional thing anyone has done all year. Drenn breaks the seal in the lamp-room and reads it alone. Forty-one, it says, and Deeplight's glass is crazed. He folds it into his coat, where nothing ever dries.
- **Defeat text:** The Wheel-Captain holds the letter up to the light, reads it twice, and laughs, because it is only numbers. By spring every roost on the Rim knows the numbers.
- **Unlocks:** `lanternkeepers_beaconrunner`, `lk_equip_signal_horn`.

## Mission 3: `lk_the_ledger` "The Ledger"
- **Map:** `greywater_stair` (overcast, seep-water on the cliff, keepers on the top landing)
- **Enemy:** `salt_concord`
- **Type:** interception.
- **Setup:** Player holds the top landing: Captain Drenn (tag `captain_drenn`) at (11,3); Oilbearer (5,4), Oilbearer (16,4), Signalman (10,3), Lantern Warden (12,3). Concord survey party climbing from the bottom: Cartographer Edda Lusk, a Surveyor carrying the ledger (tag `ledger_bearer`) at (10,17); Stair-Warden (9,16), Stair-Warden (11,16), Brineguard (8,15), Brineguard (12,15), Surveyor (6,17), Saltwright (13,17), Tollkeeper (10,15). Concord warband: Salt Levy x3, Brineguard x2, Brine Slinger x2, Surveyor, Causeway Outrider, Brine Chirurgeon.
- **Briefing:**
  Captain's log. The Concord's new survey company reached the Shoal, and Keeper Auster let them build their fires but not climb the stair. One of their cartographers, a careful woman named Edda Lusk, climbed it anyway while we were at the Reach. She measured the lamp, the lens and the oil tanks, and wrote in her ledger that the tanks have been dry for three hundred years.

  The ledger is going up the Greywater Stair to the Marshals' Office in Harrowgate. Clerks who read that a lamp burns nothing will ask what it burns instead, and clerks who ask questions send soldiers to find out. The Stair has two ways onto the top landing, the west and east flights, and we hold both.

  The ledger must not reach the Rim. Venn asks why we cannot simply tell the woman. I have no answer for her that I would put in a log.
- **Victory:** defeat_unit tag `ledger_bearer`.
- **Defeat:** reach_tile team 1, tag `ledger_bearer`, on the stair heads (4,4), (5,4), (6,4), (15,4), (16,4), (17,4); unit_lost tag `captain_drenn`; turn_limit 14.
- **Events:**
  1. Turn 1: message from **Edda Lusk**: "Keepers! I've no quarrel with you. I only wrote down what I saw."
  2. Turn 4: reinforcement, two Brine Slingers (team 1) at (8,19) and (12,19), and a Saltwright at (11,12) on the middle terrace.
  3. Turn 7: Venn tips the oil: terrain `lamp_oil` at (5,7), radius 1, 3 turns, at the foot of the west flight. Message from **Lensmaster Venn**: "There. Now the west stair burns. We could have just told her, Captain."
- **Bonus objective:** Lose no units.
- **Victory text:** Edda Lusk falls on the ninth landing with the ledger under her arm. Drenn burns it page by page in a brazier, because the lamp will not take it. Venn watches until the last page and then goes back up the stair without a word. In the count that night Drenn writes a second number under the lamps: one.
- **Defeat text:** The ledger reaches the Rim gate at dusk. Within the month a Marshal's clerk writes to the Shoal asking, very politely, what the lamp burns. Within the season, he sends men to ask in person.
- **Unlocks:** `lanternkeepers_stairkeeper`, `lk_equip_stairwell_greaves`.

## Mission 4: `lk_book_in_the_kettle` "The Book in the Kettle"
- **Map:** `the_kettle` (market day, the stalls of a dead man being sold by the lot)
- **Enemy:** `salvage_compact`
- **Type:** chase.
- **Setup:** Player: Captain Drenn (tag `captain_drenn`) at (10,17); Stairkeeper (9,18), Beaconrunner (11,18), Wick (8,19), Oilbearer (12,19). Compact: Quartermaster (11,3), Scrapper (8,8), Scrapper (13,8), Rivet Slinger (5,10), Rivet Slinger (17,11), Snare Tinker (14,12). Compact warband: Scrapper x2, Wrecker x2, Lamplighter, Rivet Slinger, Powder Monk, Tallow Mender, Bone-Sled Rider.
- **Briefing:**
  Captain's log. The broker Hesk Varrow is dead, put down in his own stall by a Concord knife, and the Compact is auctioning his stock by the lot. Lot fourteen is a keeper's book in oilcloth binding: a Vigil Book copy, taken off a drowned keeper's body forty years ago and sold four times since. Odo Brask is the auctioneer, and he has agreed to sell it to us before the bidding opens, for forty casks of lamp oil.

  We do not need lamp oil. Our lamps burn nothing. Brask does not know this, and so for sixty years we have bought our secrets back from him with a fuel we never use.

  We walk into the Kettle under the market code: no weapons drawn in the aisles. I expect Brask to keep the code. I expect it the way one expects the weather.
- **Victory:** defeat_unit tag `book_rider`.
- **Defeat:** reach_tile team 1, tag `book_rider`, on the north-west hulk gap (0,0), (1,0), (0,1), (1,1); unit_lost tag `captain_drenn`; turn_limit 12.
- **Events:**
  1. Turn 1: message from **Odo Brask**: "Captain! Forty casks, one book, and we never met. My clerk is counting the casks now. Slowly."
  2. Turn 3: the deal goes wrong. Spawn a Bone-Sled Rider (team 1, tag `book_rider`) at (11,9) in the sunk centre. Message from **Odo Brask**: "Ah. Captain. The Quartermaster has had a better offer from a gentleman with a Rim seal. Nothing personal. Everything financial."
  3. Turn 6: reinforcement, two Wreckers (team 1) at (5,6) and (6,6), covering the rider's run to the west gap.
- **Bonus objective:** Bring down the rider before turn 7.
- **Victory text:** The sled overturns in the salt and lot fourteen skids out of the wreck, binding split. Drenn picks it up: the fourth recension, complete except for the locked page, which no copy has ever carried. That page exists once, and it travels by hand. Brask sends the forty casks back the next morning with a note: "Partial refund. Partial book."
- **Defeat text:** The sled clears the hulk gap and is gone over the flats toward the Rim. Somewhere in Harrowgate, a man with a seal reads about the hand held up and does not sleep that night, or for some nights after.
- **Unlocks:** `lanternkeepers_bellringer`, `lk_spell_tithe_of_oil`.

## Mission 5: `lk_the_fallen_lamp` "The Fallen Lamp"
- **Map:** `trench_deeplight` (cold white light from below, brine falling on the outer galleries)
- **Enemy:** `hadal_court`
- **Type:** pilgrimage / escort.
- **Setup:** Player: Captain Drenn (tag `captain_drenn`) at (10,16); guest Lensmaster Oriel Venn (`lanternkeepers_lensmaster_oriel_venn`, player team, tag `lensmaster_venn`) at (11,17); Stairkeeper (9,17), Lantern Warden (12,17), Beaconrunner (10,19). Court: Bell-Knight (10,5), Bell-Knight (11,5), Pit Thrall (10,9), Pit Thrall (11,9), Lurecaller (8,9), Lurecaller (13,10), Lantern Spitter (7,3), Vent-Priest (12,2). Court warband: Pit Thrall x3, Bell-Knight, Pressure Lancer x2, Murk Diver, Vent-Priest, Trench Crab. The fallen lamp is the Court's own Beacon at (10,3).
- **Briefing:**
  Oriel Venn to Keeper Auster, from the Brinks, by the Gyre post. The letter says the glass at Deeplight is crazed. Fifty years ago this lamp fell into the trench and kept burning, and the Court built a city around it as if it were a hearth. Nobody has trimmed that lens since. I am going down to trim it.

  The Court will not let me. They think the lamp is theirs, and by every law I know they are right: they found it, they built on it, they kept it lit with nothing but their regard. Their Beacon is the lamp. If we break it to reach it, we have done the Tide's work for them.

  Captain Drenn walks the beam as far as it will let him and says he will come as far as that. A thief on a red-throated bird took the locked page off our Wick Tobin Sallow on the glass road last week, so I go down without it. I would not have read it anyway. I know what it says.
- **Victory:** reach_tile team 0, tag `lensmaster_venn`, on the lamp tiles (11,3), (10,2), (11,2), (12,3), (10,4), (11,4).
- **Defeat:** unit_lost tag `lensmaster_venn`; destroy_keystone team 1 (you broke the fallen lamp); unit_lost tag `captain_drenn`; turn_limit 15.
- **Events:**
  1. Turn 2: message from **Herald Vhaal**: "Keepers. You tend the hands that hold the weight. Answer me one question and walk to our light in peace: who lifted the sea?" Venn says nothing. **Herald Vhaal**: "Silence is also an answer, Lensmaster. It is only a rude one."
  2. Turn 5: reinforcement, a Crushing Maw (team 1) heaves up onto the south bridge at (10,13).
  3. Turn 9: reinforcement, a Deep Herald (team 1) on the north bridge at (10,6) and two Bell-Knights (team 1) on the west causeway at (3,3) and (4,3). Message from **Captain Drenn**: "Lensmaster. Mind their lamp. It's the only one down here."
- **Bonus objective:** Keep Venn above half health (unit_hp_above tag `lensmaster_venn`, 0.5).
- **Victory text:** Venn puts her scarred hands on the fallen glass and it rings like a struck bell. The crazing runs right through the lens, deeper than any grinding can reach. The lamp flickers under her palms, once, and far above the trench the sky goes the wrong colour. Venn stays to tend it. Drenn goes home alone up the beam, counting.
- **Defeat text:** The Bell-Knights close around the lamp like a fist. Venn is carried back up the Brinks on a stretcher, and the crazed glass at Deeplight goes on burning untrimmed, for now.
- **Unlocks:** `lanternkeepers_beamwright`, `lk_equip_first_lens`.

## Mission 6: `lk_what_feeds_below_the_beam` "What Feeds Below the Beam"
- **Map:** `tide_steps` (the basin half full, brine lying in the shallows, the high steps dry)
- **Enemy:** `overcurrent`
- **Type:** survival.
- **Setup:** Player: Captain Drenn (tag `captain_drenn`) at (11,23); Warden Ilse Corra, a Lantern Warden tending the Beacon (tag `warden_corra`) at (12,24); Stairkeeper (13,23), Beamwright (12,23), Glassgrinder (10,23). Overcurrent: Barrelgaze (tag `barrelgaze`) at (11,13) in the brine lake; Bellyeye Shoal (8,12), Bellyeye Shoal (15,12), Gulper (6,11), Gulper (17,11), Tongue-Louse (18,15), Driftbell (12,10). Overcurrent warband: Bellyeye Shoal x3, Gulper x2, Tongue-Louse x2, Weeping Sunfish, Hagwyrm, Siphon Chain. The Overcurrent Beacon (team 1 keystone) is the Downfall at (11,2): the place on the north rim where they keep landing.
- **Briefing:**
  Spoken by Keeper Auster over the shutter-lamp, one word per flash, and taken down by Captain Drenn, since the page itself is stolen. "Where a lamp flickers the floor of the sky goes thin, and what lives at the underside of the beam comes down through the thin place toward the light. It takes the keeper first."

  Deeplight flickered under Venn's hands, and the sky over the Tide Steps went thin the same night. Something came down into the basin before dawn. It glistens, it has too many teeth, and it dies slowly in the dry.

  Stay on the high steps where the stone is dry and let the basin do the work. Keep Warden Corra at the lamp and alive. The page is very clear about the order in which things are eaten.
- **Victory:** survive 10 turns; or destroy_keystone team 1 (the Downfall).
- **Defeat:** unit_lost tag `warden_corra`; destroy_keystone team 0; unit_lost tag `captain_drenn`.
- **Events:**
  1. Turn 1: message from **Keeper Pell Auster**: "They come where it's thin. They go to the light. Hold the dry stone. Don't follow them into the water."
  2. Turn 4: skyfall: spawn a Downward Shark (team 1) at (12,19) on the near terrace, with terrain `brine_pool` at (12,19), radius 1, 3 turns, where it lands. Message from **Warden Ilse Corra**: "It fell upward. No. It fell from up. Captain, it's looking at me."
  3. Turn 7: reinforcement, two Lure-Mothers (team 1) rise behind the line at (5,22) and (17,22). Message from **Captain Drenn**: "That light on the pool isn't ours. Nobody walk toward it."
- **Bonus objective:** Kill the Barrelgaze (defeat_unit tag `barrelgaze`).
- **Victory text:** The last of them crawls back into the basin and dries there, gasping, in a ring of shallows that steams in the sun. Corra sits down on the Beacon step and is sick. Drenn writes the page's words into the count in his own hand, under the lamps, which is the first time any keeper has put them on paper since the Vigil Oaths.
- **Defeat text:** The lure on the pool brightens, and Warden Corra walks down the steps toward it with her lamp held out in front of her. The page was right. It is always right. That is why it has a lock.
- **Unlocks:** `lanternkeepers_keeper_of_the_long_watch`, `lk_spell_beam_of_the_long_watch`.

## Mission 7: `lk_the_wet_saint` "The Wet Saint"
- **Map:** `weeping_shelf` (rain from a clear sky, the chasm open between the Beacons)
- **Enemy:** `returning_tide`
- **Type:** hunt / assassinate.
- **Setup:** Player: Captain Drenn (tag `captain_drenn`) at (4,16); Keeper of the Long Watch (5,17), Beamwright (3,17), Stairkeeper (4,15), Lantern Warden (5,18). Tide: a figure in Dunnock's soaked cloak, a Tide Prophet (`returning_tide_tide_prophet`, tag `wet_saint`) at (4,4) before the shrine; Choirmaster (5,2), Penitent (3,5), Penitent (6,5), Wringer (7,8), Anchor Bearer (7,9), Tear Slinger (6,9), Tear Slinger (8,9), Undertow Singer (18,9) on the east flank. Tide warband: Penitent x3, Drowned x2, Tideskulker x2, Shroud Mender, Rainsayer, Bloat Drowned.
- **Briefing:**
  Captain's log. For eleven years the order has hunted the Wet Saint and never once seen his face. After the Steps, Keeper Auster has decided we stop waiting for him to come to the lamps, which is the first time she has changed her mind this century. He has been seen at the shrine on the Weeping Shelf, and we are to bring the lamp's light to his face.

  The Shelf is his ground. The rain makes his people strong and our glass dim, and the chasm gives us one short causeway and one long road round the east edge. Every brine pool on the ledge has a Drowned under it, waiting to be asked.

  I do not like this. The order guards; it does not usually go looking. But Dunnock is the only man alive who has guessed what we know, and if he guessed it, he can act on it.
- **Victory:** defeat_unit tag `wet_saint`.
- **Defeat:** unit_lost tag `captain_drenn`; destroy_keystone team 0; turn_limit 14.
- **Events:**
  1. Turn 2: message from **the figure in the soaked cloak**, in Dunnock's gentle voice: "Captain Drenn. You drowned once already. Tell me, wasn't it quiet?"
  2. Turn 4: Drowned climb out of the pools behind the line: spawn three Drowned (team 1) at (3,14), (13,15) and (8,18).
  3. Turn 6: the rain doubles: terrain `brine_pool` at (7,10), radius 1, 4 turns, flooding the causeway. Message from **Keeper Pell Auster**: "Rain's heavier at the Shoal. Something's pulling on a lamp. Finish. Come home."
- **Bonus objective:** Keep Captain Drenn above half health (unit_hp_above tag `captain_drenn`, 0.5).
- **Victory text:** The figure falls in the rain, and the hood comes back on an old woman with a wringer's hands. "He went down to the light, Captain," she says. "You're late. You were always going to be." Then the rain on the Shelf turns from drizzle to downpour, and Drenn feels his lamp, three days' march away, pull at him like a hook.
- **Defeat text:** The keepers are driven back across the causeway, soaked to the bone and seeing double. On the shrine ledge the figure in the cloak raises its arms, and the rain answers it.
- **Unlocks:** `lanternkeepers_keeper_pell_auster`, `lk_equip_lamplit_mantle`.

## Mission 8: `lk_the_lamp_will_not_go_out` "The Lamp Will Not Go Out"
- **Map:** `lantern_shoal` (night, rain falling on the Shoal itself, the Concord company on the summit)
- **Enemy:** `returning_tide` (team 1) and `overcurrent` (team 2, hostile to everyone)
- **Type:** finale / hold.
- **Setup:** Player holds the south lamp: Captain Drenn (tag `captain_drenn`) at (10,17); Keeper Pell Auster (`lanternkeepers_keeper_pell_auster`, tag `keeper_auster`) at (11,18); guest Lensmaster Oriel Venn (`lanternkeepers_lensmaster_oriel_venn`, player team, tag `lensmaster_venn`) at (9,18). Tide (team 1): Wringer (10,4), Penitent (9,3), Penitent (12,3), Anchor Bearer (11,5), Choirmaster (12,2), Rainsayer (8,4), Tear Slinger (7,5), Tear Slinger (14,5). Tide warband: Penitent x3, Drowned x3, Bloat Drowned, Undertow Singer, Shroud Mender, Tideskulker x2. Overcurrent (team 2): Bellyeye Shoal (19,4) and Bellyeye Shoal (20,5) on the north-east silt (tag `fallen`); no warband, they arrive by skyfall.
- **Briefing:**
  Oriel Venn, written on the back of the count, for whoever is left to read it. Deeplight is dark. I was standing at the glass when the Tide came down the causeway with their prophet, and I watched a light that had burned for three hundred years go out under a wet hand. I came up the Brinks with my palms burned through, and the rain has followed me all the way to the Shoal.

  Commander Orrel's company holds the summit against Dunnock. We hold the lamp below it, against his people and against what is falling out of the thin sky behind them. The sea is coming down on the Shoal now. Keeper Auster says that when it rains on the Shoal itself, there is nothing left to check.

  We kept the vow for three hundred and eleven years, and the Rim keeps a lamp in every window and does not know why. Tonight I am going to tell them why. The Captain has agreed to hold the lens steady while I do it, and has asked me to spell carefully.
- **Victory:** survive 12 turns.
- **Defeat:** destroy_keystone team 0 (the Shoal lamp); unit_lost tag `keeper_auster`; unit_lost tag `lensmaster_venn`.
- **Events:**
  1. Turn 2: message from **Commander Tamsin Orrel** (from the summit): "Captain Drenn? Orrel. Dunnock is on my wall. Whatever comes out of the sky, keep it off my back."
  2. Turn 5: the floor of the sky gives way. Skyfall: spawn (team 2, tag `fallen`) a Downward Shark at (10,10), a Barrelgaze at (4,10), a Ribbon King at (16,10), Gulpers at (9,11) and (11,11). Terrain `brine_pool` at (10,10), radius 2, and at (4,10) and (16,10), radius 1, all 6 turns. Message from **Keeper Pell Auster**: "There it is. Lens up, Venn."
  3. Turn 9: Venn speaks. Message from **Lensmaster Oriel Venn**, shuttering the Shoal's beam across the whole Ebb in plain code: "THE SEA IS ABOVE YOU. THE LAMPS HOLD IT UP. KEEP YOURS LIT." Status `marked` on tag `fallen`, 3 turns, as the beam finds every one of them. grant_essence team 0, 40, as lamps answer in windows all along the Rim.
- **Bonus objective:** Keep Keeper Auster above half health (unit_hp_above tag `keeper_auster`, 0.5).
- **Victory text:** On the summit Dunnock dies with the tower's light on his face, and below him the last of the fallen things dries on the salt. Herald Vhaal stands at the foot of the tower and asks her question, and Auster answers it. Then Auster puts her hand on the glass. The rain slows, and stops. A red-throated frigatebird circles the lamp-room once and drops a folded page on the gallery rail, lock and all. Across the Ebb, in window after window, the Rim's little lamps stay lit until dawn, and this time everyone knows why.
- **Defeat text:** The beam stutters out mid-word. The last thing anyone on the Rim reads in the sky is half a sentence. Then the sky itself comes down to finish it.
- **Unlocks:** `lanternkeepers_lensmaster_oriel_venn`, `lanternkeepers_first_flame`.

## Campaign arc and secret
Missions 1 to 3 show the keepers at their best and worst: counting the lamps, keeping their bargains, and killing a curious woman to keep a ledger off the Rim. Missions 4 to 6 show the cost of the vow: the order buys back its own secrets, Venn finds the crazed glass at Deeplight, and the locked page comes true on the Tide Steps. Missions 7 and 8 bring the hunt home: Dunnock is already at Deeplight when the keepers come for him, the lamp goes dark, and the sky falls on the Shoal. The secret was never that the sea hangs above the world; the Tide guessed that, and the Court remembered it. The secret is that the keepers' silence left everyone else to guess. The campaign ends with Drenn writing a last line under the count, in his own hand: "Forty. Everyone is counting now."
