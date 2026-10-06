import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-13))
r=w0.sketch().segment((-89,23),(-9,-63)).segment((9,-63)).segment((89,23)).segment((77,48)).segment((0,-38)).segment((-77,48)).close().assemble().finalize().extrude(26).edges('>Z').chamfer(6).cut(cq.Workplane('XY').box(11,200,24).translate((-8,0,13)))