import tkinter as tk
from src.audio_engine import AudioEngine
from src.gui import EqualizerApp
import sys

def main():
    root = tk.Tk()
    
    # Initialize Audio Engine
    try:
        audio_engine = AudioEngine()
    except Exception as e:
        print(f"Error initializing Audio Engine: {e}")
        sys.exit(1)
        
    app = EqualizerApp(root, audio_engine)
    
    # Handle window close
    def on_closing():
        audio_engine.close()
        root.destroy()
        
    root.protocol("WM_DELETE_WINDOW", on_closing)
    
    root.mainloop()

if __name__ == "__main__":
    main()
