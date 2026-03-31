import sounddevice as sd
import numpy as np
import threading
from constants import SAMPLE_RATE, CHUNK_SIZE, CHANNELS, EQ_BANDS, Q_FACTOR
from dsp import DSP


class AudioEngine:
    def __init__(self):
        self.stream = None
        self.dsp = DSP()
        self.is_running = False

        # Thread-safe audio buffer
        self._lock = threading.Lock()
        self._audio_data = np.zeros(CHUNK_SIZE, dtype=np.float32)

        # Initialise all EQ filters at flat response
        self.dsp.create_filters(EQ_BANDS, Q_FACTOR)

    # ------------------------------------------------------------------
    # Stream control
    # ------------------------------------------------------------------

    def start_stream(self):
        if self.stream is not None and self.stream.active:
            return

        self.stream = sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=CHANNELS,
            blocksize=CHUNK_SIZE,
            dtype='int16',
            callback=self._audio_callback,
        )
        self.is_running = True
        self.stream.start()

    def stop_stream(self):
        self.is_running = False
        if self.stream is not None:
            self.stream.stop()
            self.stream.close()
            self.stream = None

    def close(self):
        self.stop_stream()

    # ------------------------------------------------------------------
    # Audio callback (runs on sounddevice's internal thread)
    # ------------------------------------------------------------------

    def _audio_callback(self, indata, frames, time, status):
        raw = indata[:, 0]
        processed = self.dsp.process_audio(raw)          # normalised float32

        with self._lock:
            self._audio_data = processed

    # ------------------------------------------------------------------
    # Data access (called from the GUI / main thread)
    # ------------------------------------------------------------------

    def get_audio_data(self):
        """Return (waveform, freqs, magnitude_db) for the latest audio chunk."""
        with self._lock:
            data = self._audio_data.copy()

        freqs, magnitude_db = self.dsp.compute_fft(data)
        return data, freqs, magnitude_db

    def get_eq_curve(self, freqs):
        """Return the combined EQ frequency response in dB at *freqs*."""
        return self.dsp.compute_eq_curve(freqs)

    def set_band_gain(self, band_idx, gain_db):
        if 0 <= band_idx < len(EQ_BANDS):
            freq = EQ_BANDS[band_idx]
            self.dsp.update_gain(freq, gain_db, Q_FACTOR)

    @property
    def audio_data(self):
        """Legacy read-only accessor (thread-safe)."""
        with self._lock:
            return self._audio_data.copy()
