"""Per-faction lighting presets and palettes (from world/bible/art_direction.md).

Every faction shares the same key light direction and paint settings so the board reads as one
world; only ambient, rim colour and a few strengths change. Use: LOOK = looks.LOOKS['hadal_court'].
"""
import dataclasses
from render import Look, _hex

_base = Look()

LOOKS = {
    # flat daylight
    'salt_concord': _base,
    # teal points in the dark: dimmer key, cold ambient, strong teal rim
    'hadal_court': dataclasses.replace(_base, key_int=1.15, sky=(0.42, 0.46, 0.62), sky_int=0.30,
                                       bounce=(0.35, 0.40, 0.50), bounce_int=0.15,
                                       rim_color=(0.25, 0.85, 0.78), rim_int=0.95,
                                       shadow_tint=(0.62, 0.70, 1.0)),
    # wet glints: greenish ambient, brine rim, a touch more specular feel via rim
    'returning_tide': dataclasses.replace(_base, sky=(0.58, 0.66, 0.62), rim_color=(0.40, 0.80, 0.76),
                                          rim_int=0.75, shadow_tint=(0.66, 0.80, 0.92)),
    # flares and tin lanterns: warmer key, warm rim
    'salvage_compact': dataclasses.replace(_base, key_color=(1.0, 0.90, 0.76), rim_color=(1.0, 0.72, 0.45),
                                           rim_int=0.6, bounce=(0.82, 0.70, 0.55)),
    # warm coral, glassy cyan rim
    'reef_ascendant': dataclasses.replace(_base, rim_color=(0.62, 0.90, 0.88), rim_int=0.7,
                                          bounce=(0.90, 0.72, 0.66), bounce_int=0.26),
    # lamp gold rim
    'lanternkeepers': dataclasses.replace(_base, rim_color=(0.95, 0.76, 0.40), rim_int=0.8,
                                          sky=(0.56, 0.60, 0.66)),
}

PALETTES = {
    'world': dict(salt_white=_hex('#f1ede2'), trench_black=_hex('#0c0e14'), rust=_hex('#a8552e'),
                  bone=_hex('#d9d0b4'), teal=_hex('#3fd1c4'), lamp_gold=_hex('#e3b04b'),
                  skin_light=_hex('#e0ad8c'), skin_mid=_hex('#c48a68'), skin_dark=_hex('#8a5a40'),
                  leather=_hex('#4d3526'), boot=_hex('#33261d'), wood=_hex('#6e4c31'),
                  steel=_hex('#c9d2d8'), iron=_hex('#5a5e66'), lamp=_hex('#ffcf7a')),
    'salt_concord': dict(salt=_hex('#e2ddcf'), steel_blue=_hex('#56728f'), steel_dk=_hex('#3d546c'),
                         road=_hex('#7b7d80'), brass=_hex('#b8924a'), ink=_hex('#1d2a3a')),
    'hadal_court': dict(indigo=_hex('#2b2f6b'), teal=_hex('#3fd1c4'), black=_hex('#0c0e14'),
                        iron=_hex('#4a4f66'), amber=_hex('#d98a2b')),
    'returning_tide': dict(green=_hex('#3f7a5c'), black=_hex('#0c0e14'), wet_grey=_hex('#6d7a78'),
                           linen=_hex('#cfd2c4'), brine=_hex('#4fa3a0')),
    'salvage_compact': dict(rust=_hex('#a8552e'), bone=_hex('#e8dfc6'), tallow=_hex('#d6b25e'),
                            soot=_hex('#2a2522'), flare=_hex('#c4412b')),
    'reef_ascendant': dict(coral=_hex('#e07a6a'), calcite=_hex('#f1e9df'), pink=_hex('#f3b3a4'),
                           reef_red=_hex('#9b3f3a'), lens=_hex('#9fe3e0')),
    'lanternkeepers': dict(gold=_hex('#e3b04b'), sea_grey=_hex('#8e9ba3'), lens_white=_hex('#fff6dc'),
                           slate=_hex('#2b3239'), oilskin=_hex('#c79a3a')),
}
