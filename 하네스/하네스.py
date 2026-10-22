# 하네스 v0 — 판 하나를 코드가 끌고 감: 관문 → 연기 판 → 실행 → 점검 → 판정 → 기록 · 근거 claudedocs/research_실험하네스_20261022.md · 10-22
# 사용(cadrille venv): python 하네스/하네스.py --config-name 판_127재현   (판 설정은 하네스/conf/판_*.yaml · 바탕.yaml 에서 손잡이 하나만 바꿈)
# 산출: out/하네스/<판>/ (점검점 · tb · 그림) + 하네스/판/<판>/ (설정 · 바뀐 것 · 지표 · 판정 — git 에 남김) + 하네스/results.tsv 한 줄
import os, sys, json, time, subprocess, numpy as np, hydra
from omegaconf import OmegaConf
뿌리 = "G:/art2real"; 실험 = 뿌리 + "/원화3d/실험_20261013/캐드부품"; sys.path.insert(0, 실험)
import 모델124 as B, 조립124 as C, 모델127 as M7
손잡이밖 = {"판", "기준", "대조", "점검", "hydra"}
def 펼친(d, 앞=""): return {f"{앞}{k}": v for k0, v0 in d.items() for k, v in (펼친(v0, f"{k0}.").items() if isinstance(v0, dict) else [(k0, v0)])} if isinstance(d, dict) else {앞: d}
class 관문거부(Exception): pass
# ── ① 관문 ────────────────────────────────────────────────
def 관문(cfg, 설정파일):
    판 = cfg.판; 바탕 = OmegaConf.to_container(OmegaConf.load(f"{뿌리}/하네스/conf/바탕.yaml")); 지금 = OmegaConf.to_container(cfg, resolve=True)
    a, b = (펼친({k: v for k, v in d.items() if k not in 손잡이밖}) for d in (바탕, 지금)); 바뀐 = {k: (a.get(k), b.get(k)) for k in set(a) | set(b) if a.get(k) != b.get(k)}
    문 = []
    if not cfg.기준: 문.append("기준이 없다 — 돌리기 전에 기준을 적어라")
    if cfg.대조 and cfg.대조.get("에폭") != cfg.학습.에폭: 문.append(f"대조 에폭 {cfg.대조.get('에폭')} ≠ 이 판 에폭 {cfg.학습.에폭} — 같은 시점끼리만 비교")
    if not cfg.대조: 문.append("대조가 없다")
    if f"| {판.가지} " not in open(f"{뿌리}/claudedocs/문제트리.md", encoding="utf-8").read(): 문.append(f"가지 {판.가지} 가 문제 트리에 없다")
    n = len(바뀐)
    if 판.종류 == "재현" and n: 문.append(f"재현 판인데 손잡이 {n} 개를 바꿈: {sorted(바뀐)}")
    if 판.종류 == "비교" and n != 1: 문.append(f"비교 판은 손잡이 하나만 — 지금 {n} 개: {sorted(바뀐)} (여럿이면 종류: 탐색)")
    상 = subprocess.run(["git", "-C", 뿌리, "-c", "core.quotepath=off", "status", "--porcelain", "--", 설정파일], capture_output=True, text=True, encoding="utf-8").stdout.strip()
    if 상: 문.append(f"판 설정이 커밋 안 됨({상[:2].strip()}) — 기준은 돌리기 전에 커밋해야 사전등록")
    if 문: raise 관문거부("\n  × ".join(["관문 거부:"] + 문))
    return 바뀐
# ── 부품 등록표 ───────────────────────────────────────────
def 망(cfg):
    if cfg.인코더 == "cnn": return M7.망()
    if cfg.인코더 == "cnn4": import 모델129 as M9; return M9.망("c")
    raise KeyError(cfg.인코더)
def 손실함수(cfg):
    import 손실그림124 as L
    if cfg.짝 == "부피순": return lambda o, Y, 쓰: sum(L.항목(o, Y, 쓰).values())
    if cfg.짝 == "헝가리안":
        import 모델129 as M9
        def f(o, Y, 쓰): y, s = M9.바꾼과녁(o, Y, 쓰); return sum(L.항목(o, y, s).values())
        return f
    raise KeyError(cfg.짝)
def 자료(dev):
    import torch
    z = np.load(M7.D + "그림.npz"); 이 = list(z["이름"]); 색 = {f"{r['i']:05d}": r for r in B.색인()}; 과 = [B.과녁(색[n]) for n in 이]
    X = torch.tensor(z["X"]).to(dev); Y = torch.tensor(np.stack([a for a, _ in 과])).to(dev); 쓰 = torch.tensor(np.stack([b for _, b in 과])).to(dev)
    시 = np.array([int(n) >= B.NT for n in 이]); return X, Y, 쓰, torch.tensor(np.nonzero(~시)[0]), torch.tensor(np.nonzero(시)[0]), 이, z["X"]
# ── ② 연기 판 ─────────────────────────────────────────────
def 연기(cfg, X, Y, 쓰, idx):
    import torch
    torch.cuda.reset_peak_memory_stats(); net = 망(cfg).cuda(); f = 손실함수(cfg); opt = torch.optim.AdamW(net.parameters(), 1e-3); ix = idx[:cfg.학습.미세]
    l0 = float(f(net(X[ix]).reshape(-1, C.K, B.W), Y[ix], 쓰[ix])); assert np.isfinite(l0), "연기: 첫 loss 가 수가 아님"
    for _ in range(40): opt.zero_grad(); l = f(net(X[ix]).reshape(-1, C.K, B.W), Y[ix], 쓰[ix]); l.backward(); opt.step()
    값 = {"첫loss": round(l0, 3), "한배치40걸음": round(float(l), 3), "VRAM_GB": round(torch.cuda.max_memory_allocated() / 2**30, 2)}
    assert 값["한배치40걸음"] < 0.5 * l0, f"연기: 배치 하나를 못 외움 {값}"; assert 값["VRAM_GB"] < 7.0, f"연기: VRAM {값['VRAM_GB']} GB"
    del net, opt; torch.cuda.empty_cache(); return 값
# ── ③ 실행 ────────────────────────────────────────────────
def 실행(cfg, 폴더, X, Y, 쓰, idx, vx, 이):
    import torch
    from torch.utils.tensorboard import SummaryWriter
    os.makedirs(폴더 + "점검", exist_ok=True); net = 망(cfg).cuda(); opt = torch.optim.AdamW(net.parameters(), cfg.학습.학습률, weight_decay=cfg.학습.감쇠); f = 손실함수(cfg); tb = SummaryWriter(폴더 + "tb")
    기록, 시작, t0 = [], 0, time.time()
    if os.path.exists(폴더 + "점검/마지막.pt"):
        k = torch.load(폴더 + "점검/마지막.pt"); net.load_state_dict(k["모델"]); opt.load_state_dict(k["옵티"]); 시작, 기록 = k["에폭"], k["기록"]; torch.set_rng_state(k["rng"]); print("이어 함", 시작, flush=True)
    for ep in range(시작, cfg.학습.에폭):
        net.train(); perm = idx[torch.randperm(len(idx))]; ls = []
        for b in range(0, len(perm), cfg.학습.배치):
            ix = perm[b:b + cfg.학습.배치]; opt.zero_grad(); lt = 0.
            for c in range(0, len(ix), cfg.학습.미세): jx = ix[c:c + cfg.학습.미세]; l = f(net(X[jx]).reshape(-1, C.K, B.W), Y[jx], 쓰[jx]) * len(jx) / len(ix); l.backward(); lt += float(l)
            opt.step(); ls.append(lt)
        net.eval()
        with torch.no_grad(): ov = torch.cat([net(X[vx[i:i + 100]]) for i in range(0, len(vx), 100)]).reshape(-1, C.K, B.W); lv = float(f(ov, Y[vx], 쓰[vx])); 수 = float(((ov[..., 0] > 0).sum(1) == Y[vx][..., 0].sum(1)).float().mean())
        기록.append({"에폭": ep + 1, "학습": float(np.mean(ls)), "시험": lv, "몸수맞음": 수, "초": round(time.time() - t0)}); print(기록[-1], flush=True)
        for k_, v_ in 기록[-1].items(): k_ != "에폭" and tb.add_scalar(k_, v_, ep + 1)
        torch.save(net.state_dict(), 폴더 + f"점검/{ep + 1:02d}.pt"); torch.save({"모델": net.state_dict(), "옵티": opt.state_dict(), "에폭": ep + 1, "기록": 기록, "rng": torch.get_rng_state()}, 폴더 + "점검/마지막.pt")
    tb.close(); json.dump(기록, open(폴더 + "학습.json", "w", encoding="utf-8"), ensure_ascii=False); return net, 기록
# ── ④ 점검 ────────────────────────────────────────────────
def 점검(cfg, 폴더, net, 기록, Xnp, 이):
    import torch, 층보기127 as V, 탐침128 as P
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt; plt.rcParams["font.family"] = "Malgun Gothic"
    지 = {"시험loss": round(기록[-1]["시험"], 4), "학습loss": round(기록[-1]["학습"], 4), "몸수맞음": round(기록[-1]["몸수맞음"], 4)}; net = net.cpu().eval()
    색 = {f"{r['i']:05d}": r for r in B.색인()}; 통 = [n for n in 이 if int(n) >= B.NT][:64]
    X통 = torch.tensor(Xnp[[이.index(n) for n in 통]]); Y통 = np.stack([B.과녁(색[n])[0] for n in 통]); 빈 = torch.tensor(Xnp[[이.index(n) for n in 통]].reshape(64, 3, 8, 16, 8, 16).max((3, 5)) < 40).reshape(64, 192).float()
    if "층보기" in cfg.점검:
        with torch.no_grad(): s = V.통계(V.펼침(net, X통), Y통, 빈)
        지 |= {"칸닮음4": round(s["층4 칸 닮음"], 4), "빈조각주의4": round(s["층4 빈 조각 몫"], 4), "주의엔트로피4": round(s["층4 주의 엔트로피"], 4), "자리퍼짐": round(s["출력 자리 퍼짐"], 4)}
    if "탐침" in cfg.점검:
        rng = np.random.default_rng(128); 자 = [(k, *P.한장(종, rng, 128)) for k, 종 in enumerate(P.종들) for _ in range(600)]
        y = np.array([a[0] for a in 자]); rr = np.array([a[3] for a in 자]); F = P.특징(net, [a[1] for a in 자], [a[2] for a in 자], 128)
        idx = np.random.default_rng(0).permutation(len(y)); 학, 시 = idx[:2400], idx[2400:]; 곡 = y == 1
        for b in (3, 4): 지[f"탐침{b}_구조"] = P.릿지(F[f"블록 {b}"], y, 학, 시, True); 지[f"탐침{b}_곡률"] = P.릿지(F[f"블록 {b}"], np.log(rr), 학[곡[학]], 시[곡[시]], False)
        지["탐침_구조"], 지["탐침_곡률"] = 지["탐침4_구조"], 지["탐침4_곡률"]
    if "특징" in cfg.점검:   # 실제 3면도에서 주의 · CNN 이 곡선 · 접합 · 겹친 곳을 찾나(하네스/특징.py)
        import 특징 as T; t = T.재기(net, Xnp, 이, 폴더); json.dump(t, open(폴더 + "특징.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        지 |= {"쏠림4_곡선": t["쏠림4"]["곡선"], "쏠림4_접합": t["쏠림4"]["접합·교차"], "쏠림4_빈칸": t["쏠림4"]["빈칸"], "특징탐침": t["탐침_학습CNN"][0], "특징탐침_무작위": t["탐침_무작위CNN"][0]}
    if "평가" in cfg.점검:
        import 모델125 as T5
        T5.평가(net, lambda ns: torch.tensor(Xnp[[이.index(n) for n in ns]]), 폴더); r = json.load(open(폴더 + "결과.json", encoding="utf-8")); 지 |= {"시험IoU": r["시험"]["IoU 중앙"], "학습IoU": r["학습"]["IoU 중앙"]}
    # 시트 한 장: 곡선 · 지표 대 대조 · 12003 세 장 칸 1 주의
    fig = plt.figure(figsize=(22, 10)); fig.suptitle(f"판 {cfg.판.이름} · 가지 {cfg.판.가지} · {cfg.판.종류} — {cfg.판.물음}", fontsize=17, weight="bold")
    a = fig.add_axes([.04, .55, .28, .35]); e = [r["에폭"] for r in 기록]; a.plot(e, [r["학습"] for r in 기록], "o-", label="학습 loss"); a.plot(e, [r["시험"] for r in 기록], "o-", label="시험 loss"); a.legend(); a.set_title("학습 곡선"); a.grid(alpha=.3)
    a = fig.add_axes([.38, .55, .28, .35]); a.axis("off"); 대 = dict(cfg.대조.get("값", {})) if cfg.대조 else {}
    a.text(0, 1, f"{'지표':12s} {'이 판':>9s} {'대조':>9s}", fontsize=13, family="Malgun Gothic", weight="bold", va="top")
    for k, (n, v) in enumerate(지.items()): a.text(0, .92 - k * .06, f"{n:12s} {v:9.3f} {대.get(n, float('nan')):9.3f}", fontsize=12, va="top")
    n = "12003"; x = torch.tensor(Xnp[[이.index(n)]])
    with torch.no_grad(): d = V.펼침(net, x)
    w = d["주의4"][0, 0].numpy().reshape(3, 8, 8)
    for v in range(3):
        a = fig.add_axes([.04 + v * .21, .04, .19, .45]); a.imshow(Xnp[이.index(n), v], cmap="gray"); a.imshow(np.kron(w[v] / w.max(), np.ones((16, 16))), cmap="viridis", alpha=.6, vmin=0, vmax=1); a.axis("off"); a.set_title(f"{n} {B.뷰[v]} · 4 층 칸1 주의 {w[v].sum():.2f}", fontsize=12)
    fig.savefig(폴더 + "시트.png", dpi=60); plt.close(fig); return 지
# ── ⑤ 판정 · ⑥ 기록 ──────────────────────────────────────
def 판정(cfg, 지):
    줄 = []
    for c in cfg.기준:
        v = 지.get(c.지표); ok = v is not None and {">=": v >= c.값, "<=": v <= c.값, ">": v > c.값, "<": v < c.값}[c.식]; 줄.append({"지표": c.지표, "식": c.식, "값": c.값, "이 판": v, "통과": bool(ok)})
    전 = all(r["통과"] for r in 줄); 말 = ("통과" if 전 else "실패") if cfg.판.종류 != "탐색" else ("탐색 — 이김 판정 없음 · " + ("기준 넘음" if 전 else "기준 못 넘음"))
    return {"판정": 말, "기준": 줄}
def 기록(cfg, 폴더, 바뀐, 연, 지, 판):
    남 = f"{뿌리}/하네스/판/{cfg.판.이름}/"; os.makedirs(남, exist_ok=True); 해시 = subprocess.run(["git", "-C", 뿌리, "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip()
    OmegaConf.save(cfg, 남 + "설정.yaml"); json.dump({"바뀐 손잡이": {k: list(v) for k, v in 바뀐.items()}, "git": 해시, "날짜": time.strftime("%Y-%m-%d %H:%M"), "연기": 연, "지표": 지, **판, "산출 폴더": 폴더}, open(남 + "판정.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    import shutil
    for 파 in ("시트.png", "학습.json", "특징.json", "특징.png"):
        if os.path.exists(폴더 + 파): shutil.copy(폴더 + 파, 남 + 파)
    import 보고; print("보고서", 보고.만들기(cfg.판.이름))
    표 = f"{뿌리}/하네스/results.tsv"; 새 = not os.path.exists(표)
    with open(표, "a", encoding="utf-8") as f:
        if 새: f.write("날짜\t판\t가지\t종류\t바뀐 손잡이\t판정\t시험loss\t탐침_구조\t탐침_곡률\t칸닮음4\tgit\n")
        f.write(f"{time.strftime('%m-%d %H:%M')}\t{cfg.판.이름}\t{cfg.판.가지}\t{cfg.판.종류}\t{','.join(f'{k}={v[1]}' for k, v in 바뀐.items()) or '-'}\t{판['판정']}\t{지.get('시험loss')}\t{지.get('탐침_구조')}\t{지.get('탐침_곡률')}\t{지.get('칸닮음4')}\t{해시}\n")
    print("gh 이슈: 건너뜀(공개 저장소 아직 없음)")
@hydra.main(version_base=None, config_path="conf")
def 주(cfg):
    import torch
    설정파일 = f"하네스/conf/{hydra.core.hydra_config.HydraConfig.get().job.config_name}.yaml"
    try: 바뀐 = 관문(cfg, 설정파일)
    except 관문거부 as e: print(e); sys.exit(2)
    print("관문 통과 · 바뀐 손잡이", {k: v[1] for k, v in 바뀐.items()}, flush=True)
    폴더 = f"{뿌리}/out/하네스/{cfg.판.이름}/"; os.makedirs(폴더, exist_ok=True); X, Y, 쓰, idx, vx, 이, Xnp = 자료("cuda")
    연 = 연기(cfg, X, Y, 쓰, idx) if "연기" in cfg.점검 else {}; print("연기 판 통과", 연, flush=True)
    net, 록 = 실행(cfg, 폴더, X, Y, 쓰, idx, vx, 이); del X, Y, 쓰; torch.cuda.empty_cache()
    지 = 점검(cfg, 폴더, net, 록, Xnp, 이); 판 = 판정(cfg, 지); 기록(cfg, 폴더, 바뀐, 연, 지, 판)
    print("판정", json.dumps(판, ensure_ascii=False), flush=True)
if __name__ == "__main__":
    주()
