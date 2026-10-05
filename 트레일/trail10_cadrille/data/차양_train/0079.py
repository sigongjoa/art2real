import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-13))
r=w0.sketch().segment((-58,-3),(-12,-45)).segment((12,-45)).segment((58,-3)).segment((44,25)).segment((0,-17)).segment((-44,25)).close().assemble().finalize().extrude(25).edges('>Z').chamfer(2).cut(cq.Workplane('XY').box(7,200,6).translate((0,0,13)))