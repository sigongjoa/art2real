import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-18))
r=w0.sketch().segment((-96,20),(-13,-69)).segment((13,-69)).segment((96,20)).segment((84,45)).segment((0,-44)).segment((-84,45)).close().assemble().finalize().extrude(36).cut(cq.Workplane('XY').box(7,200,8).translate((0,0,18)))