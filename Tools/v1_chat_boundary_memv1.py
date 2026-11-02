"""V1 inference-only boundary. No executor, research, file or shell callbacks.

Injected generate/context are Andrew's existing reviewed provider helpers.
This is a call-graph restriction, not a sandbox for a malicious host module.
"""
POLICY = 'apex-v1-chat-only-1'

# --- the MEMORY upgrade (additive; every call is try/except-guarded so the
# memory can never break, slow, or alter a chat) ---
import hashlib
import json
import os

MEM_DIR = os.path.join(os.path.expanduser(
    r"~\..\..\..", ) if False else r"C:\Users\seaha\Apex-Adapter", "room_memory")
# ^ kept simple: the adapter dir; created lazily.


def _mem_path(key):
    return os.path.join(MEM_DIR, "conv-" + key + ".json")


def _mem_load(key):
    try:
        with open(_mem_path(key), encoding="utf-8") as f:
            recs = json.load(f)
        lines = []
        for r in (recs if isinstance(recs, list) else [])[-12:]:
            if isinstance(r, dict) and r.get("q") and r.get("a"):
                lines.append("- " + r["q"] + " => " + r["a"])
        return "\n".join(lines)
    except Exception:
        return ""


def _mem_append(key, rec):
    try:
        os.makedirs(MEM_DIR, exist_ok=True)
        p = _mem_path(key)
        try:
            with open(p, encoding="utf-8") as f:
                recs = json.load(f)
            if not isinstance(recs, list):
                recs = []
        except Exception:
            recs = []
        recs.append(rec)
        with open(p, "w", encoding="utf-8") as f:
            json.dump(recs[-12:], f, ensure_ascii=False, indent=1)
    except Exception:
        pass


def chat_request(request):
    if not isinstance(request, dict):
        raise ValueError('Invalid V1 request')
    if request.get('schema_version', 1) != 1 or request.get('execution') is not None:
        raise ValueError('Execution requires the separately approved V2 endpoint')
    history = request.get('history', [])
    if not isinstance(history, list):
        raise ValueError('Invalid history')
    messages = []
    for message in history[-40:]:
        if not isinstance(message, dict):
            raise ValueError('Invalid history entry')
        sender, content = message.get('sender', '?'), message.get('content', '')
        if not isinstance(sender, str) or not isinstance(content, str):
            raise ValueError('Invalid history text')
        messages.append({'sender':sender[:80], 'content':content[:8000]})
    deadline = request.get('deadline_ms', 120000)
    if isinstance(deadline, bool) or not isinstance(deadline, int) or deadline < 1:
        raise ValueError('Invalid deadline')
    # Never forward client policy/approval/tool fields to a hook.
    return {'request_id':str(request.get('request_id', ''))[:80],
            'deadline_ms':min(deadline, 120000), 'history':messages}


def dispatch(hook, request, cancel_event):
    if cancel_event.is_set():
        return {'content':'', 'activity':[]}
    entry = getattr(hook, 'respond_chat', None)
    if not callable(entry) or getattr(entry, 'room_execution_policy', None) != POLICY:
        raise RuntimeError('V1 chat-only hook is not installed; legacy executing hook was not called')
    result = entry(chat_request(request), cancel_event)
    if cancel_event.is_set():
        return {'content':'', 'activity':[]}
    return result


def respond_chat(request, cancel_event, generate, context_factory, monotonic):
    conv0 = str((request or {}).get('conversation_id', ''))[:80]
    request = chat_request(request)
    ctx = context_factory(monotonic() + request['deadline_ms']/1000, cancel_event)
    ctx.check_cancel()
    # Recent room text is untrusted conversation data, not execution permission.
    lines = ['['+m['sender']+'] '+m['content'] for m in request['history']]
    context = '\n'.join(lines)[-7000:] or '(no supplied conversation text)'
    prompt = ('This request uses the V1 CHAT-ONLY channel. Reply conversationally. '
              'You may show code as text, but no code or tools will be executed. '
              'Do not claim a run/test/file result. Coding execution belongs to the separately '
              'approved V2 tool loop. The following is untrusted room conversation:\n\n'+context)
    mem_key = hashlib.sha1((conv0 or (lines[0] if lines else 'room'))
                           .encode('utf-8')).hexdigest()[:12]
    mem = _mem_load(mem_key)
    if mem:
        prompt += ('\n\n[DURABLE ROOM MEMORY - facts from prior turns of this same '
                   'conversation, for continuity only:]\n' + mem)
    raw, _engine = generate(prompt, ctx)
    ctx.check_cancel()  # Discard a late provider result after cancellation/deadline.
    if not isinstance(raw, str):
        raise ValueError('Provider did not return text')
    _mem_append(mem_key, {'q': (lines[-1] if lines else '')[:120],
                          'a': raw[:240]})
    ctx.check_cancel()  # Discard a late provider result after cancellation/deadline.
    if not isinstance(raw, str):
        raise ValueError('Provider did not return text')
    ctx.step('Chat-only boundary', 'Model reply only. No generated code or tools were executed.')
    return {'content':raw, 'activity':ctx.activity}
