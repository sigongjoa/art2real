# 하네스 「모델 구조」 — 판의 실제 모델에서 자동으로 뽑음 · 서술 틀: 모델 카드(Model Architecture and Objective) + 논문 관례(DETR 식 구성 요소 · ViT 식 하이퍼파라미터 표) + torchinfo 식 층 표 · 10-22
import torch, json
def 재기(net, cfg):
    net = net.cpu().eval(); x = torch.randint(0, 256, (1, 3, 128, 128), dtype=torch.uint8); 층 = []; 걸 = []
    def 등록(이름, m, 깊이):
        def h(_, __, out):
            o = out[0] if isinstance(out, tuple) else out
            층.append({"이름": 이름, "종류": type(m).__name__, "깊이": 깊이, "출력": list(o.shape) if hasattr(o, "shape") else "", "파라미터": sum(p.numel() for p in m.parameters())})
        걸.append(m.register_forward_hook(h))
    보일 = [("cnn", net.cnn, 1)] + [(f"cnn.{i}", b, 2) for i, b in enumerate(net.cnn)] + [("dec", net.dec, 1)] + [(f"dec.layers.{i}", l, 2) for i, l in enumerate(net.dec.layers)] + [("출", net.출, 1)]
    for 이름, m, 깊 in 보일: 등록(이름, m, 깊)
    with torch.no_grad(): net(x)
    for h in 걸: h.remove()
    순 = [n for n, _, _ in 보일]; 층.sort(key=lambda r: 순.index(r["이름"]))   # 훅은 자식이 먼저 끝남 → 위에서 아래 순서로
    합 = lambda m: sum(p.numel() for p in m.parameters())
    파 = {"cnn": 합(net.cnn), "dec": 합(net.dec), "출": 합(net.출)}; 파["토큰 표시(위치 · 그림)"] = net.자리.numel() + net.시점.numel(); 파["칸 쿼리"] = net.칸.numel(); 전 = 합(net)
    L = net.dec.layers[0]; d = net.칸.shape[1]
    표 = {"입력": f"3면도 3 장 × {cfg.데이터.그림}×{cfg.데이터.그림} · {'회색 1 채널' if cfg.인코더 == 'cnn' else '실선 · 숨은선 · 좌표 4 채널'}",
          "백본": f"CNN {len(net.cnn) if cfg.인코더 == 'cnn' else len(net.cnn) - 1} 블록(3×3 합성곱 · GroupNorm · GELU) · 그림마다 같은 가중치",
          "토큰": "그림마다 8×8 = 64 · 세 장 192 · 조각 위치 표시(학습) + 그림 표시", "모델 차원 d": d, "디코더 층": len(net.dec.layers), "어텐션 헤드": L.multihead_attn.num_heads,
          "FFN 크기": L.linear1.out_features, "칸 쿼리(덩어리 최대)": net.칸.shape[0], "칸마다 출력": f"{net.출.out_features} 숫자(있음 1 · 종류 7 · 치수 9 · 축 3 · 자리 3 · 특징 2×8 · 필렛 2)",
          "짝 방식": "부피 순 고정(칸 k ↔ 부피 k 번째)" if cfg.짝 == "부피순" else "헝가리안(비용 = 종류 + 축 + 치수 + 자리)", "총 파라미터": 전}
    목표 = "loss = 칸마다 항목 10 개의 합 — 있음(BCE) · 종류(CE) · 치수(L1 × 4) · 축(CE) · 자리(L1 × 4) · 특징 있음 · 종류 · 수치 · 필렛 있음 · 크기 · 없는 칸은 「있음」만"
    학습 = f"AdamW 학습률 {cfg.학습.학습률} · 감쇠 {cfg.학습.감쇠} · 배치 {cfg.학습.배치} · {cfg.학습.에폭} 에폭 · 학습률 일정 없음"
    return {"표": 표, "파라미터": 파, "층": 층, "목표": 목표, "학습": 학습}
def md(s):
    줄 = ["### 구성", "3면도 → **CNN 백본** → 조각 토큰 192 → **트랜스포머 디코더**(칸 쿼리가 토큰에 교차 주의) → **예측 머리**(칸마다 숫자) → 덩어리 사양 → CadQuery", "",
          "### 하이퍼파라미터", "| 항목 | 값 |", "|---|---|"] + [f"| {k} | {v:,} |" if isinstance(v, int) else f"| {k} | {v} |" for k, v in s["표"].items()]
    줄 += ["", "### 층 (torchinfo 꼴 · 입력 1 × 3 × 128 × 128 을 흘려 잼)", "| 층 | 종류 | 출력 모양 | 파라미터 |", "|---|---|---|---|"] + [f"| {'　' * (r['깊이'] - 1)}{r['이름']} | {r['종류']} | {r['출력']} | {r['파라미터']:,} |" for r in s["층"]]
    줄 += ["", "### 목표와 학습", f"- {s['목표']}", f"- {s['학습']}"]; return "\n".join(줄)

def svg(구):   # 구조도 — 판 모델 숫자로 그림(상자 · 모양 · 파라미터) · 토큰 색은 보고서 토큰을 따름
    층 = {r["이름"]: r for r in 구["층"]}; 표 = 구["표"]; cnn = [r for r in 구["층"] if r["이름"].startswith("cnn.")]; dec = [r for r in 구["층"] if r["이름"].startswith("dec.layers.")]
    W, H = 1100, 430; 글 = []
    def 상자(x, y, w, h, 제, 아래="", 색="var(--sheet)", 테="var(--rule)", 굵=False):
        글.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="10" style="fill:{색};stroke:{테};stroke-width:{2 if 굵 else 1.2}"/>')
        글.append(f'<text x="{x + w / 2}" y="{y + h / 2 - (8 if 아래 else -5)}" text-anchor="middle" class="제">{제}</text>')
        if 아래: 글.append(f'<text x="{x + w / 2}" y="{y + h / 2 + 14}" text-anchor="middle" class="작">{아래}</text>')
    def 화(x0, y0, x1, y1): 글.append(f'<line x1="{x0}" y1="{y0}" x2="{x1}" y2="{y1}" style="stroke:var(--muted);stroke-width:1.6" marker-end="url(#끝)"/>')
    상자(10, 150, 120, 80, "3면도 × 3", "1 × 128 × 128")
    x = 160
    for i, r in enumerate(cnn):
        o = r["출력"]; 상자(x, 150, 112, 80, f"블록 {i + 1}", f"{o[1]} × {o[2]}²", "var(--paper)"); 글.append(f'<text x="{x + 56}" y="{248}" text-anchor="middle" class="작">{r["파라미터"]:,}</text>')
        화(x - 30, 190, x - 2, 190) if i == 0 else 화(x - 18, 190, x - 2, 190); x += 130
    글.append(f'<text x="{160 + (x - 160 - 18) / 2}" y="{136}" text-anchor="middle" class="묶">CNN 백본 · 그림마다 같은 가중치 · {층["cnn"]["파라미터"]:,}</text>')
    화(x - 18, 190, x + 10, 190); 상자(x + 10, 140, 130, 100, "조각 토큰", f"192 × {표['모델 차원 d']}", "var(--paper)"); 글.append(f'<text x="{x + 75}" y="{258}" text-anchor="middle" class="작">+ 위치 · 그림 표시</text>')
    tx = x + 140; dx = tx + 60
    상자(dx, 20, 300, 56, f"칸 쿼리 {표['칸 쿼리(덩어리 최대)']} 개", f"학습되는 {표['칸 쿼리(덩어리 최대)']} × {표['모델 차원 d']}", "var(--paper)")
    화(dx + 150, 76, dx + 150, 104)
    상자(dx, 104, 300, 172, "", "", "var(--sheet)", "var(--ink)", True)
    글.append(f'<text x="{dx + 150}" y="{126}" text-anchor="middle" class="제">트랜스포머 디코더 × {len(dec)}</text>')
    for k, (이름, 설) in enumerate((("① 칸끼리 주의", "6 ↔ 6"), ("② 칸 → 토큰 교차 주의", f"6 → 192 · 헤드 {표['어텐션 헤드']}"), ("③ FFN", f"{표['모델 차원 d']} → {표['FFN 크기']} → {표['모델 차원 d']}"))):
        y = 140 + k * 42; 글.append(f'<rect x="{dx + 16}" y="{y}" width="268" height="34" rx="7" style="fill:var(--paper);stroke:var(--rule)"/><text x="{dx + 28}" y="{y + 22}" class="작진">{이름}</text><text x="{dx + 272}" y="{y + 22}" text-anchor="end" class="작">{설}</text>')
    글.append(f'<text x="{dx + 150}" y="{296}" text-anchor="middle" class="작">층마다 {dec[0]["파라미터"]:,} · 합 {층["dec"]["파라미터"]:,}</text>')
    화(tx, 190, dx - 2, 190)
    화(dx + 150, 276, dx + 150, 330); 상자(dx, 330, 300, 64, f"예측 머리 {표['모델 차원 d']} → {층['출']['출력'][-1]}", f"칸마다 · {층['출']['파라미터']:,}", "var(--paper)")
    화(dx + 300, 362, dx + 330, 362); 상자(dx + 330, 318, 200, 88, "덩어리 사양 × 6", "종류 · 치수 · 축 · 자리 · 구멍", "var(--sheet)")
    W = dx + 545
    return (f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="모델 구조도" class="구조도"><defs><marker id="끝" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0 0L10 5L0 10z" style="fill:var(--muted)"/></marker></defs>'
            + "".join(글) + "</svg>")
