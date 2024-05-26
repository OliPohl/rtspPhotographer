import json
import os
import threading
from threading import Event
import time
from watchdog import observers
from watchdog.events import FileSystemEventHandler

class ConfigLoader:
    def __init__(self, file_path):
        self.file_path = file_path
        self.on_config_load = Event()
        
        if not os.path.exists(self.file_path):
            print(f"\nConfiguration file not found at {self.file_path}")
            self._create_config()
        self.streams = self._load_config()
        self._setup_watchdog()


    def _create_config(self):
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
            print(f"Default configuration file created at {self.file_path}")
            print(">>> Please add your RTSP streams to the configuration file. <<<")


    def _load_config(self):
        with open(self.file_path, 'r') as file:
            data = json.load(file)
        
        print("\nLoaded configuration file:")
        for stream in data['streams']:
            print(f"## Stream: {stream['name']}, URL: {stream['url']}")
            
        self.on_config_load.set()
        return data['streams']


    def get_config(self):
        return self.streams


    def _setup_watchdog(self):
        event_handler = FileSystemEventHandler()
        event_handler.on_modified = self._watchdog_on_modified
        self.observer = observers.Observer()
        self.observer.schedule(event_handler, path=os.path.dirname(self.file_path), recursive=False)
        self.debounce_time = 2
        self.debounce_timer = None
        
        def __start_observer():
            print(f"\nWatchdog initialized")
            self.observer.start()
            while self.observer.is_alive():
                self.observer.join(1)
        
        self.observer_thread = threading.Thread(target=__start_observer)
        self.observer_thread.start()


    def _watchdog_on_modified(self, event):
        if (event.src_path == self.file_path):
            if self.debounce_timer is not None:
                self.debounce_timer.cancel()
            
            self.debounce_timer = threading.Timer(self.debounce_time, self._load_config)
            self.debounce_timer.start()



    def interrupt(self):
        self.observer.stop()
        self.observer.join()
        self.observer_thread.join()
        print("\nWatchdog terminatied")


class Photographer:
    def __init__(self, output_dir, config_loader):
        self.output_dir = output_dir
        self.config_loader = config_loader
        
        self._load_streams()
        
        self.config_event_thread = threading.Thread(target=self._wait_for_config_load_event)
        self.config_event_thread.start()


    def _wait_for_config_load_event(self):
        self.config_loader.on_config_load.wait()

        self._load_streams()
        self.config_event_thread.join()
        self.config_event_thread.start()
        
        
    def interrupt(self):
        self.config_event_thread.join()
        print("Config Event terminated")


    def _load_streams(self):

        pass


def main():
    current_dir = os.path.dirname(os.path.realpath(__file__))
    
    config_loader = ConfigLoader(os.path.join(current_dir, "config.json"))
    photographer = Photographer(current_dir, config_loader)
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        config_loader.interrupt()
        photographer.interrupt()
        print("rtspPhotographer is no longer running")


if __name__ == "__main__":
    main()




# TODO: Put progromm in autstart?