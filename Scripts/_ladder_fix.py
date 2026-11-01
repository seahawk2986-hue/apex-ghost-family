"""THE LADDER-FIXER (byte-exact, indentation-proof): the remaining
call-sites by substring-replace. Idempotent: skips already-laddered lines.
Files: JobExecutor (the translation) + I18nBuild (the extract + translate)
+ BrainUpgrades (the deception-leg)."""
import os

ROOT = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed\Scripts"
FIXES = {
    "JobExecutor.py": [('purpose="the translation")',
                        'purpose="the translation",\n'
                        '                      models=("groq", '
                        '"local-coder", "local-fast"))')],
    "I18nBuild.py": [('purpose="the strings-extract")',
                      'purpose="the strings-extract", '
                      'models=("groq", "local-coder", "local-fast"))'),
                     ('purpose="the translate")',
                      'purpose="the translate", '
                      'models=("groq", "local-coder", "local-fast"))')],
    "BrainUpgrades.py": [('purpose="the deception brain-leg")',
                          'purpose="the deception brain-leg", '
                          'models=("groq", "local-coder", "local-fast"))')],
}
for fn, pairs in FIXES.items():
    p = os.path.join(ROOT, fn)
    t = open(p, encoding="utf-8").read()
    for old, new in pairs:
        if '"groq"' in t.split(old[0])[0][-200:] if old in t else False:
            continue
        if old in t:
            t = t.replace(old, new, 1)
            print(f"[ladder-fix] {fn}: {old[:44]} -> laddered")
        else:
            print(f"[ladder-fix] {fn}: {old[:44]} NOT FOUND (verify!)")
    open(p, "w", encoding="utf-8", newline="\n").write(t)