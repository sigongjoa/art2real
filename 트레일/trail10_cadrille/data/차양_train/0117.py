import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-7))
r=w0.sketch().segment((-55,5),(-9,-41)).segment((9,-41)).segment((55,5)).segment((48,20)).segment((0,-26)).segment((-48,20)).close().assemble().finalize().extrude(14).cut(cq.Workplane('XY').box(8,200,14).translate((0,0,7)))