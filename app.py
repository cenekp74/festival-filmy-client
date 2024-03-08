import requests
import json
from datetime import datetime
import time

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
        with open('log.txt', 'a') as f:
            f.write(f'{datetime.now().strftime("%Y.%m.%d %H:%M")}: {msg}\n')

    def send_msg(self, msg: str) -> bool:
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
        
        if self.config["current_day"] == 0:
            pass
            # DODELAT STAHOVANI SOUBORU

        # DODELAT POUSTENI FILMU
        
        
if __name__ == '__main__':
    app = App()
    app.start()