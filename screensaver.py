import webview
import time
import multiprocessing

def start_screensaver(url):
    win = webview.create_window("APF Screensaver", url, width=1920, height=1080, resizable=True, maximized=True, fullscreen=True, on_top=True)
    webview.start()

def start_screensaver_multiproc(url):
    proc = multiprocessing.Process(target=start_screensaver , args=(url,))
    proc.start()
    return proc