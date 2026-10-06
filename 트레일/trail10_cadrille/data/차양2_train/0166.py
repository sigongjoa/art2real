import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-19))
r=w0.sketch().segment((-93,20),(-9,-59)).segment((9,-59)).segment((93,20)).segment((80,46)).segment((0,-33)).segment((-80,46)).close().assemble().finalize().extrude(37)