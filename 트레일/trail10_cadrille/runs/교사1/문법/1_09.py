import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,-75,0))
w1=cq.Workplane('ZX',origin=(0,0,0))
w2=cq.Workplane('ZX',origin=(0,30,0))
w3=cq.Workplane('ZX',origin=(0,48,0))
w4=cq.Workplane('XY',origin=(0,0,87))
w5=cq.Workplane('XY',origin=(0,0,-84))
r=w0.sketch().arc((98,0),(69,54),(-1,76)).arc((-71,54),(-100,0)).arc((-71,-54),(-1,-76)).arc((69,-54),(98,0)).assemble().finalize().extrude(75).union(w1.sketch().arc((86,0),(61,47),(-1,67)).arc((-63,47),(-88,0)).arc((-63,-47),(-1,-67)).arc((61,-47),(86,0)).assemble().finalize().extrude(30)).union(w2.sketch().arc((64,0),(45,35),(-1,50)).arc((-47,35),(-66,0)).arc((-47,-35),(-1,-50)).arc((45,-35),(64,0)).assemble().finalize().extrude(18)).union(w3.sketch().arc((39,0),(27,21),(-1,30)).arc((-29,21),(-41,0)).arc((-29,-21),(-1,-30)).arc((27,-21),(39,0)).assemble().finalize().extrude(10)).cut(w0.sketch().push([(-26,0)]).circle(58).finalize().extrude(58)).union(w4.sketch().segment((15,17),(85,66)).segment((78,76)).segment((9,27)).close().assemble().reset().face(w4.sketch().segment((-15,17),(-85,66)).segment((-78,76)).segment((-9,27)).close().assemble()).finalize().extrude(7)).union(w5.sketch().push([(81,-43),(-81,-43)]).rect(21,65).push([(0,61)]).rect(38,45).finalize().extrude(114)).union(w4.workplane(offset=-28).moveTo(0,-71).box(24,26,38))
