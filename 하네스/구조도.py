# 모델 구조도 — 논문 관례대로 도형으로: 특징 맵 = 크기 비례 직육면체(PlotNeuralNet 꼴) · 토큰 = 격자 · 칸 쿼리 = 색 사각형(DETR 꼴) · 디코더 = 색 층 블록 × N(Transformer 꼴) · 출력 = 칸마다 예측 덩어리 렌더 · 10-22
# 꼴 s1 가로 흐름 / s2 두 단 · 그림 파일(입력_위 · 앞 · 옆 · 칸k · 예측전체 · 정답)은 같은 폴더 · 숫자는 판 모델의 구조.json
import math
색 = {"conv": ("#f6d58a", "#e8bd57", "#d9a63a"), "in": ("#e9eef5", "#d3dbe7", "#bcc8d8"), "attn": "#f7b98f", "xattn": "#f39c6b", "norm": "#f3eaa0", "ffn": "#a9cdee", "head": "#c9b6e8",
      "q": ["#e4572e", "#29a3a3", "#7b4fd1", "#e0a400", "#3a7bd5", "#9aa0a6"], "뷰": ["#9ec5f0", "#a8dcb0", "#f5c49a"]}
def 상자3(x, y, w, h, d, 색3, 굵=1.2):   # 앞면(w × h) + 윗면 + 옆면 · 비스듬히 30°
    dx, dy = d * math.cos(math.radians(30)), d * math.sin(math.radians(30)); a, b, c = 색3; s = f'stroke="#3b3f46" stroke-width="{굵}" stroke-linejoin="round"'
    return (f'<polygon points="{x},{y} {x + dx},{y - dy} {x + w + dx},{y - dy} {x + w},{y}" fill="{b}" {s}/>'
            f'<polygon points="{x + w},{y} {x + w + dx},{y - dy} {x + w + dx},{y + h - dy} {x + w},{y + h}" fill="{c}" {s}/>'
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{a}" {s}/>')
def 글(x, y, t, 크=13, 굵=400, 가="middle", 색_="#2b2f36"): return f'<text x="{x}" y="{y}" font-size="{크}" font-weight="{굵}" text-anchor="{가}" fill="{색_}">{t}</text>'
def 화(x0, y0, x1, y1, 굽=False): return f'<path d="M{x0},{y0} {"C" + f"{(x0 + x1) / 2},{y0} {(x0 + x1) / 2},{y1}" if 굽 else ""} {x1},{y1}" fill="none" stroke="#5b616b" stroke-width="1.8" marker-end="url(#화)"/>'
def 격자(x, y, n, 칸, 색_, 진="#3b3f46"):   # n×n 토큰 격자
    return "".join(f'<rect x="{x + j * 칸}" y="{y + i * 칸}" width="{칸 - 1}" height="{칸 - 1}" fill="{색_}" stroke="{진}" stroke-width=".4"/>' for i in range(n) for j in range(n))
def 디코더(x, y, w, 쌓기=True):   # Transformer 꼴 한 층: 칸끼리 주의 → Add&Norm → 교차 주의 → Add&Norm → FFN → Add&Norm (아래에서 위로) · 잔차 화살표
    층 = [("칸끼리 주의", 색["attn"], 34), ("Add & Norm", 색["norm"], 16), ("교차 주의", 색["xattn"], 34), ("Add & Norm", 색["norm"], 16), ("FFN", 색["ffn"], 30), ("Add & Norm", 색["norm"], 16)]
    g = []; yy = y; 자리 = {}
    for 이름, c, h in reversed(층): g.append(f'<rect x="{x + 14}" y="{yy}" width="{w - 28}" height="{h}" rx="6" fill="{c}" stroke="#3b3f46" stroke-width="1"/>' + 글(x + w / 2, yy + h / 2 + 4.5, 이름, 12 if h > 20 else 10.5, 600)); 자리[이름 + str(len(자리))] = (yy, h); yy += h + 8
    전 = yy - y - 8; g.insert(0, f'<rect x="{x}" y="{y - 12}" width="{w}" height="{전 + 24}" rx="12" fill="#f4f1ea" stroke="#3b3f46" stroke-width="1.4"/>')
    for 끝 in (y + 전 - 16 - 8 - 34 / 2, y + 전 - 16 - 8 - 34 - 8 - 16 - 8 - 34 / 2, y + 30 / 2 + 24):   # 잔차(왼쪽으로 돌아 Add&Norm 으로)
        g.append(f'<path d="M{x + 14},{끝 + 22} h-10 v-{36} h10" fill="none" stroke="#5b616b" stroke-width="1.3" marker-end="url(#화)"/>')
    return "".join(g), 전 + 24
def 그리기(구, 꼴="s1", 판예측=None):
    층 = {r["이름"]: r for r in 구["층"]}; cnn = [r for r in 구["층"] if r["이름"].startswith("cnn.")]; N = len([r for r in 구["층"] if r["이름"].startswith("dec.layers.")])
    판예측 = 판예측 or []; g = []; 정의 = '<defs><marker id="화" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0 0L10 5L0 10z" fill="#5b616b"/></marker></defs>'
    s모 = lambda s: 16 + s * .78; c두 = lambda c: 5 + math.log2(max(c, 1)) * 5.2
    def 백본(x0, ymid):   # 입력 세 장 → 직육면체들 · 끝 x 반환
        for k, nm in enumerate(("위", "앞", "옆")): g.append(f'<image href="입력_{nm}.png" x="{x0 + k * 10}" y="{ymid - 60 + k * 10}" width="96" height="96" style="outline:1px solid #3b3f46"/>')
        g.append(글(x0 + 58, ymid + 66, "입력 3면도 × 3", 12, 600)); x = x0 + 150
        모양 = [(1, 128)] + [(r["출력"][1], r["출력"][2]) for r in cnn]
        for i, (c, s) in enumerate(모양):
            w, h = c두(c), s모(s); d = h * .55; g.append(상자3(x, ymid - h / 2 + d * .25, w, h, d, 색["in"] if i == 0 else 색["conv"]))
            g.append(글(x + w / 2 + d * .43, ymid + h / 2 + 34, f"{c}×{s}²", 11, 600)); x += w + d * .87 + 26
        g.append(글(x0 + 150 + (x - x0 - 150) / 2, ymid - 98, f"CNN 백본 · 블록 {len(cnn)} · 그림마다 같은 가중치", 12.5, 700)); return x
    def 토큰(x, ymid):
        for k in range(3): g.append(격자(x + k * 14, ymid - 44 + k * 14, 8, 8, 색["뷰"][k]))
        g.append(글(x + 50, ymid + 70, "조각 토큰 3 × 64", 12, 600)); g.append(글(x + 50, ymid + 86, "+ 위치 · 그림 표시", 11, 400, 색_="#5b616b")); return x + 104
    def 쿼리(x, y):
        for k in range(6): g.append(f'<rect x="{x + k * 22}" y="{y}" width="17" height="17" rx="3" fill="{색["q"][k]}" stroke="#3b3f46" stroke-width=".8"/>')
        g.append(글(x + 64, y - 8, "칸 쿼리 × 6 (학습)", 12, 600) if 꼴 == "s1" else 글(x + 64, y + 34, "칸 쿼리 × 6 (학습)", 12, 600))
    def 출력(x, y, 세로=True):
        for k in range(6):
            yy = y + k * 62 if 세로 else y; xx = x if 세로 else x + k * 70; 있 = k < len(판예측) and 판예측[k]
            g.append(f'<rect x="{xx}" y="{yy}" width="14" height="14" rx="3" fill="{색["q"][k]}" stroke="#3b3f46" stroke-width=".8"/>')
            g.append(f'<rect x="{xx + 20}" y="{yy - 18}" width="50" height="16" rx="3" fill="{색["head"]}" stroke="#3b3f46" stroke-width=".8"/>' + 글(xx + 45, yy - 6, "FFN", 10, 600))
            if 있: g.append(f'<image href="칸{k + 1}.png" x="{xx + 76}" y="{yy - 26}" width="52" height="52"/>' + 글(xx + 132, yy + 5, 판예측[k], 11, 600, "start"))
            else: g.append(글(xx + 80, yy + 5, "없음", 11, 600, "start", "#9aa0a6"))
    if 꼴 == "s1":
        W, H = 1500, 470; ym = 250; x = 백본(20, ym); g.append(화(x - 14, ym, x + 6, ym)); x = 토큰(x + 10, ym); g.append(화(x, ym, x + 40, ym))
        dx = x + 40; 블, 높 = 디코더(dx, ym - 98, 190); g.append(블); g.append(글(dx + 205, ym - 98 + 12, f"× {N}", 20, 800, "start")); 쿼리(dx + 30, ym - 98 - 64); g.append(화(dx + 95, ym - 98 - 44, dx + 95, ym - 112))
        g.append(글(dx + 95, ym + 높 - 70, "트랜스포머 디코더", 12.5, 700)); ox = dx + 270; g.append(화(dx + 190, ym, ox - 10, ym)); 출력(ox, ym - 150)
        g.append(f'<image href="예측전체.png" x="{ox + 200}" y="{ym - 140}" width="120" height="120"/>' + 글(ox + 260, ym - 8, "합친 예측", 12, 700))
        g.append(f'<image href="정답.png" x="{ox + 200}" y="{ym + 20}" width="120" height="120"/>' + 글(ox + 260, ym + 152, "정답", 12, 700))
        W = ox + 340
    else:
        ym = 150; x = 백본(20, ym); g.append(화(x - 14, ym, x + 6, ym)); tx0 = x + 10; x = 토큰(tx0, ym)
        dx, dy = 420, 360; 블, 높 = 디코더(dx, dy, 300); g.append(블); g.append(글(dx + 350, dy + 높 - 30, f"× {N}", 26, 800, "start")); g.append(글(dx + 150, dy - 22, "트랜스포머 디코더", 13, 700))
        교 = dy + 16 + 8 + 30 + 8 + 16 + 8 + 17   # 교차 주의 층 가운데(위에서: Add&Norm · FFN · Add&Norm · 교차 주의)
        g.append(f'<path d="M{tx0 + 64},{ym + 96} V{dy - 44} H{dx + 340} V{교} H{dx + 290}" fill="none" stroke="#5b616b" stroke-width="1.8" marker-end="url(#화)"/>')   # 블록 오른쪽 바깥으로 돌아 교차 주의 층으로
        g.append(글(tx0 + 72, ym + 150, "토큰 = 교차 주의의 키 · 값", 11.5, 600, "start", "#5b616b"))
        qy = dy + 높 + 24; 쿼리(dx + 85, qy); g.append(화(dx + 150, qy - 2, dx + 150, dy + 높 - 28 + 12 - 4))
        ox = dx + 400; g.append(화(dx + 300, dy + 70, ox - 10, dy + 70)); 출력(ox, dy - 60)
        g.append(f'<image href="예측전체.png" x="{ox + 200}" y="{dy - 70}" width="130" height="130"/>' + 글(ox + 265, dy + 76, "합친 예측", 12, 700))
        g.append(f'<image href="정답.png" x="{ox + 200}" y="{dy + 100}" width="130" height="130"/>' + 글(ox + 265, dy + 246, "정답", 12, 700)); W = ox + 350; H = qy + 50
    return f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="모델 구조도" class="구조도" font-family="inherit">{정의}<rect width="{W}" height="{H}" fill="#fbfaf6"/>{"".join(g)}</svg>'
