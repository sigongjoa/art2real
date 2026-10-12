# 대화 쇼츠 목소리 검사 — 줄마다 로컬 받아쓰기(faster-whisper small) 해서 대본과 글자 일치율 · < 0.75 이면 ⚠ · 사용: 받아쓰기.py <편>
import sys, csv, hashlib, difflib, re, torchaudio, numpy as np
from faster_whisper import WhisperModel
편 = sys.argv[1]; D = "G:/art2real/out/영상05/대화/" + 편; S = "G:/art2real/원화3d/과정/영상05/대화/%s/대본.tsv" % 편
rows = [r for r in csv.reader(open(S, encoding="utf-8"), delimiter="\t") if r and not r[0].startswith("#")][1:]
m = WhisperModel("small", device="cuda", compute_type="float16"); 깨끗 = lambda t: re.sub(r"[^가-힣0-9a-zA-Z]", "", t); 나쁨 = 0
for r in rows:
    p = D + "/_tts_%s.wav" % hashlib.md5(("cb" + r[0] + r[5]).encode()).hexdigest()[:10]
    t = "".join(s.text for s in m.transcribe(p, language="ko", beam_size=5)[0]); a = difflib.SequenceMatcher(None, 깨끗(r[5]), 깨끗(t)).ratio()
    w, sr = torchaudio.load(p); f = torchaudio.functional.detect_pitch_frequency(w[:1], sr).numpy().ravel(); hz = float(np.median(f[(f > 70) & (f < 400)]))
    틀목 = (r[0] == "나" and hz > 170) or (r[0] == "AI" and hz < 170)   # 나 ≈ 130 Hz · AI ≈ 210 Hz
    print("%s %.2f %4.0fHz %-3s %s ← %s" % ("⚠" if a < .75 or 틀목 else " ", a, hz, r[0], r[5][:22], t.strip()[:30]), flush=True); 나쁨 += a < .75 or 틀목
print("나쁨", 나쁨)
