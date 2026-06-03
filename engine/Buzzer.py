from .PWM import PWM
from math import e
from time import sleep

NOTE_FREQS = {
    'C':  261.63,
    'C#': 277.18, 'Db': 277.18,
    'D':  293.66,
    'D#': 311.13, 'Eb': 311.13,
    'E':  329.63,
    'F':  349.23,
    'F#': 369.99, 'Gb': 369.99,
    'G':  392.00,
    'G#': 415.30, 'Ab': 415.30,
    'A':  440.00,
    'A#': 466.16, 'Bb': 466.16,
    'B':  493.88,
}
note_map = {
    'C': 'C', 'C#': 'C#', 'DB': 'C#',
    'D': 'D', 'D#': 'D#', 'EB': 'D#',
    'E': 'E',
    'F': 'F', 'F#': 'F#', 'GB': 'F#',
    'G': 'G', 'G#': 'G#', 'AB': 'G#',
    'A': 'A', 'A#': 'A#', 'BB': 'A#',
    'B': 'B',
}
def volume2duty(volume):
    return (volume ** e / 2)

class Buzzer(PWM):
    def __init__(self, pin = 12):
        super().__init__(pin)
        self._volume = 0.5
        self.freq(560)

    def volume(self, volume=None):
        if volume is None:
            return self._volume
        if not 0 <= volume <= 1.0:
            raise ValueError("Volume must be between 0 and 1.0")
        self._volume = volume
        duty = volume ** e
        self.duty(duty / 2)

    def make_sound(self, freq, volume, duration):
        self.freq(int(freq))
        self.duty(volume2duty(volume))
        sleep(duration)
        self.duty(0)

    def beep(self):
        self.make_sound(1000, self._volume, 0.1)
    
    def boop(self):
        self.make_sound(500, self._volume, 0.1)
        
    def on(self):
        self.volume(self._volume)

    def off(self):
        self.duty(0)

    def note_to_freq(self, note: str) -> float:
        note = note.strip().upper()
        
        # Если есть октава в конце
        if note[-1].isdigit():
            octave = int(note[-1])
            note_name = note[:-1]
        else:
            octave = 4
            note_name = note


        if note_name not in note_map:
            raise ValueError(f"Unkwown note: {note_name}")

        standard_note = note_map[note_name]
        base_freq = NOTE_FREQS[standard_note]
        
        return base_freq * pow(2, octave - 4)

    def play_note(self, note: str, volume=None, duration=0.5):
        if volume is None:
            volume = self._volume
        
        freq = self.note_to_freq(note)
        self.make_sound(freq, volume, duration)

    def play_melody(self, melody, tempo=0.3):
        for note in melody:
            self.play_note(note, duration=tempo)
            sleep(tempo * 0.1)
