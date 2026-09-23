# -*- coding: utf-8 -*-
"""부품 GLB -> 웹 뷰어용 한 파일(JSON + base64 정수 좌표). 아티팩트가 glb 를 안 서빙해서 만든다 (2026-09-23)."""
import base64, json, os, sys
import numpy as np
import trimesh

D = sys.argv[1] if len(sys.argv) > 1 else r"G:\art2real\원화3d\out\원형사\mech_Mech_4UvIHxnoSR"
메타 = json.load(open(os.path.join(D, "부품.json"), encoding="utf-8"))
S = trimesh.load(os.path.join(D, "부품.glb"))
기하 = S.geometry if hasattr(S, "geometry") else {"부품01": S}
정답 = trimesh.load(os.path.join(D, "정답.glb"), force="mesh")

모두 = list(기하.values()) + [정답]
lo = np.min([m.vertices.min(0) for m in 모두], 0)
hi = np.max([m.vertices.max(0) for m in 모두], 0)
s = float((hi - lo).max()) / 32000.0


def 싸기(m, 면한도):
    if len(m.faces) > 면한도:
        m = m.simplify_quadric_decimation(face_count=면한도)
    q = np.rint((m.vertices - lo) / s).astype(np.int16)
    f = m.faces.astype(np.uint32)
    return {"v": base64.b64encode(q.tobytes()).decode(), "f": base64.b64encode(f.tobytes()).decode(),
            "면": int(len(m.faces))}


부품 = []
이름표 = {p["이름"]: p for p in 메타["부품"]}
for 이름, m in 기하.items():
    키 = 이름.split("_")[0]
    info = 이름표.get(키) or 이름표.get(이름) or {}
    c = np.asarray(m.visual.face_colors[0][:3]) if hasattr(m.visual, "face_colors") else np.array([150, 160, 170])
    부품.append(dict(싸기(m, 2500), 이름=info.get("이름", 키), 색="#%02x%02x%02x" % tuple(int(x) for x in c),
                    크기mm=info.get("크기mm", []), 부피mm3=info.get("부피mm3", 0), 빠짐=info.get("빠짐", [])))
부품.sort(key=lambda p: p["이름"])
꾸러미 = {"케이스": 메타.get("케이스", ""), "원점": [float(x) for x in lo], "눈금": s,
        "부품": 부품, "정답": 싸기(정답, 20000)}
p = os.path.join(D, "뷰어자료.json")
json.dump(꾸러미, open(p, "w", encoding="utf-8"))
print(p, round(os.path.getsize(p) / 1e6, 2), "MB · 부품", len(부품))
