import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-8))
r=w0.sketch().segment((-71,6),(-9,-32)).segment((9,-32)).segment((71,6)).segment((59,30)).segment((0,-8)).segment((-59,30)).close().assemble().finalize().extrude(15).edges('>Z').chamfer(5).cut(cq.Workplane('XY').box(4,200,14).translate((0,0,8)))