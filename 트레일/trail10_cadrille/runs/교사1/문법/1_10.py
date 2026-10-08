import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,-45,0))
w1=cq.Workplane('YZ',origin=(-58,0,0))
w2=cq.Workplane('XY',origin=(0,0,-101))
r=w0.sketch().segment((-100,39),(-100,45)).segment((-83,47)).segment((-58,55)).segment((-51,55)).segment((-25,48)).segment((-20,44)).segment((-19,34)).segment((72,-39)).segment((84,-40)).segment((94,-40)).segment((99,-55)).segment((92,-57)).segment((89,-47)).segment((72,-47)).segment((-26,30)).segment((-26,39)).close().assemble().finalize().extrude(90).cut(w1.sketch().segment((-46,-101),(-6,-101)).segment((-45,87)).segment((-46,87)).close().assemble().reset().face(w1.sketch().segment((-46,101),(-46,100)).segment((46,91)).segment((46,101)).close().assemble()).finalize().extrude(116)).cut(w2.sketch().segment((51,46),(58,46)).segment((58,-46)).segment((-40,-46)).segment((37,-24)).segment((52,-21)).segment((57,-15)).segment((51,45)).close().assemble().finalize().extrude(202))
