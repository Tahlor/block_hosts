import subprocess
message_volume = .5
set_volume_command = "[Audio]::Volume = {};"
get_volume_command = "$CurrentVolume = [Audio]::Volume;"

# Using f-string to format the commands with required values
set_volume = set_volume_command.format(message_volume)

command = f'''
{get_volume_command} ;
{set_volume.format(0)} ;
Add-Type –AssemblyName System.Speech;
(New-Object System.Speech.Synthesis.SpeechSynthesizer).Speak("Hello");
Start-Sleep -Seconds 5;
[Audio]::Volume = $CurrentVolume;
'''
print(command)
result = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, executable='powershell.exe')
print(result)
