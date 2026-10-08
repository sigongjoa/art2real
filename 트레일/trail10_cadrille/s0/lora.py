# -*- coding: utf-8 -*-
"""cadrille LoRA 학습 + 학습 과정 시각화(필수 · 10-05 사용자) (2026-10-05)
python s0/lora.py <학습 폴더> <시험 폴더> <출력 폴더> [스텝=300] [그림 간격=25] [rank=16]
  폴더 = NNNN.py(정답 레시피 · CAD-Recode 좌표 ±100) + NNNN.png(회색 4 장 2×2 · 없으면 만들어 둠)
  그림 간격마다: 시험 부품들에 대해 지금 모델이 쓴 레시피 → 실행 → 렌더 → 정답과 나란히 · 새 연산(chamfer · cut) 표시 · 손실 곡선 → 프레임 PNG
  끝나면 프레임 → 학습과정.mp4 · 기록.json(스텝 · 손실 · 최대 GPU · 초)"""
import os, sys, glob, json, time, math, random, subprocess, numpy as np, torch, trimesh
from PIL import Image, ImageDraw, ImageFont, ImageOps
H = os.path.dirname(os.path.abspath(__file__)); sys.path[:0] = [os.path.dirname(H), os.path.join(H, "stub"), H]
from transformers import AutoProcessor
from peft import LoraConfig, get_peft_model
from cadrille import Cadrille, collate
import s0 as S
from render import render
W = os.path.join(os.path.dirname(H), "weights"); F = lambda n: ImageFont.truetype("C:/Windows/Fonts/malgunbd.ttf", n); M = lambda n: ImageFont.truetype("C:/Windows/Fonts/consola.ttf", n)

def 실행(code):  # 레시피 → 단위 상자 메시(학습 규약: 코드/200 + 0.5)
    m = S.run_code(code); m.apply_scale(1 / 200.0); m.apply_translation([0.5] * 3); return m

def 그림4(code):
    m = 실행(code); it, g = S.item_img_raw(m) if hasattr(S, "item_img_raw") else S.item_img(m); return g

def 읽기(d):
    out = []
    for p in sorted(glob.glob(os.path.join(d, "*.py"))):
        g = p[:-3] + ".png"; code = open(p, encoding="utf-8").read()
        g = p[:-3] + ("_%s%s.png" % (os.environ.get("IMGSZ", "128"), "s" if os.environ.get("SHADE") == "1" else "")) if (os.environ.get("IMGSZ") or os.environ.get("SHADE")) else g
        if not os.path.exists(g): 그림4(code).save(g)
        out.append({"code": code, "img": Image.open(g).convert("RGB"), "name": os.path.basename(p)[:-3]})
    return out

def 새연산(code): return ("chamfer" in code, ".cut(" in code)

if __name__ == "__main__":
    tr_dir, te_dir, O = sys.argv[1:4]; STEPS = int(sys.argv[4]) if len(sys.argv) > 4 else 300; EVERY = int(sys.argv[5]) if len(sys.argv) > 5 else 25; RANK = int(sys.argv[6]) if len(sys.argv) > 6 else 16
    os.makedirs(os.path.join(O, "프레임"), exist_ok=True)
    tr, te = 읽기(tr_dir), 읽기(te_dir)[:4]
    model = Cadrille.from_pretrained(os.path.join(W, "cadrille"), torch_dtype=torch.bfloat16, attn_implementation="sdpa", device_map="cuda")
    proc = AutoProcessor.from_pretrained(os.path.join(W, "qwen2vl2b"), min_pixels=256 * 28 * 28, max_pixels=1280 * 28 * 28, padding_side="left")
    model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={"use_reentrant": False}); model.enable_input_require_grads()
    model = get_peft_model(model, LoraConfig(r=RANK, lora_alpha=2 * RANK, lora_dropout=0.05, target_modules=["q_proj", "k_proj", "v_proj", "o_proj"] + (["qkv", "attn.proj"] if os.environ.get("VISLORA") == "1" else []) + (["gate_proj", "up_proj", "down_proj"] if os.environ.get("MLP") == "1" else [])))   # run2: 비전 인코더 어텐션에도 LoRA(작은 디테일은 비전 쪽이 바뀌어야 — 조사 10-06)
    n_tr = sum(p.numel() for p in model.parameters() if p.requires_grad); print("학습 매개변수", n_tr)
    opt = torch.optim.AdamW([p for p in model.parameters() if p.requires_grad], lr=float(os.environ.get("LR", "1e-4")), weight_decay=0.0)
    sched = torch.optim.lr_scheduler.LambdaLR(opt, lambda s: min(1.0, (s + 1) / 20) * 0.5 * (1 + math.cos(math.pi * min(s, STEPS) / STEPS)))
    정답그림 = {t["name"]: render(*(lambda m: (np.asarray(m.vertices), np.asarray(m.faces)))(실행(t["code"])), [0.35, -0.5, -1], img_size=220) for t in te}
    기록 = {"스텝": [], "손실": [], "시험": [], "최대GPU": 0, "초당스텝": None}

    def 생성(t):
        it = {"video": [t["img"]], "description": "Generate cadquery code", "file_name": t["name"]}
        b = collate([it], processor=proc, n_points=256, eval=True)
        model.eval()
        with torch.no_grad():
            out = model.generate(input_ids=b["input_ids"].cuda(), attention_mask=b["attention_mask"].cuda(), point_clouds=b["point_clouds"].cuda(), is_pc=b["is_pc"].cuda(), is_img=b["is_img"].cuda(),
                                 pixel_values_videos=b["pixel_values_videos"].cuda(), video_grid_thw=b["video_grid_thw"].cuda(), max_new_tokens=768, do_sample=False, use_cache=True)
        model.train(); return proc.batch_decode([out[0][len(b["input_ids"][0]):]], skip_special_tokens=True)[0]

    def 프레임(step):
        cells, 요약 = [], {"ok": 0, "새연산": 0}
        for t in te:
            code = 생성(t); ch, cu = 새연산(code)
            try: m = 실행(code); im = render(np.asarray(m.vertices), np.asarray(m.faces), [0.35, -0.5, -1], img_size=220); ok = True
            except Exception: im = Image.new("RGB", (220, 220), (255, 235, 235)); ok = False
            요약["ok"] += ok; 요약["새연산"] += (ch and cu); cells.append((t["name"], im, ok, ch, cu))
        c = Image.new("RGB", (1500, 820), "white"); d = ImageDraw.Draw(c)
        d.text((20, 10), f"학습 스텝 {step} / {STEPS}", font=F(44), fill=(20, 40, 90))
        d.text((640, 22), f"실행 {요약['ok']}/{len(te)} · 모따기+홈 {요약['새연산']}/{len(te)}", font=F(32), fill=(160, 40, 50))
        for i, (n, im, ok, ch, cu) in enumerate(cells):
            x = 20 + i * 370; d.text((x, 80), "정답", font=F(24), fill=(30, 140, 70)); c.paste(정답그림[n], (x, 110))
            d.text((x, 340), "지금 모델", font=F(24), fill=(160, 40, 50)); c.paste(im, (x, 370))
            d.text((x, 595), ("실행 O" if ok else "실행 X") + ("  모따기 O" if ch else "  모따기 X") + ("  홈 O" if cu else "  홈 X"), font=F(22), fill=(40, 40, 40))
        # 손실 곡선
        x0, y0, w, h = 40, 640, 1420, 160; d.rectangle((x0, y0, x0 + w, y0 + h), outline=(180, 180, 190))
        L = 기록["손실"]
        if len(L) > 1:
            mx, mn = max(L), min(L); pts = [(x0 + w * s / STEPS, y0 + 30 + (h - 40) * (mx - l) / max(mx - mn, 1e-6)) for s, l in zip(기록["스텝"], L)]
            d.line(pts, fill=(31, 78, 140), width=3)
        d.text((x0 + 8, y0 + 4), "손실(정답 레시피와 다른 정도)", font=F(20), fill=(31, 78, 140))
        c.save(os.path.join(O, "프레임", "%05d.png" % step)); 기록["시험"].append({"스텝": step, **요약})
        try: trackio.log({"시험_실행": 요약["ok"], "시험_모따기홈": 요약["새연산"]}, step=step)
        except Exception: pass
        print("그림", step, 요약, flush=True)

    import trackio   # 스킬 huggingface-trackio — 로컬 대시보드(trackio show)
    trackio.init(project="art2real-cadrille", name=os.path.basename(O.rstrip("/\\")), config={"IMGSZ": os.environ.get("IMGSZ", "128"), "VISLORA": os.environ.get("VISLORA", "0"), "RANK": RANK, "STEPS": STEPS})
    model.train(); t0 = time.time(); 프레임(0)
    for step in range(1, STEPS + 1):
        t = random.choice(tr)
        b = collate([{"video": [t["img"]], "description": "Generate cadquery code", "answer": t["code"]}], processor=proc, n_points=256, eval=False)
        b = {k: (v.cuda() if torch.is_tensor(v) else v) for k, v in b.items()}
        loss = model(**b).loss; loss.backward()
        if step % 4 == 0 or step == STEPS: torch.nn.utils.clip_grad_norm_([p for p in model.parameters() if p.requires_grad], 1.0); opt.step(); sched.step(); opt.zero_grad()
        trackio.log({"손실": float(loss)}, step=step); 기록["스텝"].append(step); 기록["손실"].append(float(loss)); 기록["최대GPU"] = round(torch.cuda.max_memory_allocated() / 1e9, 2)
        if step % 10 == 0: print("스텝", step, "손실", round(float(loss), 4), "GPU", 기록["최대GPU"], "초/스텝", round((time.time() - t0) / step, 2), flush=True)
        if step % EVERY == 0 or step == STEPS: 프레임(step)
    기록["초당스텝"] = round((time.time() - t0) / STEPS, 2); trackio.finish()
    model.save_pretrained(os.path.join(O, "lora")); json.dump(기록, open(os.path.join(O, "기록.json"), "w", encoding="utf-8"), ensure_ascii=False)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", "2", "-pattern_type", "sequence", "-i", os.path.join(O, "프레임", "%05d.png"), "-vf", "scale=1500:820", "-pix_fmt", "yuv420p", os.path.join(O, "학습과정.mp4")])
