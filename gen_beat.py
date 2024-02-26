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

"""
import math
import random
import sys
import time
from copy import deepcopy
from threading import Thread

import numpy as np

import rtmidi_utils

SEED = int(time.time())

random.seed(SEED)

# Configuration settings
CONFIG = {
    "tempo": 4000,
    "repeat": 20,
    "mutate": 0.5,
    "darkness": 1,
    "swing": 2,
    "swing_length": 4,
    "fadeout": 0.95,
}

SKIP = 3, 2, 1, 1, 3, 2


# Define frequency and phase information for different drum sounds
FREQUENCY = {
    "bass": [4, 0],
    "snare": [2, 0],
    "low tom": [2, 1],
    "mid tom": [4, 2],
    "high tom": [2, 3],
    "rim shot": [4, 0],
    "clap": [2, 6],
    "cowbell": [2, 2],
    "cymbal": [1, 8],
    "open hat": [1, 0],
    "closed hat": [8, 1],
}


def calculate_sleep_duration(idx: int) -> float:
    """
    Calculate sleep duration with swing.

    :param idx: Current position in the loop.
    :return: Sleep duration.
    """
    beat_duration = (1 / CONFIG["tempo"]) * 15

    # if idx % 2 == 0:  # Even positions (downbeats)
    #     return beat_duration
    # else:  # Odd positions (upbeats)
    #     return beat_duration * (1 + CONFIG["swing"])

    # return beat_duration * (1 + CONFIG["swing"]*(1/(idx%CONFIG["swing_length"]+0.1)))

    return beat_duration * (1 + CONFIG["swing"]) ** (((idx % CONFIG["swing_length"]) + 1))


def play_loop(port: rtmidi_utils.MidiPort, buffer: dict) -> None:
    """
    Play a loop of MIDI notes with swing.

    :param port: MIDI output port.
    :param buffer: Dictionary containing musical notes information.
    """
    idx = 0
    playing = []

    print("Playing...")

    while not buffer["kill"]:
        start = time.time()

        # Stop playing the previous notes
        for note in playing:
            port.send([0x80, note, 0])
        playing = []

        # Play the current set of notes
        for note, vel in enumerate(
            buffer["notes"][idx]
            if idx < len(buffer["notes"])
            else buffer["pnotes"][len(buffer["pnotes"]) // 2][idx - 16]
        ):
            if vel:
                note = scale(note)
                port.send([0x90, note, 100])
                playing.append(note)

        idx += 1
        if idx >= len(buffer["notes"]) * 2:
            idx = 0

        print("\033c")
        print("Seed:", SEED)
        render(transpose(buffer["notes"]), min(idx, 15))
        render(transpose(buffer["pnotes"][len(buffer["pnotes"]) // 2]), max(idx - 16, 0) % 16)

        sl = max(calculate_sleep_duration(idx) - (time.time() - start), 0)
        print(sl)
        time.sleep(sl)

    # Stop playing the remaining notes when the loop ends
    for note in playing:
        port.send([0x80, note, 0])


def scale(note):
    if "blues" in sys.argv:
        pitch = 48
        for idx in range(note):
            pitch += SKIP[idx % 6]
        return pitch
    return 60 + note


def zeros(shape: tuple) -> list:
    """
    Generate a nested list of zeros with the specified shape.

    :param shape: Tuple representing the shape of the list.
    :return: Nested list of zeros.
    """
    if len(shape) == 1:
        return [0 for _ in range(shape[0])]
    return [zeros(shape[1:]) for _ in range(shape[0])]


def transpose(mat: list) -> list:
    """
    Transpose a matrix.

    :param mat: Input matrix.
    :return: Transposed matrix.
    """
    newmat = [[] for _ in mat[0]]
    for rdx, row in enumerate(mat):
        for cdx, col in enumerate(row):
            newmat[cdx].append(col)
    return newmat


def render(notes: list, pos: int) -> None:
    """
    Render the musical notes on the console.

    :param notes: List representing the musical notes.
    :param pos: Current position in the loop.
    """
    text = ""
    for row in notes:
        for cdx, col in enumerate(row):
            text += (
                f"\033[48;5;{int(((col / 127)*23)+232)}m"
                + ("  " if cdx != pos else "| ")
                + "\033[m"
            )
        text += "\n"
    print(text)


def prob_from_harmonic(harmonic: tuple, n_values: int = 1000) -> list:
    """
    Generate a probability distribution from a harmonic.

    :param harmonic: Tuple containing harmonic and phase information.
    :param n_values: Number of values in the distribution (default is 1000).
    :return: List representing the probability distribution.
    """
    harmonic, phase = harmonic
    probs = []
    for x in range(16):
        probs.append(math.sin(((math.pi * 2) * harmonic) * (((x + phase) % 16) / 16)) + 1.2)
    probs = [i / max(probs) for i in probs]
    sample_list = []
    for i in range(16):
        sample_list.extend([i] * int(probs[i] * n_values))
    return sample_list


def mul(arr, value):
    newarr = []
    for row in arr:
        newarr.append([])
        for col in row:
            v = col * value
            newarr[-1].append(v if v > 10 else 0)
    return newarr


def main() -> None:
    """
    Main function to run the MIDI note generation program.
    """
    print("\033c")

    buffer = {
        "kill": False,
        "notes": zeros((16, 11)),
        "pnotes": [zeros((16, 11))],
    }
    port = rtmidi_utils.MidiPort("Python Generative Beats", "out", True)

    # Generate samples based on harmonic information
    samples = list(map(prob_from_harmonic, FREQUENCY.values()))

    # Start a separate thread to play the generated notes
    play_thread = Thread(
        target=play_loop,
        args=(port, buffer),
        daemon=True,
    )
    play_thread.start()

    try:
        while True:
            buffer["notes"] = mul(buffer["notes"], CONFIG["fadeout"])
            note = random.randint(0, 10)
            pos = random.choice(samples[note])
            buffer["notes"][pos][note] = (random.random() < CONFIG["darkness"]) * 127
            buffer["pnotes"].append(deepcopy(buffer["notes"]))

            # Maintain buffer size
            if len(buffer["pnotes"]) > CONFIG["repeat"] * 2:
                buffer["pnotes"].pop(0)

            time.sleep(CONFIG["mutate"])

    except KeyboardInterrupt:
        # the ^C from the signal will complete this message; i.e. ^Cleaning up^
        print("leaning up^")

    finally:
        buffer["kill"] = True
        play_thread.join()


if __name__ == "__main__":
    main()
