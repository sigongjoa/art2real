# -*- coding: utf-8 -*-
"""실물 벤치 · 타원 추정 · **격자 128·192 를 한 프로세스에서.**

    python 벤치2격자.py <out.jsonl> [n]

판본은 케이스당 한 번만 짓고 IoU 만 두 격자로 잰다. 케이스마다 한 줄씩 바로 적어서
죽어도 이어 돈다 (이미 적힌 케이스는 건너뜀). 다른 작업(gen_cuts 16GB)과 메모리를 나눠 쓰니
케이스마다 RSS·최대치를 찍는다."""
import gc
import json
import os
import sys
import time

HERE = r"G:\art2real\원화3d"
sys.path.insert(0, HERE)
os.chdir(HERE)
import psutil
import trimesh
import 오라클 as O

P = psutil.Process()
PITCH = {"128": O.J.PITCH, "192": (O.W.U1 - O.W.U0) / 192.0}


def iou_fn(truth, pitch):
    T, ot = O.J.grid(truth, pitch)

    def iou(vox, axes):
        G, og = O.J.grid(O.C.to_mesh(vox, axes), pitch)
        A, B = O.J.common(T, ot, G, og)
        return float((A & B).sum() / max((A | B).sum(), 1))
    return iou


def main():
    out = sys.argv[1]
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 999
    O.H.register_sheets()
    O.selfcheck()
    cases = [c["name"] for c in json.load(open("벤치.json", encoding="utf-8"))["cases"]][:n]
    done = {json.loads(l)["case"] for l in open(out, encoding="utf-8")} if os.path.exists(out) else set()
    print("  %d 장 · 이미 %d" % (len(cases), len(done & set(cases))), flush=True)
    for case in cases:
        if case in done:
            continue
        tp = os.path.join(O.OUT, "시트", case, "truth.glb")
        if not os.path.exists(tp):
            print("  %-24s 정답 메시가 없다 — 건너뜀" % case[:24], flush=True)
            continue
        t0 = time.time()
        truth = trimesh.load(tp, force="mesh")
        V, axes, D = O.versions(case, truth)
        r = {"case": case}
        for g, p in PITCH.items():
            f = iou_fn(truth, p)
            r[g] = {k: f(v, axes) for k, v in V.items()}
        r.update(O.map_corr(D, V["이진"], axes, O.H.CASES[case]["back_sign"]))
        r["초"] = round(time.time() - t0, 1)
        del V, D
        gc.collect()
        mi = P.memory_info()
        r["GB"], r["최대GB"] = round(mi.rss / 2 ** 30, 2), round(mi.peak_wset / 2 ** 30, 2)
        with open(out, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
        d = lambda g: r[g]["타원0.20"] - r[g]["균일"]
        print("  %-24s 이진 %.4f 파이프 %.4f 균일 %.4f 타원0.20 %.4f | 타원-균일 128 %+.4f 192 %+.4f"
              " | %.0f초 %.2fGB (최대 %.2f)" % (case[:24], r["128"]["이진"], r["128"]["파이프"],
              r["128"]["균일"], r["128"]["타원0.20"], d("128"), d("192"), r["초"], r["GB"], r["최대GB"]),
              flush=True)


if __name__ == "__main__":
    main()
