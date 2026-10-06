import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-15))
r=w0.sketch().segment((-95,-5),(-6,-45)).segment((6,-45)).segment((95,-5)).segment((76,34)).segment((0,-6)).segment((-76,34)).close().assemble().finalize().extrude(29).edges('>Z').chamfer(5)