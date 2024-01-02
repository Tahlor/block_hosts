
from block import on_zoom_call, flush_windows, run_windows, system_beep


def test_on_zoom_call():
    result = on_zoom_call()
    print(f"ZOOM ACTIVE: {result}")

def test_flush():
    flush_windows()

def test_bell():
    #run_windows("echo ")
    # powershell -c (New-Object Media.SoundPlayer 'c:\PathTo\YourSound.wav').PlaySync();
    # echo  > ./bell.wav
    system_beep()
    print("Done with beep")

if __name__ == "__main__":
    test_bell()
    test_on_zoom_call()
    #test_flush()
