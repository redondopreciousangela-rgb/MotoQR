import os
_d = os.path.dirname(os.path.abspath(__file__))
_code = open(os.path.join(_d, "body_part0.py"), encoding="utf-8").read()
_code += open(os.path.join(_d, "body_part1.py"), encoding="utf-8").read()
exec(compile(_code, "app_body", "exec"), globals())
