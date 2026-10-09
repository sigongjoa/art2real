import sys, os, cadquery as cq, trimesh
i = int(sys.argv[1]); sp = "runs/윤곽0/결과/%02d_교차.step" % i
ns = {"cq": cq, "바탕": cq.importers.importStep(sp) if os.path.exists(sp) else None}
exec(open(sys.argv[2], encoding="utf-8").read(), ns); p = os.environ["TEMP"] + "/_w.stl"
cq.exporters.export(ns["r"], p, tolerance=0.05, angularTolerance=0.2); m = trimesh.load(p); print("watertight", m.is_watertight, len(m.faces))
