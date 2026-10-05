import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-12))
r=w0.sketch().segment((-93,20),(-9,-50)).segment((9,-50)).segment((93,20)).segment((80,46)).segment((0,-24)).segment((-80,46)).close().assemble().finalize().extrude(23).edges('>Z').chamfer(6)