import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-21))
r=w0.sketch().segment((-98,24),(-16,-57)).segment((16,-57)).segment((98,24)).segment((81,59)).segment((0,-22)).segment((-81,59)).close().assemble().finalize().extrude(41).edges('>Z').chamfer(8)