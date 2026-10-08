import cadquery as cq
# 옆으로 누운 통(x 축 회전체) + 위로 선 기둥
P = [(-99.5, 0), (-99.5, 37), (-90, 49), (-86, 57), (-80, 59), (-70, 62), (-50, 66), (-30, 69), (0, 71), (30, 69), (50, 66), (70, 62), (80, 59), (86, 57), (90, 49), (99.5, 37), (99.5, 0)]
barrel = cq.Workplane('XY').polyline(P).close().revolve(360, (-1, 0, 0), (1, 0, 0)).translate((0, -1, -18))
for sx in (-1, 1):   # 양 끝 소켓 구멍
    barrel = barrel.cut(cq.Workplane('YZ', origin=(sx * 100 if sx > 0 else -100, 0, 0)).center(-1, -18).circle(31).extrude(-85 if sx > 0 else 85))
post = cq.Workplane('XY', origin=(0, 13, 20)).circle(58).extrude(68.4)
post = post.cut(cq.Workplane('XY', origin=(0, 13.5, 30)).circle(21).extrude(60)).cut(cq.Workplane('XY', origin=(0, 13.5, 86.4)).circle(49).circle(44).extrude(3))
r = barrel.union(post)
