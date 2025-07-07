# Voice-Controlled AI Robot for Orange Pi PC

This project implements a minimal Python-based voice-controlled AI robot assistant, specifically optimized for low-latency performance on an Orange Pi PC. It utilizes various services and libraries for wake word detection, speech-to-text, AI processing, and text-to-speech.

## Features

- **Wake Word Detection:** Uses Snowboy with a custom model (`jarvis.umdl`) for the wake word "jarvis".
- **Speech-to-Text (STT):** Leverages Gladia API for fast and accurate transcription.
- **AI Agent:** Queries Grok API for intelligent responses.
- **Text-to-Speech (TTS):** Employs RHVoice for voice synthesis.
- **Audio I/O:** Uses PyAudio for audio capture and webrtcvad for Voice Activity Detection (VAD).
- **Low-Resource Optimization:** Designed with ARM low-resource environments like the Orange Pi PC in mind, keeping dependencies minimal.
- **Error Logging:** Logs errors to a local file (`robot_error.log`).

## Project Structure

- `robot.py`: The main application script containing all the core logic.
- `requirements.txt`: Lists all Python dependencies.
- `jarvis.umdl`: Placeholder for the Snowboy wake word model. **You need to replace this with your actual trained model.**
- `.env`: Configuration file for API keys (Gladia and Grok). **This file is not committed to the repository; you need to create it from `.env.example` or manually.**
- `.gitignore`: Specifies intentionally untracked files that Git should ignore.
- `robot_error.log`: Log file for errors (created automatically when an error occurs).

## Setup Instructions

### Prerequisites

1.  **Orange Pi PC:** The application is optimized for this platform.
2.  **Python 3.9+:** Ensure Python 3.9 or a newer version is installed.
3.  **API Keys:**
    *   **Gladia API Key:** For speech-to-text. Obtain from [Gladia](https://gladia.io/).
    *   **Grok API Key:** For the AI agent. Obtain from [Grok](https://grok.com/). (Note: Grok access might be specific, replace with your chosen LLM provider if needed)
4.  **Snowboy Wake Word Model:**
    *   A `jarvis.umdl` file is required. The one in the repository is a placeholder. You need to train your own model for the wake word "jarvis" using Snowboy's tools (if available) or find a compatible pre-trained model.
5.  **RHVoice:**
    *   Ensure RHVoice and a compatible English voice (e.g., `en_us`) are installed and configured on your system. Installation methods vary by Linux distribution. You may need `RHVoice-service` running or `RHVoice-test` command line tool available.
    *   The `rhvoice-wrapper` Python library might need specific setup for your RHVoice installation.

### Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd <repository-directory>
    ```

2.  **Create and configure the `.env` file:**
    Copy the provided `.env.example` (if available) or create a new `.env` file in the root directory:
    ```
    GLADIA_API_KEY="YOUR_GLADIA_API_KEY"
    GROK_API_KEY="YOUR_GROK_API_KEY"
    ```
    Replace `"YOUR_GLADIA_API_KEY"` and `"YOUR_GROK_API_KEY"` with your actual API keys.

3.  **Replace the placeholder `jarvis.umdl`:**
    Place your trained Snowboy model file for "jarvis" in the root directory, replacing the existing placeholder `jarvis.umdl`.

4.  **Install Python dependencies:**
    It's recommended to use a virtual environment:
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    ```
    *Note: Some dependencies like `pyaudio` and `snowboydecoder` might have system-level library prerequisites (e.g., `portaudio`, `atlas`). Consult their documentation for installation on your specific Orange Pi OS.*

5.  **Install System Dependencies (Example for Debian/Ubuntu based systems):**
    You might need to install libraries for PyAudio, Snowboy, and RHVoice. For example:
    ```bash
    sudo apt-get update
    sudo apt-get install python3-pyaudio libatlas-base-dev # For PyAudio and Snowboy
    # For RHVoice, follow official installation guides. It might involve adding repositories or compiling from source.
    # Ensure 'RHVoice-test' command or the required library for 'rhvoice-wrapper' is working.
    ```

### Running the Assistant

Once all dependencies are installed and configurations are set:

```bash
python3 robot.py
```

The assistant will start listening for the wake word "jarvis".

## Error Logging

Errors are logged to `robot_error.log` in the project's root directory.

## Deployment (Systemd Example)

To have the robot auto-start on boot using `systemd`:

1.  Create a service file, for example, `/etc/systemd/system/robot-assistant.service`:

    ```ini
    [Unit]
    Description=Voice Controlled AI Robot
    After=network.target sound.target

    [Service]
    User=<your_username> # Replace with the user that will run the script
    Group=<your_group>   # Replace with the group for the user
    WorkingDirectory=/path/to/your/robot-assistant # Replace with the actual path to the project
    ExecStart=/path/to/your/robot-assistant/venv/bin/python3 /path/to/your/robot-assistant/robot.py # Adjust if not using a venv or path is different
    Restart=on-failure
    StandardOutput=syslog
    StandardError=syslog
    SyslogIdentifier=robot-assistant

    [Install]
    WantedBy=multi-user.target
    ```

2.  Replace `<your_username>`, `<your_group>`, and `/path/to/your/robot-assistant` with appropriate values.

3.  Enable and start the service:
    ```bash
    sudo systemctl daemon-reload
    sudo systemctl enable robot-assistant.service
    sudo systemctl start robot-assistant.service
    ```

4.  To check the status:
    ```bash
    sudo systemctl status robot-assistant.service
    journalctl -u robot-assistant.service -f # To view logs
    ```

## Contributing

Please refer to `AGENTS.md` for guidelines if you are an AI agent contributing to this project. For human contributors, please open an issue or pull request.
