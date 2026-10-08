import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,-8,0))
w1=cq.Workplane('ZX',origin=(0,-13,0))
r=w0.sketch().segment((-100,-48),(-97,-52)).segment((-27,-52)).segment((-27,-48)).arc((38,-25),(89,65)).segment((99,65)).arc((39,-34),(-32,-57)).segment((-32,-59)).segment((-50,-61)).segment((-80,-59)).segment((-100,-56)).close().assemble().finalize().extrude(21).union(w1.sketch().segment((-100,-48),(-97,-52)).segment((-27,-52)).segment((-27,-48)).segment((-8,-44)).segment((12,-38)).segment((15,-46)).segment((-7,-52)).segment((-32,-57)).segment((-32,-59)).segment((-50,-61)).segment((-80,-59)).segment((-100,-56)).close().assemble().finalize().extrude(26))
