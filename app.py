import requests
import json
from datetime import datetime, timedelta
import time
from player import play_video_multiproc
import os
from screensaver import start_screensaver_multiproc
import multiprocessing

DEFAULT_CONFIG = {
                    "room": "III",
                    "current_day": 0,
                    "media_folder": "media/",
                    "server": "https://apf.jsnsgekom.cz",
                    "secondary_server": "https://apf2.jsnsgekom.cz",
                    "report_time_interval": 60, # client reportuje stav na server kazdych n sekund
                    "max_delay_time": 30, # flim muze byt spusten s maximalnim spozdenim n minut
                    "restart_delay": 3600, # po ukonceni se client restartuje za n sekund
                    "filenames": [],
                    "program": {},
                    "schledule": {}
                }

def current_time() -> datetime:
    return datetime.now().time()

class App:
    def __init__(self) -> None:
        try:
            self.load_config()
            if not self.validate_config():
                self.log('Config file invalid - using default config')
                self.config = DEFAULT_CONFIG
                self.write_config()
        except FileNotFoundError as e:
            self.log('No config file found - using default config')
            self.config = DEFAULT_CONFIG
            self.write_config()

    def validate_config(self) -> bool:
        keys = self.config.keys()
        for k in ["room", "current_day", "media_folder", "server", "filenames", "program", "schledule"]:
            if k not in keys:
                return False
        return True

    def load_config(self):
        with open('config.json', 'r') as f:
            self.config = json.load(f)

    def write_config(self):
        with open('config.json', 'w') as f:
            json.dump(self.config, f, indent=4)

    def log(self, msg):
        print(f'{datetime.now().strftime("%Y.%m.%d %H:%M")}: {msg}')
        with open('log.txt', 'a') as f:
            f.write(f'{datetime.now().strftime("%Y.%m.%d %H:%M")}: {msg}\n')

    def send_msg(self, msg: str) -> bool:
        self.log(f'Sending message - {msg}')
        try:
            response = requests.post(f'{self.config["server"]}/client/{self.config["room"]}/msg', data=msg)
            if response.text == '200': return True
            else:
                self.log(f'Sending message ({msg}) failed - server error')
                return False
        except:
            self.log(f'Sending message ({msg}) failed - server offline')
            self.log(f'Sending msg to secondary server')
            try: 
                _response = requests.post(f'{self.config["secondary_server"]}/client/{self.config["room"]}/msg', data=msg)
            except:
                self.log('Sending msg to secondary server failed - server offline')
            return False
        
    def get_program(self) -> bool:
        try:
            response = requests.get(f'{self.config["server"]}/get_program/{self.config["room"]}')
            if response.status_code != 200:
                self.log('Fetching progam failed - server error')
                return False
            self.config["program"] = response.json()
            self.write_config()
            return True
        except:
            self.log('Fetching program failed - server offline')
            return False
        
    def create_schledule(self) -> bool:
        if not self.config["program"]: return False
        schledule = {}
        for day in ['1', '2', '3']:
            schledule[day] = []
            for film in self.config["program"][day]:
                schledule[day].append((film["time_from"], film["filename"]))
            schledule[day] = sorted(schledule[day], key=lambda x: x[0])
        self.config["schledule"] = schledule
        self.write_config()
        return True
    
    def get_current_day(self) -> bool:
        try:
            response = requests.get(f'{self.config["server"]}/current_day')
            if response.status_code != 200:
                self.log('Fetching current day failed - server error')
                return False
            try:
                self.config["current_day"] = int(response.text)
            except:
                self.log('Fetching current day failed - invalid server response')
                return False
            self.write_config()
            return True
        except:
            self.log('Fetching current day failed - server offline')
            return False
        
    def play(self, filename):
        proc = play_video_multiproc(self.config["media_folder"] + filename)
        start_time = time.time()
        while proc.is_alive():
            t = time.time()
            if (t-start_time) >= self.config["report_time_interval"]:
                start_time = time.time()
                self.send_msg(f'Playing {filename}')

    def check_files(self):
        """
        funkce na kontrolu toho, ze vsechny media soubory ve schledule existuji v media_folder
        
        vraci list chybejicich filenames - pokud nic nechybi, vraci []
        """
        if not self.config["schledule"]: return 'Schledule not created'

        if not os.path.exists(self.config["media_folder"]): # if media folder doesnt exist, return all media files in schledule
            self.log(f'Media folder does not exist ({self.config["media_folder"]})')
            files_misssing = []
            for _day, schledule in self.config["schledule"].items():
                for _time, filename in schledule:
                    if filename is None:
                        files_misssing.append('None')
                        continue
                    files_misssing.append(filename)
            return files_misssing
        
        media_files = list(os.listdir(self.config["media_folder"]))
        files_misssing = []
        for _day, schledule in self.config["schledule"].items():
            for _time, filename in schledule:
                if filename not in media_files:
                    if filename is None:
                        files_misssing.append('None')
                        continue
                    files_misssing.append(filename)
        return files_misssing

    def run(self):
        """
        funkce na pousteni filmu - ocekava vsechny soubory v media_folder
        """
        for time_str, filename in self.config["schledule"][str(self.config["current_day"])]:
            now = current_time()
            playback_start_time = datetime.strptime(time_str, "%H:%M").time()
            if now > playback_start_time:
                # pokud je spozdeni delsi nez max delay time, skipuju tenhle film a cekam na dalsi
                if (timedelta(hours=now.hour, minutes=now.minute) - timedelta(hours=playback_start_time.hour, minutes=playback_start_time.minute)) > timedelta(minutes=self.config["max_delay_time"]):
                    self.send_msg(f'Started after {time_str} - skipping {filename}')
                    continue
                else:
                    self.send_msg(f'Starting playback: {filename} with delay')
                    self.play(filename)
                    self.send_msg(f'Finished playback: {filename}')

            elif now <= playback_start_time:
                start_screensaver_multiproc(f'{self.config["server"]}/screensaver/{self.config["room"]}')
                start_time = time.time()
                self.send_msg(f'Waiting for {time_str} to play {filename}')
                while now < playback_start_time: # wait for desired time
                    now = current_time()
                    t = time.time()
                    if (t-start_time) >= self.config["report_time_interval"]:
                        start_time = time.time()
                        self.send_msg(f'Waiting for {time_str} to play {filename}')
                os.system("taskkill -f -im firefox.exe")
                self.send_msg(f'Starting playback: {filename}')
                self.play(filename)
                self.send_msg(f'Finished playback: {filename}')
        self.send_msg('Finished all films')

    def start(self):
        self.log('START')
        if not self.send_msg('Starting'):
            self.config["server"], self.config["secondary_server"] = self.config["secondary_server"], self.config["server"]
            self.log(f"Switching to secondary server ({self.config["server"]})")
            if not self.send_msg('Starting - secondary server attempt'):
                self.config["server"], self.config["secondary_server"] = self.config["secondary_server"], self.config["server"]
                self.log("both servers unavailable")
            self.write_config()

        if self.get_program():
            self.send_msg('Fetched program')
        else:
            if not self.config["schledule"] and not self.config["program"]:
                self.log('No progam or schledule - restarting in 10s')
                time.sleep(10)
                main()
                quit()
            else:
                self.log('Continuing using locally saved program/schledule')
        if self.create_schledule():
            self.send_msg('Schledule created')
        if self.get_current_day():
            self.send_msg('Fetched current day')
        self.send_msg(f'Continuing with day: {self.config["current_day"]}')
        
        files_missing = self.check_files()
        if files_missing:
            self.send_msg(f'Missing media files: {",".join(files_missing)} - continuing anyway')
        else:
            self.send_msg('All media files present')

        if self.config["current_day"] == 0:
            if not files_missing:
                self.send_msg('Day 0 and all media files present - restarting in 10 minutes')
                time.sleep(600)
                main()
                quit()
            pass
            # DODELAT STAHOVANI SOUBORU
        else:
            self.run()
        
def main():
    app = App()
    try:
        app.start()
    except Exception as e:
        app.log(f'Critical error - {e.__repr__()} - restarting')
        app.send_msg(f'Critical error - {e.__repr__()} - restarting in 3s')
        time.sleep(3)
        main()
        quit()
    app.send_msg(f'Finished running app - starting again in {app.config["restart_delay"]}s')
    start_screensaver_multiproc(f'{app.config["server"]}/screensaver/{app.config["room"]}')
    time.sleep(app.config["restart_delay"])
    os.system("taskkill -f -im firefox.exe")
    main()

if __name__ == '__main__':
    multiprocessing.freeze_support() # tohle je potreba aby fungoval multiproc v pyinstalleru (ale jenom --onedir ne --onefile)
    main()