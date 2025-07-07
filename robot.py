import os
import pyaudio
import snowboydecoder
import webrtcvad
from gladia import Gladia
import requests # Added requests
# from groq import Groq # Removed Groq SDK
import rhvoice # Assuming this is a valid import for a wrapper
import logging
from dotenv import load_dotenv
import json # For crafting JSON payloads

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(filename='robot_error.log', level=logging.ERROR,
                    format='%(asctime)s %(levelname)s %(name)s %(threadName)s : %(message)s')

# Configuration
SNOWBOY_MODEL = "jarvis.umdl"
WAKE_WORD = "jarvis"
GLADIA_API_KEY = os.getenv("GLADIA_API_KEY")
GROK_API_KEY = os.getenv("GROK_API_KEY")
GROK_API_URL = "https://api.groq.com/openai/v1/chat/completions" # Standard Grok API endpoint
RHVOICE_VOICE = "en_us"
AUDIO_FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
CHUNK_DURATION_MS = 30  # supports 10, 20 and 30 (ms)
CHUNK_BYTES = (RATE * CHUNK_DURATION_MS // 1000) * pyaudio.get_sample_size(AUDIO_FORMAT)
VAD_AGGRESSIVENESS = 3 # 0 (least aggressive) to 3 (most aggressive)


class VoiceAssistant:
    def __init__(self):
        self.audio = pyaudio.PyAudio()
        self.vad = webrtcvad.Vad(VAD_AGGRESSIVENESS)
        self.gladia_client = Gladia(api_key=GLADIA_API_KEY)
        # self.grok_client = Groq(api_key=GROK_API_KEY) # Removed Groq SDK client
        # For RHVoice, direct instantiation might vary.
        # If 'rhvoice' is a wrapper, this might be correct.
        # If it requires a service or command line, adjust self.speak()
        try:
            self.rhvoice_tts = rhvoice.TTS(lang=RHVOICE_VOICE)
        except Exception as e:
            logging.warning(f"Could not initialize rhvoice.TTS: {e}. TTS might not work.")
            self.rhvoice_tts = None # Ensure it's defined

        self.detector = None
        self.listening_for_command = False

    def _init_detector(self):
        # Initialize Snowboy detector
        self.detector = snowboydecoder.HotwordDetector(SNOWBOY_MODEL, sensitivity=0.5)

    def _capture_audio_stream(self):
        return self.audio.open(format=AUDIO_FORMAT,
                               channels=CHANNELS,
                               rate=RATE,
                               input=True,
                               frames_per_buffer=CHUNK_BYTES)

    def listen_for_wake_word(self):
        if not self.detector:
            self._init_detector()
        print(f"Listening for wake word '{WAKE_WORD}'...")
        self.detector.start(detected_callback=self._wake_word_detected,
                            interrupt_check=lambda: False,
                            sleep_time=0.03)
        self.detector.terminate() # Ensure cleanup

    def _wake_word_detected(self):
        print("Wake word detected!")
        snowboydecoder.play_audio_file(snowboydecoder.DETECT_DING) # Optional: play a sound
        self.listening_for_command = True
        if self.detector: # Stop snowboy temporarily
            self.detector.terminate()
            self.detector = None


    async def capture_and_transcribe(self, stream):
        print("Listening for command...")
        frames = []
        silence_frames = 0
        max_silence_frames = int(2 * 1000 / CHUNK_DURATION_MS) # 2 seconds of silence

        while self.listening_for_command:
            try:
                audio_chunk = stream.read(CHUNK_BYTES, exception_on_overflow=False)
                is_speech = self.vad.is_speech(audio_chunk, RATE)

                if is_speech:
                    frames.append(audio_chunk)
                    silence_frames = 0
                elif frames: # If speech has started and now there's silence
                    silence_frames += 1
                    if silence_frames > max_silence_frames:
                        print("End of speech detected by VAD.")
                        self.listening_for_command = False # Stop listening after silence
                        break
                # If no speech yet, keep listening without appending silence
                # This avoids sending leading silence to Gladia

            except IOError as e:
                logging.error(f"Audio capture error: {e}")
                self.listening_for_command = False
                break
            except Exception as e:
                logging.error(f"Unexpected error during capture: {e}")
                self.listening_for_command = False
                break

        if not frames:
            print("No speech captured.")
            return None

        print("Processing speech...")
        full_audio_data = b''.join(frames)

        try:
            # Note: Gladia Python SDK might not have a direct streaming audio method like this.
            # This is a conceptual representation. You might need to save to a file or adapt.
            # For true streaming with Gladia, you'd typically use their WebSocket API.
            # The SDK might offer a helper for this or you might need to implement it.
            # Assuming gladia_client.audio_transcription can handle bytes directly:
            response = await self.gladia_client.audio_transcription.create(
                audio_data=full_audio_data, # This needs to be the correct way to send bytes
                language='english', # Or auto-detect if supported
                output_format='txt' # Or 'json' for more details
            )
            # The actual response object structure will depend on the Gladia SDK
            transcription = response.transcription if hasattr(response, 'transcription') else str(response)
            print(f"Transcription: {transcription}")
            return transcription.strip()
        except Exception as e:
            logging.error(f"Gladia transcription error: {e}", exc_info=True)
            print(f"Error during transcription: {e}")
            return None

    async def get_ai_response(self, text):
        if not text:
            return "I didn't catch that. Could you please repeat?"
        if not GROK_API_KEY:
            logging.error("GROK_API_KEY not found for get_ai_response.")
            return "My connection to the AI brain is not configured."

        headers = {
            "Authorization": f"Bearer {GROK_API_KEY}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": "mixtral-8x7b-32768", # Or other compatible Grok model
            "messages": [
                {
                    "role": "user",
                    "content": text,
                }
            ],
            "temperature": 0.7, # Example: Adjust for creativity vs. conciseness
        }

        try:
            print(f"Sending to Grok API: {text}")
            # Using await with a non-async requests call needs a thread or asyncio.to_thread
            # For simplicity in this context, if requests is used directly in an async def,
            # it will block. For true async, httpx or aiohttp would be better.
            # However, to stick to `requests` as per prompt, we'll make it blocking here.
            # If this function must remain truly async, `asyncio.to_thread` is needed.
            # Let's assume for now that a brief block here is acceptable for the flow.
            # If not, this would need to be:
            # loop = asyncio.get_event_loop()
            # response = await loop.run_in_executor(None, lambda: requests.post(GROK_API_URL, headers=headers, json=payload))

            # Direct blocking call (simplest change, makes this part of async func blocking)
            api_response = requests.post(GROK_API_URL, headers=headers, json=payload, timeout=20)
            api_response.raise_for_status()  # Raises an HTTPError for bad responses (4XX or 5XX)

            response_data = api_response.json()

            if response_data.get("choices") and len(response_data["choices"]) > 0:
                message = response_data["choices"][0].get("message")
                if message and message.get("content"):
                    content = message["content"]
                    print(f"Grok API response: {content}")
                    return content
            logging.error(f"Unexpected Grok API response format: {response_data}")
            return "I received a strange response from my brain."

        except requests.exceptions.Timeout:
            logging.error("Grok API request timed out.")
            print("Error: Grok API request timed out.")
            return "My AI brain is taking too long to respond."
        except requests.exceptions.RequestException as e:
            logging.error(f"Grok API request error: {e}", exc_info=True)
            print(f"Error querying Grok API: {e}")
            return "I'm having trouble connecting to my brain right now."
        except Exception as e:
            logging.error(f"Unexpected error in get_ai_response: {e}", exc_info=True)
            print(f"Unexpected error processing AI response: {e}")
            return "An unexpected error occurred while thinking."

    def speak(self, text):
        if not text:
            return
        if not self.rhvoice_tts and not os.path.exists("/usr/bin/RHVoice-test"):
            logging.error("RHVoice not initialized and RHVoice-test not found. Cannot speak.")
            print("Error: TTS not available.")
            return
        try:
            print(f"Speaking: {text}")
            # Prefer rhvoice-wrapper if available and initialized
            if self.rhvoice_tts:
                 # This depends on the actual API of the rhvoice-wrapper
                 # Common methods are .say(), .speak(), .tts() then play
                 # Assuming a .say() or .speak() method that is blocking
                self.rhvoice_tts.say(text) # Or .speak(text)
            elif os.path.exists("/usr/bin/RHVoice-test"): # Fallback to CLI
                # Ensure text is properly escaped for shell command
                # For security and robustness, using pipes with subprocess is better than os.system
                import subprocess
                process = subprocess.Popen(['RHVoice-test', '-p', RHVOICE_VOICE], stdin=subprocess.PIPE)
                process.communicate(input=text.encode('utf-8'))
            else:
                # This case should ideally be caught by the initial check, but as a safeguard:
                logging.warning("TTS called but no method available.")
                print("TTS: No speak method available.")
                return # No TTS method available

            print("Finished speaking.")

        except Exception as e:
            logging.error(f"RHVoice error: {e}", exc_info=True)
            print(f"Error during speech synthesis: {e}")

    async def run(self):
        # Main loop
        while True:
            self.listening_for_command = False # Reset command listening state
            self.listen_for_wake_word() # Blocks until wake word

            if self.listening_for_command: # True if wake word was detected
                stream = self._capture_audio_stream()
                try:
                    transcription = await self.capture_and_transcribe(stream)
                    if transcription:
                        ai_response = await self.get_ai_response(transcription)
                        self.speak(ai_response)
                    else:
                        self.speak("Sorry, I didn't get that.")
                finally:
                    stream.stop_stream()
                    stream.close()
            # Reset for next wake word cycle
            self.listening_for_command = False
            if self.detector: # ensure snowboy is stopped if it was running
                self.detector.terminate()
                self.detector = None


async def main():
    # Check for API keys
    if not GLADIA_API_KEY:
        logging.error("GLADIA_API_KEY not found. Please set it in the .env file.")
        print("Error: GLADIA_API_KEY not found. Please set it in the .env file.")
        return
    if not GROK_API_KEY:
        logging.error("GROK_API_KEY not found. Please set it in the .env file.")
        print("Error: GROK_API_KEY not found. Please set it in the .env file.")
        return

    assistant = VoiceAssistant()
    try:
        await assistant.run()
    except KeyboardInterrupt:
        print("Assistant stopped by user.")
    except Exception as e:
        logging.error(f"Critical error in main loop: {e}", exc_info=True)
        print(f"A critical error occurred: {e}")
    finally:
        assistant.audio.terminate()
        if assistant.detector:
            assistant.detector.terminate()
        print("Assistant shut down.")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
