import sounddevice as sd
from scipy.io.wavfile import write
import numpy as np

def record(filename):
    # Settings
    samplerate = 16000
    duration = 10     
    # filename = "temp_recorded.wav"

    print("🎤 Recording started...")
    audio = sd.rec(int(samplerate * duration), samplerate=samplerate, channels=1, dtype='int16')
    sd.wait()  # Wait until recording is finished
    print("✅ Recording finished.")

    write(filename, samplerate, audio)
    print(f"💾 Saved to {filename}")
