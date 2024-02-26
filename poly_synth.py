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


Create a live programming sound server that can be interacted with from another file
"""

import math
import os
import struct
import sys
from importlib import reload

import numpy as np
import soundcard as sc

import rtmidi_utils
import synth_patchbay

# First 4 bits of status byte:
NOTEON = 0x9
NOTEOFF = 0x8
DSP_WAVE_TXT = ""

BLOCKS = 32
BATCH = 256


NOT_VALID_BANNER = "\n" + "#" * 26 + "\n# Your code is not valid #\n" + "#" * 26 + "\n"


def midi_to_freq(midi):
    """
    Convert a MIDI note number to its corresponding frequency.

    The formula used to convert a MIDI note to frequency is based on the formula:
    frequency = (440 / 32) * (2 ** ((midi - 9 + 12) / 12))
    where:
    - 440 is the reference frequency for A4
    - 32 is a constant that adjusts the scale
    - (midi - 9 + 12) is used to shift the MIDI range to match the desired reference note (A4)
    - 2 ** ((midi - 9 + 12) / 12) calculates the power of 2 to determine the frequency ratio
    """

    return 13.75 * (2 ** ((midi + 3) / 12))


def check_mod_reload(exception=False):
    """
    Check if the "synth_patchbay" module has changed and, if so, reload the module.
    """

    global DSP_WAVE_TXT

    # Read the content of "synth_patchbay.py" file
    with open("synth_patchbay.py", encoding="utf-8") as handle:
        data = handle.read()
        handle.close()

    # Compare the content of "synth_patchbay.py" with the existing content
    # in the DSP_WAVE_TXT global variable
    if data != DSP_WAVE_TXT:
        try:
            # Reload the "synth_patchbay" module
            reload(synth_patchbay)
            if exception:
                raise exception

            # If NOT_VALID_BANNER is present in the new data,
            # remove it and update the "synth_patchbay.py" file
            if NOT_VALID_BANNER in data:
                with open("synth_patchbay.py", "w", encoding="utf-8") as handle:
                    handle.write(data.replace(NOT_VALID_BANNER, ""))
                    handle.close()

        except Exception as error:
            print("invalid code")
            # If a Error occurs during module reload,
            # append NOT_VALID_BANNER to "synth_patchbay.py" to mark it as not valid
            with open("synth_patchbay.py", "a", encoding="utf-8") as handle:
                handle.write(NOT_VALID_BANNER)
                handle.close()
            data += NOT_VALID_BANNER

    # Update the DSP_WAVE_TXT global variable with the new data
    DSP_WAVE_TXT = data


def main():
    """
    Main function that initializes audio and MIDI processing and supervies the full process.
    """
    print("Enter your password for real-time priority:")
    # auto-renice to increase process priority
    os.system(f"sudo renice -n -20 -p {os.getpid()}")
    print("\033c")

    port = rtmidi_utils.MidiPort(
        "Python Polyphonic Synth", "in", True if len(sys.argv) == 1 else sys.argv[1]
    )

    # Get the default speaker
    default_speaker = sc.default_speaker()

    # Start the audio player with the specified sample rate and block size
    with default_speaker.player(samplerate=48000, blocksize=BLOCKS, channels=1) as spk:
        time = 0
        note_list = []
        print("\033cRunning...\n")
        exception = False
        while True:
            for msg in port.iter_pending():
                if msg.type == "note_on":
                    # Append a new entry to the note_list with frequency,
                    # volume press status, and growing status
                    note_list.append([int(midi_to_freq(msg.note)), 0, True, True])
                elif msg.type == "note_off":
                    # Update the growing status to False for the matching entry in the note_list
                    for idx, entry in enumerate(note_list):
                        if entry[0] == int(midi_to_freq(msg.note)) and entry[2]:
                            note_list[idx][2] = False

            # uncomment to show latency in the terminal
            # print("\033[ASpeaker latency:", spk.latency)

            # Every 10 iterations, check if the "synth_patchbay" module needs to be reloaded
            if time % 100 == 0:
                check_mod_reload(exception)
                exception = False

            # Generate audio samples using the "synth_patchbay" module
            # and play them through the speaker
            try:
                audio, note_list = synth_patchbay.get_sin(
                    (np.arange(BATCH, dtype=float) + time) / 48000, note_list
                )
            except exception:
                pass
            spk.play(audio)

            # Remove entries from note_list list where volume is 0 and growing status is False
            note_list = [i for i in note_list if i[1] != 0 or i[2]]

            time += BATCH


if __name__ == "__main__":
    main()
