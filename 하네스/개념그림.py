# 개념 그림 — 판의 모델 구조 · 논문 방법을 /anatomy 로 그린 움직이는 그림(mp4 · gif) · 하네스/개념그림/<이름>/ · 10-23 사용자 「개념 설명할 때 GIF 가 필수로 포함」
# 구조 키(설정에서) → 그림 이름 · 관문은 그림 없는 구조를 막음 · 기록 단계가 판 폴더에 개념.mp4 · 개념.gif 로 넣음 · 보고서 「모델 구조」 칸 맨 위에 재생
import os, shutil
뿌리 = "G:/art2real"; 폴더 = f"{뿌리}/하네스/개념그림/"
구조표 = {   # 구조 키 → 그림 이름(하네스/개념그림/<이름>/<이름>.mp4)
    "선지도/cnn/합침=전부": "ours137",
    "선지도/cnn/합침=전부/다중": "ours139",   # 139 다중 라벨 머리
}
논문표 = {"L-CNN": "lcnn", "PPGNet": "ppgnet", "PICASSO": "picasso", "GAT-CADNet": "gatcadnet"}   # 분석 글이 이 방법을 말하면 그림을 붙임
def 키(cfg):
    if cfg.get("목표", "CAD") != "선지도": return None   # CAD 과제(127 계열)는 아직 그림 없음 — 관문 대상 아님
    s = cfg.get('선지도', {}); return f"선지도/{cfg.인코더}/합침={s.get('합침', '없음')}" + ("/다중" if s.get("다중") else "")
def 찾기(cfg):
    k = 키(cfg); n = 구조표.get(k) if k else None
    return (n, f"{폴더}{n}/{n}.mp4") if n and os.path.exists(f"{폴더}{n}/{n}.mp4") else (None, None)
def 넣기(cfg, 판폴더):   # 판 폴더에 개념.mp4 · 개념.gif · 개념.txt(그림 이름)
    n, mp4 = 찾기(cfg)
    if not n: return None
    shutil.copy(mp4, 판폴더 + "개념.mp4")
    if os.path.exists(f"{폴더}{n}/{n}.gif"): shutil.copy(f"{폴더}{n}/{n}.gif", 판폴더 + "개념.gif")
    open(판폴더 + "개념.txt", "w", encoding="utf-8").write(n); return n
if __name__ == "__main__":   # 자체 시험
    from omegaconf import OmegaConf
    c = OmegaConf.create({"목표": "선지도", "인코더": "cnn", "선지도": {"합침": "전부"}}); assert 찾기(c)[0] == "ours137", 찾기(c)
    c2 = OmegaConf.create({"목표": "선지도", "인코더": "cnn", "선지도": {"합침": "블록1"}}); assert 찾기(c2)[0] is None
    assert 키(OmegaConf.create({"목표": "CAD", "인코더": "cnn"})) is None
    print("개념그림 시험 통과")
