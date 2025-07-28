from matplotlib.path import Path
from abc import ABC, abstractmethod

class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def transform(self, t):
        a, b, c, d, e, f = t

        new_x = a*self.x + b*self.y + c
        new_y = d*self.x + e*self.y + f

        self.x = new_x
        self.y = new_y

    def tuple(self):
        return self.x, self.y


class SVGMoveBase(ABC):
    @abstractmethod
    def svg_move(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def transform(self, t) -> None:
        raise NotImplementedError

    @abstractmethod
    def x_coords(self):
        raise NotImplementedError

    @abstractmethod
    def y_coords(self):
        raise NotImplementedError

    @abstractmethod
    def mpl_path(self):
        raise NotImplementedError


class SVGMoveTo(SVGMoveBase):
    def __init__(self, a):
        self.a = a

    def transform(self, t):
        self.a.transform(t)

    def svg_move(self):
        return f"M {self.a.x:.3f},{self.a.y:.3f}"

    def x_coords(self):
        return [self.a.x]

    def y_coords(self):
        return [self.a.y]

    def mpl_path(self):
        code = [Path.MOVETO]
        vertices = [self.a.tuple()]
        return vertices, code



class SVGLineTo(SVGMoveBase):
    def __init__(self, a):
        self.a = a

    def transform(self, t):
        self.a.transform(t)

    def svg_move(self):
        return f"L {self.a.x:.3f},{self.a.y:.3f}"

    def x_coords(self):
        return [self.a.x]

    def y_coords(self):
        return [self.a.y]

    def mpl_path(self):
        code = [Path.LINETO]
        vertices = [self.a.tuple()]
        return vertices, code


class SVGConicTo(SVGMoveBase):
    def __init__(self, a, b):
        self.a = a
        self.b = b

    def transform(self, t):
        self.a.transform(t)
        self.b.transform(t)

    def svg_move(self):
        return f"Q {self.a.x:.3f},{self.a.y:.3f} {self.b.x:.3f},{self.b.y:.3f}"

    def x_coords(self):
        return [self.a.x, self.b.x]

    def y_coords(self):
        return [self.a.y, self.b.y]

    def mpl_path(self):
        code = [Path.CURVE3]*2
        vertices = [self.a.tuple(), self.b.tuple()]
        return vertices, code


class SVGCubicTo(SVGMoveBase):
    def __init__(self, a, b, c):
        self.a = a
        self.b = b
        self.c = c

    def transform(self, t):
        self.a.transform(t)
        self.b.transform(t)
        self.c.transform(t)

    def svg_move(self):
        return f"C {self.a.x:.3f},{self.a.y:.3f} {self.b.x:.3f},{self.b.y:.3f} {self.c.x:.3f},{self.c.y:.3f}"

    def x_coords(self):
        return [self.a.x, self.b.x, self.c.x]

    def y_coords(self):
        return [self.a.y, self.b.y, self.c.y]

    def mpl_path(self):
        code = [Path.CURVE4]*3
        vertices = [self.a.tuple(), self.b.tuple(), self.c.tuple()]
        return vertices, code

class SVGClosePolygon(SVGMoveBase):
    def __init__(self):
        pass

    def transform(self, t):
        pass

    def svg_move(self):
        return f"Z"

    def x_coords(self):
        return []

    def y_coords(self):
        return []

    def mpl_path(self):
        code = [Path.CLOSEPOLY]
        vertices = [(0, 0)]
        return vertices, code