import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-5))
r=w0.sketch().segment((-67,9),(-4,-41)).segment((4,-41)).segment((67,9)).segment((56,32)).segment((0,-18)).segment((-56,32)).close().assemble().finalize().extrude(10).cut(cq.Workplane('XY').box(4,200,8).translate((-8,0,5)))