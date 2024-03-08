import requests
import json
from datetime import datetime

class App:
    def __init__(self) -> None:
        self.load_config()

    def load_config(self):
        with open('config.json', 'r') as f:
            self.config = json.load(f)

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
            self.program = response.json()
            return True
        except:
            self.log('Fetching program failed - server offline')
            return False
        
    def start(self):
        self.log('START')
        self.send_msg('Starting')
        self.get_program()
        self.send_msg('Fetched program')
        print(self.program)

if __name__ == '__main__':
    app = App()
    app.start()