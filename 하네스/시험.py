# 하네스 자체 시험 — 10-22 코드 리뷰가 찾은 구멍이 다시 열리지 않는지 · 학습 없음 · 1 분 안 · 사용: python 하네스/시험.py
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from omegaconf import OmegaConf
import 하네스 as H, 쇼츠 as S
def 설정(**덧):
    c = OmegaConf.merge(OmegaConf.load(H.뿌리 + "/하네스/conf/바탕.yaml"), OmegaConf.load(H.뿌리 + "/하네스/conf/판_127재현.yaml")); c.pop("defaults", None); c.pop("hydra", None)
    for k, v in 덧.items(): OmegaConf.update(c, k, v)
    return c
def 거부말(c, 덮=()):
    try: H.관문(c, "하네스/conf/판_127재현.yaml", 덮); return ""
    except H.관문거부 as e: return str(e)
if __name__ == "__main__":
    # 쇼츠: 「해당 없음」 이 앞에 붙은 답은 막힌 곳이 있는 것
    assert not S.막힘없음("적용 규칙: 해당 없음\n1. 「모델」 이 뭔지 모른다\n2. 숫자 기준이 없다"), "앞 20 자 「없음」에 속음"
    assert S.막힘없음("적용 규칙: 해당 없음\n없음") and S.막힘없음("「없음」.")
    # 관문: 잘못된 기준 식 · 점검에 없는 지표 · 명령줄 덮어쓰기 · 괄호 든 시도
    assert "기준 식" in 거부말(설정(**{"기준": [{"지표": "시험loss", "식": "=>", "값": 1}]}))
    assert "점검 「평가」" in 거부말(설정(**{"기준": [{"지표": "시험IoU", "식": ">=", "값": .7}]}))
    assert "명령줄 덮어쓰기" in 거부말(설정(), ("학습.학습률=1e-3",))
    assert "시도는" in 거부말(설정(**{"판.시도": "그림을 키우면 0.75 를 넘는다(블록 4)"}))
    # 관문: 개념 그림 없는 구조(선지도 · 합침 블록1)는 거부 · 그림 있는 구조(합침 전부)는 이 이유로는 안 막음
    선 = lambda 합: 설정(**{"목표": "선지도", "선지도.합침": 합})
    assert "개념 그림이 없다" in 거부말(선("블록1")) and "개념 그림이 없다" not in 거부말(선("전부"))
    # 이어 하기 열쇠: 설정이 바뀌면 달라지고 판 문장만 바뀌면 그대로
    a = H.열쇠(설정(), "abc"); assert a != H.열쇠(설정(**{"학습.학습률": 1e-3}), "abc") and a != H.열쇠(설정(), "def") and a == H.열쇠(설정(**{"판.물음": "다른 말"}), "abc")
    print("하네스 시험 통과 — 쇼츠 읽기 판정 · 관문 4 가지 · 이어 하기 열쇠")
