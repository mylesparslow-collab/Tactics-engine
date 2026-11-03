# Brinewake campaigns 2 to 8: outline

One campaign per faction, 8 missions each, built like Campaign 1 ("The Light at Lantern Shoal", Salt Concord).
All seven are set in the same year (311 AE) around the same crisis, seen from different sides, so the stories
cross: the Tide put out the lamp at Deeplight that Tamsin hears go dark; the Court is the bell that climbs the
Shoal in Concord mission 8; Wren Halloway is the thief who robbed the Lanternkeepers; the Overcurrent fall
through the sky that Deeplight's dark lamp left thin.

Every campaign: starts with its lead hero, a few commons, one spell and one equipment; each mission unlocks two
relics; the last mission unlocks the faction's remaining hero(es) or exotic. All 14 existing maps are reused.
Collection: every faction now has a campaign that awards its cards, so the collection shows where each card is
earned. The "unlock everything" playtest switch stays ON for now (flip `UNLOCK_ALL` in collection.ts to make
campaigns the only way to earn cards).

Suggested play order (all open from the start): Concord, Tide, Court, Compact, Lanternkeepers, Reef, Gyre, Overcurrent.

---

## 2. Returning Tide: "The Weeping Shelf"  (id `the_weeping_shelf`)
**Lead:** Sister Maren Ketch, senior wringer, who believes and is starting to count. With Prophet Imre Dunnock
and Captain Oswin Brack (the drowned Hulk captain who wants his crew back). A prequel that runs into Campaign 1.
**Arc:** the Tide's road from holy ground to putting out a lighthouse. Maren does every terrible thing asked of
her, and in the last mission she is the one who sees what the rain actually is.
1. **Rain on the Faithful** (weeping_shelf, vs Concord): the Rainwatch comes to clear the shrine. Hold the rain.
2. **The Broken Toll** (greywater_stair, vs Concord): ambush salt convoys on the Stair; stop the wagons reaching the top.
3. **Brack's Crew** (kelpmire, vs Reef Ascendant): raise Oswin Brack's drowned crew from the kelp before the Reef eats them; escort.
4. **Paper Swords** (the_kettle, vs Salvage Compact): collect the forged Concord arms from broker Hesk Varrow; the Compact double-cross.
5. **Wringing the Wells** (tide_steps, vs Concord): drain four wells (hold them) before the relief column arrives.
6. **Lamp and Wall, the Other Side** (lantern_shoal, vs Concord): the first assault on the Shoal, from the Tide's side. You are meant to lose... Dunnock says "test the wall". Survive and withdraw.
7. **The Glass Road** (glasswork_reach, vs Lanternkeepers): the keepers' beams on open glass; break through to the Brinks.
8. **The Light Goes Out at Deeplight** (trench_deeplight, vs Hadal Court + Lanternkeepers): reach the fallen lamp and put it out. Victory text: the rain starts. Maren tastes it and understands it will not stop for anyone.

## 3. Hadal Court: "The Weight Returns"  (id `the_weight_returns`)
**Lead:** Herald Vhaal, the Third Bell, carrying one question up from the trench: who lifted the sea? With Orrun
Tessk (the Bell-Knight who stood the night watch and was never relieved) and Maelis Quell (the Vent-Priest
carrying a flame to the open sky).
**Arc:** slow, enormous, formal. The Court climbs. Everyone they meet lies to them, until the last keeper doesn't.
1. **The Long Climb** (boiling_floor, vs Salvage Compact): Compact powder crews blasting the vents for grease. Maelis's flame must survive.
2. **Deeplight Rising** (trench_deeplight, vs Salt Concord): Concord prospectors at the fallen lamp. Hold the city.
3. **The Unsigned Treaty** (saltpan_bastions, vs Salt Concord): Orrun Tessk wants a Concord officer to sign for the theft. Take the fort, capture (kill) the Verge commander.
4. **The Upper Kin** (tide_steps, vs Overcurrent): the sky thins and the Overcurrent fall. The Court will not strike first: survive until they dry out.
5. **The Market of Liars** (the_kettle, vs Salvage Compact): Vhaal asks Odo Brask her question; Brask sells an answer. Escort Vhaal through the ambush.
6. **The Rain That Faces Upward** (weeping_shelf, vs Returning Tide): the Tide claim the Court as fellow mourners; they are not. Break the Shrine.
7. **What the Glass Remembers** (glasswork_reach, vs Lanternkeepers): the keepers bar the road to the Shoal. Bell-Knights march into the beams.
8. **The Third Bell** (lantern_shoal, vs Lanternkeepers + Returning Tide): reach the lamp. Vhaal asks her question of Keeper Auster, who answers it. The Court stays to guard the glass. Unlocks Orrun Tessk and Maelis Quell.

## 4. Salvage Compact: "Mother Hull"  (id `compact_mother_hull`)
**Lead:** Ketta Vane, fastest rider on the salt, who just wants open flat and nobody on it. With Odo Brask
(always selling) and Brother Ashmaw (who wants the old hulls to burn bright enough to be seen from the Rim).
**Arc:** neutrality is a lie the Compact tells itself. By the end it has to pick a side, and picks the lamps.
1. **Breakers' Yard** (breakers_yard, vs Gyre): Torr Ashby's riders are stripping a fresh wreck. Run them off the carcass.
2. **Cut and Run** (the_kettle, vs Salt Concord): Concord toll-agents raid the market. Get the sleds and the strongboxes out.
3. **Grease and Glory** (boiling_floor, vs Hadal Court): Ashmaw's powder works at the vents; the Court comes up through the floor.
4. **The Roost Debt** (gull_stacks, vs Gyre): Wren Halloway stole a Compact strongbox. Climb the stacks and take it back.
5. **Embargo** (saltpan_bastions, vs Salt Concord): the Concord closes the salt roads; break the star fort's gate.
6. **Kelp and Carcass** (kelpmire, vs Overcurrent): something fell from the sky and doesn't rot. Harvest it before it eats the crew.
7. **The Archive** (mother_hull, vs Salt Concord): Tamsin's company is in the ribs (Concord mission 6, other side). Hold the skull as long as you can, get Brask out.
8. **The Warm Heart** (mother_hull, vs Hadal Court + Returning Tide): with Deeplight out, the Court and the Tide both come for Mother Hull. The Compact signs with the lamps and holds. Unlocks Brother Ashmaw and the Harpoon Engine.

## 5. Lanternkeepers: "The Long Watch"  (id `the_long_watch`)
**Lead:** Captain Hollis Drenn, drowned captain bound to a lamp, commander of the Lamplit. With Lensmaster Oriel
Venn (who wants to prove a keeper can strike) and Keeper Pell Auster.
**Arc:** the keepers count the lamps, find fewer each year, and finally break the vow of silence.
1. **Counting the Lamps** (glasswork_reach, vs Returning Tide): a Tide splinter on the glass road. Keep the beam lanes clear.
2. **Signal Fire** (gull_stacks, vs Gyre): a Gyre messenger rider went missing with a sealed letter. Get it back, and say nothing.
3. **The Ledger** (greywater_stair, vs Salt Concord): the Concord wants the Shoal lamp catalogued. Stop the survey party reaching the top landing.
4. **The Book in the Kettle** (the_kettle, vs Salvage Compact): buy back a stolen Vigil Book copy; the deal goes wrong.
5. **The Fallen Lamp** (trench_deeplight, vs Hadal Court): Venn's mission to tend the lamp in the Court's city. Reach the glass.
6. **What Feeds Below the Beam** (tide_steps, vs Overcurrent): where a lamp flickered, the locked page comes true.
7. **The Wet Saint** (weeping_shelf, vs Returning Tide): hunt Imre Dunnock on holy ground. He isn't there.
8. **The Lamp Will Not Go Out** (lantern_shoal, vs Returning Tide + Overcurrent): Deeplight is dark; the Shoal must hold. Venn speaks. Unlocks Oriel Venn and First Flame.

## 6. Reef Ascendant: "Coralspire"  (id `coralspire`)
**Lead:** Coralspire, eldest colony. Briefings are written as the colony's slow plural thought ("we"). With
Marrowbloom (that eats the dead) and Glasswake (the lens-colony that remembers every shape).
**Arc:** the Reef wants the Ebb forever, and slowly learns that it is made of the sea it is fighting to keep away.
1. **First Light** (oyster_banks, vs Salvage Compact): Compact cutters harvesting living reef. Wake, and grow.
2. **The Mass Grave** (breakers_yard, vs Salvage Compact): Marrowbloom eats the yard's dead. Overgrow the wreck.
3. **Kelp Remembers** (kelpmire, vs Returning Tide): Tide wringers draining the mire. Hold the wet.
4. **Salt Kills** (saltpan_bastions, vs Salt Concord): the Concord salts the earth around the spire. Break the salt works.
5. **The Lens** (glasswork_reach, vs Lanternkeepers): Glasswake wakes in the beam glass. The keepers try to grind it out.
6. **Crumbling Branches** (tide_steps, vs Hadal Court): the eldest branches fail; the Court comes for the brine basin you need.
7. **Taste of Rain** (weeping_shelf, vs Returning Tide): the colony reaches the rain and heals. It understands.
8. **Overgrowth** (lantern_shoal, vs Overcurrent + Returning Tide): the Reef grows a wall around a lighthouse to protect it, choosing to starve slowly rather than let everything drown. Unlocks Marrowbloom, Glasswake.

## 7. Gyre: "The Carrion Wheel"  (id `the_carrion_wheel`)
**Lead:** Wren Halloway, roost-thief on a frigatebird, chasing the score so big the whole Rim has to admit it was
her. With Roost-Mother Oskeline and Captain Torr Ashby (who sells battles their own cleanup).
**Arc:** the famous theft. Wren robs a Lanternkeeper of the Vigil Book's locked page, reads it, and learns the sky
isn't the one place nobody can take.
1. **The Cliff Shoot** (gull_stacks, vs Salt Concord): Concord bird-shooters on the nesting stacks. Drive them off.
2. **Maps for Sale** (greywater_stair, vs Returning Tide): fly a Concord survey party's maps down the Stair, through a Tide ambush.
3. **First on the Carcass** (breakers_yard, vs Salvage Compact): Torr Ashby races the Compact for a dead leviathan.
4. **Rob the Broker** (the_kettle, vs Salvage Compact): Wren lifts Odo Brask's strongbox in the middle of market day.
5. **A Lantern's Pocket** (glasswork_reach, vs Lanternkeepers): the famous robbery. Steal the locked page and fly.
6. **Every Bird Comes Home** (kelpmire, vs Hadal Court): the Court hunts the thief; Oskeline calls the flock to cover the retreat.
7. **The Wrong Sky** (tide_steps, vs Overcurrent): the birds refuse to fly. Something is coming down.
8. **The Wheel Comes Down** (gull_stacks, vs Overcurrent): the Overcurrent fall on the nests. Hold the roost. Wren gives the page back. Unlocks Oskeline, Torr Ashby, Mother of the Wheel.

## 8. Overcurrent: "What Feeds Below the Beam"  (id `what_feeds_below`)
**Lead:** The Undersinging. The Overcurrent have no language, so briefings are entries from the Vigil Book's
locked page, kept by a keeper watching them; events are the animals' "voices" (hunger, light, dry).
With Mother Mantle and Saint Rictus.
**Arc:** after Deeplight goes dark the floor of the sky thins, and they fall, hunting light. Pure horror,
a short brutal campaign where the player is the monster.
1. **The Floor Thins** (tide_steps, vs Salt Concord): first fall. A Concord patrol in the basin. Feed.
2. **Wet Ground** (oyster_banks, vs Reef Ascendant): find water before you dry. Take the shallows.
3. **The Slime Knot** (kelpmire, vs Salvage Compact): carcass-hunters with harpoons. Eat the hunters.
4. **A Saint Is Fed** (weeping_shelf, vs Returning Tide): Saint Rictus's Tide splinter feeds it; the main Tide does not approve.
5. **The Upper Kin** (boiling_floor, vs Hadal Court): the Court will not strike first. You will.
6. **Brightest Prey** (glasswork_reach, vs Lanternkeepers): the beams. Go toward the light.
7. **The Hooked Arms** (mother_hull, vs Salvage Compact): Mother Mantle drags the Compact's hulks apart.
8. **Below the Beam** (lantern_shoal, vs Lanternkeepers + Salt Concord): swarm the brightest light in the world. Victory is the locked page's last line. Unlocks Mother Mantle, Saint Rictus, The Thinning.
