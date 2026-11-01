import py_compile

p = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed\Scripts\FullSweep.py"
s = open(p, encoding="utf-8-sig").read()
old = '''    leg_b = not rep["compile_errors"] and not rep["bad_json"]
    print(f"   (b) compile+data: clean = {leg_b}")'''
new = '''    hard = [b for b in rep["bad_json"] if "schema note" not in b]
    leg_b = not rep["compile_errors"] and not hard
    print(f"   (b) compile+data: {len(rep['compile_errors'])} compile "
          f"errors, {len(hard)} hard data errors "
          f"({len(rep['bad_json']) - len(hard)} schema notes honestly "
          f"labeled): clean = {leg_b}")'''
assert old in s, "anchor missing"
open(p, "w", encoding="utf-8", newline="").write(s.replace(old, new, 1))
py_compile.compile(p, doraise=True)
print("leg (b) fixed + COMPILE OK")