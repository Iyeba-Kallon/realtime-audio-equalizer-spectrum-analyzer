import numpy as np
from scipy.signal import sosfilt, sosfreqz
from speqtr.constants import SAMPLE_RATE, CHUNK_SIZE

# Normalization factor: converts raw int16 amplitudes to [-1.0, 1.0] range
_INT16_MAX = 32768.0


class DSP:
    def __init__(self):
        self.filters = {}  # band_freq -> SOS coefficients
        self.gains = {}    # band_freq -> dB gain
        self.zi = {}       # band_freq -> filter state (for continuity between chunks)

    # ------------------------------------------------------------------
    # Filter design
    # ------------------------------------------------------------------

    def design_peaking_eq(self, f0, db_gain, Q, fs):
        """
        Design a digital peaking EQ filter (RBJ Audio EQ Cookbook).
        Returns a single SOS section: [[b0, b1, b2, 1.0, a1, a2]].
        """
        A = 10 ** (db_gain / 40.0)
        w0 = 2 * np.pi * f0 / fs
        alpha = np.sin(w0) / (2 * Q)
        cos_w0 = np.cos(w0)

        b0 = 1 + alpha * A
        b1 = -2 * cos_w0
        b2 = 1 - alpha * A
        a0 = 1 + alpha / A
        a1 = -2 * cos_w0
        a2 = 1 - alpha / A

        return np.array([[b0 / a0, b1 / a0, b2 / a0, 1.0, a1 / a0, a2 / a0]])

    # ------------------------------------------------------------------
    # Filter management
    # ------------------------------------------------------------------

    def create_filters(self, bands, Q=1.414):
        """Initialise all band filters at 0 dB (flat response)."""
        for band in bands:
            self.update_gain(band, 0.0, Q)

    def update_gain(self, band_freq, gain_db, Q):
        """Recompute filter coefficients for *band_freq* with new *gain_db*."""
        self.gains[band_freq] = gain_db
        self.filters[band_freq] = self.design_peaking_eq(band_freq, gain_db, Q, SAMPLE_RATE)

        if band_freq not in self.zi:
            self.zi[band_freq] = np.zeros((1, 2))

    # ------------------------------------------------------------------
    # Processing
    # ------------------------------------------------------------------

    def process_audio(self, audio_data):
        """
        Apply all active peaking filters in series to *audio_data*.
        Accepts int16 ndarray; returns float32 ndarray (normalised to [-1, 1]).
        """
        processed = audio_data.astype(np.float32) / _INT16_MAX

        for band_freq, sos in self.filters.items():
            processed, z_out = sosfilt(sos, processed, zi=self.zi[band_freq])
            self.zi[band_freq] = z_out

        return processed

    # ------------------------------------------------------------------
    # Analysis
    # ------------------------------------------------------------------

    def compute_fft(self, audio_data):
        """
        Compute the magnitude spectrum of *audio_data* (float32, [-1, 1]).
        Returns (frequencies, magnitude_db).
        """
        n = len(audio_data)
        window = np.hanning(n)
        windowed = audio_data * window

        fft_out = np.fft.rfft(windowed)
        freqs = np.fft.rfftfreq(n, 1.0 / SAMPLE_RATE)

        # Compensate for the Hanning window power loss (sum of window / n)
        window_gain = np.sum(window) / n
        magnitude = np.abs(fft_out) / (n * window_gain + 1e-12)
        magnitude_db = 20 * np.log10(magnitude + 1e-9)

        return freqs, magnitude_db

    def compute_eq_curve(self, freqs):
        """
        Calculate the combined frequency response (dB) of all stacked filters
        at the given *freqs* array.  Used for the EQ overlay on the spectrum plot.
        """
        if not self.filters:
            return np.zeros_like(freqs)

        # Start with unity response
        h_combined = np.ones(len(freqs), dtype=complex)

        for sos in self.filters.values():
            _, h = sosfreqz(sos, worN=freqs, fs=SAMPLE_RATE)
            h_combined *= h

        return 20 * np.log10(np.abs(h_combined) + 1e-9)
