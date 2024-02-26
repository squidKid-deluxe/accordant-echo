
# Accordant Echo

This repository contains a collection of Python scripts for algorithmic music generation and software synthesis. These scripts utilize various techniques to generate music algorithmically, ranging from drum sampling to live programming synthesizer creation.

## Scripts

### 1. `gen_beat.py`

This script implements an algorithmic music generation algorithm based on MIDI input. It utilizes a set of rules and probabilities to generate musical sequences, providing a flexible framework for creating algorithmic compositions.

### 2. `synth_patchbay.py`

The `synth_patchbay` script serves as a patchbay for the polysynth, allowing users to interactively create and modify synth patches in real-time. It provides a programmer friendly interface for tweaking parameters and exploring different sound textures.

### 3. `poly_synth.py`

This script sets up a live programming sound server that can be interacted with from `synth_patchbay.py`. It enables users to dynamically generate and manipulate polyphonic sound patterns using live coding techniques, fostering experimentation and creativity.

### 4. `rtmidi_utils.py`

The `rtmidi_utils` script provides a simple wrapper similar to the mido library for working with MIDI input and output using the `rtmidi` library. It offers convenient abstractions for handling MIDI messages and ports, making it easier to integrate MIDI functionality into Python projects.

### 5. `drum_sampler.py`

The `drum_sampler` script implements a polyphonic drum sampler that allows users to play drum sounds read from the appropriate folder using MIDI input. It supports real-time interaction for playing and switching between different drum kits, providing a versatile tool for creating rhythmic patterns.

## Usage

To use these scripts, simply download or clone the repository to your local machine. Ensure that you have Python3.8+ installed, along with the necessary dependencies specified in the `requirements.txt` file. You can then run each script individually using Python (excepting `rtmidi_utils`, which is just a library).  Running `poly_synth.py` or `drum_sampler.py`, creating a virtual port in either (or both) allows you to connect to them via JACK (with a2j) or ALSA, which in turn enables you to connect them to a MIDI device, a DAW, or, if you run `gen_beat.py`, algorithmic beats!

## Contributing

If you find any issues or have suggestions for improvements, feel free to open an issue or submit a pull request. Contributions are welcome!
