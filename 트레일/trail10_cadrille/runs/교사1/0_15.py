import cadquery as cq
from OCP.gp import gp_GTrsf, gp_Mat, gp_XYZ
from OCP.BRepBuilderAPI import BRepBuilderAPI_GTransform
def ell(a, b, c, ctr):   # 타원체 = 단위 구 비균등 축척
    g = gp_GTrsf(); g.SetVectorialPart(gp_Mat(a, 0, 0, 0, b, 0, 0, 0, c)); g.SetTranslationPart(gp_XYZ(*ctr))
    return cq.Workplane().add(cq.Shape.cast(BRepBuilderAPI_GTransform(cq.Solid.makeSphere(1, dir=cq.Vector(0, 1, 0), angleDegrees1=-90).wrapped, g, True).Shape()))
C = (0, -43, 53.8)
shell = ell(100, 86, 107.6, C).cut(ell(95, 80.5, 101.5, C))
r = shell.intersect(cq.Workplane('XY').box(220, 100, 106.8).translate((0, 7, 0)))
