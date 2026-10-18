import os
import sys
import zlib
import base64

_d = os.path.dirname(os.path.abspath(__file__))
_names = ["app_zlib_0a.txt", "app_zlib_0b.txt", "app_zlib_1.txt"]
_parts = []
for _n in _names:
    _p = os.path.join(_d, _n)
    if not os.path.exists(_p):
        raise RuntimeError(f"MotoQR: missing {_n} in {_d}. Files: {os.listdir(_d)}")
    with open(_p, "r", encoding="ascii") as _f:
        _parts.append(_f.read().strip())

try:
    _raw = base64.b64decode("".join(_parts))
    _code = zlib.decompress(_raw).decode("utf-8")
except Exception as _e:
    raise RuntimeError(f"MotoQR: failed to decode app body: {_e}") from _e

_ns = {"__name__": "app", "__file__": os.path.join(_d, "app_body.py")}
try:
    exec(compile(_code, "app_body.py", "exec"), _ns)
except Exception as _e:
    raise RuntimeError(f"MotoQR: failed to load app body: {_e}") from _e

if "app" not in _ns:
    raise RuntimeError("MotoQR: Flask app object not found after load")

# Export for gunicorn app:app
app = _ns["app"]

# Re-export public names so routes/helpers remain available
for _k, _v in _ns.items():
    if not _k.startswith("_"):
        globals()[_k] = _v
