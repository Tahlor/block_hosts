from block import on_zoom_call, flush_windows


def test_on_zoom_call():
    result = on_zoom_call()
    print(result)

def test_flush():
    flush_windows()

if __name__ == "__main__":
    #test_on_zoom_call()
    test_flush()