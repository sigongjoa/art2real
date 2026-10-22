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
