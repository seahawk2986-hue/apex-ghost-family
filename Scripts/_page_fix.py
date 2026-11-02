"""THE PAGE-FIX (file-based; never inline for quote-heavy edits)."""
p = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed\ApexChatPage.html"
s = open(p, encoding="utf-8-sig").read()
s = s.replace('s.textContent="SEND"', 's.textContent="Send"')
s = s.replace(
    'document.getElementById("send").onclick=()=>{if(streamCtrl){return;}send();};',
    'document.getElementById("send").onclick=()=>send();')
open(p, "w", encoding="utf-8").write(s)
print("[page] the stop-click + the label = fixed")
# the quick-sanity: the send's function = parses (the JS-check via a real parser
# = node? none - the honest-check = the balanced-brace-count of the send-block
i0 = s.find("let streamCtrl=null")
sblk = s[i0:i0 + 4200]
print("braces in the send-block:", sblk.count("{") - sblk.count("}"))
print("stops wired:", 'streamCtrl.abort()' in s, '| aria-live:', 'aria-live' in s)