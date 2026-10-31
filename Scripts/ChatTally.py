"""THE $ TALLY - top-right corner of the chat window, live from the ledger."""
import json
import re

P = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed\ApexChatPage.html"
src = open(P, encoding="utf-8-sig").read()

CSS = """
#apex-money-tally{position:fixed;top:10px;right:14px;z-index:9999;
  background:#0e1a14;color:#57e389;border:1px solid #2c5f40;border-radius:14px;
  padding:6px 14px;font:600 13px/1.3 'Segoe UI',system-ui,sans-serif;
  box-shadow:0 2px 10px rgba(0,0,0,.35);cursor:default;user-select:none}
#apex-money-tally small{color:#9fd8b8;font-weight:400;margin-left:6px}
"""
JS = """
(async function apexMoneyTally(){
  const el = document.createElement('div');
  el.id = 'apex-money-tally';
  el.textContent = '$ --.--';
  el.title = "The family's earned money (net of spend; 80% spending cap)";
  document.body.appendChild(el);
  async function tick(){
    try{
      const r = await fetch('/talk/status');
      const j = await r.json();
      const v = (typeof j.money_usdc === 'number') ? j.money_usdc.toFixed(2) : '--.--';
      el.innerHTML = '$ ' + v + '<small>earned</small>';
    }catch(e){}
  }
  tick(); setInterval(tick, 30000);
})();
"""

if "apex-money-tally" in src:
    print("tally already present")
else:
    if "</style>" in src:
        src = src.replace("</style>", CSS + "</style>", 1)
    else:
        src = src.replace("</head>", "<style>" + CSS + "</style></head>", 1)
    if "</body>" in src:
        src = src.replace("</body>", "<script>" + JS + "</script></body>", 1)
    else:
        src += "<script>" + JS + "</script>"
    open(P, "w", encoding="utf-8-sig").write(src)
    print("tally injected (top-right, live-polling /talk/status every 30s)")