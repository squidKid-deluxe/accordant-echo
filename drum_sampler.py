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

Drum Sampler

"""
import curses
import json
import os
import sys
import warnings
from statistics import mode

import numpy as np
import soundcard
from readchar import readchar
from scipy.io import wavfile

from rtmidi_utils import MidiPort

PATH = str(os.path.dirname(os.path.abspath(__file__))) + "/"
CHOP_SIZE = 256


def load_samples(drumkits, kit_number):
    """
    Load drum samples from the specified drumkit.

    Args:
        drumkits (list): List of available drumkit names.
        kit_number (int): Index of the selected drumkit.

    Returns:
        tuple: A tuple containing the loaded samples and the sample rate.
    """
    kit_path = os.path.join(PATH, "drumkits", drumkits[kit_number])
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        # Load all samples from the selected drumkit
        samples = {
            i.split(".")[0]: wavfile.read(os.path.join(kit_path, i))
            for i in sorted(os.listdir(kit_path))
        }

    # Determine the most common sample rate among the loaded samples
    sample_rate = mode([i[0] for i in samples.values()])

    # Extract the audio data from the loaded samples
    samples = {k: v[1] for k, v in samples.items()}

    # sort the samples to be in the same arder as they would be on an 808
    samples = [
        samples.get("kick", None),
        samples.get("snare", None),
        samples.get("lowtom", None),
        samples.get("tom", None),
        samples.get("hitom", None),
        samples.get("perc", None),
        samples.get("clap", None),
        samples.get("cowbell", None),
        samples.get("crash", None),
        samples.get("openhat", None),
        samples.get("closedhat", None),
        None,
    ]

    new_samples = []
    # Normalize the samples and convert them to floating point format
    for sample in samples:
        if sample is None:
            new_samples.append(None)
        elif sample.dtype == np.int32:
            new_samples.append(sample.astype(float) / 2147483647)
        elif sample.dtype == np.int16:
            new_samples.append(sample.astype(float) / 65535)
        elif sample.dtype == float:
            new_samples.append(sample)
        else:
            # Unsupported type
            new_samples.append(None)

    return new_samples, sample_rate


def main():
    """
    Main function to run the drum sampler.
    """
    # Initialize MIDI input port
    in_port = MidiPort("Python Drum Sampler", "in", True if len(sys.argv) == 1 else sys.argv[1])
    # Initialize default speaker
    speaker = soundcard.default_speaker()
    # Get a list of available drumkits
    drumkits = sorted(os.listdir(os.path.join(PATH, "drumkits")))
    print("\033c")  # Clear the screen
    print(json.dumps(dict(enumerate(drumkits)), indent=4))  # Print available drumkits
    kit_number = int(input("Select drumkit id: "))  # Prompt user to select a drumkit

    # Load samples for the selected drumkit
    samples, sample_rate = load_samples(drumkits, kit_number)
    playing = []

    # Initialize curses for keyboard input
    stdscr = curses.initscr()
    curses.noecho()
    curses.cbreak()
    stdscr.keypad(True)
    stdscr.nodelay(True)
    try:
        # Discard any pending MIDI messages
        for msg in in_port.iter_pending():
            pass
        # Start processing MIDI messages and playing sounds
        with speaker.player(samplerate=sample_rate, blocksize=512) as spk:
            while True:
                # Check for new MIDI messages
                for msg in in_port.iter_pending():
                    # Add notes to be played based on received MIDI messages
                    if msg.type == "note_on" and samples[msg.note % 12] is not None:
                        playing.append([msg.note % 12, CHOP_SIZE])
                # Initialize buffer for playing sounds
                play_buffer = np.zeros_like(samples[0][:CHOP_SIZE]).astype(float)
                kill = []
                # Generate audio buffer based on currently playing notes
                for idx, note in enumerate(playing):
                    try:
                        sample_chunk = samples[note[0]][note[1] : note[1] + CHOP_SIZE]
                        play_buffer += np.pad(
                            sample_chunk,
                            (0, CHOP_SIZE - sample_chunk.shape[0]),
                            "constant",
                            constant_values=(0),
                        )
                        if playing[idx][1] > samples[note[0]].shape[0]:
                            kill.append(idx)
                        playing[idx][1] += CHOP_SIZE
                    except TypeError:
                        kill.append(idx)
                # Remove finished notes from the list of playing notes
                for i in kill:
                    playing[i] = 0
                playing = [i for i in playing if i]
                # Play the generated audio buffer
                spk.play(play_buffer)
                # Check for keyboard input to switch drumkits
                if 47 < (kit := stdscr.getch()) < 57:
                    samples, _ = load_samples(drumkits, kit - 48)
    except KeyboardInterrupt:
        pass
    finally:
        # Clean up curses
        curses.nocbreak()
        stdscr.keypad(False)
        curses.echo()
        curses.endwin()


if __name__ == "__main__":
    main()
