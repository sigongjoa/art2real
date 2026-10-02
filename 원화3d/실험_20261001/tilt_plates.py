# 보이는 넓이 → 판 방향 → 정면 윤곽을 그 각도로 세운 판 (10-02).
# 정면에서 보이는 넓이 = A·cosθ · 옆에서 = A·sinθ  (θ = 판이 정면에서 옆으로 돌아간 각, 세로축 기준)
# 좌우 짝 부위는 정면에 둘 다 보이고 옆에는 한쪽만 → 정면 넓이 ÷ 2. 가운데 부위(뿔 · 미간 · 미늘 · 턱)는 가운데서 접힌 V 로 본다.
# 판 위치(앞뒤) = 옆 원화에서 그 부위 칸의 앞 끝. 판의 깊이 범위는 옆 칸의 앞뒤 폭을 넘지 않게 자른다.
import json, numpy as np, cv2, trimesh, shapely.geometry as sg, shapely.ops as so
D=json.load(open("cut/three_views.json",encoding="utf-8")); V=D["views"]
쌍={"투구 돔","이마판","차양 · 눈썹 능선","번개","눈구멍","눈","눈 둘레 테","마스크 볼판","볼날개"}
제외={"안테나 뿌리 · 잔 조각","깃 (머리 아님)"}
F=np.vstack([np.array(c["poly"]) for c in V["정면"].values()]); xc=(F[:,0].min()+F[:,0].max())/2
S=np.vstack([np.array(c["poly"]) for c in V["옆"].values()]); umax=S[:,0].max()
def area(polys): return sum(abs(cv2.contourArea(np.array(p,np.float32))) for p in polys)
표=[]; 
for g in D["groups"]:
    if g["name"] in 제외: continue
    fp=[np.array(V["정면"][str(n)]["poly"],float) for n in g["cells"]["정면"] if str(n) in V["정면"]]; sp=[np.array(V["옆"][str(n)]["poly"],float) for n in g["cells"]["옆"] if str(n) in V["옆"]]; qp=[np.array(V["3/4"][str(n)]["poly"],float) for n in g["cells"]["3/4"] if str(n) in V["3/4"]]
    Af=area(fp)/(2 if g["name"] in 쌍 else 1); As=area(sp); Aq=area(qp)
    th=float(np.degrees(np.arctan2(As,Af))); thc=min(th,75.0)
    zs=np.vstack(sp)[:,0]; zfront=umax-zs.min(); zback=umax-zs.max(); depth=zfront-zback        # 옆: z앞 = umax-u (뒤통수 쪽 0)
    표.append({"부위":g["name"],"정면%":round(Af/100,1),"옆%":round(As/100,1),"3/4%":round(Aq/100,1),"각도":round(th,0),"쓴각도":round(thc,0),"앞z":round(zfront,1),"깊이폭":round(depth,1),"color":V["정면"][str(g["cells"]["정면"][0])]["color"],"fp":[p.tolist() for p in fp]})
# 3/4 확인: 3/4 넓이 ∝ A·cos(θ-φ) — φ 를 맞춰 상관을 본다
A=np.array([np.hypot(t["정면%"],t["옆%"]) for t in 표]); th=np.radians([t["각도"] for t in 표]); q=np.array([t["3/4%"] for t in 표])
best=max(((np.corrcoef(A*np.abs(np.cos(th-np.radians(p))),q)[0,1],p) for p in range(10,81,5)))
print("3/4 예측 상관",round(best[0],2),"φ",best[1])
for t in 표: print(f'{t["부위"]:12s} 정면 {t["정면%"]:5.1f} 옆 {t["옆%"]:5.1f} → {t["각도"]:3.0f}°  앞z {t["앞z"]:5.1f} 깊이폭 {t["깊이폭"]:5.1f}')
# 판 짓기
out=[]
for i,t in enumerate(표):
    polys=[sg.Polygon(np.c_[p[:,0]-xc,p[:,1]]).buffer(0) for p in map(np.array,t["fp"])]; poly=so.unary_union([p for p in polys if p.area>0])
    if poly.is_empty: continue
    geoms=list(poly.geoms) if hasattr(poly,"geoms") else [poly]; th=np.radians(t["쓴각도"]); ms=[]
    for pg in geoms:
        if pg.area<0.5: continue
        mm=trimesh.creation.extrude_polygon(pg,2.0); v=mm.vertices.copy()
        if t["부위"] in 쌍: piv=min(abs(pg.bounds[0]),abs(pg.bounds[2])) if pg.bounds[0]*pg.bounds[2]>0 else 0.0; dx=np.clip(np.abs(v[:,0])-piv,0,None)
        else: dx=np.abs(v[:,0])
        z=t["앞z"]-np.minimum(dx*np.tan(th),t["깊이폭"])-v[:,2]; mm.vertices=np.c_[v[:,0],v[:,1],z]; ms.append(mm)
    if not ms: continue
    m=trimesh.util.concatenate(ms)
    m.export(f"cut/tilt/obj/T_{i}.obj"); out.append({"i":i,"부위":t["부위"],"color":t["color"]})
json.dump({"표":[{k:v for k,v in t.items() if k!="fp"} for t in 표],"판":out,"3/4상관":round(float(best[0]),2),"φ":best[1]},open("cut/tilt/index.json","w",encoding="utf-8"),ensure_ascii=False,indent=1)
