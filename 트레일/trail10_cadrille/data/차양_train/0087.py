import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-14))
r=w0.sketch().segment((-86,3),(-7,-43)).segment((7,-43)).segment((86,3)).segment((73,29)).segment((0,-17)).segment((-73,29)).close().assemble().finalize().extrude(28).cut(cq.Workplane('XY').box(5,200,18).translate((39,0,14)))