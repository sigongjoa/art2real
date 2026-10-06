import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-22))
r=w0.sketch().segment((-93,22),(-6,-54)).segment((6,-54)).segment((93,22)).segment((74,61)).segment((0,-15)).segment((-74,61)).close().assemble().finalize().extrude(43).edges('>Z').chamfer(12).cut(cq.Workplane('XY').box(6,200,12).translate((0,0,22)))