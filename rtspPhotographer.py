import json
import os
import threading
import sys
from threading import Event
import time
from watchdog import observers
from watchdog.events import FileSystemEventHandler
import vlc

class ConfigLoader:
    def __init__(self, file_path):
        self.file_path = file_path
        self.on_config_load = Event()
        
        if not os.path.exists(self.file_path):
            print(f"\nConfiguration file not found at {self.file_path}")
            self._create_config()
        else:
            self._load_config()
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
            print("\n>>> Please add your RTSP streams to the configuration file. <<<")


    def _load_config(self):
        with open(self.file_path, 'r') as file:
            data = json.load(file)
        
        print("\nLoaded configuration file:")
        for stream in data['streams']:
            print(f"## Stream: {stream['name']}, URL: {stream['url']}")
            
        self.on_config_load.set()
        self.streams = data['streams']


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



class Photographer:
    def __init__(self, output_dir, config_loader):
        self.output_dir = output_dir
        self.config_loader = config_loader
        self.stream_threads = []

        self.config_event_thread = threading.Thread(target=self._wait_for_config_load_event, daemon=True)
        self.config_event_thread.start()


    def _wait_for_config_load_event(self):
        while True:
            self.config_loader.on_config_load.wait()
            self._load_streams()
            self.config_loader.on_config_load.clear()


    def interrupt(self):
        self._stop_stream_threads()


    def _load_streams(self):
        self.streams = self.config_loader.get_config()
        if not self.streams or self.streams is None:
            return

        self._stop_stream_threads()
        print(f"\nTrying to load {len(self.streams)} streams:")
        for stream in self.streams:
            thread = threading.Thread(target=self._stream_thread, args=(stream.get('name'), stream.get('url')))
            thread.start()
            self.stream_threads.append(thread)


    def _stop_stream_threads(self):
        self.stream_threads_flag = False
        if self.stream_threads == []:
            return
        
        self.stream_threads_flag = True
        for thread in self.stream_threads:
            thread.join()
            
        self.stream_threads_flag = False
        self.stream_threads = []


    def _stream_thread(self, name, url):
        try:
            media_player = vlc.Instance("--vout=dummy").media_player_new()
            media = vlc.Media(url)
        except Exception as e:
            self._stream_thread(name, url)
            return
        
        while True:
            print(f"\nTrying to connect to stream {name} at {url}")
            media_player.set_media(media)
            media_player.play()
            
            first_frame = True
            
            time.sleep(5)
            while media_player.will_play():
                counter = 0
                while not media_player.is_playing():
                    time.sleep(0.1)
                    counter += 1
                    if counter > 50:
                        print(f"Connection to stream {name} at {url} failed")
                        break
                
                if first_frame:
                    print(f"Succesfully connected to stream {name} at {url}")
                    first_frame = False
                    
                media_player.video_take_snapshot(0, os.path.join(self.output_dir, f"{name}.jpg"), 0, 0)
                time.sleep(1)
                
                if self.stream_threads_flag:
                    break
            if self.stream_threads_flag:
                break
        media_player.stop()
        media_player.release()


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
        print("rtspPhotographer has been terminated")
        sys.exit()


if __name__ == "__main__":
    main()




# TODO: Install vlc when not installed
# TODO: refresh stream every hour?
# TODO: remove error messages from vlc
# TODO: run vlc in dummy mode