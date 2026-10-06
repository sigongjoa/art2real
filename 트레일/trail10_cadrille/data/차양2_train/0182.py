import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-21))
r=w0.sketch().segment((-95,-3),(-13,-55)).segment((13,-55)).segment((95,-3)).segment((81,26)).segment((0,-26)).segment((-81,26)).close().assemble().finalize().extrude(41).edges('>Z').chamfer(5).cut(cq.Workplane('XY').box(10,200,38).translate((46,0,21)))