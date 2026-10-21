"""Convertit un script '# %%' en .ipynb puis l'exécute de bout en bout (équivalent Restart & Run All).
Usage : python _executer_notebook.py 01_cadrage_eda.py"""
import json, sys, re
from pathlib import Path
from jupyter_client.manager import start_new_kernel


def lines(t):
    l = t.split("\n")
    return [x + "\n" for x in l[:-1]] + [l[-1]]


def parse(src):
    cells, cur, kind = [], [], "code"
    for line in src.splitlines():
        m = re.match(r"^# %%(.*)$", line)
        if m:
            if any(l.strip() for l in cur):
                cells.append((kind, cur))
            kind, cur = ("markdown" if "[markdown]" in m.group(1) else "code"), []
            continue
        cur.append(line)
    if any(l.strip() for l in cur):
        cells.append((kind, cur))
    out = []
    for kind, ls in cells:
        while ls and not ls[0].strip(): ls.pop(0)
        while ls and not ls[-1].strip(): ls.pop()
        if kind == "markdown":
            ls = [re.sub(r"^# ?", "", l) for l in ls]
        out.append((kind, "\n".join(ls)))
    return out


py = Path(sys.argv[1])
km, kc = start_new_kernel(kernel_name="python3", cwd=str(py.parent))
kc.execute_interactive("%matplotlib inline", timeout=60)
nb, count = [], 0
for kind, text in parse(py.read_text()):
    if kind == "markdown":
        nb.append({"cell_type": "markdown", "metadata": {}, "source": lines(text)}); continue
    count += 1; outs = []

    def hook(msg):
        t, c = msg["msg_type"], msg["content"]
        if t == "stream":
            if outs and outs[-1].get("output_type") == "stream" and outs[-1]["name"] == c["name"]:
                outs[-1]["text"] += c["text"]
            else:
                outs.append({"output_type": "stream", "name": c["name"], "text": c["text"]})
        elif t in ("execute_result", "display_data"):
            o = {"output_type": t, "data": {k: v for k, v in c["data"].items() if k in ("text/plain", "text/html", "image/png")}, "metadata": {}}
            if t == "execute_result": o["execution_count"] = count
            outs.append(o)
        elif t == "error":
            outs.append({"output_type": "error", "ename": c["ename"], "evalue": c["evalue"], "traceback": c["traceback"]})

    r = kc.execute_interactive(text, output_hook=hook, timeout=3000)
    if r["content"]["status"] == "error":
        print("ERREUR :\n", text[:300], "\n", "\n".join(r["content"]["traceback"])[-2500:])
        kc.stop_channels(); km.shutdown_kernel(); sys.exit(1)
    for o in outs:
        if o["output_type"] == "stream": o["text"] = lines(o["text"])
        elif "data" in o:
            for k in ("text/plain", "text/html"):
                if k in o["data"]: o["data"][k] = lines(o["data"][k])
    nb.append({"cell_type": "code", "execution_count": count, "metadata": {}, "outputs": outs, "source": lines(text)})
kc.stop_channels(); km.shutdown_kernel()
py.with_suffix(".ipynb").write_text(json.dumps({"cells": nb, "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}, "language_info": {"name": "python"}}, "nbformat": 4, "nbformat_minor": 5}, indent=1, ensure_ascii=False))
print("OK", py.with_suffix(".ipynb").name)
