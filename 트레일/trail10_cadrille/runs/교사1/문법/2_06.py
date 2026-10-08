import cadquery as cq
w0=cq.Workplane('YZ',origin=(-95,0,0))
w1=cq.Workplane('XY',origin=(0,0,-70))
w2=cq.Workplane('XY',origin=(0,0,11))
w3=cq.Workplane('XY',origin=(0,0,-63))
r=w0.sketch().segment((-90,-69),(48,-69)).segment((48,58)).segment((38,67)).segment((8,67)).segment((2,40)).segment((-8,14)).segment((-30,3)).segment((-50,16)).segment((-58,58)).segment((-68,66)).segment((-84,60)).segment((-94,30)).segment((-94,-30)).close().assemble().finalize().extrude(190).cut(w1.sketch().push([(0,-20)]).circle(40).finalize().extrude(25)).union(w2.sketch().push([(0,-35)]).circle(24).finalize().extrude(32)).union(w3.sketch().push([(0,74)]).circle(16).finalize().extrude(32)).union(w1.sketch().push([(0,74)]).circle(22).finalize().extrude(23)).union(w1.sketch().push([(0,-35)]).circle(18).finalize().extrude(89))
