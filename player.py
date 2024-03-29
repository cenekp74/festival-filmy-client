import vlc
import multiprocessing
import pyautogui
from time import sleep

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
    sleep(2)
    bring_window_to_top('VLC (Direct3D11 output)')
    return proc

def bring_window_to_top(window_title):
    window_pos = pyautogui.getWindowsWithTitle(window_title)
    if len(window_pos) > 0:
        window_pos[0].activate()
    else:
        print("Window not found.")