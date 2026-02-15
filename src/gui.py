import tkinter as tk
from tkinter import ttk
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from matplotlib import style

from .constants import EQ_BANDS, SAMPLE_RATE, CHUNK_SIZE, MIN_FREQ, MAX_FREQ, MIN_DB, MAX_DB

# Use a dark style for better aesthetics
style.use('dark_background')

class EqualizerApp:
    def __init__(self, root, audio_engine):
        self.root = root
        self.root.title("Real-time Audio Equalizer")
        self.root.geometry("1000x800")
        
        self.audio_engine = audio_engine
        self.sliders = []
        
        self._setup_ui()
        self._setup_plots()
        
        # Start update loop
        self.root.after(33, self.update_plots) # ~30 fps

    def _setup_ui(self):
        # Main Layout
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Control Panel (Top)
        control_panel = ttk.LabelFrame(main_frame, text="Controls", padding="5")
        control_panel.pack(fill=tk.X, side=tk.TOP, pady=5)
        
        ttk.Button(control_panel, text="Start Capture", command=self.audio_engine.start_stream).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_panel, text="Stop Capture", command=self.audio_engine.stop_stream).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_panel, text="Reset EQ", command=self.reset_eq).pack(side=tk.LEFT, padx=5)
        
        # Equalizer Sliders (Left)
        eq_frame = ttk.LabelFrame(main_frame, text="Equalizer", padding="10")
        eq_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5)
        
        for i, freq in enumerate(EQ_BANDS):
            frame = ttk.Frame(eq_frame)
            frame.pack(side=tk.LEFT, fill=tk.Y, padx=5)
            
            label_text = f"{freq}Hz" if freq < 1000 else f"{freq/1000:.1f}kHz"
            ttk.Label(frame, text=label_text).pack(side=tk.TOP)
            
            slider = tk.Scale(
                frame,
                from_=12, to=-12,  # dB range
                orient=tk.VERTICAL,
                length=300,
                resolution=0.1,
                command=lambda val, idx=i: self.on_slider_change(idx, val)
            )
            slider.set(0)
            slider.pack(side=tk.TOP, fill=tk.Y, expand=True)
            self.sliders.append(slider)
            
    def _setup_plots(self):
        # Matplotlib Figure
        plot_frame = ttk.Frame(self.root)
        plot_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.fig = Figure(figsize=(8, 8), dpi=100)
        self.ax_spectrum = self.fig.add_subplot(211)
        self.ax_waveform = self.fig.add_subplot(212)
        
        self.fig.tight_layout(pad=3.0)
        
        # Spectrum Plot
        self.ax_spectrum.set_title("Frequency Spectrum")
        self.ax_spectrum.set_xlabel("Frequency (Hz)")
        self.ax_spectrum.set_ylabel("Magnitude (dB)")
        self.ax_spectrum.set_xlim(MIN_FREQ, MAX_FREQ)
        self.ax_spectrum.set_ylim(MIN_DB, MAX_DB)
        self.ax_spectrum.set_xscale('log')
        self.spec_line, = self.ax_spectrum.plot([], [], color='cyan', lw=1.5)
        self.ax_spectrum.grid(True, which='both', alpha=0.3)
        
        # Waveform Plot
        self.ax_waveform.set_title("Waveform")
        self.ax_waveform.set_ylim(-32768, 32767) # 16-bit audio range
        self.ax_waveform.set_xlim(0, CHUNK_SIZE)
        self.ax_waveform.grid(True, alpha=0.3)
        self.wave_line, = self.ax_waveform.plot([], [], color='lime', lw=1)
        
        self.canvas = FigureCanvasTkAgg(self.fig, plot_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def on_slider_change(self, idx, val):
        val = float(val)
        self.audio_engine.set_band_gain(idx, val)

    def reset_eq(self):
        for slider in self.sliders:
            slider.set(0)

    def update_plots(self):
        if self.audio_engine.is_running:
            data, freqs, magnitude_db = self.audio_engine.get_audio_data()
            
            # Update Waveform
            self.wave_line.set_data(np.arange(len(data)), data)
            
            # Update Spectrum
            # Ensure dimensions match
            if len(freqs) == len(magnitude_db):
                self.spec_line.set_data(freqs, magnitude_db)
            
            self.canvas.draw_idle()
            
        self.root.after(33, self.update_plots)
