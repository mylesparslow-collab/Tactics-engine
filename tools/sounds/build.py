#!/usr/bin/env python3
"""Build src/audio/assets/{sfx,amb} from licensed sound packs.

Nothing here synthesises sound: every output is a trimmed / level-matched / EQ'd
copy of a recorded sample from a CC0 or CC BY pack (see src/audio/CREDITS.md).

Usage:  python3 tools/sounds/build.py <packs-dir>

<packs-dir> must contain git clones of:
  kenney-interface-sounds   (github.com/Calinou/kenney-interface-sounds, CC0)
  kenney-ui-audio           (github.com/Calinou/kenney-ui-audio, CC0)
  kenney-rpg-audio-for-godot, kenney-impact-sounds-for-godot (github.com/Boyquotes/..., CC0)
  Meta-open-sound           (github.com/facebookincubator/Meta-open-sound; Oculus Audio Pack is CC BY 4.0)
"""
import os, subprocess, sys, shutil, glob

PACKS = sys.argv[1] if len(sys.argv) > 1 else '/tmp/claude-0/packs'
OUT = os.path.join(os.path.dirname(__file__), '..', '..', 'src', 'audio', 'assets')
OCU = f'{PACKS}/Meta-open-sound/corpora/oculus-audio-pack/ogg'
SRC = {
    'KI': f'{PACKS}/kenney-interface-sounds/addons/kenney_interface_sounds',
    'KU': f'{PACKS}/kenney-ui-audio/addons/kenney_ui_audio',
    'KR': f'{PACKS}/kenney-rpg-audio-for-godot/addons/kenney rpg audio',
    'KX': f'{PACKS}/kenney-impact-sounds-for-godot/addons/kenney impact sounds',
    'O': OCU,
}

def find(spec):
    pack, pat = spec.split(':', 1)
    base = SRC[pack]
    hits = sorted(glob.glob(os.path.join(base, pat)))
    if pack == 'KR' and not hits:
        hits = sorted(glob.glob(os.path.join(base, 'kenney rpg ' + pat)))
    if not hits:
        sys.exit(f'no match for {spec}')
    return hits

def enc(src, dst, filt='', bitrate='72k', mono=True, maxdur=None, fade_out=0.0):
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    chain = ['silenceremove=start_periods=1:start_threshold=-55dB:start_silence=0.01']
    if filt: chain.append(filt)
    if fade_out and maxdur:
        chain.append(f'afade=t=out:st={max(0, maxdur - fade_out):.3f}:d={fade_out}')
    cmd = ['ffmpeg', '-v', 'error', '-y', '-i', src]
    if maxdur: cmd += ['-t', str(maxdur)]
    cmd += ['-af', ','.join(chain)]
    if mono: cmd += ['-ac', '1']
    cmd += ['-ar', '44100', '-codec:a', 'libmp3lame', '-b:a', bitrate, dst]
    subprocess.run(cmd, check=True)

# bank -> (list of sources, options). Sources are 'PACK:glob' (each glob may expand to several files).
# opts: filt (ffmpeg audio filter), dur (max seconds), fade (fade-out seconds), gain (dB)
SFX = {
    # --- interface ---------------------------------------------------------------------------
    'ui_hover':   (['KU:rollover1.wav', 'KU:rollover2.wav', 'KU:rollover3.wav', 'KU:rollover4.wav'], dict(gain=-8)),
    'ui_click':   (['KU:click2.wav', 'KU:click3.wav', 'KU:click4.wav', 'KU:click5.wav'], dict()),
    'ui_confirm': (['KI:confirmation_00[123].wav'], dict()),
    'ui_back':    (['KI:back_00[123].wav'], dict()),
    'ui_open':    (['KI:open_00[123].wav'], dict()),
    'ui_close':   (['KI:close_00[123].wav'], dict()),
    'ui_error':   (['KI:error_00[456].wav'], dict()),
    'ui_select':  (['KI:select_00[1234].wav'], dict()),
    'ui_toggle':  (['KI:toggle_00[123].wav'], dict()),
    'ui_page':    (['KR:book_flip_[123].ogg'], dict(dur=0.6)),
    # --- cards & turn ------------------------------------------------------------------------
    'card_draw':  (['KR:handle_small_leather*.ogg', 'KR:cloth_belt*.ogg'], dict(dur=0.7)),
    'card_play':  (['KR:book_place_[123].ogg'], dict()),
    'turn_end':   (['O:DOORMetl_HatchClose_OS_01.ogg', 'O:MECHLvr_LeverPull_OS_0[12].ogg'], dict(dur=1.0, fade=0.2)),
    'bell':       (['KX:impact_bell_heavy_00[0-4].ogg'], dict()),
    'battle_start': (['O:MUSCStngr_SnareCrash_OS_01.ogg', 'O:UIMisc_BelltreeUp_OS_01.ogg'], dict(dur=2.5, fade=0.5)),
    # --- footsteps by ground ----------------------------------------------------------------
    'step_stone': (['KX:footstep_concrete_00[0-4].ogg'], dict(dur=0.4)),
    'step_salt':  (['KX:footstep_snow_00[0-4].ogg'], dict(dur=0.4)),   # crunchy: salt flats
    'step_silt':  (['O:FEETHmn_ShoeDirtWalk_OS_0[1-5].ogg'], dict(dur=0.5)),
    'step_reef':  (['KX:footstep_grass_00[0-4].ogg'], dict(dur=0.4)),
    'step_wood':  (['KX:footstep_wood_00[0-4].ogg'], dict(dur=0.4)),
    'step_metal': (['O:FEETHmn_ShoeMetalWalk_OS_0[1-5].ogg'], dict(dur=0.5)),
    # movement flavour layered under the step, by creature type
    'mv_gear':    (['O:CLOTHMvmt_MovementWithGear_OS_0[1-4].ogg'], dict(dur=0.6)),
    'mv_clank':   (['KX:impact_plate_light_00[0-2].ogg', 'KX:impact_metal_light_00[0-1].ogg'], dict(dur=0.5)),
    'mv_servo':   (['O:MOTRSrvo_Servo_OS_0[12].ogg'], dict(dur=0.7)),
    'mv_squelch': (['O:GORESqsh_BloodSquishSlimy_OS_0[1-4].ogg'], dict(dur=0.5)),
    'mv_drag':    (['O:CHAINMvmt_ChainsCreepy_OS_0[12].ogg'], dict(dur=0.9, fade=0.2)),
    'blink':      (['O:WHSH_WhooshMedium_OS_0[123].ogg'], dict(dur=0.7)),
    # --- attacks (the wind-up / swing) -------------------------------------------------------
    'atk_blade':  (['O:WEAPSwrd_Sword_OS_0[12].ogg', 'KR:knife_slice*.ogg', 'O:WEAPAxe_WoodCutAxe_OS_01.ogg'], dict(dur=0.9, fade=0.2)),
    'atk_blunt':  (['O:SWSH_Swoosh_OS_0[1-6].ogg'], dict(dur=0.7)),
    'atk_claw':   (['O:WHSH_WhooshSmall_OS_0[123].ogg', 'O:CLOTHMvmt_ClothingMovement_OS_0[12].ogg'], dict(dur=0.6)),
    'atk_shoot':  (['KR:cloth_[123].ogg', 'O:WHSH_WhooshSmall_OS_0[123].ogg'], dict(dur=0.6)),
    'atk_magic':  (['O:MAGSpel_MagicSpell_OS_0[12].ogg'], dict(dur=1.6, fade=0.4)),
    'atk_siege':  (['O:MACHInd_Hydraulic_OS_01.ogg', 'O:METLImpt_HammerAnvil_OS_01.ogg', 'O:TOOLPowr_PowerTool_OS_0[1-3].ogg'], dict(dur=1.2, fade=0.3)),
    # --- impacts ----------------------------------------------------------------------------
    'hit_flesh':  (['O:FGHTImpt_PunchRegular_OS_0[1-6].ogg', 'KX:impact_punch_medium_00[0-4].ogg'], dict(dur=0.7)),
    'hit_heavy':  (['KX:impact_punch_heavy_00[0-4].ogg', 'O:FGHTImpt_PunchHarder_OS_0[1-4].ogg'], dict(dur=0.9)),
    'hit_crit':   (['O:FGHTImpt_PunchHardest_OS_01.ogg', 'O:GOREBone_BonesBreaking_OS_0[123].ogg'], dict(dur=1.0)),
    'hit_armor':  (['KX:impact_plate_medium_00[0-2].ogg', 'O:METLImpt_MetalHitSurface_OS_0[1-3].ogg'], dict(dur=0.8)),
    'hit_squish': (['O:GORESqsh_BloodSquishSlimy_OS_0[1-4].ogg'], dict(dur=0.7)),
    'hit_salt':   (['KX:impact_glass_light_00[0-2].ogg'], dict(dur=0.8)),
    'hit_crush':  (['KX:impact_soft_heavy_00[0-2].ogg', 'O:WOODImpt_LargeWoodDrop_OS_01.ogg'], dict(dur=1.0)),
    'hit_metal':  (['KX:impact_metal_heavy_00[0-2].ogg', 'KX:impact_metal_medium_00[0-2].ogg'], dict(dur=1.0)),
    'hit_beacon': (['KX:impact_mining_00[0-4].ogg', 'KX:impact_plate_heavy_00[0-2].ogg'], dict(dur=1.2)),
    'beacon_fall': (['O:DSGNImpt_ImpactCreepyReverb_OS_0[123].ogg', 'KX:impact_bell_heavy_00[0-2].ogg'], dict(dur=3.0, fade=1.0)),
    'push':       (['KX:impact_wood_medium_00[0-1].ogg', 'O:WHSH_WhooshMedium_OS_0[12].ogg'], dict(dur=0.8)),
    'shatter':    (['O:GLASBrk_GlassBottleBreak_OS_01.ogg', 'O:CERMImpt_CeramicSmallImpact_OS_01.ogg'], dict(dur=1.2, fade=0.3)),
    # --- spells & effects -------------------------------------------------------------------
    'spell':      (['KX:impact_glass_heavy_00[0-2].ogg'], dict(dur=1.4, fade=0.4)),
    'cast':       (['KX:impact_glass_medium_00[0-2].ogg'], dict(dur=1.0, fade=0.3)),
    'chime':      (['O:UIMisc_BelltreeUp_OS_01.ogg', 'O:UIMisc_Powerup_OS_0[12].ogg'], dict(dur=1.6, fade=0.5)),
    'status':     (['KI:glass_00[1-6].wav'], dict(dur=0.8)),
    'curse':      (['O:METLFric_ScratchCreepyReverb_OS_0[12].ogg', 'O:VOXWhsp_WhispersCreepyReverb_OS_01.ogg'], dict(dur=1.4, fade=0.4)),
    'revive':     (['O:MUSCKeyd_PipeOrganCreepy_OS_01.ogg', 'O:UIMisc_BelltreeUp_OS_01.ogg'], dict(dur=3.0, fade=1.2)),
    'deploy':     (['O:CLOTHMvmt_MovementWithGear_OS_0[1-4].ogg', 'KR:draw_knife_[123].ogg'], dict(dur=0.8)),
    'equip':      (['KR:belt_handle_[12].ogg', 'O:METLImpt_MetalObjDrop_OS_0[12].ogg'], dict(dur=0.8)),
    'essence':    (['KR:handle_coins*.ogg', 'O:OBJCoin_CoinDrop_OS_01.ogg'], dict(dur=1.0, fade=0.2)),
    # --- unit voices by body type -----------------------------------------------------------
    'vh_hurt':    (['O:VOXMale_Male01Hurt_OS_0[12].ogg', 'O:VOXMale_Male02Hurt_OS_0[12].ogg', 'O:VOXFem_Female01Hurt_OS_0[12].ogg', 'O:VOXFem_Female02Hurt_OS_0[12].ogg'], dict(dur=1.0, fade=0.2)),
    'vh_die':     (['O:VOXMale_Male01Death_OS_0[12].ogg', 'O:VOXMale_Male02Death_OS_01.ogg', 'O:VOXFem_Female01Death_OS_0[12].ogg', 'O:VOXFem_Female02Death_OS_0[12].ogg'], dict(dur=2.0, fade=0.4)),
    'vh_effort':  (['O:VOXEfrt_*.ogg'], dict(dur=0.8, fade=0.15)),
    'vl_hurt':    (['O:CREAHmn_OgreHurt_OS_0[123].ogg', 'O:CREAHmn_TrollHurt_OS_0[12].ogg'], dict(dur=1.2, fade=0.2)),
    'vl_die':     (['O:CREAHmn_OgreDeath_OS_0[123].ogg', 'O:CREAHmn_TrollDeath_OS_0[12].ogg'], dict(dur=2.5, fade=0.5)),
    'vl_effort':  (['O:CREAHmn_OgreEffort_OS_01.ogg', 'O:CREAHmn_TrollEffort_OS_01.ogg'], dict(dur=1.0, fade=0.2)),
    'vg_hurt':    (['O:CREAHmn_GiantHurt_OS_0[123].ogg'], dict(dur=1.4, fade=0.3)),
    'vg_die':     (['O:CREAHmn_GiantDeath_OS_0[123].ogg', 'O:CREAHmn_GiantDeathScream_OS_01.ogg'], dict(dur=3.0, fade=0.6)),
    'vg_effort':  (['O:CREAHmn_GiantEffort_OS_01.ogg'], dict(dur=1.2, fade=0.2)),
    'vd_hurt':    (['O:VOXMale_GroanCreepy_OS_01.ogg', 'O:VOXFem_GroanCreepy_OS_01.ogg'], dict(dur=1.6, fade=0.4)),
    'vd_die':     (['O:VOXWhsp_WhispersCreepyReverb_OS_01.ogg', 'O:VOXMale_Male01DeathScream_OS_01.ogg', 'O:VOXFem_Female01DeathScream_OS_01.ogg'], dict(dur=2.5, fade=0.6, filt='lowpass=f=3500')),
    'vd_effort':  (['O:VOXFem_GroanCreepy_OS_01.ogg'], dict(dur=1.0, fade=0.3)),
    'vc_hurt':    (['O:CREAMnstr_CreatureCreepy_OS_0[123].ogg'], dict(dur=1.3, fade=0.3)),
    'vc_die':     (['O:CREAMnstr_CreatureCreepyReverb_OS_0[123].ogg'], dict(dur=2.5, fade=0.6)),
    'vc_effort':  (['O:CREAMnstr_CreatureCreepy_OS_0[123].ogg'], dict(dur=0.8, fade=0.2, gain=-3)),
    'vm_hurt':    (['O:METLImpt_MetalHitSurface_OS_0[4-5].ogg', 'KX:impact_tin_medium_00[0-2].ogg'], dict(dur=0.8)),
    'vm_die':     (['O:METLImpt_MetalObjDrop_OS_0[34].ogg', 'O:MACHFan_FanOff_OS_01.ogg', 'O:MACHHvac_HVACOff_OS_01.ogg'], dict(dur=2.2, fade=0.5)),
    'vm_effort':  (['O:MOTRSrvo_Servo_OS_0[12].ogg', 'O:MACHInd_Hydraulic_OS_01.ogg'], dict(dur=0.9, fade=0.2)),
    # --- stingers -----------------------------------------------------------------------------
    'victory':    (['O:MUSCStngr_VictoryOrchestral_OS_0[123].ogg'], dict(dur=4.0, fade=0.8, stereo=True)),
    'defeat':     (['O:MUSCStngr_LossOrchestral_OS_0[123].ogg'], dict(dur=4.0, fade=0.8, stereo=True)),
}

# Ambient beds: name -> (source, filter, trim seconds, loop crossfade seconds). Looped seamlessly in the browser.
AMB = {
    'surf':       ('O:WATRWave_OceanWaves_LOOP_01.ogg',          'highpass=f=60', 45, 3.0),
    'overhead':   ('O:AMBUndwtr_Underwater_LOOP_01.ogg',         'highpass=f=40', 45, 3.0),
    'wind':       ('O:WINDVege_WindTreesBirdsFlies_LOOP_01.ogg', 'lowpass=f=1800,highpass=f=50', 60, 4.0),
    'wind_light': ('O:WINDVege_LightWindTreesBirds_LOOP_01.ogg', 'lowpass=f=2200,highpass=f=50', 60, 4.0),
    'lap':        ('O:WATRLap_WaterLapping_LOOP_01.ogg',         'highpass=f=80', 45, 3.0),
    'drone':      ('O:DSGNDron_DroneCreepy_OS_01.ogg',           'lowpass=f=900', 45, 4.0),
    'bubbles':    ('O:WATRBubl_WaterBubbles_LOOP_01.ogg',        'highpass=f=100', 40, 3.0),
    'rain':       ('O:RAINVege_ForestRain_LOOP_01.ogg',          'highpass=f=150', 45, 3.0),
    'chimes':     ('O:MUSCChim_WindChimes_LOOP_01.ogg',          '', 31, 2.5),
    'flag':       ('O:CLOTHFlp_FlagFlapping_LOOP_01.ogg',        'lowpass=f=2500', 30, 2.0),
}
# One-shot "accent" sounds the ambience scheduler sprinkles in: name -> sources
ACCENT = {
    'creak':   (['O:WOODFric_CreaksCreepyReverb_OS_0[12].ogg', 'O:WOODFric_CreaksCreepy_OS_0[12].ogg'], dict(dur=4.0, fade=1.0)),
    'chains':  (['O:CHAINMvmt_ChainsCreepy_OS_0[12].ogg'], dict(dur=4.0, fade=1.0, filt='lowpass=f=2500')),
    'gull':    (['O:AMBForst_ForestBirds_OS_0[123].ogg'], dict(dur=4.0, fade=1.0, filt='lowpass=f=3000')),
    'bell_far': (['KX:impact_bell_heavy_00[0-4].ogg'], dict(dur=3.0, fade=1.5, filt='lowpass=f=1400', gain=-6)),
    'whisper': (['O:VOXWhsp_WhispersCreepyReverb_OS_01.ogg'], dict(dur=4.0, fade=1.0, gain=-6)),
    'drip':    (['O:WATRBubl_WaterBubbles_LOOP_01.ogg'], dict(dur=2.5, fade=1.0)),
    'metal_groan': (['O:METLFric_ScratchCreepyReverb_OS_0[12].ogg'], dict(dur=3.0, fade=1.0, filt='lowpass=f=2200')),
}

def peak_db(path, filt='', dur=None):
    af = ','.join(x for x in ['silenceremove=start_periods=1:start_threshold=-55dB:start_silence=0.01', filt, 'volumedetect'] if x)
    r = subprocess.run(['ffmpeg', '-hide_banner', '-i', path] + (['-t', str(dur)] if dur else []) + ['-af', af, '-f', 'null', '-'], capture_output=True, text=True)
    for line in r.stderr.splitlines():
        if 'max_volume' in line:
            return float(line.split('max_volume:')[1].split('dB')[0])
    return 0.0

def build_oneshots(table, subdir):
    out = os.path.join(OUT, subdir)
    shutil.rmtree(out, ignore_errors=True)
    n = 0
    for bank, (specs, o) in table.items():
        files = [f for s in specs for f in find(s)]
        for i, f in enumerate(files):
            filt = o.get('filt', '')
            g = o.get('gain', 0)
            # peak-normalise every file to -4.5 dBFS (headroom for the MP3 encoder) so banks are level-matched, then apply the bank's gain
            chain = ','.join(x for x in [filt, f'volume={-4.5 - peak_db(f, filt, o.get('dur')) + g:.2f}dB'] if x)
            enc(f, os.path.join(out, f'{bank}_{i}.mp3'), chain, bitrate='96k' if o.get('stereo') else '48k',
                mono=not o.get('stereo'), maxdur=o.get('dur'), fade_out=o.get('fade', 0.03 if o.get('dur') else 0))
            n += 1
    return n

def build_beds():
    out = os.path.join(OUT, 'amb')
    shutil.rmtree(out, ignore_errors=True)
    os.makedirs(out)
    for name, (spec, filt, dur, xf) in AMB.items():
        src = find(spec)[0]
        tmp = f'/tmp/_bed_{name}.wav'
        # equal-power crossfade of the tail onto the head so the loop point is inaudible
        full = ['ffmpeg', '-v', 'error', '-y', '-i', src, '-t', str(dur), '-ac', '1', '-ar', '44100']
        chain = ','.join(x for x in [filt, 'loudnorm=I=-24:TP=-3:LRA=11'] if x)
        subprocess.run(full + ['-af', chain, tmp], check=True)
        # simpler & robust: output = (file[xf:] ) with its last xf seconds crossfaded into file[0:xf]
        real = float(subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', tmp]))
        fc = (f'[0:a]asplit=3[s1][s2][s3];'
              f'[s1]atrim=start={xf}:end={real - xf},asetpts=PTS-STARTPTS[a];'
              f'[s2]atrim=start={real - xf},asetpts=PTS-STARTPTS[b];'
              f'[s3]atrim=0:{xf},asetpts=PTS-STARTPTS[head];'
              f'[b][head]acrossfade=d={xf}:c1=qsin:c2=qsin[j];[a][j]concat=n=2:v=0:a=1[o]')
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', tmp, '-filter_complex', fc, '-map', '[o]',
                        '-ar', '44100', '-codec:a', 'libmp3lame', '-b:a', '48k', os.path.join(out, f'{name}.mp3')], check=True)
        os.remove(tmp)

if __name__ == '__main__':
    only = sys.argv[2] if len(sys.argv) > 2 else 'all'
    if only in ('all', 'sfx'):
        print('sfx files:', build_oneshots(SFX, 'sfx'))
        print('accent files:', build_oneshots(ACCENT, 'accent'))
    if only in ('all', 'beds'):
        build_beds()
        print('beds:', len(AMB))
