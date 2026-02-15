import numpy as np
from scipy.signal import iirpeak, sosfilt
from .constants import SAMPLE_RATE, CHUNK_SIZE

class DSP:
    def __init__(self):
        self.filters = {} # Dictionary to store filter coefficients for each band
        self.gains = {}   # Dictionary to store current gain for each band (in dB)
        self.zi = {}      # Dictionary to store filter state (zi) for each band to prevent clicks

    def create_filters(self, bands, Q=1.414):
        """
        Initializes the filters for all bands with 0dB gain (flat response).
        """
        for band in bands:
            self.update_gain(band, 0.0, Q)

    def design_peaking_eq(self, f0, db_gain, Q, fs):
        """
        Design a digital peaking filter (RBJ Audio EQ Cookbook).
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
        
        # Normalize by a0 and return as SOS section
        # SOS format: [b0, b1, b2, a0, a1, a2]
        return np.array([[b0/a0, b1/a0, b2/a0, 1.0, a1/a0, a2/a0]])

    def update_gain(self, band_freq, gain_db, Q):
        """
        Updates the filter coefficients for a specific band based on new gain.
        """
        self.gains[band_freq] = gain_db
        # Filter is designed for the band center freq
        self.filters[band_freq] = self.design_peaking_eq(band_freq, gain_db, Q, SAMPLE_RATE)
        
        # Initialize filter state if not exists
        if band_freq not in self.zi:
            # sosfilt state shape is (n_sections, 2)
            self.zi[band_freq] = np.zeros((1, 2))

    def process_audio(self, audio_data, bands):
        """
        Applies all active filters to the audio data in series.
        """
        if not bands:
            return audio_data

        processed_data = audio_data.astype(np.float32)
        
        # Apply filters in series
        for band in bands:
            if band in self.filters:
                sos = self.filters[band]
                # Apply filter, update state
                # Note: zi must be updated in place or re-assigned
                processed_data, z_out = sosfilt(sos, processed_data, zi=self.zi[band])
                self.zi[band] = z_out
                
        return processed_data

    def compute_fft(self, audio_data):
        """
        Computes the FFT of the audio data.
        Returns frequencies and magnitude in dB.
        """
        # Windowing
        window = np.hanning(len(audio_data))
        windowed_data = audio_data * window
        
        # FFT
        fft_out = np.fft.rfft(windowed_data)
        freqs = np.fft.rfftfreq(len(windowed_data), 1/SAMPLE_RATE)
        
        # Magnitude in dB
        magnitude = np.abs(fft_out)
        magnitude_db = 20 * np.log10(magnitude + 1e-9) # Add small epsilon to avoid log(0)
        
        return freqs, magnitude_db
