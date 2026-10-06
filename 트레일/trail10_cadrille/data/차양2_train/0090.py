import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-16))
r=w0.sketch().segment((-98,7),(-13,-45)).segment((13,-45)).segment((98,7)).segment((82,39)).segment((0,-13)).segment((-82,39)).close().assemble().finalize().extrude(32).cut(cq.Workplane('XY').box(10,200,18).translate((12,0,16)))