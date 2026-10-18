import os
_d = os.path.dirname(os.path.abspath(__file__))
_parts = []
_i = 0
while True:
    _p = os.path.join(_d, "plain_seg_%d.py" % _i)
    if not os.path.exists(_p):
        break
    _parts.append(open(_p, encoding="utf-8").read())
    _i += 1
if not _parts:
    raise RuntimeError("MotoQR: no plain_seg_*.py found in " + _d)
_ns = {"__name__": "app", "__file__": os.path.join(_d, "app.py")}
exec(compile("".join(_parts), os.path.join(_d, "app.py"), "exec"), _ns)
app = _ns["app"]
app.root_path = _d
app.template_folder = os.path.join(_d, "templates")
app.static_folder = os.path.join(_d, "static")
for _k, _v in list(_ns.items()):
    if not _k.startswith("_"):
        globals()[_k] = _v
