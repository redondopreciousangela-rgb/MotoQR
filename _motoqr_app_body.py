import os
_d = os.path.dirname(os.path.abspath(__file__))
_p0 = os.path.join(_d, "body_part0.py")
_p1 = os.path.join(_d, "body_part1.py")
_code = open(_p0, encoding="utf-8").read()
if os.path.exists(_p1):
    _code += open(_p1, encoding="utf-8").read()
exec(compile(_code, "app_body", "exec"), globals())
