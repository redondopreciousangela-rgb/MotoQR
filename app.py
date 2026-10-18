# loading from body parts if present, else inline minimal bootstrap
import os
_BASE = os.path.dirname(os.path.abspath(__file__))
_p0 = os.path.join(_BASE, 'body_part0.py')
_p1 = os.path.join(_BASE, 'body_part1.py')
if os.path.exists(_p0):
    _code = open(_p0, encoding='utf-8').read()
    if os.path.exists(_p1):
        _code += open(_p1, encoding='utf-8').read()
    exec(compile(_code, 'app_body', 'exec'), globals())
else:
    raise SystemExit('Missing body_part0.py / body_part1.py — upload from PythonProject artifacts')
