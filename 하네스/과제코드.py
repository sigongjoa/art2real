# 하네스 과제 「코드생성」 — 도면 → cadrille(2B 언어 모델 · CadQuery 를 이미 앎) LoRA 미세조정 → CadQuery 글 → 실행 → 실루엣 IoU · 10-24
# 입력(코드.입력): 선글 = 판 137 선지도 → 벡터화(141~143 규칙) → 선마다 글 한 줄(우리 인코더 · 145) | 도면 = 3면도 그림 그대로 cadrille 의 Qwen2-VL ViT 로(146 · 순수 ViT 기준선)
# 정답: 사양 → CadQuery 글(하네스/코드글.py · 왕복 부피 IoU ≥ 0.995) · 학습 3000 · 시험 299(번호 ≥ B.NT · 선지도 판과 같은 얼린 시험)
# 평가: 생성 글을 일꾼 프로세스에서 실행(시간 상한) → 데이터117.렌더 실루엣 → 정답(조립124.짓기) 실루엣과 IoU · 실패 = 0 · 127 의 0.737 과 같은 자
import os, sys, json, glob, time, math, random, numpy as np
뿌리 = "G:/art2real"; sys.path.insert(0, 뿌리 + "/하네스"); sys.path.insert(0, 뿌리 + "/원화3d/실험_20261013/캐드부품")
캐 = 뿌리 + "/트레일/trail10_cadrille"; 자료폴더 = 뿌리 + "/out/하네스/코드자료/"; 뷰글자 = "TFS"   # 위 · 앞 · 옆
지시 = "3-view line list. T=top F=front S=side. L=line A=arc: x0 y0 x1 y1 [mid x y], h=hidden. Write CadQuery code.\n"
# ── 1. 자료 ─────────────────────────────────────────────
def _글하나(i):   # 정답 사양 → 글 파일(일꾼 프로세스 · CadQuery 가 걸려도 본 프로세스는 안 멈춤)
    p = 자료폴더 + f"글/{i}.py"
    if os.path.exists(p): return
    try:
        import 코드글, 모델124 as B
        s = json.load(open(B.D + f"사양/{i}.json", encoding="utf-8")); open(p, "w", encoding="utf-8").write(코드글.글로(s["코드"]))
    except Exception as ex: open(p + ".err", "w", encoding="utf-8").write(str(ex)[:300])
def _오류(p):   # 생성 글 파일 하나 실행 → p.err(오류 꼴 · 첫 줄) · 성공이면 빈 파일 · 렌더 실패만으로는 왜 깨졌는지 모름(10-24 145 실행률 0.455)
    try:
        import 코드글; 글 = open(p, encoding="utf-8").read(); compile(글, "생성", "exec"); 코드글.실행(글); 말 = ""   # compile 먼저 = 줄 번호가 생성 글 기준(머리말 6 줄 빼고)
    except Exception as ex: 말 = f"{type(ex).__name__}: {str(ex).splitlines()[0][:120] if str(ex) else ''}"
    open(p + ".err", "w", encoding="utf-8").write(말)
def 오류들(파일들, 초=60):   # → {파일: 오류 말} · 시간 넘으면 「시간 넘음」
    일꾼(_오류, [f for f in 파일들 if not os.path.exists(f + ".err")], 초)
    return {f: open(f + ".err", encoding="utf-8").read() if os.path.exists(f + ".err") else "시간 넘음" for f in 파일들}
def 일꾼(함수, 일, 초=120, n=6):   # 부품마다 프로세스 · 시간 상한(과제세뷰.투영들 과 같은 꼴)
    import multiprocessing as mp
    도는 = {}
    while 일 or 도는:
        while 일 and len(도는) < n: i = 일.pop(); pr = mp.Process(target=함수, args=(i,)); pr.start(); 도는[i] = (pr, time.time())
        for i, (pr, t) in list(도는.items()):
            if not pr.is_alive(): 도는.pop(i)
            elif time.time() - t > 초: pr.kill(); 도는.pop(i)
        time.sleep(.2)
def 줄글(선들, v):   # 벡터화 선 목록 → 글 줄들(긴 선부터 최대 120 줄 · 자리 순 정렬)
    줄 = []
    for l in sorted(선들, key=lambda l: -l["_m"].sum())[:120]:
        x0, y0 = l["시작"]; x1, y1 = l["끝"]; t = f"{뷰글자[v]} {'A' if l['종류'] == '원호' else 'L'} {x0} {y0} {x1} {y1}"
        if l["종류"] == "원호": t += f" {l['중간'][0]} {l['중간'][1]}"
        줄.append((y0, x0, t + (" h" if l["숨음"] else "")))
    return [t for *_, t in sorted(줄)]
def _선하나(k):   # 부품 k(자료 순번)의 세 뷰 → 선 글
    z = np.load(자료폴더 + "선지도.npz"); n = str(z["이름"][k]); p = 자료폴더 + f"선/{n}.txt"
    if os.path.exists(p): return
    import 과제벡터화 as V
    줄 = []
    for v in range(3): 줄 += 줄글(V.벡터화(z["있"][k, v], z["열"][k, v].astype(np.float32), z["숨"][k, v], 2., 이음=True, 숨메움=True), v)
    open(p, "w", encoding="utf-8").write("\n".join(줄))
def 자료(입력판="137전부합침"):   # 글(정답) · 선(입력) 을 부품 3299 개 모두 · 한 번 만들면 재사용
    import torch, 과제선지도 as G, 분석그림 as A, 모델124 as B
    from omegaconf import OmegaConf
    for d in ("글", "선"): os.makedirs(자료폴더 + d, exist_ok=True)
    이름들 = sorted(os.path.basename(f)[:5] for f in glob.glob(f"{뿌리}/out/하네스/선정답/*.npz"))   # 선지도가 있는 3299 개만(색인 전체 12000+ 로 돌려 쓸데없이 길었음 · 10-24)
    일꾼(_글하나, [n for n in 이름들 if not os.path.exists(자료폴더 + f"글/{n}.py") and not os.path.exists(자료폴더 + f"글/{n}.py.err")])
    if not os.path.exists(자료폴더 + "선지도.npz"):
        c = OmegaConf.load(f"{뿌리}/하네스/판/{입력판}/설정.yaml"); X, Y, _, idx, vx, 이, Xnp = G.자료("cuda", c); net = A.불러(입력판).cuda(); 있, 열, 숨 = [], [], []
        for b in range(0, len(X), 64):
            o = G.예측(net, X[b:b + 64])[:, :, :G.출].float(); pr = o[:, :, :G.K].softmax(2)
            있.append((1 - pr[:, :, 0] > .5).cpu().numpy()); 열.append(torch.sigmoid(o[:, :, G.K + 1]).half().cpu().numpy()); 숨.append((o[:, :, G.K] > 0).cpu().numpy())
        np.savez(자료폴더 + "선지도.npz", 이름=np.array(이), 있=np.concatenate(있), 열=np.concatenate(열), 숨=np.concatenate(숨), X=Xnp); del X, Y, net; torch.cuda.empty_cache()
    z = np.load(자료폴더 + "선지도.npz"); 일꾼(_선하나, [k for k, n in enumerate(z["이름"]) if not os.path.exists(자료폴더 + f"선/{n}.txt")], 초=300)
    return 목록()
def 목록():   # → [(부품, 시험?, 입력 선 글, 정답 글)] 둘 다 있는 것만
    import 모델124 as B
    out = []
    for p in sorted(glob.glob(자료폴더 + "선/*.txt")):
        n = os.path.basename(p)[:5]; g = 자료폴더 + f"글/{n}.py"
        if os.path.exists(g): out.append((n, int(n) >= B.NT, open(p, encoding="utf-8").read(), open(g, encoding="utf-8").read()))
    return out
def 도면그림(n):   # 3면도 → 256 회색 2×2(위 · 앞 / 옆 · 빈칸) · cadrille 영상 입력
    from PIL import Image
    z = np.load(자료폴더 + "선지도.npz", mmap_mode="r"); x = z["X"][list(z["이름"]).index(n)]; g = np.full((256, 256), 255, np.uint8)
    for v, (r, c) in enumerate(((0, 0), (0, 1), (1, 0))): g[r * 128:(r + 1) * 128, c * 128:(c + 1) * 128] = 255 - x[v]
    return Image.fromarray(g).convert("RGB")
# ── 2. 학습 · 생성 ───────────────────────────────────────
def 항목(n, 선, 글, 입력, 정답=True):
    it = {"description": 지시 + 선 if 입력 == "선글" else "Generate cadquery code", "file_name": n}
    if 입력 == "도면": it["video"] = [도면그림(n)]
    if 정답: it["answer"] = 글
    return it
def 모델(rank=16):
    import torch
    from transformers import AutoProcessor
    from peft import LoraConfig, get_peft_model
    sys.path.insert(0, 캐); from cadrille import Cadrille
    m = Cadrille.from_pretrained(캐 + "/weights/cadrille", torch_dtype=torch.bfloat16, attn_implementation="sdpa", device_map="cuda")
    proc = AutoProcessor.from_pretrained(캐 + "/weights/qwen2vl2b", min_pixels=256 * 28 * 28, max_pixels=1280 * 28 * 28, padding_side="left")
    m.gradient_checkpointing_enable(gradient_checkpointing_kwargs={"use_reentrant": False}); m.enable_input_require_grads()
    m = get_peft_model(m, LoraConfig(r=rank, lora_alpha=2 * rank, lora_dropout=.05, target_modules=["q_proj", "k_proj", "v_proj", "o_proj"])); return m, proc
def 묶(items, proc, eval=False):
    import torch; sys.path.insert(0, 캐); from cadrille import collate
    b = collate(items, processor=proc, n_points=256, eval=eval); return {k: (v.cuda() if torch.is_tensor(v) else v) for k, v in b.items()}
def 손실(model, b):   # 답(코드) 자리만 lm_head → CE · 10-24 선 글 입력 중앙 1829 토큰에 전체 자리 float logits(151k 어휘)가 8 GB 를 넘어 공유 메모리 19.8 GB 로 샘
    import torch, torch.nn.functional as F
    base = model.get_base_model(); head = base.lm_head; base.lm_head = torch.nn.Identity()
    try: h = base(**{k: v for k, v in b.items() if k != "labels"}).logits
    finally: base.lm_head = head
    y = b["labels"][:, 1:]; m = y != -100; return F.cross_entropy(head(h[:, :-1][m]).float(), y[m])
def 생성(model, proc, items, 배=4, 최대=1024):
    import torch
    model.eval(); out = []
    for s in range(0, len(items), 배):
        b = 묶(items[s:s + 배], proc, eval=True); 인 = {k: b[k] for k in ("input_ids", "attention_mask", "point_clouds", "is_pc", "is_img") if k in b}
        if b.get("pixel_values_videos") is not None: 인 |= {"pixel_values_videos": b["pixel_values_videos"], "video_grid_thw": b["video_grid_thw"]}
        with torch.no_grad(): g = model.generate(**인, max_new_tokens=최대, do_sample=False, use_cache=True)
        out += proc.batch_decode([o[len(i):] for i, o in zip(b["input_ids"], g)], skip_special_tokens=True)
        if len(items) > 8 and (s // 배) % 10 == 0: print(f"생성 {len(out)}/{len(items)}", flush=True)   # 10-24 145 생성 1 시간을 못 봤음
    model.train(); return out
# ── 3. 평가 ─────────────────────────────────────────────
def 평가(이름들, 글들):   # 생성 글 · 정답 사양 → 실루엣 IoU(병렬렌더 「글」 · 「조립」)
    import 모델124 as B
    색 = {f"{r['i']:05d}": r for r in B.색인()}
    렌 = B.병렬렌더([("글", g) for g in 글들] + [("조립", 색[n]["코드"]) for n in 이름들]); k = len(글들); 줄 = []
    for t, n in enumerate(이름들):
        예, 정 = 렌[t], 렌[k + t]; iou = 0. if 예 is None or 정 is None else float((예[1] & 정[1]).sum() / max((예[1] | 정[1]).sum(), 1))
        줄.append({"부품": n, "실행": 예 is not None, "IoU": round(iou, 4)})
    return 줄, 렌
def 점검(cfg, 폴더):   # 하네스가 부름: 자료 → LoRA 학습(학습.스텝 · 4 스텝마다 갱신) → 시험 생성 → 실행 · IoU → 그림
    import torch
    s = cfg.코드; 입력 = str(s.입력); 목 = 자료(); 학 = [x for x in 목 if not x[1]]; 시 = [x for x in 목 if x[1]]
    if s.get("시험수"): 시 = 시[:int(s.시험수)]
    random.seed(int(cfg.학습.get("시드", 0))); torch.manual_seed(int(cfg.학습.get("시드", 0)))
    model, proc = 모델(int(s.get("랭크", 16))); 스텝 = int(cfg.학습.스텝); 누적 = 4
    opt = torch.optim.AdamW([p for p in model.parameters() if p.requires_grad], lr=float(cfg.학습.학습률), weight_decay=0.)
    sched = torch.optim.lr_scheduler.LambdaLR(opt, lambda t: min(1., (t + 1) / 20) * .5 * (1 + math.cos(math.pi * min(t, 스텝 // 누적) / max(스텝 // 누적, 1))))
    고정 = [항목(n, l, g, 입력) for n, _, l, g in 시[:16]]; 기록 = []; 묶음손 = []; t0 = time.time()
    검 = 검증부품(시); 검폴더 = 폴더 + "검증/"; os.makedirs(검폴더, exist_ok=True)
    def 검증생성(step):   # 10-24 사용자 「스텝별 validation 결과가 어떻게 바뀌는지 코드랑 렌더 둘 다」 · 고정 시험 부품 넷 · 탐욕 생성
        for (n, _, l, g), 글 in zip(검, 생성(model, proc, [항목(n, l, g, 입력, 정답=False) for n, _, l, g in 검])): open(검폴더 + f"{step:05d}_{n}.py", "w", encoding="utf-8").write(글)
    검증생성(0); model.train()
    for step in range(1, 스텝 + 1):
        n, _, l, g = random.choice(학); loss = 손실(model, 묶([항목(n, l, g, 입력)], proc)); (loss / 누적).backward(); 묶음손.append(float(loss))
        if step % 누적 == 0: torch.nn.utils.clip_grad_norm_([p for p in model.parameters() if p.requires_grad], 1.); opt.step(); sched.step(); opt.zero_grad()
        if step % 250 == 0 or step == 스텝:
            model.eval()
            with torch.no_grad(): 시손 = float(np.mean([float(손실(model, 묶([it], proc))) for it in 고정]))
            model.train(); 검증생성(step); 기록.append({"에폭": step, "학습": float(np.mean(묶음손[-250:])), "시험": 시손, "초": round(time.time() - t0), "GPU": round(torch.cuda.max_memory_allocated() / 1e9, 2)}); print(기록[-1], flush=True)
    model.save_pretrained(폴더 + "lora"); json.dump(기록, open(폴더 + "학습.json", "w", encoding="utf-8"), ensure_ascii=False)
    글들 = 생성(model, proc, [항목(n, l, g, 입력, 정답=False) for n, _, l, g in 시]); os.makedirs(폴더 + "생성", exist_ok=True)
    for (n, *_), 글 in zip(시, 글들): open(폴더 + f"생성/{n}.py", "w", encoding="utf-8").write(글)
    del model; torch.cuda.empty_cache()
    줄, 렌 = 평가([x[0] for x in 시], 글들)
    오 = 오류들([폴더 + f"생성/{r['부품']}.py" for r in 줄 if not r["실행"]])
    for r in 줄: r["오류"] = 오.get(폴더 + f"생성/{r['부품']}.py", "")
    json.dump(줄, open(폴더 + "평가.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    iou = np.array([r["IoU"] for r in 줄]); 그림(폴더, 시, 글들, 렌, 줄, 입력); 검증정리(폴더, 검, {x[0]: 렌[len(글들) + t] for t, x in enumerate(시)})
    return {"코드_실행률": round(float(np.mean([r["실행"] for r in 줄])), 4), "코드_IoU": round(float(np.median(iou)), 4), "코드_IoU평균": round(float(iou.mean()), 4),
            "코드_학습loss": round(기록[-1]["학습"], 4), "코드_시험loss": round(기록[-1]["시험"], 4), "시험loss": round(기록[-1]["시험"], 4), "학습loss": round(기록[-1]["학습"], 4)}
def 검증부품(시):   # 시트와 같은 넷: 12050 + 앞 셋
    보 = [x for x in 시 if x[0] == "12050"] + 시[:3]; return list({x[0]: x for x in 보}.values())[:4]
def 검증정리(폴더, 검, 정렌):   # 검증/*.py → 렌더 · IoU · 오류 → 검증.json · 검증/<스텝>_<부품>.png · 검증.png(행 = 스텝 · 열 = 부품)
    import 모델124 as B; from PIL import Image
    파 = sorted(glob.glob(폴더 + "검증/*.py")); 글 = [open(f, encoding="utf-8").read() for f in 파]; 렌 = B.병렬렌더([("글", g) for g in 글]); 오 = 오류들([f for f, x in zip(파, 렌) if x is None]); 줄 = []
    for f, g, x in zip(파, 글, 렌):
        st, n = os.path.basename(f)[:-3].split("_"); 정 = 정렌.get(n); iou = 0. if x is None or 정 is None else float((x[1] & 정[1]).sum() / max((x[1] | 정[1]).sum(), 1))
        if x is not None: Image.fromarray(np.asarray(x[0])).resize((200, 200)).save(f[:-3] + ".png")
        줄.append({"스텝": int(st), "부품": n, "실행": x is not None, "IoU": round(iou, 4), "오류": 오.get(f, ""), "글": g})
    for n, 정 in 정렌.items():
        if n in {r["부품"] for r in 줄} and 정 is not None: Image.fromarray(np.asarray(정[0])).resize((200, 200)).save(폴더 + f"검증/정답_{n}.png")
    json.dump(줄, open(폴더 + "검증.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt; plt.rcParams["font.family"] = "Malgun Gothic"
    부 = [x[0] for x in 검]; 스 = sorted({r["스텝"] for r in 줄}); fig, ax = plt.subplots(len(스) + 1, len(부), figsize=(3 * len(부), 3 * (len(스) + 1))); ax = np.atleast_2d(ax)
    fig.suptitle("스텝별 검증 — 같은 시험 부품 넷에 모델이 쓴 코드를 실행한 모양", fontsize=15, weight="bold")
    for c, n in enumerate(부):
        p = 폴더 + f"검증/정답_{n}.png"; ax[0, c].imshow(Image.open(p) if os.path.exists(p) else np.ones((8, 8))); ax[0, c].set_title(f"정답 {n}", fontsize=12)
        for k, st in enumerate(스):
            r = next((r for r in 줄 if r["스텝"] == st and r["부품"] == n), None); p = 폴더 + f"검증/{st:05d}_{n}.png"
            ax[k + 1, c].imshow(Image.open(p) if os.path.exists(p) else np.full((8, 8, 3), [1, .9, .9])); ax[k + 1, c].set_title(f"스텝 {st} · " + (f"IoU {r['IoU']:.2f}" if r and r["실행"] else (r["오류"].split(":")[0] if r else "없음")), fontsize=10)
    for a in ax.flat: a.axis("off")
    fig.savefig(폴더 + "검증.png", dpi=50, bbox_inches="tight"); plt.close(fig)
def 그림(폴더, 시, 글들, 렌, 줄, 입력):   # 시험 부품 넷: 입력 · 정답 렌더 · 생성 렌더 · IoU
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt; from PIL import Image
    plt.rcParams["font.family"] = "Malgun Gothic"; k = len(글들); 보 = [i for i, x in enumerate(시) if x[0] == "12050"] + list(range(min(3, k)))
    보 = list(dict.fromkeys(보))[:4]; fig, ax = plt.subplots(len(보), 3, figsize=(15, 5.2 * len(보))); ax = np.atleast_2d(ax)
    fig.suptitle(f"코드 생성({'선 토큰 → 언어 모델' if 입력 == '선글' else '도면 → ViT → 언어 모델'}) — 입력 · 정답 · 생성 코드를 실행한 모양", fontsize=17, weight="bold")
    for r, i in enumerate(보):
        n = 시[i][0]; 정, 예 = 렌[k + i], 렌[i]
        ax[r, 0].imshow(도면그림(n)); ax[r, 0].set_title(f"입력 {n}", fontsize=14)
        ax[r, 1].imshow(정[0] if 정 is not None else np.ones((8, 8))); ax[r, 1].set_title("정답", fontsize=14)
        ax[r, 2].imshow(예[0] if 예 is not None else np.full((8, 8, 3), [1, .9, .9])); ax[r, 2].set_title(f"생성 · IoU {줄[i]['IoU']:.2f}" if 예 is not None else "생성 코드 실행 실패", fontsize=14)
        for a in ax[r]: a.axis("off")
    fig.savefig(폴더 + "시트.png", dpi=60, bbox_inches="tight"); plt.close(fig)
    i = 보[0]; n = 시[i][0]
    if 렌[k + i] is not None: Image.fromarray(np.asarray(렌[k + i][0])).save(폴더 + "정답.png")
    if 렌[i] is not None: Image.fromarray(np.asarray(렌[i][0])).save(폴더 + "예측전체.png")
    도면그림(n).save(폴더 + "도면_앞.png")
if __name__ == "__main__":   # 자체 시험(가벼움): 줄글 꼴 · 도면그림 크기
    print(줄글([{"_m": np.ones((2, 2), bool), "시작": [1, 2], "끝": [3, 4], "종류": "원호", "중간": [2, 5], "숨음": True}], 1))
    assert 줄글([{"_m": np.ones((2, 2), bool), "시작": [1, 2], "끝": [3, 4], "종류": "직선", "중간": [2, 3], "숨음": False}], 0) == ["T L 1 2 3 4"]
    print("과제코드 시험 통과")
