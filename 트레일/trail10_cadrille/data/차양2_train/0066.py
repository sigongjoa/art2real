import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-17))
r=w0.sketch().segment((-86,-5),(-13,-46)).segment((13,-46)).segment((86,-5)).segment((74,19)).segment((0,-22)).segment((-74,19)).close().assemble().finalize().extrude(34).cut(cq.Workplane('XY').box(7,200,34).translate((8,0,17)))