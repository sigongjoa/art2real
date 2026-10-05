import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-8))
r=w0.sketch().segment((-66,12),(-4,-40)).segment((4,-40)).segment((66,12)).segment((59,26)).segment((0,-26)).segment((-59,26)).close().assemble().finalize().extrude(16).cut(cq.Workplane('XY').box(7,200,16).translate((12,0,8)))