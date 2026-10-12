# 한 줄을 받아쓰기 일치율 ≥ 0.85 될 때까지 다시 굽기(최대 8 번) · 사용: 줄다시.py 누구 "말" 출력.wav
import sys, os, re, difflib, subprocess, torchaudio
from chatterbox.mtl_tts import ChatterboxMultilingualTTS
from faster_whisper import WhisperModel
누구, 말, 출력 = sys.argv[1:4]; m = ChatterboxMultilingualTTS.from_pretrained(device="cuda"); W = WhisperModel("small", device="cuda", compute_type="float16")
참고 = "G:/art2real/out/tts/참고_나.wav" if 누구 == "나" else "G:/art2real/out/tts/참고_AI.wav"; 깨끗 = lambda t: re.sub(r"[^가-힣0-9a-zA-Z]", "", t); 최고 = (-1, None)   # 둘 다 늘 참고(참고 없이 굽으면 직전 목소리가 남음)
for k in range(8):
    w = m.generate(말, language_id="ko", audio_prompt_path=참고); p = 출력 + ".raw.wav"; torchaudio.save(p, w, m.sr)
    q = 출력 + ".%d.wav" % k; subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", p, "-af", "areverse,silenceremove=start_periods=1:start_threshold=-45dB,areverse", "-ac", "1", "-ar", "24000", q], check=True); os.remove(p)
    t = "".join(s.text for s in W.transcribe(q, language="ko", beam_size=5)[0]); a = difflib.SequenceMatcher(None, 깨끗(말), 깨끗(t)).ratio()
    import numpy as np; ww, sr = torchaudio.load(q); f = torchaudio.functional.detect_pitch_frequency(ww[:1], sr).numpy().ravel(); hz = float(np.median(f[(f > 70) & (f < 400)]))
    if (누구 == "나" and hz > 170) or (누구 == "AI" and hz < 170): a -= 1   # 목소리가 바뀌면 탈락
    print(k, round(a, 2), round(hz), t.strip()[:30], flush=True)
    if a > 최고[0]:
        if 최고[1]: os.remove(최고[1])
        최고 = (a, q)
    else: os.remove(q)
    if a >= .85: break
os.replace(최고[1], 출력); print("고름", round(최고[0], 2))
