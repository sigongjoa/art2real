import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-22))
r=w0.sketch().segment((-91,-5),(-13,-56)).segment((13,-56)).segment((91,-5)).segment((74,29)).segment((0,-22)).segment((-74,29)).close().assemble().finalize().extrude(43).edges('>Z').chamfer(8).cut(cq.Workplane('XY').box(6,200,40).translate((-23,0,22)))