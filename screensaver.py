import os
import time
import multiprocessing
import threading
from pywinauto.keyboard import send_keys
from player import focus_to_window

def wait_and_send_key(delay=5, key="a"):
    time.sleep(delay)
    send_keys(key)

def waint_and_focus(delay=3):
    time.sleep(delay)
    focus_to_window("Firefox")

def start_screensaver(url):
    thread = threading.Thread(target=wait_and_send_key) # tohle je tu kvuli tomu, ze browsery zakazujou audio autoplay dokud user neinteraguje se strankou - nepovedlo se mi to nijak obejit
    thread.start()
    thread = threading.Thread(target=waint_and_focus)
    thread.start()
    os.system("taskkill -f -im firefox.exe")
    os.system(f"firefox\FirefoxPortable.exe --kiosk {url} -foreground")