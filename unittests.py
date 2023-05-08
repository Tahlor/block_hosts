
from block import on_zoom_call, flush_windows, run_windows


def test_on_zoom_call():
    result = on_zoom_call()
    print(result)

def test_flush():
    flush_windows()

def test_bell():
    run_windows("echo ")
    # powershell -c (New-Object Media.SoundPlayer 'c:\PathTo\YourSound.wav').PlaySync();
    # echo  > ./bell.wav


if __name__ == "__main__":
    test_on_zoom_call()
    #test_flush()
    test_bell()
