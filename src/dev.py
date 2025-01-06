from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import subprocess
import time
import sys
import os

class CodeChangeHandler(FileSystemEventHandler):
    def __init__(self):
        self.process = None
        self.restart_app()

    def restart_app(self):
        if self.process:
            self.process.terminate()
            self.process.wait()

        self.process = subprocess.Popen([sys.executable, os.path.dirname(__file__) + "/main.py"])

    def on_modified(self, event):
        if event.src_path.endswith('.py'):
            print(f"Detected change in {event.src_path}")
            self.restart_app()

if __name__ == "__main__":
    event_handler = CodeChangeHandler()
    observer = Observer()
    observer.schedule(event_handler, path='.', recursive=True)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        if event_handler.process:
            event_handler.process.terminate()
    observer.join()