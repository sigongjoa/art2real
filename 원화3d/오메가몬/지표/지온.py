# -*- coding: utf-8 -*-
"""부품 그래프 데이터 타입 (10-02 「수치에서 추상화된 영역으로」 · claudedocs/research_아모달_지온_20261002.md).
컷 사이엔 추상(지온 · 관계 · 덮음)만 옮기고, 수치는 부품마다 주 뷰 관찰 하나에서만.

  관찰  = 한 컷이 말한 것(칸 번호 · 지온 읽기 · 자기 틀 치수). 컷끼리 달라도 그대로 쌓는다.
  부품  = 우리가 정한 것(이름 · 쪽 · 층 · 지온 · 주 뷰). 사람이 고친다.
  붙음  = 자식이 부모 표면에 고정(지온 관계 종류 · 조인트). 부품마다 부모 하나 → 나무.
  덮음  = 한 컷에서 앞이 뒤를 가림. 컷마다 따로(앞뒤는 컷 사이에 옮기지 않는다).
  그래프.검사() = 나무인가 · 같은 이름 관찰끼리 지온이 같은가 · 좌우 짝 지온이 같은가 → 경보 목록.
3D 는 여기 없다 — 블렌더 쪽이 이 파일(json)을 읽어 짓는다."""
from dataclasses import dataclass, field, asdict
from enum import Enum
import json


class 단면(str, Enum): 각 = "각"; 둥 = "둥"
class 축(str, Enum): 곧 = "곧"; 휨 = "휨"
class 크기(str, Enum): 일정 = "일정"; 좁아짐 = "좁아짐"; 불룩 = "불룩"; 잘록 = "잘록"
class 끝(str, Enum): 잘림 = "잘림"; 뾰족 = "뾰족"; 둥긂 = "둥긂"
class 관계(str, Enum):
    끝끝 = "끝-끝"          # 포갠 판 사슬(미늘)
    끝가운데 = "끝-가운데"   # 꽂힘(뿔 → 이마판)
    위얹힘 = "위에-얹힘"     # 덮어 붙음(차양 → 투구 돔)
    안 = "안에-듦"           # 박힘(눈 → 눈구멍)


@dataclass(frozen=True)
class 지온:
    단면: 단면; 축: 축; 크기: 크기; 끝: 끝
    def __str__(self): return f"{self.단면.value}/{self.축.value}/{self.크기.value}/{self.끝.value}"


@dataclass
class 관찰:
    컷: str                        # "정면" · "옆" · "3/4"
    칸: list                       # 그 컷의 선파츠 칸 번호
    지온: "지온 | None" = None      # 그 컷에서 읽은 지온(못 읽으면 None)
    치수: dict = field(default_factory=dict)   # 자기 틀(머리 단위) 폭 · 높이 등 — 주 뷰일 때만 쓴다
    근거: str = ""


@dataclass
class 부품:
    이름: str                      # "차양"
    쪽: str = "가운데"              # 왼 · 가운데 · 오른
    층: int = 2                    # 0 코어 · 1 큰 판 · 2 장식
    지온: "지온 | None" = None      # 정한 지온(사람 확인 전엔 관찰에서 초안)
    주뷰: str = "정면"
    관찰들: list = field(default_factory=list)
    부피: dict = field(default_factory=dict)    # 10-02: 앞면 깊이 · 두께 · 돌출(머리 단위) — TripoSG ∩ 칸 기둥에서
    @property
    def 키(self): return f"{self.이름}/{self.쪽}"
    def 치수(self):
        """수치는 주 뷰 관찰에서만."""
        return next((o.치수 for o in self.관찰들 if o.컷 == self.주뷰), {})


@dataclass
class 붙음:
    자식: str; 부모: str; 관계: 관계; 조인트: str = "고정"; 근거: str = ""

@dataclass
class 덮음:
    컷: str; 앞: str; 뒤: str; 점수: float = 0.0


@dataclass
class 그래프:
    부품들: dict = field(default_factory=dict)   # 키 → 부품
    붙음들: list = field(default_factory=list)
    덮음들: list = field(default_factory=list)

    def 더하기(self, p: 부품): self.부품들[p.키] = p; return p

    def 검사(self):
        경보 = []
        부모 = {}
        for e in self.붙음들:
            if e.자식 in 부모: 경보.append(f"부모 둘: {e.자식} ← {부모[e.자식]} · {e.부모}")
            부모[e.자식] = e.부모
        for k, p in self.부품들.items():
            if p.층 > 0 and k not in 부모: 경보.append(f"떠 있음(부모 없음): {k}")
            seen, cur = set(), k                 # 고리 검사
            while cur in 부모:
                if cur in seen: 경보.append(f"고리: {k}"); break
                seen.add(cur); cur = 부모[cur]
            읽힘 = {str(o.지온) for o in p.관찰들 if o.지온}
            if len(읽힘) > 1: 경보.append(f"컷마다 지온 다름: {k} {sorted(읽힘)}")
        for k, p in self.부품들.items():          # 좌우 짝
            if p.쪽 == "왼":
                q = self.부품들.get(f"{p.이름}/오른")
                if q is None: 경보.append(f"짝 없음: {k}")
                elif p.지온 and q.지온 and p.지온 != q.지온: 경보.append(f"짝 지온 다름: {k} {p.지온} ↔ {q.지온}")
        return 경보

    def 저장(self, path):
        d = {"부품들": [asdict(p) for p in self.부품들.values()], "붙음들": [asdict(e) for e in self.붙음들], "덮음들": [asdict(e) for e in self.덮음들]}
        json.dump(d, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=str)

    @classmethod
    def 읽기(cls, path):
        d = json.load(open(path, encoding="utf-8")); g = cls()
        def G(x): return 지온(단면(x["단면"]), 축(x["축"]), 크기(x["크기"]), 끝(x["끝"])) if x else None
        for p in d["부품들"]:
            p["지온"] = G(p["지온"]); p["관찰들"] = [관찰(**{**o, "지온": G(o["지온"])}) for o in p["관찰들"]]; g.더하기(부품(**p))
        g.붙음들 = [붙음(**{**e, "관계": 관계(e["관계"])}) for e in d["붙음들"]]; g.덮음들 = [덮음(**e) for e in d["덮음들"]]
        return g


if __name__ == "__main__":   # 자체 검사: 칸 26 오독(미간판으로 읽음)이 「짝 없음」으로 잡히고, 고친 뒤 사라지는가
    import tempfile, os
    쐐기 = 지온(단면.각, 축.곧, 크기.좁아짐, 끝.뾰족)
    g = 그래프()
    g.더하기(부품("코어", 층=0, 지온=지온(단면.둥, 축.휨, 크기.불룩, 끝.둥긂)))
    g.더하기(부품("이마판", "왼", 1, 지온(단면.각, 축.휨, 크기.일정, 끝.잘림)))
    g.더하기(부품("이마판", "오른", 1, 지온(단면.각, 축.휨, 크기.일정, 끝.잘림)))
    g.더하기(부품("차양", "왼", 2, 쐐기, 관찰들=[관찰("정면", [20], 쐐기, {"폭": 9.0})]))
    g.더하기(부품("미간판", "가운데", 2, 쐐기, 관찰들=[관찰("정면", [26], 쐐기)]))          # 오독
    for e in [("이마판/왼", "코어"), ("이마판/오른", "코어"), ("차양/왼", "이마판/왼"), ("미간판/가운데", "이마판/오른")]:
        g.붙음들.append(붙음(*e, 관계.위얹힘))
    a = g.검사(); assert any("짝 없음: 차양/왼" in x for x in a), a
    del g.부품들["미간판/가운데"]; g.붙음들 = [e for e in g.붙음들 if e.자식 != "미간판/가운데"]
    g.더하기(부품("차양", "오른", 2, 쐐기, 관찰들=[관찰("정면", [26], 쐐기)])); g.붙음들.append(붙음("차양/오른", "이마판/오른", 관계.위얹힘))
    assert g.검사() == [], g.검사()
    g.부품들["차양/오른"].관찰들.append(관찰("옆", [4], 지온(단면.각, 축.곧, 크기.일정, 끝.잘림)))      # 옆 컷이 다르게 읽음
    assert any("컷마다 지온 다름" in x for x in g.검사())
    p = os.path.join(tempfile.gettempdir(), "지온_검사.json"); g.저장(p); h = 그래프.읽기(p)
    assert h.검사() == g.검사() and h.부품들["차양/왼"].치수() == {"폭": 9.0}
    print("ok", g.검사())
