import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-7))
r=w0.sketch().segment((-84,-4),(-12,-41)).segment((12,-41)).segment((84,-4)).segment((75,14)).segment((0,-23)).segment((-75,14)).close().assemble().finalize().extrude(13).cut(cq.Workplane('XY').box(5,200,6).translate((-34,0,7))).cut(cq.Workplane('XY').box(6,200,6).translate((42,0,7)))