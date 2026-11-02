"""The ApexChat layout-cure: force single-column chat, cap the width, keep the style."""
import io
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
P = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed\ApexChatPage.html"
css = open(P, encoding="utf-8-sig").read()

cures = {
    "body{": "body{max-width:100%;overflow-x:hidden;",
    "#chat{flex:1;overflow-y:auto;padding:16px 12px;display:flex;flex-direction:column;gap:10px}":
        ("#chat{flex:1;overflow-y:auto;padding:16px 12px;display:flex;flex-direction:column;"
         "gap:10px;width:100%;max-width:780px;margin:0 auto;column-count:1;grid-template-columns:none}"),
    ".row{display:flex;gap:8px;max-width:88%}":
        ".row{display:flex;gap:8px;max-width:92%;width:100%;column-count:1}",
}
n = 0
for old, new in cures.items():
    if old in css:
        css = css.replace(old, new)
        n += 1
# the guard: no column/grid anywhere that can split the chat
css += ("\n/* the layout-cure: single-column, width-capped, no grid split */\n"
        "*{column-span:none!important}\n"
        "#chat,.row,.bubble{columns:1!important;grid-area:auto!important}"
        "\n.row .bubble{flex:1 1 auto;min-width:0}\n")
open(P, "w", encoding="utf-8").write(css)
print("[ApexChatPage]:", n, "cures applied + the no-split guard = appended")
print("[done]: refresh the browser tab — the chat = single-column, capped, centered")