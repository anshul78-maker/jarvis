# JARVIS Setup Guide
## Your Personal AI Agent — Complete Installation

---

## STEP 1 — Install Claude Code (Anthropic's Official Agent)

Claude Code is a terminal-based agent that can control your computer, write
code, manage files, and browse the web autonomously.

### Requirements
- Node.js 18 or higher
- An Anthropic API key (get one free at https://console.anthropic.com)

### Install

```bash
# Install globally
npm install -g @anthropic-ai/claude-code

# Run it
claude
```

### First Run
```bash
# Set your API key (only needed once)
export ANTHROPIC_API_KEY=your_key_here

# Start Claude Code
claude

# Example commands you can give it:
# "Open my Downloads folder and show me the 5 largest files"
# "Create a Python script that renames all my photos by date"
# "Search my Documents for any PDF about invoices"
# "Open Chrome and go to Gmail"
```

### Make API Key Permanent (so you don't retype it)

**Windows (PowerShell):**
```powershell
[System.Environment]::SetEnvironmentVariable("ANTHROPIC_API_KEY","your_key","User")
```

**Mac/Linux:**
```bash
echo 'export ANTHROPIC_API_KEY=your_key_here' >> ~/.bashrc
source ~/.bashrc
```

---

## STEP 2 — Set Up the Full Python JARVIS Agent

### 2a. Install Python (if not installed)
Download from https://python.org — version 3.10 or higher.

### 2b. Install Dependencies

```bash
# Navigate to the jarvis folder
cd jarvis

# Install all packages
pip install -r requirements.txt
```

**Common Issues:**
- `pyaudio` fails on Windows → install from:
  https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio
  then: `pip install PyAudio‑0.2.14‑cpXX‑...whl`
- `pyaudio` fails on Mac → run first: `brew install portaudio`
- Linux → run first: `sudo apt-get install python3-pyaudio portaudio19-dev`

### 2c. Add Your API Key

Open `jarvis.py` and replace line 24:
```python
API_KEY = "YOUR_API_KEY_HERE"
```
with your actual key from https://console.anthropic.com

OR better, set it as environment variable (see Step 1 above).

### 2d. Run JARVIS

```bash
# Text mode (easiest)
python jarvis.py

# Voice mode (speak to it!)
python jarvis.py --voice
```

---

## STEP 3 — Features & How to Use Them

### 3a. Voice Control
```
You:    "Hey Jarvis, open YouTube"
JARVIS: Opens YouTube in your browser

You:    "Create a file on my desktop called notes.txt"
JARVIS: Creates the file

You:    "Remind me to call mom in 20 minutes"
JARVIS: Sets a reminder, notifies you at the right time
```

### 3b. File Management
```
You:    "Search my Documents for all PDF files"
You:    "Move budget.xlsx to my Desktop"
You:    "Delete the file temp_old.txt"
You:    "Create a new folder called Projects"
```

### 3c. App & Web Control
```
You:    "Open Spotify"
You:    "Open Google Chrome and go to GitHub"
You:    "Take a screenshot and save it to Desktop"
You:    "Open the terminal and run ls -la"
```

### 3d. Memory
JARVIS remembers your conversations for 7 days automatically.
It stores everything in: ~/.jarvis_memory.db

```
You:    "Remember that my work email is work@company.com"
You:    "What was that email I told you about?"
```

### 3e. Reminders
```
You:    "Remind me to check my emails in 1 hour"
You:    "Set a reminder for meeting prep in 30 minutes"
```

---

## STEP 4 — Make JARVIS Start Automatically

### Windows (Start on login)
1. Press Win + R → type `shell:startup` → Enter
2. Create a shortcut to: `python C:\path\to\jarvis\jarvis.py`

### Mac (Start on login via launchd)
Create file: `~/Library/LaunchAgents/com.jarvis.agent.plist`
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "...">
<plist version="1.0">
<dict>
    <key>Label</key><string>com.jarvis.agent</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>/Users/YOU/jarvis/jarvis.py</string>
    </array>
    <key>RunAtLoad</key><true/>
</dict>
</plist>
```
Then: `launchctl load ~/Library/LaunchAgents/com.jarvis.agent.plist`

### Linux (systemd service)
Create file: `/etc/systemd/system/jarvis.service`
```ini
[Unit]
Description=JARVIS AI Agent
After=network.target

[Service]
User=YOUR_USERNAME
WorkingDirectory=/home/YOU/jarvis
ExecStart=/usr/bin/python3 jarvis.py
Restart=always

[Install]
WantedBy=multi-user.target
```
Then: `sudo systemctl enable jarvis && sudo systemctl start jarvis`

---

## Quick Reference Card

| What you say           | What JARVIS does              |
|------------------------|-------------------------------|
| "Open [app name]"      | Launches the app              |
| "Go to [website]"      | Opens in browser              |
| "Create file [name]"   | Creates file on your system   |
| "Search for [*.pdf]"   | Finds matching files          |
| "Move [file] to [dir]" | Moves the file                |
| "Screenshot"           | Takes and saves screenshot    |
| "Remind me in X mins"  | Sets a timer/reminder         |
| "Run [command]"        | Executes terminal command     |
| "voice"                | Toggles voice mode on/off     |
| "clear"                | Clears conversation history   |
| "quit"                 | Shuts JARVIS down             |

---

## Troubleshooting

**No voice output:**
- `pip install pyttsx3`
- On Linux: `sudo apt install espeak`

**No voice input (microphone):**
- Check microphone is connected and allowed in system settings
- `pip install SpeechRecognition pyaudio`

**API errors:**
- Make sure `ANTHROPIC_API_KEY` is set correctly
- Check you have API credits at https://console.anthropic.com

**pyautogui not working:**
- On macOS: grant Accessibility permissions in System Preferences
- On Linux: `sudo apt install python3-xlib`
