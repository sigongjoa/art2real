# 판정기준93 T0 — 이미 있는 예측(학습 없음)의 층 맞음을 가장 가까운 선까지 거리 칸으로 · 껍질 어긋남 화소 뺌 · 10-19
# 사용(venv): 거리93.py [이름 ...] → 거리93.json · 학습69 의 진단 모드도 칸()을 가져다 씀
import sys, json, numpy as np, cv2
O = "G:/art2real/out/설명/캐드부품/"; 칸들 = [(0, 2), (3, 8), (9, 16), (17, 32), (33, 999)]
def 칸(입, g, p):   # 입 (3+, N, N) 한 방향 입력 · g 정답 층 · p 예측 → [(맞음 수, 화소 수) × 칸]
    안 = 입[1] > 0; 껍 = np.where(입[2] == 17, 32, 입[2].astype(int) * 2); 쓸 = 안 & (g >= 껍)
    거 = cv2.distanceTransform((입[0] == 0).astype(np.uint8), cv2.DIST_L2, 3); 맞 = p == g
    return [((맞 & 쓸 & (거 >= a) & (거 <= b)).sum(), (쓸 & (거 >= a) & (거 <= b)).sum()) for a, b in 칸들]
if __name__ == "__main__":
    입 = np.load(O + "입력51.npy", mmap_mode="r"); 층 = np.load(O + "층32.npy", mmap_mode="r"); 결 = {}
    for 이름 in sys.argv[1:] or ["판0", "넓은숨은"]:
        부 = np.load(O + "학습69_%s/예측부품.npy" % 이름); P = np.load(O + "학습69_%s/예측.npy" % 이름, mmap_mode="r"); s = np.zeros((5, 2))
        for n, i in enumerate(부):
            for k in range(6): s += np.array(칸(입[i, k], 층[i, k].astype(int), P[n, k].astype(int)))
        결[이름] = {"%d–%d" % c: [round(a / max(b, 1), 3), int(b)] for c, (a, b) in zip(칸들, s)}; print(이름, 결[이름], flush=True)
    json.dump(결, open("거리93.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
