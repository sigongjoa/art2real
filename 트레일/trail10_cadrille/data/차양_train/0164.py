import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-8))
r=w0.sketch().segment((-85,18),(-8,-26)).segment((8,-26)).segment((85,18)).segment((74,40)).segment((0,-4)).segment((-74,40)).close().assemble().finalize().extrude(16)