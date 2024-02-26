r"""
 _______                          __               __   
|   _   |.----.----.-----.----.--|  |.---.-.-----.|  |_ 
|       ||  __|  __|  _  |   _|  _  ||  _  |     ||   _|
|___|___||____|____|_____|__| |_____||___._|__|__||____|
                                                        
             _______        __                          
            |    ___|.----.|  |--.-----.                
            |    ___||  __||     |  _  |                
            |_______||____||__|__|_____|     

Algorithmic Music Generation

Patchbay for the Polysynth

Be careful, this updates the synth live (as soon as you save it); I recommend an external
limiter to prevent potential audio equipment or hearing damage, the presets here should be
pretty safe, though.
"""
import math
import random

import numpy as np

ATTACK = 10
DECAY = 10
SUSTAIN = 1
RELEASE = 10


def sin(t, note, mul):
    """Generate a sine wave."""
    return (np.sin(t * math.pi * note[0] * mul)) * note[1] * 0.5


def saw(t, note, mul):
    """Generate a sawtooth wave."""
    return (((t * note[0] * mul) % 2) - 1) * note[1]


def sqr(t, note, mul):
    """Generate a square wave."""
    return ((((t * note[0] * mul) % 2) - 1) * 2).astype(int) * note[1]


def detune(fun, args, amount, spread):
    """Apply detuning to a given waveform."""
    return sum(
        fun(args[0], args[1], args[-1] + ((i / spread) * amount))
        for i in range(-spread, spread + 1)
    )


pvalue = None


def get_sin(t, note_list):
    global pvalue
    # TODO LFOs

    # Initialize
    value = np.zeros(t.shape)
    for idx, note in enumerate(note_list[:]):
        ##################################
        #            WAVEFORM            #
        ##################################

        ###################################
        # simple square wave
        value += sqr(t, note, 1) * 0.5
        ###################################
        # drawbar organ
        # value += sin(t, note, 1)
        # value += sin(t, note, 0.5)
        # value += sin(t, note, 2)

        ###################################
        # supersaw
        # value += detune(saw, (t, note, 1), 0.01, 2)
        ###################################

        ##################################
        #               FX               #
        ##################################

        # distortion
        # value = np.clip(value, -0.9, 0.9)

        ###################################
        #               ADSR              #
        ###################################

        # Release
        if not note[2]:
            note_list[idx][1] -= 1 / RELEASE
        # Attack
        # if growing and we're not at full volume
        elif note[3] and note[1] < 1:
            # increase volume
            note_list[idx][1] += 1 / ATTACK
        # if we're growing and we are at full volume
        elif note[3]:
            # stop growing
            note_list[idx][3] = False
        # Decay + Sustain
        # if we're not growing
        elif not note[3] and note[1] > SUSTAIN and DECAY:
            # decrease volume unless we are at sustain level
            note_list[idx][1] -= 1 / DECAY

        # keep things reasonable
        note_list[idx][1] = max(min(note_list[idx][1], 1.01), 0)

    value *= 0.5  # volume

    # attempt at low pass filter
    # value is a numpy array shape=(128,) (128 may vary)
    # pvalue is either None or the previous value

    if pvalue is not None:
        nvalue = np.append(value, pvalue)
        nvalue = moving_average(nvalue, 10)[value.shape[0] :]
    else:
        nvalue = value

    return nvalue, note_list


def moving_average(a, n=3):
    ret = np.cumsum(a, dtype=float)
    ret[n:] = ret[n:] - ret[:-n]
    return ret[n - 1 :] / n
