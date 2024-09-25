import webview
import time
import multiprocessing
import threading
from pywinauto.keyboard import send_keys

def wait_and_send_key(delay=3, key="a"):
    time.sleep(delay)
    send_keys(key)

def start_screensaver(url):
    win = webview.create_window("APF Screensaver", url, width=1920, height=1080, resizable=True, maximized=True, fullscreen=True, on_top=True)
    thread = threading.Thread(target=wait_and_send_key) # tohle je tu kvuli tomu, ze browsery zakazujou audio autoplay dokud user neinteraguje se strankou - nepovedlo se mi to nijak obejit
    thread.start()
    webview.start()

def start_screensaver_multiproc(url):
    proc = multiprocessing.Process(target=start_screensaver , args=(url,))
    proc.start()
    return proc