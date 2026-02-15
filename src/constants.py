# Audio Configuration
SAMPLE_RATE = 44100
CHUNK_SIZE = 1024  # Buffer size for PyAudio
FORMAT_WIDTH = 2   # 16-bit audio
CHANNELS = 1       # Mono input

# Equalizer Bands (Center Frequencies)
EQ_BANDS = [60, 250, 1000, 4000, 8000, 16000]
Q_FACTOR = 1.414   # Bandwidth control

# Visualization
FFT_BINS = CHUNK_SIZE // 2
MIN_FREQ = 20
MAX_FREQ = 22000
MIN_DB = -80
MAX_DB = 0
