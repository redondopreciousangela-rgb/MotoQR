import os, zlib, base64
_d = os.path.dirname(os.path.abspath(__file__))
_names = ["app_zlib_0a.txt", "app_zlib_0b.txt", "app_zlib_1.txt"]
_parts = []
for _n in _names:
    _p = os.path.join(_d, _n)
    if not os.path.exists(_p):
        raise SystemExit(f"MotoQR: missing {_n}")
    _parts.append(open(_p, encoding="ascii").read().strip())
_code = zlib.decompress(base64.b64decode("".join(_parts))).decode("utf-8")
exec(compile(_code, "app.py", "exec"), globals())
