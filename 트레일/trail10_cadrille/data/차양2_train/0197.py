import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-17))
r=w0.sketch().segment((-93,10),(-17,-61)).segment((17,-61)).segment((93,10)).segment((74,49)).segment((0,-22)).segment((-74,49)).close().assemble().finalize().extrude(34).cut(cq.Workplane('XY').box(11,200,6).translate((16,0,17)))