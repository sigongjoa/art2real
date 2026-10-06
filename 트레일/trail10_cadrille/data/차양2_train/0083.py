import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-14))
r=w0.sketch().segment((-97,12),(-17,-48)).segment((17,-48)).segment((97,12)).segment((81,44)).segment((0,-16)).segment((-81,44)).close().assemble().finalize().extrude(27).edges('>Z').chamfer(6)