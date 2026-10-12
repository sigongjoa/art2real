# 대화쇼츠 TTS=chatterbox 용 — 일감 json [{"말", "누구", "출력"}] 을 한 번에 굽는다 · 나 = 기본 목소리(남 131 Hz) · AI = 참고_AI.wav(SunHi 한 줄) 따라함 · 로컬 GPU · 10-12 사용자 고름
import sys, json, os, torchaudio
from chatterbox.mtl_tts import ChatterboxMultilingualTTS
일 = json.load(open(sys.argv[1], encoding="utf-8")); m = ChatterboxMultilingualTTS.from_pretrained(device="cuda"); 참고 = {"나": "G:/art2real/out/tts/참고_나.wav", "AI": "G:/art2real/out/tts/참고_AI.wav"}   # 10-12: 참고 없이 굽으면 직전 참고 목소리가 남음(나가 AI 목소리로 나옴) → 둘 다 늘 참고
for j in 일:
    w = m.generate(j["말"], language_id="ko", audio_prompt_path=참고[j["누구"]])
    torchaudio.save(j["출력"], w, m.sr); print("ok", j["출력"][-20:], flush=True)
