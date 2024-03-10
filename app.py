import requests
import json
from datetime import datetime, timedelta
import time
from player import play_video_multiproc
import os

REPORT_TIME_INTERVAL = 60 # client reportuje stav na server kazdych n sekund
MAX_DELAY_TIME = 5 # flim muze byt spusten s maximalnim spozdenim n minut
RESTART_DELAY = 120 # po ukonceni se client restartuje za n sekund

def current_time() -> datetime:
    return datetime.now().time()

class App:
    def __init__(self) -> None:
        self.load_config()

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
            if (t-start_time) >= REPORT_TIME_INTERVAL:
                start_time = time.time()
                self.send_msg(f'Playing {filename}')

    # funkce na kontrolu toho, ze vsechny soubory existuji v media/
    def check_files(self):
        media_files = list(os.listdir(self.config["media_folder"]))
        if not self.config["schledule"]: return 'Schledule not created'
        files_misssing = []
        for _day, schledule in self.config["schledule"].items():
            for _time, filename in schledule:
                if filename not in media_files:
                    if filename is None:
                        files_misssing.append('None')
                        continue
                    files_misssing.append(filename)
        return files_misssing

    # funkce na pousteni filmu - ocekava vsechny soubory v media/
    def run(self):
        for time_str, filename in self.config["schledule"][str(self.config["current_day"])]:
            now = current_time()
            playback_start_time = datetime.strptime(time_str, "%H:%M").time()
            if now > playback_start_time:
                # pokud je spozdeni delsi nez max delay time, skipuju tenhle film a cekam na dalsi
                if (timedelta(hours=now.hour, minutes=now.minute) - timedelta(hours=playback_start_time.hour, minutes=playback_start_time.minute)) > timedelta(minutes=MAX_DELAY_TIME):
                    self.send_msg(f'Started after {time_str} - skipping {filename}')
                    continue
                else:
                    self.send_msg(f'Starting playback: {filename} with delay')
                    self.play(filename)
                    self.send_msg(f'Finished playback: {filename}')

            elif now <= playback_start_time:
                # DODELAT SPORIC OBRAZOVKY
                start_time = time.time()
                self.send_msg(f'Waiting for {time_str} to play {filename}')
                while now < playback_start_time: # wait for desired time
                    now = current_time()
                    t = time.time()
                    if (t-start_time) >= REPORT_TIME_INTERVAL:
                        start_time = time.time()
                        self.send_msg(f'Waiting for {time_str} to play {filename}')
                self.send_msg(f'Starting playback: {filename}')
                self.play(filename)
                self.send_msg(f'Finished playback: {filename}')
        self.send_msg('Finished all films')

    def start(self):
        self.log('START')
        self.send_msg('Starting')
        if self.get_program():
            self.send_msg('Fetched program')
        else:
            if not self.config["schledule"] and not self.config["program"]:
                self.log('No progam or schledule - restarting in 10s')
                time.sleep(10)
                self.start()
                quit()
            else:
                self.log('Continuing using locally saved program/schledule')
        if self.create_schledule():
            self.send_msg('Schledule created')
        if self.get_current_day():
            self.send_msg('Fetched current day')
        self.send_msg(f'Continuing with day: {self.config["current_day"]}')
        
        if self.config["current_day"] == 0:
            pass
            # DODELAT STAHOVANI SOUBORU
        else:
            files_missing = self.check_files()
            if files_missing:
                self.send_msg(f'Missing media files: {",".join(files_missing)} - continuing anyway')
            else:
                self.send_msg('All media files present')
            # POUSTENI FILMU
            self.run()
        
def main():
    app = App()
    try:
        app.start()
    except Exception as e:
        app.log(f'Critical error - {e.__repr__()} - restarting')
        app.send_msg(f'Critical error - {e.__repr__()} - restarting')
        main()
        quit()
    app.send_msg(f'Finished running app - starting again in {RESTART_DELAY}s')
    time.sleep(RESTART_DELAY)
    main()

if __name__ == '__main__':
    main()