import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-8))
r=w0.sketch().segment((-75,-2),(-13,-38)).segment((13,-38)).segment((75,-2)).segment((68,12)).segment((0,-24)).segment((-68,12)).close().assemble().finalize().extrude(15).edges('>Z').chamfer(2).cut(cq.Workplane('XY').box(4,200,10).translate((0,0,8)))