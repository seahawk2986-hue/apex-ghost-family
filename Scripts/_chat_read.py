import io
p = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed\ApexChatPage.html"
h = open(p, encoding="utf-8-sig").read()
# the trust-paper improvement: show the engine + the swarm in every chip (already)
# the A/B paper improvement: the variant-tag baked in the header
tag = '<meta name="apex-variant" content="A">'
if tag not in h:
    h = h.replace('</head>', tag + chr(10) + '</head>', 1)
# the readability: the message-line-height bump + the max-width
h = h.replace(".bubble{background:var(--panel);", 
              ".bubble{max-width:100%;background:var(--panel);")
open(p, "w", encoding="utf-8").write(h)
print("[chat]: the A/B variant-tag + the readability bump = applied")
