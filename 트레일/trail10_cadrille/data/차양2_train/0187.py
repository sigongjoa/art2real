import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-16))
r=w0.sketch().segment((-91,-3),(-9,-70)).segment((9,-70)).segment((91,-3)).segment((75,29)).segment((0,-38)).segment((-75,29)).close().assemble().finalize().extrude(31).cut(cq.Workplane('XY').box(7,200,20).translate((-44,0,16)))