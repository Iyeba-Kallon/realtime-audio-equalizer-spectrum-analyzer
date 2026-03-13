# Real-time Audio Equalizer & Spectrum Analyzer

A professional-grade, high-fidelity audio analysis and equalization tool built with Python. This application captures real-time audio input, processes it through a 10-band peaking equalizer, and provides live visualizations of both the waveform and frequency spectrum.

![App Preview](https://via.placeholder.com/800x600?text=Equalizer+App+Interface) <!-- Replace with actual screenshot when available -->

## ✨ Features

- **Professional 10-Band EQ**: Standardized bands (31Hz to 16kHz) with ±12dB gain control.
- **Accurate Spectrum Analysis**: Real-time FFT with proper dBFS normalization.
- **Visual Overlays**: 
  - **Live EQ Curve**: See exactly how your filters are shaping the audio.
  - **Peak Hold**: Tracks and decays from maximum peaks for better level monitoring.
- **Audio Presets**: Quick-access profiles like *Bass Boost*, *Treble Boost*, *V-Shape*, and *Vocal*.
- **Modern Dark UI**: Sleek, high-contrast interface designed for professional environments.
- **Thread-Safe Core**: Robust audio capturing using `PyAudio` and `threading` to ensure zero-flicker performance.

## 🛠️ Tech Stack

- **Language**: Python 3.10+
- **Audio Engine**: `PyAudio` (PortAudio wrapper)
- **DSP**: `NumPy` & `SciPy` (Signal processing)
- **GUI**: `Tkinter` (Themed with `ttk`)
- **Graphics**: `Matplotlib` (High-performance plotting)

## 🚀 Getting Started

### Prerequisites

You'll need Python installed. It is recommended to use a virtual environment.

### Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/Iyeba-Kallon/realtime-audio-equalizer-spectrum-analyzer.git
   cd realtime-audio-equalizer-spectrum-analyzer
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
   *Note: On some systems, you may need to install `portaudio` development headers separately (e.g., `sudo apt install libportaudio2` on Linux).*

### Running the App

Simply run the main script:
   ```bash
   python main.py
   ```

## 📖 How it Works

1. **Capture**: The `AudioEngine` opens a stream via `PyAudio` to capture system or microphone input.
2. **DSP Pipeline**:
   - Audio is converted to normalized `float32`.
   - Each EQ band is a second-order IIR peaking filter (RBJ design).
   - Filters are applied in series to the incoming chunks.
3. **Analysis**: An FFT (Fast Fourier Transform) is computed with a Hanning window to generate the magnitude spectrum.
4. **Visualization**: The GUI thread pulls the processed data through a thread-safe lock and updates the Matplotlib plots at ~30 FPS.

## 🤝 Contributing

Contributions are welcome! Feel free to open an issue or submit a pull request for new features (like recording, output playback, or more visualizer types).

## 📄 License

This project is licensed under the MIT License.
