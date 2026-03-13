import tkinter as tk
from tkinter import ttk
import numpy as np
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib import style

from .constants import (
    EQ_BANDS, SAMPLE_RATE, CHUNK_SIZE,
    MIN_FREQ, MAX_FREQ, MIN_DB, MAX_DB,
    EQ_PRESETS,
)

# Dark Matplotlib theme
style.use("dark_background")

# ── Colour palette ───────────────────────────────────────────────────────────
CLR_BG       = "#1a1a2e"   # deep navy
CLR_PANEL    = "#16213e"   # slightly lighter panel
CLR_ACCENT   = "#0f3460"   # mid-blue accents
CLR_TEXT     = "#e0e0e0"   # light grey text
CLR_CYAN     = "#00d4ff"   # spectrum line
CLR_GREEN    = "#39ff14"   # waveform / running indicator
CLR_ORANGE   = "#ff9f43"   # EQ curve overlay
CLR_PEAK     = "#ff4757"   # peak-hold line
CLR_STOPPED  = "#ff4757"   # stopped indicator

# Peak-hold decay constant (fraction dropped per frame at 30 fps)
PEAK_DECAY = 0.92


class EqualizerApp:
    def __init__(self, root, audio_engine):
        self.root = root
        self.root.title("Real-time Audio Equalizer & Spectrum Analyzer")
        self.root.geometry("1280x860")
        self.root.configure(bg=CLR_BG)
        self.root.resizable(True, True)

        self.audio_engine = audio_engine

        # Per-slider state
        self.sliders    = []
        self.db_vars    = []   # StringVar for the dB value label under each slider

        # Peak-hold state (one value per FFT frequency bin)
        self._peak_hold = None

        self._apply_styles()
        self._build_ui()
        self._setup_plots()

        # Kick off the 30 fps update loop
        self.root.after(33, self._update_plots)

    # ── ttk Styling ──────────────────────────────────────────────────────────

    def _apply_styles(self):
        style = ttk.Style(self.root)
        style.theme_use("clam")

        style.configure(".",
                        background=CLR_BG,
                        foreground=CLR_TEXT,
                        fieldbackground=CLR_PANEL,
                        font=("Segoe UI", 9))

        style.configure("TFrame",        background=CLR_BG)
        style.configure("TLabelframe",   background=CLR_BG,   foreground=CLR_CYAN,
                         bordercolor=CLR_ACCENT, relief="groove")
        style.configure("TLabelframe.Label", background=CLR_BG, foreground=CLR_CYAN,
                         font=("Segoe UI", 9, "bold"))

        style.configure("TButton",
                        background=CLR_ACCENT, foreground=CLR_TEXT,
                        padding=(8, 4), relief="flat",
                        font=("Segoe UI", 9))
        style.map("TButton",
                  background=[("active", "#1a4a80"), ("pressed", "#0a2550")])

        style.configure("TLabel",   background=CLR_BG, foreground=CLR_TEXT)
        style.configure("TCombobox",
                        fieldbackground=CLR_PANEL, background=CLR_ACCENT,
                        foreground=CLR_TEXT, selectbackground=CLR_ACCENT)

    # ── UI Construction ───────────────────────────────────────────────────────

    def _build_ui(self):
        # ── Root grid: top bar | content | status bar ──
        self.root.rowconfigure(1, weight=1)
        self.root.columnconfigure(0, weight=1)

        # Top control bar
        ctrl = ttk.LabelFrame(self.root, text="Controls", padding=(10, 6))
        ctrl.grid(row=0, column=0, sticky="ew", padx=8, pady=(8, 0))

        ttk.Button(ctrl, text="▶  Start Capture",
                   command=self._start).pack(side=tk.LEFT, padx=4)
        ttk.Button(ctrl, text="■  Stop Capture",
                   command=self._stop).pack(side=tk.LEFT, padx=4)

        ttk.Separator(ctrl, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y,
                                                     padx=10, pady=2)

        ttk.Label(ctrl, text="Preset:").pack(side=tk.LEFT, padx=(0, 4))
        self._preset_var = tk.StringVar(value="Flat")
        preset_cb = ttk.Combobox(ctrl, textvariable=self._preset_var,
                                 values=list(EQ_PRESETS.keys()),
                                 state="readonly", width=14)
        preset_cb.pack(side=tk.LEFT, padx=4)
        preset_cb.bind("<<ComboboxSelected>>", self._apply_preset)

        ttk.Button(ctrl, text="↺  Reset EQ",
                   command=self._reset_eq).pack(side=tk.LEFT, padx=4)

        # Content area: EQ panel (left) + plots (right)
        content = ttk.Frame(self.root)
        content.grid(row=1, column=0, sticky="nsew", padx=8, pady=6)
        content.rowconfigure(0, weight=1)
        content.columnconfigure(1, weight=1)

        self._build_eq_panel(content)
        self._build_plot_area(content)

        # Status bar
        self._status_var = tk.StringVar(value="○  STOPPED")
        status_bar = tk.Label(self.root, textvariable=self._status_var,
                              bg=CLR_PANEL, fg=CLR_STOPPED,
                              anchor="w", padx=12, pady=4,
                              font=("Segoe UI", 9, "bold"))
        status_bar.grid(row=2, column=0, sticky="ew")
        self._status_label = status_bar

    def _build_eq_panel(self, parent):
        eq_frame = ttk.LabelFrame(parent, text="Equalizer (10-Band)", padding=(8, 6))
        eq_frame.grid(row=0, column=0, sticky="ns", padx=(0, 6))

        # dB scale markers on the left edge
        scale_col = ttk.Frame(eq_frame)
        scale_col.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 6))
        for db_label in ["+12", "+6", "0", "-6", "-12"]:
            ttk.Label(scale_col, text=db_label, width=4,
                      anchor="e").pack(expand=True, fill=tk.Y)

        for i, freq in enumerate(EQ_BANDS):
            col = ttk.Frame(eq_frame)
            col.pack(side=tk.LEFT, fill=tk.Y, padx=3)

            label_text = f"{freq}Hz" if freq < 1000 else f"{freq//1000}k"
            ttk.Label(col, text=label_text,
                      font=("Segoe UI", 8)).pack(side=tk.TOP)

            db_var = tk.StringVar(value="0.0 dB")
            self.db_vars.append(db_var)

            slider = tk.Scale(
                col,
                from_=12, to=-12,
                orient=tk.VERTICAL,
                length=260,
                resolution=0.5,
                showvalue=False,           # we draw our own value label
                troughcolor=CLR_PANEL,
                bg=CLR_BG,
                fg=CLR_CYAN,
                activebackground=CLR_CYAN,
                highlightthickness=0,
                command=lambda val, idx=i: self._on_slider(idx, val),
            )
            slider.set(0)
            slider.pack(side=tk.TOP, fill=tk.Y, expand=True)

            # dB value label (updates live)
            ttk.Label(col, textvariable=db_var,
                      font=("Segoe UI", 8),
                      width=7, anchor="center").pack(side=tk.TOP)

            self.sliders.append(slider)

    def _build_plot_area(self, parent):
        plot_frame = ttk.Frame(parent)
        plot_frame.grid(row=0, column=1, sticky="nsew")

        self.fig = Figure(figsize=(9, 7.5), dpi=100,
                          facecolor="#0d1117")
        self.fig.subplots_adjust(hspace=0.42, left=0.08, right=0.97,
                                 top=0.95, bottom=0.08)

        self._build_spectrum_axes()
        self._build_waveform_axes()

        self.canvas = FigureCanvasTkAgg(self.fig, plot_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def _build_spectrum_axes(self):
        ax = self.fig.add_subplot(211)
        ax.set_facecolor("#0d1117")
        ax.set_title("Frequency Spectrum", color=CLR_TEXT,
                     fontsize=10, pad=6)
        ax.set_xlabel("Frequency (Hz)", color=CLR_TEXT, fontsize=8)
        ax.set_ylabel("Magnitude (dBFS)", color=CLR_TEXT, fontsize=8)
        ax.set_xlim(MIN_FREQ, MAX_FREQ)
        ax.set_ylim(MIN_DB, MAX_DB)
        ax.set_xscale("log")
        ax.tick_params(colors=CLR_TEXT, labelsize=7)
        ax.spines[:].set_color(CLR_ACCENT)
        ax.grid(True, which="both", color=CLR_ACCENT, alpha=0.25, linestyle="--")

        # ─ plot lines ─
        self._spec_line,  = ax.plot([], [], color=CLR_CYAN,    lw=1.2,
                                    label="Live spectrum")
        self._peak_line,  = ax.plot([], [], color=CLR_PEAK,    lw=0.8,
                                    linestyle=":",  label="Peak hold")
        self._eq_line,    = ax.plot([], [], color=CLR_ORANGE,  lw=1.5,
                                    linestyle="--", label="EQ curve", alpha=0.85)

        ax.legend(loc="lower right", fontsize=7,
                  facecolor=CLR_PANEL, labelcolor=CLR_TEXT, framealpha=0.7)
        ax.axhline(0, color=CLR_TEXT, lw=0.5, alpha=0.4)  # 0 dBFS reference

        self._ax_spectrum = ax

    def _build_waveform_axes(self):
        ax = self.fig.add_subplot(212)
        ax.set_facecolor("#0d1117")
        ax.set_title("Waveform", color=CLR_TEXT, fontsize=10, pad=6)
        ax.set_xlabel("Sample", color=CLR_TEXT, fontsize=8)
        ax.set_ylabel("Amplitude", color=CLR_TEXT, fontsize=8)
        ax.set_xlim(0, CHUNK_SIZE)
        ax.set_ylim(-1.05, 1.05)     # normalised float range
        ax.tick_params(colors=CLR_TEXT, labelsize=7)
        ax.spines[:].set_color(CLR_ACCENT)
        ax.grid(True, color=CLR_ACCENT, alpha=0.2, linestyle="--")
        ax.axhline(0, color=CLR_TEXT, lw=0.5, alpha=0.4)

        self._wave_line, = ax.plot([], [], color=CLR_GREEN, lw=0.9)
        self._ax_waveform = ax

    # ── Plot update loop (30 fps) ─────────────────────────────────────────────

    def _update_plots(self):
        if self.audio_engine.is_running:
            data, freqs, mag_db = self.audio_engine.get_audio_data()

            # Waveform
            self._wave_line.set_data(np.arange(len(data)), data)

            if len(freqs) == len(mag_db):
                # Live spectrum
                self._spec_line.set_data(freqs, mag_db)

                # Peak-hold — initialise or decay
                if self._peak_hold is None or len(self._peak_hold) != len(mag_db):
                    self._peak_hold = mag_db.copy()
                else:
                    risen = mag_db > self._peak_hold
                    self._peak_hold[risen] = mag_db[risen]
                    self._peak_hold[~risen] = (
                        self._peak_hold[~risen] * PEAK_DECAY
                        + mag_db[~risen] * (1 - PEAK_DECAY)
                    )
                self._peak_line.set_data(freqs, self._peak_hold)

                # EQ curve overlay
                eq_db = self.audio_engine.get_eq_curve(freqs)
                self._eq_line.set_data(freqs, eq_db)

            self.canvas.draw_idle()

        self.root.after(33, self._update_plots)

    # ── Control callbacks ─────────────────────────────────────────────────────

    def _start(self):
        self.audio_engine.start_stream()
        self._status_var.set("●  RUNNING")
        self._status_label.configure(fg=CLR_GREEN)
        self._peak_hold = None   # reset peak-hold on each new capture

    def _stop(self):
        self.audio_engine.stop_stream()
        self._status_var.set("○  STOPPED")
        self._status_label.configure(fg=CLR_STOPPED)

    def _on_slider(self, idx, val):
        gain = float(val)
        self.audio_engine.set_band_gain(idx, gain)
        sign = "+" if gain > 0 else ""
        self.db_vars[idx].set(f"{sign}{gain:.1f} dB")

    def _reset_eq(self):
        for i, slider in enumerate(self.sliders):
            slider.set(0)
            # _on_slider is triggered by set(), so db_var updates automatically

    def _apply_preset(self, _event=None):
        name = self._preset_var.get()
        gains = EQ_PRESETS.get(name, [0] * len(EQ_BANDS))
        for i, (slider, gain) in enumerate(zip(self.sliders, gains)):
            slider.set(gain)
            # _on_slider fires automatically
