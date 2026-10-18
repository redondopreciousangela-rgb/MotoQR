import os
_BASE = os.path.dirname(os.path.abspath(__file__))
_BODY = os.path.join(_BASE, "_motoqr_app_body.py")
with open(_BODY, "r", encoding="utf-8") as _f:
    exec(compile(_f.read(), "_motoqr_app_body.py", "exec"), globals())
