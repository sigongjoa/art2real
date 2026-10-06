import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-16))
r=w0.sketch().segment((-93,13),(-13,-57)).segment((13,-57)).segment((93,13)).segment((81,38)).segment((0,-32)).segment((-81,38)).close().assemble().finalize().extrude(31).cut(cq.Workplane('XY').box(7,200,16).translate((6,0,16))).cut(cq.Workplane('XY').box(10,200,8).translate((23,0,16)))