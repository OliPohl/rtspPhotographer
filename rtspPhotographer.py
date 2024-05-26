import json
import os
import threading
import time
from watchdog import observers
from watchdog.events import FileSystemEventHandler

class ConfigLoader:
    def __init__(self, file_path):
        self.file_path = file_path
        
        if not os.path.exists(self.file_path):
            print(f"\nConfiguration file not found at {self.file_path}.")
            self.create_config()
        self.streams = self.load_config()
        self.setup_watchdog()


    def create_config(self):
        data = {
            "streams": [
                {
                    "name": "example_stream",
                    "url": "rtsp://example.com/stream",
                }
            ]
        }
        with open(self.file_path, 'w') as file:
            json.dump(data, file, indent=4)
            print(f"Default configuration file created at {self.file_path}.")
            print(">>> Please add your RTSP streams to the configuration file. <<<")


    def load_config(self):
        with open(self.file_path, 'r') as file:
            data = json.load(file)
        
        print("\nLoaded configuration file:")
        for stream in data['streams']:
            print(f"## Stream: {stream['name']}, URL: {stream['url']}")
        return data['streams']


    def setup_watchdog(self):
        event_handler = FileSystemEventHandler()
        event_handler.on_modified = self.watchdog_on_modified
        observer = observers.Observer()
        observer.schedule(event_handler, path=os.path.dirname(self.file_path), recursive=False)
        self.debounce_time = 2
        self.debounce_timer = None
        
        def start_observer():
            print(f"\Watchdog initialized.")
            observer.start()
            while observer.is_alive():
                observer.join(1)
        
        self.observer_thread = threading.Thread(target=start_observer)
        self.observer_thread.start()


    def watchdog_on_modified(self, event):
        if (event.src_path == self.file_path):
            if self.debounce_timer is not None:
                self.debounce_timer.cancel()
            
            self.debounce_timer = threading.Timer(self.debounce_time, self.load_config)
            self.debounce_timer.start()


    def interrupt(self):
        self.observer.stop()
        self.observer.join()
        self.observer_thread.join()
        print("\nWatchdog terminatied.")


class Photographer:
    def __init__(self):
        pass


def main():
    config_loader = ConfigLoader(os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json"))


if __name__ == "__main__":
    main()