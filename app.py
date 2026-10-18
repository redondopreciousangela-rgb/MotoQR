import os, zlib, base64
_d = os.path.dirname(os.path.abspath(__file__))
_parts = []
_i = 0
while True:
    _p = os.path.join(_d, f"app_zlib_{_i}.txt")
    if not os.path.exists(_p):
        break
    _parts.append(open(_p, encoding="ascii").read().strip())
    _i += 1
if not _parts:
    raise SystemExit("MotoQR: missing app_zlib_*.txt — upload incomplete")
_code = zlib.decompress(base64.b64decode("".join(_parts))).decode("utf-8")
exec(compile(_code, "app.py", "exec"), globals())
