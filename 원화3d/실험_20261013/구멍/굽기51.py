# 쇼츠 51 — 학습 스냅(학습/스냅.json) → CadQuery STL · 겹침 · 그림 → 블렌더 EEVEE → 템플릿 프레임 → Chatterbox 목소리 → mp4 · 10-13
# venv python 굽기51.py   (학습.py 가 끝난 뒤 한 번에) → out/설명/구멍/학습/51_구멍학습.mp4 · 프레임 png 는 학습/프레임/
import os, sys, json, subprocess, hashlib, wave, numpy as np
from PIL import Image, ImageDraw
H_ = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, H_)
import 캐드점수 as K
A = "G:/art2real/out/설명/구멍/"; L = A + "학습/"; FR = L + "프레임/"; os.makedirs(FR, exist_ok=True)
BL = "C:/Program Files/Blender Foundation/Blender 4.0/blender.exe"; CB = "G:/art2real/out/tts/chatterbox/Scripts/python.exe"; CBS = "G:/art2real/원화3d/과정/영상05/tts/굽기_chatterbox.py"
CH = "G:/art2real/out/영상05/캐릭터시안/누끼/"; 인물 = {"나": CH + "표정_2_후드개발자_말.png", "AI": CH + "표정_6_안드로이드_말.png"}
W_ = 1   # 지켜볼 그림 넷 중 화면 주인공(구멍이 커서 변화가 잘 보임 · 넷 모두 끝 판에서 보임)
S = json.load(open(L + "스냅.json", encoding="utf-8")); 정 = S["정답"][W_]; 스 = S["스냅"]

# 대사: (누구, 말, 스냅 처음, 스냅 끝) — 스냅 번호는 0 · 25 · 50 … 걸음 순
대사 = [("나", "AI한테 구멍 맞추기를 진짜로 시켜 봤어.", 0, 0),
        ("AI", "처음엔 어떤 그림이 와도 똑같은 구멍을 뚫었어요.", 0, 3),
        ("나", "그림을 안 본 거네?", 3, 3),
        ("AI", "네. 백 걸음쯤부터 그림을 보기 시작했어요.", 4, 5),
        ("나", "오, 구멍이 옆으로 가네.", 5, 7),
        ("AI", "지어 보고 겹쳐 보고, 점수 좋은 쪽으로 계속 고쳤거든요.", 7, 11),
        ("나", "지금은 몇 점이야?", 11, 13),
        ("AI", "처음 보는 그림 백 장에서 영점 구육팔이요. 처음엔 영점 팔사였고요.", 13, 16),
        ("AI", "정육면체가 커서 점수가 원래 후해요. 그래도 그림을 안 보는 답은 영점 팔사에서 못 올라가요.", 16, 16),
        ("나", "다음은 진짜 로봇 부품이지?", 16, 16),
        ("AI", "네, 그걸로 해 볼게요.", 16, 16)]

def 재료():
    import cadquery as cq
    a, m = K.그림(*정); big = Image.new("RGB", (512, 512), (250, 248, 240)); d = ImageDraw.Draw(big); p = lambda v: (v + 12) / 24 * 512
    d.rectangle((p(-10), p(-10), p(10), p(10)), outline=(30, 30, 35), width=5); r, x, y = 정; d.ellipse((p(x - r), p(-y - r), p(x + r), p(-y + r)), outline=(30, 30, 35), width=5); big.save(L + "그림_w%d.png" % W_)
    for s in 스:
        w = s["지켜볼"][W_]; 이름 = "학습_s%03d" % s["걸음"]
        cq.exporters.export(K.짓기(w["r"], w["x"], w["y"]), A + "r%s.stl" % 이름, tolerance=0.01, angularTolerance=0.05)
        c = K.윗면(K.짓기(w["r"], w["x"], w["y"])); z = Image.new("RGB", (128, 128), (250, 248, 240)); z.paste((90, 140, 240), (0, 0), Image.fromarray((c * 170).astype(np.uint8)))
        z = z.resize((512, 512), Image.NEAREST); ImageDraw.Draw(z).ellipse((p(x - r), p(-y - r), p(x + r), p(-y + r)), outline=(220, 40, 40), width=4); ImageDraw.Draw(z).rectangle((p(-10), p(-10), p(10), p(10)), outline=(220, 40, 40), width=4)
        z.save(A + "겹침_%s.png" % 이름)
    subprocess.run([BL, "-b", "-P", os.path.join(H_, "렌더_빛.py"), "--"] + ["학습_s%03d" % s["걸음"] for s in 스], check=True, stdout=subprocess.DEVNULL)

def 판정(w):
    r, x, y = 정
    if w["IoU"] >= .96: return "맞음", True   # 화면 표시용(판정기준과 무관)
    if abs(w["r"] - r) > .5: return ("작다" if w["r"] < r else "크다"), False
    if math.hypot(w["x"] - x, w["y"] - y) > .7: return "옆으로 샘", False
    return "거의", False

def 템플릿():
    T = json.load(open(os.path.join(H_, "템플릿.json"), encoding="utf-8")); T["제목"]["나머지"] = "가 구멍을 배우는 중"; T["시간축"]["보일칸"] = 7
    T["에폭"] = [dict(형태="학습_s%03d" % s["걸음"], 이름="걸음 %d" % s["걸음"], 눈금="%d" % s["걸음"], 그림=L + "그림_w%d.png" % W_, 판정=판정(s["지켜볼"][W_])[0], 맞음=판정(s["지켜볼"][W_])[1]) for s in 스]
    T["형태"]["겹침"] = "겹침_%s.png"; json.dump(T, open(L + "템플릿_51.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)

def 목소리():
    일, 파일 = [], []
    for 누구, 말, _, _ in 대사:
        k = hashlib.md5((누구 + 말).encode()).hexdigest()[:10]; f = L + "_tts_%s.wav" % k; 파일.append(f)
        if not os.path.exists(f): 일.append({"말": 말, "누구": 누구, "출력": f + ".raw.wav"})
    if 일:
        json.dump(일, open(L + "_cb일감.json", "w", encoding="utf-8"), ensure_ascii=False); subprocess.run([CB, CBS, L + "_cb일감.json"], check=True)
        for j in 일: subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", j["출력"], "-af", "areverse,silenceremove=start_periods=1:start_threshold=-45dB,areverse", "-ac", "1", "-ar", "24000", j["출력"][:-8]], check=True); os.remove(j["출력"])
    return 파일

def 영상(파일):
    os.environ["TEMPLATE"] = L + "템플릿_51.json"; import 프레임디자인 as P
    FPS, GAP = 24, .35; 소리 = []; 순 = []
    for (누구, 말, a, b), f in zip(대사, 파일):
        with wave.open(f) as w: x = np.frombuffer(w.readframes(w.getnframes()), np.int16)
        n = int(np.ceil((len(x) / 24000 + GAP) * FPS)); 소리.append(np.concatenate([x, np.zeros(int(n / FPS * 24000) - len(x), np.int16)]))
        for i in range(n): 순.append((누구, 말, a + int((b - a + 1) * i / n) if b > a else a))
    with wave.open(L + "_목소리.wav", "wb") as w: w.setnchannels(1); w.setsampwidth(2); w.setframerate(24000); w.writeframes(np.concatenate(소리).tobytes())
    캐시 = {}
    for i, (누구, 말, k) in enumerate(순):
        if (누구, 말, k) not in 캐시:
            P.T["대사"]["예시말"] = 말; P.T["대사"]["인물"] = 인물[누구]; p = FR + "f_%03d_%s.png" % (k, hashlib.md5(말.encode()).hexdigest()[:6]); P.프레임(k + 1).save(p); 캐시[(누구, 말, k)] = p
    with open(L + "_목록.txt", "w", encoding="utf-8") as f:
        for t in 순: f.write("file '%s'\nduration %.5f\n" % (캐시[t], 1 / FPS))
    out = L + "51_구멍학습.mp4"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", L + "_목록.txt", "-i", L + "_목소리.wav", "-r", str(FPS), "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", "-c:a", "aac", "-b:a", "192k", "-shortest", out], check=True)
    print(out, round(len(순) / FPS, 1), "초 · 프레임 그림", len(캐시))

if __name__ == "__main__":
    import math
    if "재료" in sys.argv or not os.path.exists(A + "빛_r학습_s%03d.png" % 스[-1]["걸음"]): 재료()
    템플릿(); 영상(목소리())
