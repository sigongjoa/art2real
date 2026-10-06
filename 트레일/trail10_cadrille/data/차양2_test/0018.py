import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-20))
r=w0.sketch().segment((-87,23),(-9,-48)).segment((9,-48)).segment((87,23)).segment((73,51)).segment((0,-20)).segment((-73,51)).close().assemble().finalize().extrude(40).edges('>Z').chamfer(5).cut(cq.Workplane('XY').box(11,200,22).translate((0,0,20)))