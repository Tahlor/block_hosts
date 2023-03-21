from block import on_zoom_call, windows_flush


def test_on_zoom_call():
    result = on_zoom_call()
    print(result)

def test_flush():
    windows_flush()

if __name__ == "__main__":
    #test_on_zoom_call()
    test_flush()