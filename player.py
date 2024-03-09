import vlc
import multiprocessing

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
    return proc