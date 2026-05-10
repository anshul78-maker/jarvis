#!/usr/bin/env python3
"""
JARVIS - Personal AI Agent
Powered by Claude API | Voice + Memory + Computer Control
"""

import os
import json
import time
import subprocess
import webbrowser
import shutil
import sqlite3
import datetime
import threading
from pathlib import Path

# ── Optional imports (install via requirements.txt) ──────────────────────────
try:
    import anthropic
except ImportError:
    print("❌ Run: pip install anthropic")
    exit(1)

try:
    import speech_recognition as sr
    VOICE_INPUT = True
except ImportError:
    VOICE_INPUT = False
    print("⚠️  Voice input disabled. Run: pip install SpeechRecognition pyaudio")

try:
    import pyttsx3
    VOICE_OUTPUT = True
except ImportError:
    VOICE_OUTPUT = False
    print("⚠️  Voice output disabled. Run: pip install pyttsx3")

try:
    import pyautogui
    COMPUTER_CONTROL = True
except ImportError:
    COMPUTER_CONTROL = False
    print("⚠️  Computer control disabled. Run: pip install pyautogui")

# ─────────────────────────────────────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────────────────────────────────────
API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
if not API_KEY:
    print("\n❌ ERROR: No API key found!")
    print("   Open jarvis.py in Notepad and set your key on line 24:")
    print('   API_KEY = "sk-ant-your-key-here"')
    print("   Get a key at: https://console.anthropic.com\n")
    exit(1)
MODEL   = "claude-opus-4-5"
DB_PATH = Path.home() / ".jarvis_memory.db"

SYSTEM_PROMPT = """You are JARVIS, a highly intelligent personal AI assistant running locally on the user's computer.
You help with:
- Answering questions and having conversations
- Opening apps, websites, and files
- Managing files and folders
- Running system commands
- Reminding the user of tasks
- Performing web searches

When the user asks you to DO something on their computer, respond with a JSON action block like:
{"action": "open_app", "target": "notepad"}
{"action": "open_url", "target": "https://google.com"}
{"action": "run_command", "command": "ls -la"}
{"action": "create_file", "path": "~/test.txt", "content": "Hello!"}
{"action": "search_files", "query": "*.pdf", "directory": "~/Documents"}
{"action": "move_file", "source": "~/file.txt", "destination": "~/Documents/"}
{"action": "delete_file", "path": "~/old_file.txt"}
{"action": "remind", "message": "Call mom", "minutes": 30}
{"action": "screenshot", "save_path": "~/Desktop/screenshot.png"}

For normal conversation, just reply naturally. Be concise, smart, and helpful.
Always remember the user's preferences and past conversations."""

# ─────────────────────────────────────────────────────────────────────────────
# MEMORY (SQLite)
# ─────────────────────────────────────────────────────────────────────────────
class Memory:
    def __init__(self):
        self.conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
        self._setup()

    def _setup(self):
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                role TEXT,
                content TEXT,
                timestamp TEXT
            );
            CREATE TABLE IF NOT EXISTS facts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT UNIQUE,
                value TEXT,
                updated TEXT
            );
            CREATE TABLE IF NOT EXISTS reminders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message TEXT,
                due_time TEXT,
                done INTEGER DEFAULT 0
            );
        """)
        self.conn.commit()

    def add_message(self, role: str, content: str):
        self.conn.execute(
            "INSERT INTO conversations (role, content, timestamp) VALUES (?, ?, ?)",
            (role, content, datetime.datetime.now().isoformat())
        )
        self.conn.commit()

    def get_recent(self, limit: int = 20) -> list:
        rows = self.conn.execute(
            "SELECT role, content FROM conversations ORDER BY id DESC LIMIT ?",
            (limit,)
        ).fetchall()
        return [{"role": r[0], "content": r[1]} for r in reversed(rows)]

    def save_fact(self, key: str, value: str):
        self.conn.execute(
            "INSERT OR REPLACE INTO facts (key, value, updated) VALUES (?, ?, ?)",
            (key, value, datetime.datetime.now().isoformat())
        )
        self.conn.commit()

    def get_fact(self, key: str) -> str | None:
        row = self.conn.execute("SELECT value FROM facts WHERE key=?", (key,)).fetchone()
        return row[0] if row else None

    def add_reminder(self, message: str, minutes: int):
        due = (datetime.datetime.now() + datetime.timedelta(minutes=minutes)).isoformat()
        self.conn.execute(
            "INSERT INTO reminders (message, due_time) VALUES (?, ?)",
            (message, due)
        )
        self.conn.commit()
        return due

    def get_due_reminders(self) -> list:
        now = datetime.datetime.now().isoformat()
        rows = self.conn.execute(
            "SELECT id, message FROM reminders WHERE due_time <= ? AND done = 0",
            (now,)
        ).fetchall()
        for row in rows:
            self.conn.execute("UPDATE reminders SET done=1 WHERE id=?", (row[0],))
        self.conn.commit()
        return [r[1] for r in rows]

    def clear_old(self, days: int = 7):
        cutoff = (datetime.datetime.now() - datetime.timedelta(days=days)).isoformat()
        self.conn.execute("DELETE FROM conversations WHERE timestamp < ?", (cutoff,))
        self.conn.commit()


# ─────────────────────────────────────────────────────────────────────────────
# VOICE ENGINE
# ─────────────────────────────────────────────────────────────────────────────
class VoiceEngine:
    def __init__(self):
        if VOICE_OUTPUT:
            self.engine = pyttsx3.init()
            self.engine.setProperty('rate', 175)
            self.engine.setProperty('volume', 1.0)
            voices = self.engine.getProperty('voices')
            # Pick a deeper voice if available
            for v in voices:
                if 'male' in v.name.lower() or 'david' in v.name.lower():
                    self.engine.setProperty('voice', v.id)
                    break
        if VOICE_INPUT:
            self.recognizer = sr.Recognizer()
            self.recognizer.pause_threshold = 0.8
            self.recognizer.energy_threshold = 300

    def speak(self, text: str):
        print(f"\n🤖 JARVIS: {text}\n")
        if VOICE_OUTPUT:
            self.engine.say(text)
            self.engine.runAndWait()

    def listen(self) -> str | None:
        if not VOICE_INPUT:
            return None
        try:
            with sr.Microphone() as source:
                print("🎤 Listening...")
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=15)
            text = self.recognizer.recognize_google(audio)
            print(f"👤 You said: {text}")
            return text
        except sr.WaitTimeoutError:
            return None
        except sr.UnknownValueError:
            return None
        except Exception as e:
            print(f"⚠️  Voice error: {e}")
            return None


# ─────────────────────────────────────────────────────────────────────────────
# COMPUTER CONTROL
# ─────────────────────────────────────────────────────────────────────────────
class ComputerControl:
    @staticmethod
    def open_app(name: str) -> str:
        name = name.lower()
        # Windows
        apps_win = {
            'notepad': 'notepad.exe', 'calculator': 'calc.exe',
            'paint': 'mspaint.exe', 'explorer': 'explorer.exe',
            'chrome': 'chrome', 'firefox': 'firefox',
            'word': 'winword', 'excel': 'excel',
            'vscode': 'code', 'terminal': 'cmd.exe',
            'spotify': 'spotify', 'discord': 'discord',
        }
        # macOS
        apps_mac = {
            'safari': 'Safari', 'chrome': 'Google Chrome',
            'finder': 'Finder', 'terminal': 'Terminal',
            'vscode': 'Visual Studio Code', 'spotify': 'Spotify',
            'notes': 'Notes', 'calendar': 'Calendar',
        }
        import platform
        try:
            if platform.system() == 'Windows':
                app = apps_win.get(name, name)
                subprocess.Popen(app, shell=True)
            elif platform.system() == 'Darwin':
                app = apps_mac.get(name, name)
                subprocess.Popen(['open', '-a', app])
            else:  # Linux
                subprocess.Popen([name], shell=True)
            return f"✅ Opened {name}"
        except Exception as e:
            return f"❌ Could not open {name}: {e}"

    @staticmethod
    def open_url(url: str) -> str:
        if not url.startswith('http'):
            url = 'https://' + url
        webbrowser.open(url)
        return f"✅ Opened {url}"

    @staticmethod
    def run_command(cmd: str) -> str:
        try:
            result = subprocess.run(
                cmd, shell=True, capture_output=True, text=True, timeout=15
            )
            output = result.stdout or result.stderr or "Done."
            return output[:500]  # Truncate long output
        except subprocess.TimeoutExpired:
            return "⚠️  Command timed out."
        except Exception as e:
            return f"❌ Error: {e}"

    @staticmethod
    def create_file(path: str, content: str = "") -> str:
        try:
            p = Path(path).expanduser()
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(content)
            return f"✅ Created {p}"
        except Exception as e:
            return f"❌ {e}"

    @staticmethod
    def search_files(query: str, directory: str = "~") -> str:
        try:
            d = Path(directory).expanduser()
            results = list(d.rglob(query))[:10]
            if not results:
                return f"No files matching '{query}' found in {d}"
            return "\n".join(str(r) for r in results)
        except Exception as e:
            return f"❌ {e}"

    @staticmethod
    def move_file(source: str, destination: str) -> str:
        try:
            s = Path(source).expanduser()
            d = Path(destination).expanduser()
            shutil.move(str(s), str(d))
            return f"✅ Moved {s.name} to {d}"
        except Exception as e:
            return f"❌ {e}"

    @staticmethod
    def delete_file(path: str) -> str:
        try:
            p = Path(path).expanduser()
            if p.is_dir():
                shutil.rmtree(p)
            else:
                p.unlink()
            return f"✅ Deleted {p.name}"
        except Exception as e:
            return f"❌ {e}"

    @staticmethod
    def take_screenshot(save_path: str = "~/Desktop/screenshot.png") -> str:
        if not COMPUTER_CONTROL:
            return "⚠️  pyautogui not installed."
        try:
            p = Path(save_path).expanduser()
            screenshot = pyautogui.screenshot()
            screenshot.save(str(p))
            return f"✅ Screenshot saved to {p}"
        except Exception as e:
            return f"❌ {e}"


# ─────────────────────────────────────────────────────────────────────────────
# ACTION EXECUTOR
# ─────────────────────────────────────────────────────────────────────────────
def execute_action(action_data: dict, memory: Memory) -> str:
    action = action_data.get("action", "")
    cc = ComputerControl()

    if action == "open_app":
        return cc.open_app(action_data.get("target", ""))
    elif action == "open_url":
        return cc.open_url(action_data.get("target", ""))
    elif action == "run_command":
        return cc.run_command(action_data.get("command", ""))
    elif action == "create_file":
        return cc.create_file(
            action_data.get("path", "~/new_file.txt"),
            action_data.get("content", "")
        )
    elif action == "search_files":
        return cc.search_files(
            action_data.get("query", "*"),
            action_data.get("directory", "~")
        )
    elif action == "move_file":
        return cc.move_file(
            action_data.get("source", ""),
            action_data.get("destination", "")
        )
    elif action == "delete_file":
        confirm = input(f"⚠️  Delete '{action_data.get('path')}'? (yes/no): ").strip().lower()
        if confirm == "yes":
            return cc.delete_file(action_data.get("path", ""))
        return "❌ Deletion cancelled."
    elif action == "remind":
        due = memory.add_reminder(
            action_data.get("message", "Reminder"),
            action_data.get("minutes", 5)
        )
        return f"✅ Reminder set for {due}"
    elif action == "screenshot":
        return cc.take_screenshot(action_data.get("save_path", "~/Desktop/screenshot.png"))
    else:
        return f"⚠️  Unknown action: {action}"


# ─────────────────────────────────────────────────────────────────────────────
# JARVIS BRAIN
# ─────────────────────────────────────────────────────────────────────────────
class Jarvis:
    def __init__(self):
        self.client  = anthropic.Anthropic(api_key=API_KEY)
        self.memory  = Memory()
        self.voice   = VoiceEngine()
        self._reminder_thread_running = True
        self._start_reminder_thread()

    def _start_reminder_thread(self):
        def check_reminders():
            while self._reminder_thread_running:
                due = self.memory.get_due_reminders()
                for msg in due:
                    print(f"\n⏰ REMINDER: {msg}")
                    self.voice.speak(f"Reminder: {msg}")
                time.sleep(30)

        t = threading.Thread(target=check_reminders, daemon=True)
        t.start()

    def think(self, user_input: str) -> str:
        self.memory.add_message("user", user_input)
        history = self.memory.get_recent(20)

        response = self.client.messages.create(
            model=MODEL,
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            messages=history
        )
        reply = response.content[0].text
        self.memory.add_message("assistant", reply)
        return reply

    def process(self, user_input: str) -> str:
        raw = self.think(user_input)

        # Check if the response contains an action
        import re
        json_match = re.search(r'\{[^{}]*"action"[^{}]*\}', raw)
        if json_match:
            try:
                action_data = json.loads(json_match.group())
                result = execute_action(action_data, self.memory)
                # Clean text around the JSON
                text_before = raw[:json_match.start()].strip()
                clean_reply = text_before if text_before else f"Done! {result}"
                return f"{clean_reply}\n[{result}]"
            except json.JSONDecodeError:
                pass

        return raw

    def run(self, use_voice: bool = False):
        self.voice.speak("JARVIS online. How can I help you?")
        print("=" * 55)
        print("  JARVIS — Your Personal AI Agent")
        print("  Type 'voice' to toggle voice mode")
        print("  Type 'clear' to clear chat history")
        print("  Type 'quit' to exit")
        print("=" * 55)

        while True:
            try:
                # Get input
                if use_voice and VOICE_INPUT:
                    user_input = self.voice.listen()
                    if not user_input:
                        continue
                else:
                    user_input = input("👤 You: ").strip()

                if not user_input:
                    continue

                # Special commands
                if user_input.lower() == 'quit':
                    self.voice.speak("Goodbye!")
                    self._reminder_thread_running = False
                    break
                elif user_input.lower() == 'voice':
                    use_voice = not use_voice
                    mode = "ON" if use_voice else "OFF"
                    self.voice.speak(f"Voice mode {mode}")
                    continue
                elif user_input.lower() == 'clear':
                    self.memory.clear_old(days=0)
                    print("🗑️  History cleared.")
                    continue

                # Process and respond
                response = self.process(user_input)
                self.voice.speak(response)

            except KeyboardInterrupt:
                self.voice.speak("Shutting down. Goodbye!")
                break


# ─────────────────────────────────────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys
    use_voice = "--voice" in sys.argv or "-v" in sys.argv
    jarvis = Jarvis()
    jarvis.run(use_voice=use_voice)
