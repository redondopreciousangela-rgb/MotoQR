import os
import zlib
import base64

_d = os.path.dirname(os.path.abspath(__file__))
_names = ["app_zlib_0a.txt", "app_zlib_0b.txt", "app_zlib_1.txt"]
_parts = []
for _n in _names:
    _p = os.path.join(_d, _n)
    if not os.path.exists(_p):
        raise RuntimeError(
            f"MotoQR: missing {_n} in {_d}. Present: {os.listdir(_d)}"
        )
    with open(_p, "r", encoding="ascii") as _f:
        _parts.append(_f.read().strip())

try:
    _code = zlib.decompress(base64.b64decode("".join(_parts))).decode("utf-8")
except Exception as _e:
    raise RuntimeError(f"MotoQR: failed to decode app body: {_e}") from _e

_ns = {
    "__name__": "app",
    "__file__": os.path.join(_d, "app.py"),
}
try:
    exec(compile(_code, os.path.join(_d, "app.py"), "exec"), _ns)
except Exception as _e:
    raise RuntimeError(f"MotoQR: failed to load app body: {type(_e).__name__}: {_e}") from _e

if "app" not in _ns:
    raise RuntimeError("MotoQR: Flask app object missing after load")

app = _ns["app"]
# Ensure templates/static resolve next to this package on Render
app.root_path = _d
app.template_folder = os.path.join(_d, "templates")
app.static_folder = os.path.join(_d, "static")

for _k, _v in _ns.items():
    if not _k.startswith("_"):
        globals()[_k] = _v
