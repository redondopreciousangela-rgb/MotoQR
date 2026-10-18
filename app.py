import os
_d = os.path.dirname(os.path.abspath(__file__))
_i = 0
_parts = []
while True:
    _p = os.path.join(_d, f"app_seg_{_i}.py")
    if not os.path.exists(_p):
        break
    _parts.append(open(_p, encoding="utf-8").read())
    _i += 1
if not _parts:
    raise SystemExit("MotoQR: missing app_seg_*.py segments — redeploy failed")
exec(compile("".join(_parts), "app.py", "exec"), globals())
