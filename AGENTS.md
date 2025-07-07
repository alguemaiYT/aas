## Agent Instructions for Voice-Controlled AI Robot Project

Welcome, AI Agent! This document provides guidelines for working on the Voice-Controlled AI Robot project.

### Project Overview

The primary goal is to create a minimal, low-latency voice assistant for the Orange Pi PC. Key aspects include:
- Wake word detection (Snowboy)
- Speech-to-Text (Gladia)
- AI processing (Grok)
- Text-to-Speech (RHVoice)
- Python 3.9+
- Optimization for ARM low-resource environments.

### Core Files

- `robot.py`: Main application logic. This is a single-file script design.
- `requirements.txt`: Python dependencies.
- `jarvis.umdl`: Snowboy wake word model. (Currently a placeholder)
- `.env`: Stores API keys. **Do not commit this file or its contents directly into code.**
- `README.md`: Project documentation.
- `AGENTS.md`: This file.

### Development Guidelines

1.  **Understand the Constraints:**
    *   **Low Latency:** All modifications should prioritize speed and responsiveness.
    *   **Minimal Dependencies:** Only add new dependencies if absolutely necessary and they are lightweight.
    *   **Orange Pi PC Target:** Code should be compatible with ARM architecture and resource limitations of this device.
    *   **Python 3.9+:** Ensure code compatibility.

2.  **API Keys and Sensitive Information:**
    *   API keys are managed via the `.env` file, loaded using `python-dotenv`.
    *   **Never hardcode API keys or other sensitive credentials directly into the source code (`robot.py` or any other script).**
    *   If you need to add a new configurable secret, add it to the `.env` structure and document it in `README.md`.

3.  **Modifying `robot.py`:**
    *   **Single File Structure:** The project aims for a single-file script for simplicity. If considering breaking it into multiple files, this would be a significant change and should be justified by substantial improvements in clarity or maintainability.
    *   **Error Handling:** Implement robust error handling. Log errors to `robot_error.log` using the configured logger. Provide user-friendly feedback via TTS when appropriate (e.g., "I couldn't connect to the internet").
    *   **Asynchronous Operations:** Use `async` and `await` for I/O-bound operations (like API calls) to maintain responsiveness, as demonstrated in the current `robot.py`.
    *   **Comments and Clarity:** Write clear, concise comments, especially for complex logic or non-obvious decisions.
    *   **Audio Processing:** Pay close attention to audio formats, rates, and chunk sizes. These are critical for VAD and STT accuracy.

4.  **Dependencies (`requirements.txt`):**
    *   If adding or changing a dependency, update `requirements.txt`.
    *   Ensure the chosen libraries are compatible with the Orange Pi PC environment (ARM). Some libraries might require system-level dependencies. Document these in `README.md`.

5.  **Wake Word Model (`jarvis.umdl`):**
    *   This file is a binary model. You will not be able. to modify its content directly.
    *   If the task involves changing the wake word or its properties, it implies retraining or obtaining a new model file. This is outside the scope of typical code changes you would make.

6.  **Documentation:**
    *   Keep `README.md` updated with any changes to setup, configuration, or operation.
    *   If you add new features or change existing ones significantly, ensure they are documented.

7.  **Testing (Conceptual):**
    *   While a formal test suite might not be in place for this minimal project, manually test your changes thoroughly.
    *   Consider edge cases: no internet, API errors, invalid audio input, etc.
    *   If you implement new functions, consider how they could be unit-tested in principle.

8.  **Committing Changes:**
    *   Follow standard commit message conventions: a short subject line (max 50 chars), a blank line, and a more detailed body if necessary.
    *   Ensure `.gitignore` is respected.

9.  **Specific Library Notes:**
    *   **Snowboy:** Sensitivity and model paths are key configurations.
    *   **Gladia:** The SDK usage for streaming/byte input should be verified against their latest documentation if issues arise. Latency targets are important.
    *   **Grok:** Model selection and response style ("concise") are important.
    *   **RHVoice:** Relies on system installation. Python wrappers might vary. The current implementation uses `os.system` which is functional but could be improved if a robust Pythonic binding is preferred and works well on Orange Pi.
    *   **PyAudio & WebrtcVAD:** Correct audio stream parameters are crucial. VAD aggressiveness affects when the system detects the end of speech.

10. **Interacting with User/Requestor:**
    *   If a request is ambiguous or seems to conflict with project goals (e.g., adding a very heavy dependency), ask for clarification.
    *   Clearly state any assumptions you make.

By following these guidelines, you'll help maintain the project's focus and ensure its suitability for the target environment.
