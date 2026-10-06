import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-16))
r=w0.sketch().segment((-98,9),(-15,-63)).segment((15,-63)).segment((98,9)).segment((84,37)).segment((0,-35)).segment((-84,37)).close().assemble().finalize().extrude(32).edges('>Z').chamfer(7).cut(cq.Workplane('XY').box(12,200,16).translate((42,0,16)))