"""THE CHAT-ROUTE'S LIVE-PROOF: CrossBrain.ask(task_class='chat') through
the learned route (the groq-120b first)."""
import sys

sys.path.insert(0, r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed\Scripts")
import CrossBrain as XB

r = XB.ask('Reply ONLY the JSON {"ok": 1}.', task_class="chat",
           max_tokens=60)
print("[chat-route LIVE] ->", (r or "NONE")[:70])
print("[chat-route VERDICT]", "PASS (the learned route serves)" if
      '"ok"' in (r or "") else "HONEST-CHECK: " + str(r)[:60])