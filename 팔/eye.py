"""카메라와 기계 좌표를 잇는다.

마커를 안 붙인다. 기계 자신이 기준물이다 — 좌표를 아는 지점으로 보내놓고
거기가 화면 어디인지 보면, 그 대응 4쌍이 사상을 정한다.

이 방식이 마커보다 나은 이유는 편해서가 아니다. 도면이 아니라 **실제 거동**을
재기 때문이다. 링크 길이 오차·호밍 오프셋·백래시·처짐이 전부 이 사상 안에
흡수된다. "X60 을 명령하면 실제로 어디에 나타나는가" 를 직접 재는 것이다.

기계 치수가 한 개도 안 들어간다. 그래서 팔이 없어도 이 파일은 검증된다.
"""
import sys
import cv2
import numpy as np

# ponytail: 고정 카메라(eye-to-hand) 전제. 팔에 카메라를 달면(eye-in-hand)
# locate() 대신 cv2.phaseCorrelate 로 화면 전체 이동을 재야 한다.

MIN_BLOB_PX = 200        # 이보다 작은 변화는 노이즈로 본다
DIFF_THRESH = 25         # 0~255. 조명이 흔들리면 올린다


def locate(background, frame, thresh=DIFF_THRESH, min_px=MIN_BLOB_PX):
    """배경에 없던 것의 무게중심 (x, y) 픽셀. 못 찾으면 None.

    배경은 '팔이 시야 밖에 있을 때' 한 장이다. 두 프레임을 그냥 빼면
    떠난 자리와 도착한 자리가 둘 다 남아서 중점이 잡힌다 — 그래서 배경을 쓴다.
    """
    a, b = (cv2.cvtColor(x, cv2.COLOR_BGR2GRAY) if x.ndim == 3 else x
            for x in (background, frame))
    d = cv2.GaussianBlur(cv2.absdiff(a, b), (5, 5), 0)
    _, m = cv2.threshold(d, thresh, 255, cv2.THRESH_BINARY)

    n, _, stats, cent = cv2.connectedComponentsWithStats(m, 8)
    if n < 2:
        return None
    i = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))   # 0번은 배경
    if stats[i, cv2.CC_STAT_AREA] < min_px:
        return None
    return tuple(cent[i])


class Calib:
    """기계 mm <-> 화면 픽셀. 대응 4쌍 이상으로 호모그래피를 푼다.

    4쌍이면 원근까지 잡힌다. 3쌍만 쓰면 아핀이라 카메라가 비스듬할 때 틀어진다.
    """

    def __init__(self, H, residual_px):
        self.H = H
        self.residual_px = residual_px     # 이 값이 캘리브레이션의 신뢰도다

    @classmethod
    def fit(cls, mm_pts, px_pts):
        mm = np.asarray(mm_pts, np.float32).reshape(-1, 1, 2)
        px = np.asarray(px_pts, np.float32).reshape(-1, 1, 2)
        if len(mm) < 4:
            raise ValueError(f"4쌍 이상 필요, {len(mm)}쌍 받음")
        H, _ = cv2.findHomography(mm, px, 0)     # 점이 적으니 RANSAC 안 쓴다
        if H is None:
            raise ValueError("호모그래피 실패 — 점들이 일직선이 아닌지 확인")
        err = np.linalg.norm(cv2.perspectiveTransform(mm, H) - px, axis=2).ravel()
        return cls(H, float(err.max()))

    def to_px(self, mm):
        p = cv2.perspectiveTransform(np.asarray([[mm]], np.float32), self.H)
        return tuple(p[0, 0])

    def to_mm(self, px):
        p = cv2.perspectiveTransform(np.asarray([[px]], np.float32),
                                     np.linalg.inv(self.H))
        return tuple(p[0, 0])


def calibrate(arm, shoot, grid=((20, 20), (60, 20), (60, 60), (20, 60)), z=30):
    """팔을 격자점으로 보내며 대응쌍을 모은다. 이게 전체 절차다.

    arm   : arm.Arm — move(x, y, z) 가 동작 완료까지 블로킹해야 한다
    shoot : () -> BGR 프레임
    """
    arm.move(x=grid[0][0], y=grid[0][1], z=z + 40)   # 배경은 팔을 치우고 찍는다
    background = shoot()

    mm, px = [], []
    for x, y in grid:
        arm.move(x=x, y=y, z=z)
        p = locate(background, shoot())
        if p is None:
            raise RuntimeError(f"({x},{y}) 에서 팔을 못 찾음 — 조명이나 시야 확인")
        mm.append((x, y))
        px.append(p)
    return Calib.fit(mm, px)


def demo():
    """자체 점검. 카메라도 팔도 없이 돈다 — 아는 사상을 심고 되찾는지 본다."""
    # 1) 알려진 호모그래피(원근 포함)를 심고, 잡음을 얹어 되찾는다
    true_H = np.array([[3.1, 0.15, 120.0],
                       [0.10, 3.05, 90.0],
                       [0.0009, 0.0004, 1.0]])
    mm = [(20, 20), (60, 20), (60, 60), (20, 60), (40, 45)]
    src = np.asarray(mm, np.float32).reshape(-1, 1, 2)
    px = cv2.perspectiveTransform(src, true_H).reshape(-1, 2)
    rng = np.random.default_rng(0)
    noisy = px + rng.normal(0, 0.3, px.shape)          # 검출 잡음 0.3px

    c = Calib.fit(mm, noisy)
    assert c.residual_px < 1.0, f"잔차가 크다: {c.residual_px:.2f}px"

    # 왕복이 제자리로 돌아와야 한다
    back = c.to_mm(c.to_px((37.0, 51.0)))
    assert np.allclose(back, (37.0, 51.0), atol=0.2), back

    # 학습에 안 쓴 점도 맞아야 한다 (외삽 아닌 내삽)
    got = np.asarray(c.to_px((45.0, 30.0)))
    want = cv2.perspectiveTransform(np.asarray([[[45.0, 30.0]]], np.float32),
                                    true_H)[0, 0]
    assert np.linalg.norm(got - want) < 1.5, (got, want)

    # 2) locate() — 배경에 흰 사각형 하나를 얹고 그 중심을 찾는다
    bg = np.full((240, 320), 40, np.uint8)
    fr = bg.copy()
    cv2.rectangle(fr, (150, 100), (180, 130), 220, -1)   # 중심 (165, 115)
    p = locate(bg, fr)
    assert p is not None and np.allclose(p, (165, 115), atol=1.5), p

    # 없으면 없다고 해야 한다 — 잘못 찾는 것보다 중요하다
    assert locate(bg, bg.copy()) is None

    # 일직선 점은 사상이 안 정해진다. 조용히 틀린 값을 주면 안 된다
    try:
        Calib.fit([(0, 0), (1, 1), (2, 2), (3, 3)], [(0, 0), (1, 1), (2, 2), (3, 3)])
    except ValueError:
        pass

    print(f"check OK — 잔차 {c.residual_px:.2f}px, 왕복 오차 "
          f"{np.linalg.norm(np.subtract(back, (37.0, 51.0))):.3f}mm")


def live(cam=0):
    """웹캠으로 locate() 만 눈으로 확인. 손을 넣었다 빼보면 된다."""
    cap = cv2.VideoCapture(cam)
    if not cap.isOpened():
        raise SystemExit(f"카메라 {cam} 못 엶")
    for _ in range(10):
        cap.read()                       # 자동노출 안정화
    ok, bg = cap.read()
    print("배경 찍음. 손을 넣어봐. q 로 종료")
    while ok:
        ok, fr = cap.read()
        p = locate(bg, fr)
        if p:
            cv2.circle(fr, (int(p[0]), int(p[1])), 8, (0, 0, 255), 2)
        cv2.imshow("eye", fr)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break
    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    live(int(sys.argv[2]) if len(sys.argv) > 2 else 0) if "--live" in sys.argv else demo()
