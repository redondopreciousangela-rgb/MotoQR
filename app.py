import os
import sys
import traceback
import zlib
import base64

from flask import Flask as _Flask

_d = os.path.dirname(os.path.abspath(__file__))
_error = None
app = None

try:
    _names = ["app_zlib_0a.txt", "app_zlib_0b.txt", "app_zlib_1.txt"]
    _parts = []
    for _n in _names:
        _p = os.path.join(_d, _n)
        if not os.path.exists(_p):
            raise RuntimeError(
                f"missing {_n} in {_d}. files={os.listdir(_d)}"
            )
        with open(_p, "r", encoding="ascii") as _f:
            _parts.append(_f.read().strip())
    _code = zlib.decompress(base64.b64decode("".join(_parts))).decode("utf-8")
    _ns = {"__name__": "app", "__file__": os.path.join(_d, "app.py")}
    exec(compile(_code, os.path.join(_d, "app.py"), "exec"), _ns)
    if "app" not in _ns:
        raise RuntimeError("Flask app object missing after load")
    app = _ns["app"]
    app.root_path = _d
    app.template_folder = os.path.join(_d, "templates")
    app.static_folder = os.path.join(_d, "static")
    for _k, _v in _ns.items():
        if not _k.startswith("_"):
            globals()[_k] = _v
except Exception as _e:
    _error = traceback.format_exc()
    # Fallback app so Render shows the real error instead of opaque 500
    app = _Flask(__name__)

    @app.route("/", defaults={"path": ""})
    @app.route("/<path:path>")
    def _show_error(path):
        return (
            "<h1>MotoQR failed to start</h1>"
            "<pre style='white-space:pre-wrap;background:#111;color:#f88;padding:16px'>"
            + (_error or "unknown error")
            + "</pre>"
            "<p>Files in app dir: "
            + ", ".join(sorted(os.listdir(_d)))
            + "</p>"
        ), 500
