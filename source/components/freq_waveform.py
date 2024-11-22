import numpy as np
import pygame
import pyaudio
from scipy.fftpack import fft
from .button import Button
from .. import constants as c


class FreqButton(Button):
    def __init__(self, x, y, group=None, name=c.MAP_BUTTON):
        super().__init__(x, y, button_type="freq", group=group, name=name)
        self.recording = False
        self.points = []
        self.frequencies = []
        self.stream = None
        self.p = None

    def start_recording(self):
        if not self.recording:
            self.recording = True
            self.points = []
            self.frequencies = []
            self.p = pyaudio.PyAudio()
            self.stream = self.p.open(format=pyaudio.paInt16, channels=1, rate=c.RATE, input=True,
                                      frames_per_buffer=c.CHUNK)
            # Discard initial frames for stability
            for _ in range(5):
                self.stream.read(c.CHUNK)
            self.press()

    def stop_recording(self):
        if self.recording:
            self.release()
            if self.stream:
                self.stream.stop_stream()
                self.stream.close()
            if self.p:
                self.p.terminate()
            self.recording = False

    def process_audio_data(self):
        if not self.recording or not self.stream:
            return

        try:
            data = np.frombuffer(self.stream.read(c.CHUNK), dtype=np.int16) / 32768.0  # Normalize
            pitch = self.get_pitch(data)
            self.update_frequencies(pitch)
            self.update_points()
        except Exception as e:
            print(f"Error processing audio: {e}")

    def get_pitch(self, data):
        fft_data = fft(data)
        freqs = np.fft.fftfreq(len(fft_data), 1 / c.RATE)
        magnitude = np.abs(fft_data)
        peak_idx = np.argmax(magnitude)
        return abs(freqs[peak_idx])

    def update_frequencies(self, pitch):
        alpha = 0.03
        if self.frequencies:
            smoothed_pitch = alpha * pitch + (1 - alpha) * self.frequencies[-1]
        else:
            smoothed_pitch = pitch

        self.frequencies.append(smoothed_pitch)

        if len(self.frequencies) > c.SCREEN_WIDTH:
            self.frequencies.pop(0)

    def update_points(self):
        self.points.clear()
        for i, freq in enumerate(self.frequencies):
            x = i + self.rect.x
            y = c.SCREEN_HEIGHT - int((freq / 1500) * c.SCREEN_HEIGHT)  # Scale frequency
            self.points.append((x, y))
