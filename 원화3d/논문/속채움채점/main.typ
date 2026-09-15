#import "../틀.typ": *

#let 판 = json("판정.json")
#let 판뺌 = json("판정_뺌.json")
#let 안 = json("안보임.json")
#let 넘 = json("넘침.json")
#let 장 = csv("장별.csv", row-type: dictionary)
#let 바뀐 = 장.filter(r => float(r.fill) > 1.05)

#show: 논문.with(
  title: "속 빈 정답은 치마 속을 감점한다",
  english: "Hollow ground truth penalizes skirt interiors: slice-filled ground truth for scoring three-view visual-hull prototypes",
  authors: "art2real · 원화3d",
  date: "2026-09-15",
  meta: "커밋 9686547 · 2c15f81 · c2b6fd6 · 실험_20260915/겉면채점.py · 머리가림.py · 속채움그림.py",
  abstract: [
    원화 세 판(정면 · 옆 · 뒤)의 실루엣 교집합으로 레진 굿즈 원형을 세우고, 게임용 3D 모델을 정답으로 3D IoU 를 잰다.
    드레스 캐릭터에서 점수가 0.37 까지 떨어졌는데, 원인은 원형이 아니라 정답이었다. 정답의 치마는 얇은 천이라 속이 비었고,
    원형은 원리상 속이 차 있다. 우리는 정답 복셀을 높이마다 닫힌 구멍만 채운 *층 속채움 정답*을 제안한다.
    이 부피는 수평 시점 어디서도 보이지 않는다. 실물 벤치 29장에서 판본 순서 · 같은 부피 대조군 판정 · 분해능이 모두 유지되고
    (지금 원형 중앙 IoU #수(판.at("속 채운 정답").at("격자128").at("중앙 이진 · 타원 · 오라클").at(1))),
    드레스 장은 0.37 → 0.77 로 오른다. 다만 장끼리 순위가 흔들려 절대값 비교에는 쓰지 않는다.
  ],
  keywords: ("visual hull", "채점 기준", "가려진 부피", "굿즈 원형", "3D IoU"),
)

= 서론

원화3d 는 2D 원화만 가진 IP 소유자에게 출력 가능한 원형을 준다. 파이프라인은 학습 · 생성 없이 세 판의 실루엣 교집합(visual hull @laurentini1994)을 만들고, 판 분할과 깊이맵으로 안쪽을 깎는다. 원형이 원화와 얼마나 맞는지는 정답이 있는 벤치로 잰다 — 3D 모델을 세 판으로 렌더하고, 그 모델을 정답으로 3D IoU 를 계산한다.

벤치의 드레스 캐릭터는 늘 낮았다. 정답 깊이를 넣은 천장조차 0.39~0.62 에서 멈췄다. 처음 가설은 긴 머리였고, 입력을 재자 틀렸다(4.1 절). 넘친 부피는 드레스 천 쪽에 몰려 있었고, 사람 판단은 짧았다 — *굿즈 원형은 치마 속이 안 보여도 된다.* 이 논문은 그 판단을 채점 기준으로 옮기고, 새 자가 좋은 원형과 나쁜 원형을 여전히 가르는지 판정한다.

기여는 셋이다. (1) 층 속채움 정답의 정의와, 그것이 세 판에서 보이지 않는 부피의 부분집합이라는 확인. (2) 돌리기 전에 적은 판정 세 가지와 29장 결과. (3) 새 에이전트 검토가 찾은 판정의 약점과 그 보정.

= 관련 연구

*가려진 곳의 visual hull.* Guan 외 @guan2006 는 가림물이 있을 때 실루엣을 「물체 ∪ 가림물」로 넓혀, 정답이 hull 안에 든다는 보장을 지키는 가장 좁은 hull 을 짓는다. 이후 여러 시점 영상에서 가림물 모양을 베이즈 융합으로 되찾는다 @guan2007. 둘 다 영상이 전제다. 회전체의 안 · 밖 visual hull 은 해석적으로 계산된다 @laurentini1999.

*옷을 몸 위에 짓기.* 스케치 기반 옷 모델링은 몸의 거리장 위에 앞 · 뒤 윤곽으로 껍질을 짓고 @turquin2007, 경계 고리만으로 전개가능 곡면을 세우기도 한다 @rose2007. 옷 입은 실루엣은 몸의 느슨한 상한이다 @balan2008. 이들은 속을 *복원*하려 한다. 우리는 복원하지 않고, 원화가 담을 수 없는 속을 *채점에서 뺀다.*

= 방법

== 벤치와 판본

실물 벤치는 손으로 얼린 29장이다(`벤치.json`). 이 중 `소체` 는 `base_female` 과 같은 메시라 서로 다른 모델은 28장이다. 판본은 넷이다.

#표(
  columns: (auto, 1fr),
  align: (left, left),
  header: ([판본], [뜻]),
  [이진], [깎기 전 hull. 바닥],
  [타원 1.00], [타원 단면 깊이 · lam 1.00. 지금 후보 기본값],
  [오라클 1.00], [정답 깊이 · lam 1.00. 천장],
  [균일\@타원], [이진 hull 을 타원 1.00 과 같은 부피까지 고르게 민 면. 제 부피 대조군],
)

IoU 는 격자 128 과 192 에서 잰다. 정답 복셀 $T$ 는 메시 표면을 굽고 바깥에서 홍수채움해 얻는다.

== 층 속채움 정답

정답 복셀을 높이 $z$ 층마다 잘라, 층 안에서 테두리에 둘러싸인 빈 곳만 채운다.

$ F = union.big_z op("fill")(T_z) $ <eq-fill>

$op("fill")$ 은 2D 구멍 채움이다. 치마는 층마다 고리라서 속이 차고, 다리 사이처럼 밖과 이어진 틈은 안 찬다. 층 안에서 닫힌 칸은 어떤 수평 광선도 닿지 못한다. 정면 · 옆 · 뒤는 모두 수평 시점이므로 $F$ 는 세 판이 원리적으로 볼 수 없는 부피다. 이를 직접 재기 위해 앞 · 뒤 · 옆 한쪽 광선이 처음 닿기 전 빈 칸을 「보인다」로 두고, 나머지 빈 칸을 $U$ 라 한다.

$ U = overline(T) inter H_(+y) inter H_(-y) inter H_(+x) $ <eq-unseen>

$H_d$ 는 $d$ 방향 광선이 이미 물체를 지난 칸이다. $F without T subset.eq U$ 여야 한다.

== 판정 — 돌리기 전에 적었다

- *배관.* 속 빈 정답 · 격자 128 의 세 판본 IoU 가 옛 기록과 |차| \< 0.002.
- *Q1 순서.* 속 채운 정답에서 중앙값이 이진 \< 타원 \< 오라클, 격자 둘 다.
- *Q2 판정 보존.* 타원 대 균일 판정(평균 \> 0 · 과반 승)이 두 정답에서 같다.
- *Q3 분해능.* 속 채운 정답에서 오라클 − 이진 중앙 ≥ 0.05, 타원 − 이진 중앙 \> 0.

셋 다 통과하면 속 채운 정답을 판본 비교의 표준으로 올린다.

= 실험

== 입력부터 — 머리카락이 아니었다

VRoid 11장은 원본 재질 이름(`_HAIR` · `_CLOTH` · `_SKIN`)이 있어 화소마다 부위 정답을 얻는다. 머리카락은 뒤판에서 거의 다 보이고(가려진 몫 ≤ 0.05, 한 장만 0.15), 「긴 머리」 장도 어깨에서 끝났다(@fig-hair). hull 이 넘친 복셀을 가장 가까운 정답 부위에 나누면, 드레스 장의 넘침은 천 쪽에 몰렸다(@tab-over).

#figure(
  image("그림/머리가림.png", width: 100%),
  caption: [`avatarsample_g` 의 세 판. 파랑 = 보이는 머리카락 · 빨강 = 가려진 머리카락 · 주황 테 = 몸 밖 머리카락 · 회색 = 몸과 옷.],
) <fig-hair>

#figure(
  {
    let cs = (("sakurada_fumiriya", "몸에 붙는 옷"), ("base_female", "짧은 치마"), ("avatarsample_g", "퍼진 드레스"),
              ("hairsample_female", "같은 드레스"), ("avatarsample_d_darkness", "긴 드레스"))
    표(
      columns: (1fr, auto, auto, auto),
      align: (left, right, right, right),
      header: ([케이스], [넘침 전체], [천 쪽], [머리 쪽]),
      ..cs.map(((c, label)) => {
        let r = 넘.at(c).at("이진")
        let t = float(r.at("넘침/정답"))
        (label, 수(t, d: 2), 수(t * float(r.at("천")), d: 2), 수(t * float(r.at("머리카락")), d: 2))
      }).flatten(),
    )
  },
  caption: [이진 hull 의 넘친 부피를 가장 가까운 정답 부위에 나눴다. 정답 부피 대비 · 격자 128. 부위마다 따로 채워 「머리 쪽」은 머리 부위 전체를 뜻한다.],
) <tab-over>

== 29장 판정

배관은 29장 모두 차이 #판.at("배관 최대차") 로 통과했다. 판정 결과는 @tab-verdict 다. 속 채운 정답에서도 순서가 서고, 타원은 같은 부피 대조군을 두 정답에서 같은 장 수로 이긴다. Q1 · Q2 · Q3 모두 통과했다. 중복 `소체` 를 빼고 28장으로 다시 판정해도 같다.

#figure(
  {
    let cell(t, g) = {
      let b = 판.at(t).at(g)
      let m = b.at("중앙 이진 · 타원 · 오라클")
      let w = b.at("타원−균일 평균 · 이긴 장")
      (수(m.at(0)), 수(m.at(1)), 수(m.at(2)), [#부호(w.at(0)) (#w.at(1)/29)])
    }
    표(
      columns: (auto, auto, auto, auto, auto, auto),
      align: (left, left, right, right, right, right),
      header: ([정답], [격자], [이진], [타원], [오라클], [타원−균일]),
      [속 빈], [128], ..cell("속 빈 정답", "격자128"),
      [], [192], ..cell("속 빈 정답", "격자·192"),
      [속 채운], [128], ..cell("속 채운 정답", "격자128"),
      [], [192], ..cell("속 채운 정답", "격자·192"),
    )
  },
  caption: [29장 중앙 IoU 와 제 부피 대조군. 괄호는 타원이 이긴 장.],
) <tab-verdict>

== 검토 — 판정이 약했다

맥락 없는 새 에이전트에게 계획 · 판정 · 기록만 주고 검토를 맡겼다. 지적은 이렇다. 속채움 배율 ≤ 1.05 인 19장은 두 정답에서 값이 같고 이미 14승이다. 과반은 15승이므로 Q2 가 떨어지려면 바뀌는 장의 승이 거의 전부 뒤집혀야 했다. 미리 적은 판정은 떨어지기 어려웠다.

그래서 속채움이 실제로 바꾸는 #바뀐.len() 장만 떼어 다시 봤다(@tab-changed). 순서가 서고, 대조군 승 수가 그대로다. 장마다 대조군 부호가 두 정답에서 뒤집힌 곳은 격자 128 에서 #장.filter(r => (float(r.ell_h) - float(r.uni_h)) * (float(r.ell_f) - float(r.uni_f)) < 0).len() 장이다. 검토는 두 정답의 장 순위 상관이 0.78 · 0.71 에 그친다는 점도 짚었다. 그래서 이 자는 *판본끼리 비교*에만 쓰고, 장끼리 절대값이나 「IoU 0.8」 같은 문구에는 쓰지 않는다.

#figure(
  {
    let col(k) = 바뀐.map(r => r.at(k))
    let wins(a, b) = 바뀐.filter(r => float(r.at(a)) > float(r.at(b))).len()
    표(
      columns: (auto, auto, auto, auto, auto),
      align: (left, right, right, right, right),
      header: ([정답], [이진], [타원], [오라클], [타원 \> 균일]),
      [속 빈], 수(중앙(col("bin_h"))), 수(중앙(col("ell_h"))), 수(중앙(col("ora_h"))), [#wins("ell_h", "uni_h")/#바뀐.len()],
      [속 채운], 수(중앙(col("bin_f"))), 수(중앙(col("ell_f"))), 수(중앙(col("ora_f"))), [#wins("ell_f", "uni_f")/#바뀐.len()],
    )
  },
  caption: [속채움 배율 \> 1.05 인 장만. 격자 128 중앙 IoU.],
) <tab-changed>

== 층 채움이 못 채우는 곳

$F without T subset.eq U$ (@eq-unseen) 는 29장 · 격자 둘에서 모두 성립했다. 드레스 장은 $U$ 대부분을 층 채움이 채운다. 한쪽으로 열린 오목부와 옆으로 뻗은 소매 속은 층 안에서 닫히지 않아 못 채운다(@tab-unseen). 얇은 껍질이 격자에서 새면 같은 모델이 격자마다 다르게 찬다 — `robot_Robot_ejDr` 는 속채움이 128 에서 0, 192 에서 0.16 이다.

#figure(
  {
    let cs = (("avatarsample_d_darkness", "긴 드레스"), ("avatarsample_g", "퍼진 드레스"), ("mech_Drill_8uBbH7Dvmb", "드릴 로봇"),
              ("wizard_Wizard_o87Upt5uHX", "로봇형 마법사"), ("witch_Witch_vWI9PHfjcy", "팔 벌린 마녀"), ("robot_Robot_ejDr8lRglP", "로봇"))
    표(
      columns: (1fr, auto, auto, auto),
      align: (left, right, right, right),
      header: ([케이스], [$U$], [채움], [못 채운 $U$]),
      ..cs.map(((c, label)) => {
        let r = 안.at(c).at("128")
        (label, 수(r.at("안보임/정답")), 수(r.at("속채움/정답")), 수(r.at("못채운안보임/정답")))
      }).flatten(),
    )
  },
  caption: [세 판에서 안 보이는 빈 부피 $U$ 와 층 채움. 정답 부피 대비 · 격자 128.],
) <tab-unseen>

== 모양으로 본 결과

#figure(
  placement: top,
  scope: "parent",
  {
    let cs = (("avatarsample_d_darkness", "긴 드레스"), ("avatarsample_g", "퍼진 드레스"), ("sakurada_fumiriya", "몸에 붙는 옷"),
              ("cloak_Chest_Closed_AngpV0HxD8", "닫힌 궤짝"), ("cape_Hat_Stylised_lNN3PlrjSa", "모자"), ("witch_Witch_vWI9PHfjcy", "팔 벌린 마녀"))
    grid(
      columns: 3,
      column-gutter: 6pt,
      row-gutter: 5pt,
      ..cs.map(((c, label)) => {
        let r = 장.find(x => x.case == c)
        stack(spacing: 2pt,
          image("그림/" + c + ".png", width: 100%),
          align(center, text(size: 7.4pt)[*#label* · 속채움 #r.fill 배 · 타원 #r.ell_h → #r.ell_f]))
      }),
    )
  },
  caption: [x 가운데에서 잘라 비스듬히 밑에서 본 3D. 칸마다 왼쪽 = 정답(회색 원래 · 파랑 채운 속 · 주황 안 보이는데 못 채운 곳), 오른쪽 = 속 채운 정답 대 타원 1.00(회색 겹침 · 빨강 원형이 넘침 · 보라 원형이 모자람). 28장 전부는 부록 @fig-all.],
) <fig-shape>

@fig-shape 에서 드레스 장은 속을 채우면 오른쪽 칸이 거의 겹침이다. 남는 오차는 두 종류다. 사람은 옷과 무관하게 *팔 · 다리가 넘치고*(빨강), 닫힌 궤짝 · 모자처럼 각진 것은 *모서리가 깎여 모자라다*(보라). 팔을 옆으로 뻗은 마녀는 소매 속이 주황이다.

= 한계

층 채움은 수평으로 닫힌 속만 채운다. 한쪽으로 열린 오목부 · 옆으로 뻗은 소매 속은 남고, 얇은 껍질은 격자에 따라 샌다. 판정 규칙은 바뀌지 않는 장이 결과를 받치는 구조라 약했다. 사후에 바뀌는 장만 다시 봤지만, 그 기준(1.05)도 사후에 정했다. 정답은 전부 렌더한 판에서 나와 세 판이 자동으로 맞는다 — 손그림 원화의 판 불일치는 이 벤치가 재지 않는다.

= 결론과 다음

속 빈 정답은 원화가 담을 수 없는 치마 속을 감점했다. 층 속채움 정답으로 바꿔도 판본 순서 · 대조군 판정 · 분해능이 유지되어, 판본 비교의 표준으로 조건부 채택한다(속 빈 정답 열을 같이 남기고 절대값 문구에는 안 쓴다). 다음은 셋이다. 정의를 $U$ 로 바꿔 같은 판정을 한 번 더 한다. 각진 물건은 둥근 단면을 안 쓰는 선택의 천장이 평균 +0.007 에 그쳐, 깊이 줄기(판 분할 · 평면 후보)로 넘긴다. 사람 팔 · 다리의 넘침(천장까지 평균 0.12)이 가장 큰 남은 몫이다.

#v(0.4em)
#text(font: sans, weight: "bold", size: 8.6pt)[재현]
#v(0.2em)
```
python 원화3d/실험_20260915/머리가림.py        # 입력 · 넘침
python 원화3d/실험_20260915/겉면채점.py 벤치 30  # 29장
python 원화3d/실험_20260915/겉면채점.py 벤치판정 [소체]
python 원화3d/실험_20260915/겉면채점.py 안보임
python 원화3d/실험_20260915/속채움그림.py 30 && ... 모음
```

#참고문헌(bibliography("refs.bib", style: "ieee", title: none))

#pagebreak()

#place(top, scope: "parent", float: true, [
  = 부록

  #figure(
    image("그림/전체.png", width: 100%),
    caption: [실물 28장 전부. 속채움 배율 큰 순. 색은 @fig-shape 와 같다.],
  ) <fig-all>
])

#pagebreak()

#place(top, scope: "parent", float: true, [
  #figure(
    {
      표(
        columns: (1fr, auto, auto, auto, auto, auto),
        align: (left, right, right, right, right, right),
        header: ([케이스], [속채움 배], [이진], [타원 1.00], [오라클 1.00], [균일\@타원]),
        ..장.map(r => (사례(r.case), r.fill, [#r.bin_h → #r.bin_f], [#r.ell_h → #r.ell_f], [#r.ora_h → #r.ora_f], [#r.uni_h → #r.uni_f])).flatten(),
      )
    },
    caption: [장별 IoU, 속 빈 정답 → 속 채운 정답. 격자 128 · 속채움 배율 큰 순.],
  ) <tab-all>
])
