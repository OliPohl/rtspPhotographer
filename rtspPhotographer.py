import json
import os
import threading
import sys
from threading import Event
import time
from watchdog import observers
from watchdog.events import FileSystemEventHandler
import datetime
import ffmpeg
import cv2
import numpy as np


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
            print("\n>>> Please add your RTSP streams to the configuration file <<<")
        sys.exit()


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
        
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

        self.config_event_thread = threading.Thread(target=self._wait_for_config_load_event, daemon=True)
        self.config_event_thread.start()

        self.refresh_thread = threading.Thread(target=self._refresh_streams, daemon=True)
        self.refresh_thread.start()


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


    def _refresh_streams(self):
        while True:
            now = datetime.datetime.now().time()
            tomorrow = datetime.datetime.now() + datetime.timedelta(days=1)
            target_time = datetime.time(3, 0, 0)
            if now > target_time:
                target_datetime = datetime.datetime.combine(tomorrow, target_time)
            else:
                target_datetime = datetime.datetime.combine(datetime.datetime.now(), target_time)

            time_to_wait = (target_datetime - datetime.datetime.now()).total_seconds()
            time.sleep(time_to_wait)

            print("\nRestarting streams...")
            self._load_streams()


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
            while True:
                print(f"\nTrying to connect to {name} at {url}...")
                first_frame = True
                
                args = {"rtsp_transport": "tcp", "fflags": "nobuffer", "flags": "low_delay", "timeout": "1"}
                print("Probing stream...")
                probe = ffmpeg.probe(url)
                print("capturing stream info...")
                cap_info = next((stream for stream in probe['streams'] if stream['codec_type'] == 'video'))
                width = cap_info['width']
                height = cap_info['height']
                print("processing stream...")
                process = (ffmpeg
                            .input(url, **args)
                            .output('pipe:', format='rawvideo', pix_fmt='rgb24')
                            .overwrite_output()
                            .run_async(pipe_stdout=True))

                last_time = time.time()
                while True:
                    in_bytes = process.stdout.read(1280 * 720 * 3)
                    
                    if not in_bytes:
                        print(f"\nConnection to {name} at {url} lost")
                        process.kill()
                        break
                
                    if first_frame:
                        first_frame = False
                        print(f"\nSuccessfully connected to {name} at {url}!")
                        
                    if time.time() - last_time <= 60:
                        in_frame = (np.frombuffer(in_bytes, np.uint8).reshape([height, width, 3]))
                        
                        frame = cv2.resize(in_frame, (1280, 720))
                        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                        cv2.imwrite(os.path.join(self.output_dir, name + ".jpg"), frame)
                        
                        last_time = time.time()

                    if self.stream_threads_flag:
                        process.kill()
                        raise KeyboardInterrupt
        except KeyboardInterrupt:
            print(f"\nConnection to {name} at {url} interrupted")
            pass



def main():
    current_dir = os.path.dirname(os.path.realpath(__file__))
    output_dir = os.path.join(current_dir, "Photos")
    
    config_loader = ConfigLoader(os.path.join(current_dir, "config.json"))
    photographer = Photographer(output_dir, config_loader)
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        config_loader.interrupt()
        photographer.interrupt()
        print("\nrtspPhotographer has been terminated")
        sys.exit()


if __name__ == "__main__":
    main()