import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-7))
r=w0.sketch().segment((-95,-4),(-8,-38)).segment((8,-38)).segment((95,-4)).segment((83,21)).segment((0,-13)).segment((-83,21)).close().assemble().finalize().extrude(14)