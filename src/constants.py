# Audio Configuration
SAMPLE_RATE = 44100
CHUNK_SIZE = 1024  # Buffer size for PyAudio
FORMAT_WIDTH = 2   # 16-bit audio
CHANNELS = 1       # Mono input

# Equalizer Bands (Center Frequencies) — Standard 10-band
EQ_BANDS = [31, 62, 125, 250, 500, 1000, 2000, 4000, 8000, 16000]
Q_FACTOR = 1.414   # Bandwidth control (~1 octave)

# Visualization
FFT_BINS = CHUNK_SIZE // 2
MIN_FREQ = 20
MAX_FREQ = 22000
MIN_DB = -80
MAX_DB = 10

# Presets: name -> list of dB gains, one per EQ_BAND
EQ_PRESETS = {
    "Flat":         [ 0,  0,  0,  0,  0,  0,  0,  0,  0,  0],
    "Bass Boost":   [ 8,  7,  5,  2,  0,  0,  0,  0,  0,  0],
    "Treble Boost": [ 0,  0,  0,  0,  0,  0,  2,  4,  6,  8],
    "V-Shape":      [ 6,  5,  2,  0, -2, -2,  0,  2,  5,  6],
    "Vocal":        [-2, -2,  0,  3,  5,  5,  3,  1,  0, -1],
}
