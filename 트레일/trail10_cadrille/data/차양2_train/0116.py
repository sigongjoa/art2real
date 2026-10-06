import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-12))
r=w0.sketch().segment((-86,19),(-16,-60)).segment((16,-60)).segment((86,19)).segment((74,44)).segment((0,-35)).segment((-74,44)).close().assemble().finalize().extrude(24)