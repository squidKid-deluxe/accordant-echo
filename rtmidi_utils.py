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

Simple rtmidi wrapper

"""


import rtmidi
import rtmidi.midiutil


class MidiMessage:
    """
    Represents a MIDI message.
    Placeholder class for easier compatibility with the mido module
    """

    def __init__(self, data):
        """
        Initialize MidiMessage object.

        Args:
            data (list): List representing MIDI message data.
        """
        self.data = data
        self.type = {
            0x90: "note_on",
            0x80: "note_off",
        }.get(data[0], "unknown")
        self.note = data[1]
        self.vel = data[2]


class MidiPort:
    """Represents a MIDI port."""

    def __init__(self, name, direction, connect=None):
        """
        Initialize MidiPort object.

        Args:
            name (str): Name of the MIDI port, will be passed to rtmidi.
            direction (str): Direction of the MIDI port, either 'in' or 'out'.
            connect (str/bool, optional): Connection port number, None for virtual port,
                or True for UI connection.

        Raises:
            ValueError: If port direction or connection point is invalid
        """
        self.name = name
        self.direction = direction
        self.msgs = []

        assert self.direction in ["in", "out"], ValueError(
            f"Direction must be either 'in' or 'out', got '{self.direction}'"
        )

        if self.direction == "in":
            self.port = rtmidi.MidiIn()
            if connect == True:
                rtmidi.midiutil.list_input_ports()
                connect = input("    Enter to create virtual port\n\n? ")
            if connect is None:
                self.port.open_virtual_port(name=self.name)
            elif str(connect).isdigit():
                self.port.open_port(int(connect), name=self.name)
            else:
                raise ValueError("Invalid connection port, must be integer")
            self.port.set_callback(self._callback)
        else:
            if connect == True:
                rtmidi.midiutil.list_output_ports()
                connect = input("? ")
            self.port = rtmidi.MidiOut()
            if connect is None:
                self.port.open_virtual_port(name=self.name)
            elif str(connect).isdigit():
                self.port.open_port(int(connect), name=self.name)
            else:
                raise ValueError("Invalid connection port, must be integer")

    def _callback(self, data, _):
        """Internal callback function for MIDI input."""
        self.msgs.append(data[0])

    def iter_pending(self):
        """Iterator for pending MIDI messages."""
        for _ in self.msgs[:]:
            yield MidiMessage(self.msgs.pop(0))

    def send(self, msg):
        """
        Send a MIDI message.

        Args:
            msg (list): MIDI message to be sent.

        Raises:
            AttributeError: If trying to send data to an 'in' port.
            ValueError: If the MIDI message is invalid.
        """
        assert self.direction == "out", AttributeError("Cannot send data to 'in' port.")
        if len(msg) == 3 and all(isinstance(i, (int, float)) for i in msg):
            self.port.send_message([int(i) for i in msg])
        else:
            raise ValueError("Invalid midi message, use list of three numbers")
        # FIXME add more types of acceptable messages
