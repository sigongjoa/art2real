# -*- coding: utf-8 -*-
"""채점(trail10 venv · CadQuery 있음): 출력 jsonl 의 코드 실행 → 원본 STL 과 IoU(둘 다 중심 · 긴 변 1 로 맞춤 · 64³). python s/score.py <입력.jsonl> <출력.jsonl> <채점.jsonl>"""
import sys, json, os, numpy as np, trimesh, tempfile
from concurrent.futures import ProcessPoolExecutor
def norm(m):
    lo, hi = m.bounds; m = m.copy(); m.apply_translation(-(lo + hi) / 2); m.apply_scale(1.0 / (hi - lo).max()); return m
def cap(gb=8):   # 작업자 메모리 상한(Job Object) — 넘으면 MemoryError · 10-06 kind() 를 메인에서 돌려 python 75 GB · PC 두 번 다운
    import ctypes as C; from ctypes import wintypes as W
    class Basic(C.Structure): _fields_ = [("t1", C.c_int64), ("t2", C.c_int64), ("LimitFlags", W.DWORD), ("w1", C.c_size_t), ("w2", C.c_size_t), ("n", W.DWORD), ("aff", C.c_size_t), ("pri", W.DWORD), ("sch", W.DWORD)]
    class Ext(C.Structure): _fields_ = [("B", Basic), ("io", C.c_uint64 * 6), ("ProcessMemoryLimit", C.c_size_t), ("j", C.c_size_t), ("p1", C.c_size_t), ("p2", C.c_size_t)]
    k = C.WinDLL("kernel32"); k.CreateJobObjectW.restype = k.GetCurrentProcess.restype = C.c_void_p
    k.SetInformationJobObject.argtypes = [C.c_void_p, C.c_int, C.c_void_p, W.DWORD]; k.AssignProcessToJobObject.argtypes = [C.c_void_p, C.c_void_p]
    e = Ext(); e.B.LimitFlags = 0x100; e.ProcessMemoryLimit = gb << 30; h = k.CreateJobObjectW(None, None)
    assert k.SetInformationJobObject(h, 9, C.byref(e), C.sizeof(e)) and k.AssignProcessToJobObject(h, k.GetCurrentProcess()), "메모리 상한 실패"

def occ(m, g):   # 속 판정: open3d(embree) — trimesh.contains 는 1.7 만 면에서 335 s · 수십 GB(10-06 PC 다운 범인) · 결과 같음
    import open3d as o3d
    s = o3d.t.geometry.RaycastingScene(); s.add_triangles(o3d.core.Tensor(m.vertices.astype(np.float32)), o3d.core.Tensor(m.faces.astype(np.uint32)))
    return s.compute_occupancy(o3d.core.Tensor(g.astype(np.float32))).numpy() > 0.5
def one(args):   # -1 = 코드 실행 · 내보내기 실패(모델 탓) · -3 = 채점 실패(자 탓) — 둘을 섞지 않는다
    code, stl = args
    try:
        import cadquery as cq
        ns = {"cq": cq, "__name__": "__main__"}; exec(code, ns)
        obj = ns.get("result") or ns.get("r") or next((v for v in ns.values() if isinstance(v, (cq.Workplane, cq.Shape))), None)
        p = os.path.join(tempfile.gettempdir(), "z_%d.stl" % os.getpid()); cq.exporters.export(obj, p)
    except Exception:
        return -1.0
    try:
        a, b = norm(trimesh.load(stl, force="mesh")), norm(trimesh.load(p)); n = 64
        g = (np.indices((n, n, n)).reshape(3, -1).T + 0.5) / n - 0.5
        ia = occ(a, g) if a.is_watertight else np.zeros(len(g), bool); ib = occ(b, g) if b.is_watertight else np.zeros(len(g), bool)
        u = (ia | ib).sum(); return float((ia & ib).sum() / u) if u else 0.0
    except Exception:
        return -3.0
if __name__ == "__main__":
    IN = {json.loads(l)["이름"]: json.loads(l) for l in open(sys.argv[1], encoding="utf-8")}
    OUT = [json.loads(l) for l in open(sys.argv[2], encoding="utf-8")]; S = sys.argv[3]
    done = {json.loads(l)["이름"] for l in open(S, encoding="utf-8")} if os.path.exists(S) else set()
    pool = ProcessPoolExecutor(1)
    for o in OUT:
        if o["이름"] in done: continue
        ious = []
        for c in o["코드"]:
            fu = pool.submit(one, (c, IN[o["이름"]]["stl"]))
            try: ious.append(round(fu.result(timeout=25), 3))
            except Exception:
                ious.append(-2.0)
                for p in list(pool._processes.values()): p.kill()
                pool.shutdown(wait=False, cancel_futures=True); pool = ProcessPoolExecutor(1)
        open(S, "a", encoding="utf-8").write(json.dumps({"이름": o["이름"], "IoU": ious, "최고": max(ious)}, ensure_ascii=False) + "\n"); print(o["이름"][:50], ious, flush=True)
