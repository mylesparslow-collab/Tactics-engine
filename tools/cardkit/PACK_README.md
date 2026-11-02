# Brinewake card art for ChatGPT

174 cards: 90 champions and heroes, 48 spells, 36 equipment. One folder per card, grouped by faction and numbered in the order to paint them (champions first, then heroes, spells, equipment).

Each folder holds:

- `prompt.txt`: paste this into ChatGPT.
- `model.png` (champions and heroes): the unit's in-game 3D model. Upload it with the prompt so the painting matches the unit on the board.
- `faction_models.png` (spells and equipment): the faction's unit models, for palette and costume language.

## How to run it

1. Open one ChatGPT chat per faction and do that faction's cards in order. ChatGPT keeps the look steadier inside one chat.
2. For each card, attach the image(s) in its folder, paste `prompt.txt`, and send.
3. When the first champion of a faction looks right, keep going in that chat. If a later card drifts, add "Match the painting style of the first card in this chat."
4. Ask for a redo if it adds text, a border or a frame, or if the character doesn't match the model.
5. Save each result named by its card id, e.g. `salt_concord_brineguard.png` (the id is the folder name after the number). Drop them all in `/mnt/project-files/card-art/finished/` (any subfolders are fine).

Claude converts finished paintings to `content/cards/<id>.webp` (512x768) and they replace the interim model-render art in the game automatically.

## The format, in short

Vertical 2:3 (1024x1536), full-bleed, no text or borders. The card's name plate and rules panel cover the bottom 40%, so faces and key props sit in the top 60%.
