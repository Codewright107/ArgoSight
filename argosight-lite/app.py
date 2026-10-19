"""Argosight Lite: a local UI that explores and simulates the farmvibes-ai repo (no cluster needed)."""
import collections
from pathlib import Path

import numpy as np
import yaml
from flask import Flask, jsonify, render_template, request

REPO = Path(__file__).resolve().parent.parent / "farmvibes-ai"
WF_ROOT, OPS_ROOT = REPO / "workflows", REPO / "ops"
app = Flask(__name__)


def flat(s):
    return " ".join(str(s or "").split())


def load_ops():
    ops = {}
    for f in sorted(OPS_ROOT.glob("*/*.yaml")):
        try:
            d = yaml.safe_load(f.read_text())
        except Exception:
            continue
        if not isinstance(d, dict) or "name" not in d:
            continue
        desc = d.get("description") or {}
        ops[d["name"]] = {
            "name": d["name"],
            "inputs": d.get("inputs") or {},
            "output": d.get("output") or {},
            "parameters": {k: str(v) for k, v in (d.get("parameters") or {}).items()},
            "short": flat(desc.get("short_description")),
            "long": flat(desc.get("long_description")),
        }
    return ops


def load_workflows():
    wfs = {}
    for f in sorted(WF_ROOT.rglob("*.yaml")):
        try:
            d = yaml.safe_load(f.read_text())
        except Exception:
            continue
        if not isinstance(d, dict) or "tasks" not in d:
            continue
        rel = f.relative_to(WF_ROOT).with_suffix("")
        desc = d.get("description") or {}
        tasks = {}
        for k, v in (d.get("tasks") or {}).items():
            v = v or {}
            tasks[k] = {"id": k, "op": v.get("op"), "workflow": v.get("workflow"),
                        "parameters": {a: str(b) for a, b in (v.get("parameters") or {}).items()}}
        edges = []
        for e in d.get("edges") or []:
            dests = e["destination"] if isinstance(e["destination"], list) else [e["destination"]]
            edges += [{"from": e["origin"], "to": x} for x in dests]
        for name, targets in (d.get("sources") or {}).items():
            edges += [{"from": f"@in:{name}", "to": t} for t in (targets or [])]
        for name, origin in (d.get("sinks") or {}).items():
            edges.append({"from": origin, "to": f"@out:{name}"})
        wfs[str(rel)] = {
            "id": str(rel), "name": d.get("name", rel.name),
            "category": "/".join(rel.parts[:-1]) or "core",
            "short": flat(desc.get("short_description")),
            "long": flat(desc.get("long_description")),
            "sources": {k: flat(v) for k, v in (desc.get("sources") or {}).items()} or
                       {k: "" for k in (d.get("sources") or {})},
            "sinks": {k: flat(v) for k, v in (desc.get("sinks") or {}).items()} or
                     {k: "" for k in (d.get("sinks") or {})},
            "parameters": {k: flat(v) for k, v in (desc.get("parameters") or {}).items()} or
                          {k: "" for k in (d.get("parameters") or {})},
            "tasks": tasks, "edges": edges,
        }
    return wfs


OPS, WFS = load_ops(), load_workflows()
BY_NAME = collections.defaultdict(list)
for w in WFS.values():
    BY_NAME[w["name"]].append(w["id"])


def resolve(task):
    """Resolve a task to ('op'|'workflow', id) and its description."""
    if task.get("op") in OPS:
        return "op", task["op"], OPS[task["op"]]["short"]
    wid = task.get("workflow")
    if wid in WFS:
        return "workflow", wid, WFS[wid]["short"]
    return ("op" if task.get("op") else "workflow"), task.get("op") or wid, ""


def topo(w):
    deps = {t: set() for t in w["tasks"]}
    for e in w["edges"]:
        a, b = e["from"].split(".")[0], e["to"].split(".")[0]
        if a in deps and b in deps and a != b:
            deps[b].add(a)
    levels, done = [], set()
    while len(done) < len(deps):
        lvl = [t for t in deps if t not in done and deps[t] <= done]
        if not lvl:
            lvl = [t for t in deps if t not in done]
        levels.append(lvl)
        done |= set(lvl)
    return levels


def summary(w):
    return {k: w[k] for k in ("id", "name", "category", "short", "long")} | {
        "n_tasks": len(w["tasks"]), "sources": list(w["sources"]), "sinks": list(w["sinks"])}


@app.get("/")
def home():
    return render_template("index.html")


@app.get("/api/overview")
def overview():
    cats = collections.Counter(w["category"].split("/")[0] for w in WFS.values())
    return jsonify({"workflows": len(WFS), "ops": len(OPS), "categories": cats,
                    "tasks": sum(len(w["tasks"]) for w in WFS.values())})


@app.get("/api/workflows")
def workflows():
    return jsonify([summary(w) for w in WFS.values()])


@app.get("/api/workflow")
def workflow():
    w = WFS.get(request.args.get("id", ""))
    if not w:
        return jsonify({"error": "not found"}), 404
    tasks = []
    for t in w["tasks"].values():
        kind, ref, desc = resolve(t)
        tasks.append(t | {"kind": kind, "ref": ref, "desc": desc})
    return jsonify(w | {"tasks": tasks, "levels": topo(w)})


@app.get("/api/ops")
def ops():
    return jsonify(list(OPS.values()))


@app.post("/api/indices")
def api_indices():
    b = {k: float(v) for k, v in request.get_json().items() if v not in ("", None)}
    g, r, nir, blue, swir = (b.get(k, 0) for k in ("green", "red", "nir", "blue", "swir"))
    d = lambda x, y: float(x / y) if y else None
    return jsonify({"NDVI": d(nir - r, nir + r), "NDWI": d(g - nir, g + nir),
                    "EVI": d(2.5 * (nir - r), nir + 6 * r - 7.5 * blue + 1),
                    "SAVI": d(1.5 * (nir - r), nir + r + 0.5), "NDMI": d(nir - swir, nir + swir)})


@app.post("/api/season")
def api_season():
    pts = [(p["date"], float(p["ndvi"])) for p in request.get_json()["points"]]
    if len(pts) < 4:
        return jsonify({"error": "Need at least 4 points"}), 400
    dates, v = zip(*pts)
    v = np.array(v)
    peak = int(v.argmax())
    lo, hi = v.min(), v[peak]
    em = next((i for i in range(peak + 1) if v[i] >= lo + .3 * (hi - lo)), 0)
    hv = next((i for i in range(peak, len(v)) if v[i] <= lo + .5 * (hi - lo)), len(v) - 1)
    return jsonify({"emergence": dates[em], "peak": dates[peak], "harvest": dates[hv],
                    "peak_ndvi": round(float(hi), 3), "mean_ndvi": round(float(v.mean()), 3)})


if __name__ == "__main__":
    print(f"Loaded {len(WFS)} workflows, {len(OPS)} ops")
    app.run(port=5050, debug=False)
