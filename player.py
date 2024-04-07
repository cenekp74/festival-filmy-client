import vlc
import multiprocessing
from time import sleep
import pygetwindow as gw
import pywinauto

def play_video(filename):
    player = vlc.MediaPlayer(filename)
    player.play()
    player.set_fullscreen(True)
    while True:
        if player.get_state() == vlc.State.Ended:
            player.release()
            return
        
def play_video_multiproc(filename) -> multiprocessing.Process:
    proc = multiprocessing.Process(target=play_video, args=(filename,))
    proc.start()
    sleep(5)
    focus_to_window('VLC (Direct3D11 output)')
    return proc


def focus_to_window(window_title):
    windows = gw.getWindowsWithTitle(window_title)
    if len(windows) > 0:
        window = windows[0]      
        if window.isActive == False:
            pywinauto.application.Application().connect(handle=window._hWnd).top_window().set_focus()
    else:
        print("Window not found.")