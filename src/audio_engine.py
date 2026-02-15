import pyaudio
import numpy as np
import threading
import time
from .constants import SAMPLE_RATE, CHUNK_SIZE, FORMAT_WIDTH, CHANNELS, EQ_BANDS, Q_FACTOR
from .dsp import DSP

class AudioEngine:
    def __init__(self):
        self.p = pyaudio.PyAudio()
        self.stream = None
        self.dsp = DSP()
        self.is_running = False
        self.audio_data = np.zeros(CHUNK_SIZE) # Raw/Processed audio for display
        
        # Initialize filters
        self.dsp.create_filters(EQ_BANDS, Q_FACTOR)

    def start_stream(self):
        if self.stream is not None and self.stream.is_active():
            return

        self.stream = self.p.open(
            format=pyaudio.paInt16,
            channels=CHANNELS,
            rate=SAMPLE_RATE,
            input=True,
            frames_per_buffer=CHUNK_SIZE,
            stream_callback=self._audio_callback
        )
        self.is_running = True
        self.stream.start_stream()

    def stop_stream(self):
        if self.stream is not None:
            self.stream.stop_stream()
            self.stream.close()
            self.stream = None
        self.is_running = False

    def close(self):
        self.stop_stream()
        self.p.terminate()

    def _audio_callback(self, in_data, frame_count, time_info, status):
        # Convert byte data to numpy array
        audio_data = np.frombuffer(in_data, dtype=np.int16)
        
        # Process audio with DSP (Equalizer)
        # Note: We are processing inplace/copying in DSP. 
        # For visualization, we want to see the effect of the EQ.
        processed_data = self.dsp.process_audio(audio_data, EQ_BANDS)
        
        # Store for GUI to read
        # Using a lock if necessary, but for simple visualization, 
        # atomic write of reference or just overwriting is often acceptable for 30fps
        # We'll normalize for display here to avoid doing it in GUI
        self.audio_data = processed_data
        
        # If we were playing back audio, we would return (processed_data.tobytes(), pyaudio.paContinue)
        # But this is just an analyzer/viz tool, so we return the input or silence to output (if output was active).
        # Since this is Input-only stream, return value is ignored for output, but required for continuation.
        return (in_data, pyaudio.paContinue)

    def get_audio_data(self):
        """
        Returns the latest processed audio data and its FFT.
        """
        data = self.audio_data
        freqs, magnitude_db = self.dsp.compute_fft(data)
        return data, freqs, magnitude_db

    def set_band_gain(self, band_idx, gain_db):
        if 0 <= band_idx < len(EQ_BANDS):
            freq = EQ_BANDS[band_idx]
            self.dsp.update_gain(freq, gain_db, Q_FACTOR)
