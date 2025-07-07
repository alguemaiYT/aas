import os
import pyaudio
import snowboydecoder
import webrtcvad
from gladia import Gladia
from groq import Groq
import rhvoice
import logging
from dotenv import load_dotenv

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
        self.grok_client = Groq(api_key=GROK_API_KEY)
        self.rhvoice_tts = rhvoice.TTS(lang=RHVOICE_VOICE)
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
            logging.error(f"Gladia transcription error: {e}")
            print(f"Error during transcription: {e}")
            return None

    async def get_ai_response(self, text):
        if not text:
            return "I didn't catch that. Could you please repeat?"
        try:
            print(f"Sending to Grok: {text}")
            chat_completion = self.grok_client.chat.completions.create(
                messages=[
                    {
                        "role": "user",
                        "content": text,
                    }
                ],
                model="mixtral-8x7b-32768", # Or other Grok model
            )
            response = chat_completion.choices[0].message.content
            print(f"Grok response: {response}")
            return response
        except Exception as e:
            logging.error(f"Grok API error: {e}")
            print(f"Error querying Grok: {e}")
            return "I'm having trouble connecting to my brain right now."

    def speak(self, text):
        if not text:
            return
        try:
            print(f"Speaking: {text}")
            # RHVoice usage might vary depending on the specific Python wrapper
            # This is a conceptual example. The actual API might be different.
            # For instance, it might save to a file and then play it.
            # Or it might directly stream to an audio output.

            # Assuming a simple blocking speak method for now
            # You might need to install 'rhvoice-wrapper' or similar
            # and ensure RHVoice service is running.
            # Example: self.rhvoice_tts.say(text)
            # Or:
            # wav_data = self.rhvoice_tts.tts(text)
            # play_wav_data(wav_data) # You'd need a function for this

            # For simplicity, using a placeholder for actual speech synthesis call
            # In a real scenario, you would integrate RHVoice properly.
            # This often involves calling a command-line tool or using a specific library.
            # For example, if RHVoice-test is installed:
            os.system(f'echo "{text}" | RHVoice-test -p {RHVOICE_VOICE}')
            print("Finished speaking.")

        except Exception as e:
            logging.error(f"RHVoice error: {e}")
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
