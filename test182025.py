from transitions import Machine
import azure.cognitiveservices.speech as speechsdk
import time
import os
import string
from chatbot import chatbot_with_memory
from audio_v0 import play_saved_audio_without_interrupt
from dotenv import load_dotenv
from fastapi import FastAPI, Request
import threading
import uvicorn
from fall_detect_local import start_watching  # <- Import watcher module
# Load environment variables from .env file
from speaker
from class_keyword_publisher import KeywordPublisher
import subprocess
import rospy
import re
import signal
import threading

 
load_dotenv()
 
shutdown_event = threading.Event()
 
def handle_sigint(sig, frame):
    print("🛑 SIGINT received. Setting shutdown event...")
    shutdown_event.set()
 
signal.signal(signal.SIGINT, handle_sigint)
 
 
 
# ---------------------- Configuration ----------------------
speech_key = os.getenv("SPEECH_KEY")
service_region = "eastus"
keyword_model_path = "rooee.table"
wake_word = "Ruyi"
 
# ---------------------- Command List ----------------------
command_phrases = {
    "stop following me", "stop follow me", "stop following", "pose",
    "come closer", "come close", "come here", "go away",
    "follow me", "move close", "stop", "break", "home", "go to home", "go home"
}
 
# ---------------------- Check Model File ----------------------
if not os.path.exists(keyword_model_path):
    print(f"❌ ERROR: Model file not found at: {keyword_model_path}")
    exit(1)
 
# ---------------------- Setup ----------------------
speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=service_region)
keyword_model = speechsdk.KeywordRecognitionModel(keyword_model_path)
 
AUDIO = speechsdk.AudioConfig(use_default_microphone=True, filename= None, stream= None, device_name = None)
 
#------------------ NAVIGATION Replies ---------------------------
def get_navigation_reply(command: str) -> str:
    command = command.lower().strip()
 
    responses = {
        "stop following me": "Okay, I will stop following you now.",
        "stop follow me": "Alright, I will stay here and not follow you anymore.",
        "stop following": "Understood, I'm stopping now.",
        "pose": "Holding position. Please let me know when you're ready to continue.",
        "come closer": "Coming closer. Please make sure the path is clear.",
        "come close": "Approaching you now. Let me know if I’m too close.",
        "come here": "On my way to you. Stay where you are, please.",
        "go away": "Understood. I will move away and maintain a safe distance.",
        "follow me": "Following you now. Please move slowly and safely.",
        "move close": "Moving closer to you. Please stand still.",
        "stop": "I’ve stopped moving. Awaiting your next instruction.",
        "break": "Pausing all navigation tasks. Say 'resume' to continue.",
        "home": "Returning to the charging station now.",
        "go to home": "Heading back to my home base.",
        "go home": "Navigating to the home station now.",
        "sleep": "Entering sleep mode. Call me if you need assistance.",
        "go to sleep": "Activating sleep mode. I’ll be here if needed.",
        "leave": "Understood. I’ll leave the room quietly.",
        "pause": "Pausing movement. Let me know when to resume.",
        "go to dock": "Okay! Moving towards the dock!"
    }
 
    # Find best match if exact key not found (to support slight misspellings or variants)
    for key in responses:
        if key in command:
            return responses[key]
 
    return "I'm sorry, I didn't understand that command. Could you please repeat it?"
 
 
# ------------ Robot Screen ------------
param_name = "/smiley_param"
param_value = "smiling"
param_value_listening = "sttrunning"
param_value_converstion = "conversation"
 
 #-------- Speaker ID------
speaker_audio=5
volume=150
 
#keyword_publisher = KeywordPublisher()
def publish_command(text):
    intent = 'control'
    print("intent is : ", intent)
    reply =get_navigation_reply(text)
   
    #keyword_publisher.publish_keyword(intent, text)
    play_saved_audio_without_interrupt(reply,speaker_audio,volume)
    print(f"Control Published: {text}")
 
 
# ---------------------- FSM States ----------------------
states = [
    'IDLE',              # Initial startup state
    'WAKEWORD',          # Listening for wake word
    'SPEECH_RECOG',      # Speech-to-text
    'BOT_PROCESS',       # Send input to chatbot
    'BOT_RESPONSE',      # Play bot response via TTS
    # 'LISTEN_WAIT',       # 7-second listening window
    'FALL_INTERRUPT',    # Fall detected interrupt
    'FALL_CONVO',        # Fall-related conversation
    'RESUME_PREVIOUS'    # Resume the state before interrupt
]
 
 
 
# ---------------------- FSM Class ----------------------
class ChatbotFSM:
    def __init__(self):
        self.machine = Machine(model=self, states=states, initial='IDLE')
        self.state_stack = []  # To save/restore previous state on interrupt
 
        # using for speech:
        self.last_transcript = ""
        self.last_response = ""
 
        self.fall_info_message = ""  # fallback if no API data yet
 
        # Initialize recognizer once
        try:
            self.recognizer = speechsdk.SpeechRecognizer(
                speech_config=speech_config,
                audio_config=AUDIO
            )
        except Exception as e:
            print(f"❌ Error initializing recognizer: {e}")
            self.recognizer = None
 
 
        # Normal conversation transitions
        self.machine.add_transition('start', 'IDLE', 'WAKEWORD')
        self.machine.add_transition('wakeword_detected', 'WAKEWORD', 'SPEECH_RECOG')
        self.machine.add_transition('speech_done', 'SPEECH_RECOG', 'BOT_PROCESS')
        self.machine.add_transition('bot_replied', 'BOT_PROCESS', 'BOT_RESPONSE')
        self.machine.add_transition('tts_finished', 'BOT_RESPONSE', 'SPEECH_RECOG')
 
        # Fall interrupt flowc
        self.machine.add_transition('fall_detected', '*', 'FALL_INTERRUPT', before='save_current_state')
        self.machine.add_transition('fall_alert_spoken', 'FALL_INTERRUPT', 'FALL_CONVO')
        # Fall conversation continues into chatbot mode
        self.machine.add_transition('fall_convo_done', 'FALL_CONVO', 'SPEECH_RECOG')
 
        # Fallback universal transition to WAKEWORD
        self.machine.add_transition('to_WAKEWORD', '*', 'WAKEWORD')
       
    def record_audio(self, filename="temp_recorded.wav", duration=5, sample_rate=16000):
        print("🎙️ Recording started...")
        recording = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=1, dtype='int16')
        sd.wait()
        wav.write(filename, sample_rate, recording)
        print("✅ Recording saved.")
 
    def recognize_speech_once(self):
        if self.recognizer is None:
            print("⚠ Recognizer is not initialized.")
            # self.to_WAKEWORD()
            self.on_enter_SPEECH_RECOG()
            return
 
        try:
            subprocess.run(["rosparam", "set", param_name, "sttrunning"])
            self.record_audio("temp_recorded.wav")
            speaker = detect_speaker()
            print(speaker)
            audio_config = speechsdk.AudioConfig(filename="temp_recorded.wav")
            recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)
            result = self.recognizer.recognize_once_async().get()
            subprocess.run(["rosparam", "set", param_name, "smiling"])
        except Exception as e:
            print(f"❌ Error during recognition: {e}")
            # self.to_WAKEWORD()
            self.on_enter_SPEECH_RECOG()
            return
 
        if result.reason == speechsdk.ResultReason.RecognizedSpeech:
            transcript = result.text.strip().lower()
            if transcript:
                print(f"[🗣] Heard: {transcript}")
                self.last_transcript = transcript
                self.speech_done()
                return
 
        elif result.reason == speechsdk.ResultReason.NoMatch:
            print(f"⚠ NoMatch — Recognizer heard: '{result.text.strip()}'")
            print("❌ No usable input. Returning to wakeword.")
            self.on_enter_SPEECH_RECOG()
            return
 
                   
 
 
 
    def save_current_state(self):
        print(f"[🧠] Saving state: {self.state}")
        self.state_stack.append(self.state)
 
    def restore_previous_state(self):
        if self.state_stack:
            previous = self.state_stack.pop()
            print(f"[🔁] Resuming state: {previous}")
            if previous == 'WAKEWORD':
                self.to_WAKEWORD()
            elif previous == 'SPEECH_RECOG':
                self.wakeword_detected()
            elif previous == 'BOT_PROCESS':
                self.speech_done()
            elif previous == 'BOT_RESPONSE':
                self.bot_replied()
            # elif previous == 'LISTEN_WAIT':
            #     self.tts_finished()
            else:
                print(f"[⚠] Unknown state '{previous}', falling back to WAKEWORD")
                self.to_WAKEWORD()
        else:
            print("[⚠] No previous state saved, going to WAKEWORD")
            self.to_WAKEWORD()
 
 
    def on_enter_SPEECH_RECOG(self):
        print(f"[🎙] Entered SPEECH_RECOG — streaming for command")
        self.recognize_speech_once()
 
 
 
    def on_enter_BOT_PROCESS(self):
        text = self.last_transcript.strip().lower()
        text = remove_punctuation(text)
         
       
        if text in command_phrases:
            print("✅ Detected as a robot command.")
 
            publish_command(text)
 
            self.to_WAKEWORD()
 
        else:
            print(f"[🤖] Processing through chatbot: {text}")
            self.last_response = chatbot_with_memory(text, verbose=False)
 
            #publish_convo(self.last_response)
            self.bot_replied()
 
       
 
 
    def on_enter_BOT_RESPONSE(self):
        print(f"[🔊] Speaking: {self.last_response}")
 
        subprocess.run(["rosparam", "set", param_name, "conversation"])
 
        play_saved_audio_without_interrupt(self.last_response,speaker_audio,volume)
 
        subprocess.run(["rosparam", "set", param_name, "smiling"])
 
        if self.state == "BOT_RESPONSE":  # Only trigger if still in expected state
            self.tts_finished()
        else:
            print(f"[⚠] Skipping tts_finished — current state is {self.state}")
 
 
 
    def on_enter_FALL_INTERRUPT(self):
        print("[🗣] Starting fall-related conversation...")
 
        try:
            response = chatbot_with_memory(
                self.last_transcript + "Note : As the User Fall! Ask Him about his health as a Healthcare-Companion. Ensure is User Okay need any help. Give as Much as Human Behaviour as you can. Make it concise response not a long paragraphic ones",
                verbose=False
            )
            self.last_response = response
            print("Fall Detected: ", response)
            play_saved_audio_without_interrupt(response,speaker_audio,volume)
            # ✅ Only trigger transition if state is still valid
            if self.state == "FALL_INTERRUPT":
                self.fall_alert_spoken()
            else:
                print(f"[⚠] Skipping fall_alert_spoken — current state is {self.state}")
        except Exception as e:
            print(f"❌ Error in fall conversation: {e}")
 
 
 
    def on_enter_FALL_CONVO(self):
        print("[🩹] Fall Convo started — transitioning to speech recog")
        self.fall_convo_done()  # Continue to chatbot mode
 
def listen_for_wake_word():
    print("🎤 Wake word listener started...")
 
    def on_recognized(evt):
        if evt.result.reason == speechsdk.ResultReason.RecognizedKeyword:
            print(f"\n✅ Wake word '{wake_word}' detected!")
            #play_saved_audio_without_interrupt("Hello! Mister Chen I am here to keep you company.",speaker_audio,volume)
            fsm.wakeword_detected()  # FSM transition
 
    def on_canceled(evt):
        print(f"⚠ Wakeword recognition canceled: {evt.reason}")
 
    while not shutdown_event.is_set():
        if fsm.state != "WAKEWORD":
            time.sleep(0.2)
            continue
 
        try:
            keyword_recognizer = speechsdk.SpeechRecognizer(
                speech_config=speech_config,
                audio_config=AUDIO
            )
 
            keyword_recognizer.recognized.connect(on_recognized)
            keyword_recognizer.canceled.connect(on_canceled)
 
            keyword_recognizer.start_keyword_recognition_async(keyword_model).get()
 
            while fsm.state == "WAKEWORD" and not shutdown_event.is_set():
                time.sleep(0.1)
 
            keyword_recognizer.stop_keyword_recognition_async().get()
 
        except Exception as e:
            print(f"❌ Wake word loop error: {e}")
            time.sleep(1)
 
 
        # Let FSM handle the rest — loop will restart automatically
 
 
def remove_punctuation(text):
    """Removes punctuation from the input text."""
    return text.translate(str.maketrans('', '', string.punctuation))
 
 
 
def handle_new_csv_data(is_new, new_data):
    if is_new:
        for _, row in new_data.iterrows():
            status = row.get("event", "Unknown")
            timestamp = row.get("ts", "Unknown")
            location = row.get("place", "Unknown")
 
            print(f"[✔ CSV ALERT] Status: {status}, Time: {timestamp}, Location: {location}")
            fsm.fall_info_message = (
                f"Fall detected in the {location} at {timestamp}. "
                f"Status: {status}. Please respond calmly and provide instructions."
            )
            fsm.last_transcript = fsm.fall_info_message
            print("[🚨] Triggering fall FSM transition...")
            fsm.fall_detected()
    else:
        print("[📄] No new fall events.")
 
 
## start the State
fsm = ChatbotFSM()
fsm.start()  # goes from IDLE → WAKEWORD
 
 
if __name__ == "__main__":
    print("🟢 Starting FSM Chatbot + Fall Detection via CSV")
 
    # ✅ Initialize ROS node
    try:
        rospy.init_node('fsm_keyword_node', anonymous=True)
        print("✅ ROS node initialized.")
    except rospy.exceptions.ROSException as e:
        print(f"❌ Failed to initialize ROS node: {e}")
        exit(1)
   
    subprocess.run(["rosparam", "set", param_name, param_value])
 
 
    # Start CSV watcher
    threading.Thread(
        target=start_watching,
        args=(r"/home/nvidia/AI_Results/FALL/fall_results.csv", handle_new_csv_data, shutdown_event),
        daemon=True
    ).start()
 
    # Start wake word listener thread
    threading.Thread(target=listen_for_wake_word, daemon=True).start()
 
    try:
        while not shutdown_event.is_set():
            time.sleep(1)
    except KeyboardInterrupt:
        print("🛑 Ctrl+C detected. Shutting down...")
        shutdown_event.set()
        time.sleep(2)
 
