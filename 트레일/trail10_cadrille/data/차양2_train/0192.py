import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-13))
r=w0.sketch().segment((-92,8),(-10,-55)).segment((10,-55)).segment((92,8)).segment((79,34)).segment((0,-29)).segment((-79,34)).close().assemble().finalize().extrude(26).cut(cq.Workplane('XY').box(7,200,16).translate((0,0,13)))