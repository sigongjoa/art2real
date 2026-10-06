# -*- coding: utf-8 -*-
"""Zero-To-CAD 생성: 입력 jsonl(이름 · 그림 8 장 경로) → 출력 jsonl(이름 · 코드들). python s/gen.py <입력.jsonl> <출력.jsonl> [표집 수=1]"""
import sys, json, os, torch
from PIL import Image
from transformers import Qwen3VLForConditionalGeneration, AutoProcessor
W = "weights/zerotocad"; IN, OUT = sys.argv[1], sys.argv[2]; K = int(sys.argv[3]) if len(sys.argv) > 3 else 1
model = Qwen3VLForConditionalGeneration.from_pretrained(W, torch_dtype=torch.bfloat16, device_map="cuda"); proc = AutoProcessor.from_pretrained(W)
SYS = "You are a CAD code assistant. Given multiple rendered views of a 3D shape, generate clean, well-structured CadQuery Python code that accurately reproduces the geometry."
done = {json.loads(l)["이름"] for l in open(OUT, encoding="utf-8")} if os.path.exists(OUT) else set()
for line in open(IN, encoding="utf-8"):
    it = json.loads(line)
    if it["이름"] in done: continue
    views = [Image.open(p).convert("RGB") for p in it["그림"]]
    msgs = [{"role": "system", "content": SYS}, {"role": "user", "content": [*[{"type": "image", "image": v} for v in views], {"type": "text", "text": "Generate CadQuery code for this shape."}]}]
    text = proc.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True)
    inp = proc(text=[text] * K, images=views * K, return_tensors="pt").to("cuda")
    with torch.no_grad():
        out = model.generate(**inp, max_new_tokens=2048, do_sample=K > 1, temperature=1.0, top_p=0.95)
    codes = proc.batch_decode(out[:, inp.input_ids.shape[1]:], skip_special_tokens=True)
    open(OUT, "a", encoding="utf-8").write(json.dumps({"이름": it["이름"], "코드": codes}, ensure_ascii=False) + "\n")
    print(it["이름"][:50], "GPU %.1f" % (torch.cuda.max_memory_allocated() / 1e9), flush=True)
