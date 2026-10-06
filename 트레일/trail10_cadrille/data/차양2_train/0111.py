import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-14))
r=w0.sketch().segment((-89,-1),(-17,-60)).segment((17,-60)).segment((89,-1)).segment((71,35)).segment((0,-24)).segment((-71,35)).close().assemble().finalize().extrude(27)