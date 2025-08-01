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

# record("new_recordings/hasnain1.wav")

# import sounddevice as sd
# from scipy.io.wavfile import write
# import numpy as np
# import queue
# import time
# import os

# samplerate = 16000  # 16kHz
# block_duration = 0.5  # seconds per chunk
# block_size = int(samplerate * block_duration)
# silence_threshold = 500  # energy level
# max_silence_duration = 0.5  # seconds


# q = queue.Queue()

# def callback(indata, frames, time, status):
#     if status:
#         print(status)
#     q.put(indata.copy())

# def record(filename):
#     print("🎤 Start speaking...")

#     audio_data = []
#     silence_start = None

#     with sd.InputStream(samplerate=samplerate, channels=1, dtype='int16', callback=callback, blocksize=block_size):
#         while True:
#             block = q.get()
#             audio_data.append(block)

#             # Check if this block is silent
#             rms = np.sqrt(np.mean(block.astype(np.int32)**2))
#             if rms < silence_threshold:
#                 if silence_start is None:
#                     silence_start = time.time()
#                 elif time.time() - silence_start > max_silence_duration:
#                     print("🛑 Silence detected. Stopping...")
#                     break
#             else:
#                 silence_start = None

#     full_audio = np.concatenate(audio_data, axis=0)
#     os.makedirs(os.path.dirname(filename), exist_ok=True)
#     write(filename, samplerate, full_audio)
#     print(f"💾 Saved to {filename}")


# filename = "new_recordings/shaiza5.wav"
# record(filename)
