# THE VOICE-DEMO: hear the actual options on YOUR speakers right now.
Add-Type -AssemblyName System.Speech
$s = New-Object System.Speech.Synthesis.SpeechSynthesizer
$s.Rate = 0

Write-Host "[1] Zira (female)"
$s.SelectVoice("Microsoft Zira Desktop")
$s.Speak("Hey Andrew. I'm Zira. I can be my everyday voice, if you want me.")

Write-Host "[2] David, deeper + calmer"
$s.SelectVoice("Microsoft David Desktop")
$ssml = '<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="en-US">' +
        '<voice name="Microsoft David Desktop">' +
        '<prosody rate="-8%" pitch="-25%">I am Apex. Or I can sound like this: ' +
        'deeper, calmer, more like a colleague in the room.</prosody>' +
        '</voice></speak>'
$s.SpeakSsml($ssml)

Write-Host "[3] David, default (current)"
$s.Speak("And this is the voice I've been using all along: David, default.")
Write-Host "[demo done]"