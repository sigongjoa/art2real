import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-8))
r=w0.sketch().segment((-89,10),(-12,-34)).segment((12,-34)).segment((89,10)).segment((77,34)).segment((0,-10)).segment((-77,34)).close().assemble().finalize().extrude(16).cut(cq.Workplane('XY').box(3,200,16).translate((-32,0,8)))