from collections import namedtuple

import numpy as np


class Point(namedtuple('Point', ['x', 'y'])):
    def round(self):
        return Point(x=int(np.round(self.x)), y=int(np.round(self.y)))

    def __add__(self, other):
        if isinstance(other, Point):
            return Point(x=self.x + other.x, y=self.y + other.y)
        return Point(x=self.x + other, y=self.y + other)

    def __mul__(self, other):
        return Point(x=self.x * other, y=self.y * other)
