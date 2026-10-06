import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-16))
r=w0.sketch().segment((-90,-1),(-17,-48)).segment((17,-48)).segment((90,-1)).segment((76,27)).segment((0,-20)).segment((-76,27)).close().assemble().finalize().extrude(32).edges('>Z').chamfer(5).cut(cq.Workplane('XY').box(8,200,22).translate((-17,0,16)))