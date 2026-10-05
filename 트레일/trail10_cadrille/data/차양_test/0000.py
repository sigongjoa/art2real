import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-13))
r=w0.sketch().segment((-60,13),(-12,-53)).segment((12,-53)).segment((60,13)).segment((49,36)).segment((0,-30)).segment((-49,36)).close().assemble().finalize().extrude(25).edges('>Z').chamfer(5).cut(cq.Workplane('XY').box(5,200,8).translate((11,0,13)))