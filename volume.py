import subprocess
import re

def get_volume_windows():
    command = "[Audio]::Volume"

    result = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, executable='powershell.exe')

    # Extract the float number at the end of the string
    output = result.stdout.decode().strip()
    #print(f"'{output}'")
    match = re.search(r"(\d+(\.\d+)?)\s*$", output)

    if match:
        volume = float(match.group(1))
        print(f"Found volume: {volume}")
    else:
        volume = .5
        print(f"Unknown volume, using {volume}")

    return volume


if __name__=='__main__':
    print(get_volume_windows())
