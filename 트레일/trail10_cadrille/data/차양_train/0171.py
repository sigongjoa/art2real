import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-10))
r=w0.sketch().segment((-67,0),(-14,-44)).segment((14,-44)).segment((67,0)).segment((59,17)).segment((0,-27)).segment((-59,17)).close().assemble().finalize().extrude(19).cut(cq.Workplane('XY').box(5,200,6).translate((26,0,10))).cut(cq.Workplane('XY').box(3,200,6).translate((28,0,10)))