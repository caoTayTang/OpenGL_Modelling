import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import math
from .base import Geometry


class Triangle(Geometry):
    VERTEX_SHADER = "shaders/color_interp.vert"
    FRAGMENT_SHADER = "shaders/color_interp.frag"

    def __init__(self, vert_shader=None, frag_shader=None):
        super().__init__(vert_shader, frag_shader)
        self._generate_geometry()

    def _generate_geometry(self):
        self.vertices = np.array([
            [0.0, 0.5, 0.0],
            [-0.5, -0.5, 0.0],
            [0.5, -0.5, 0.0]
        ], dtype=np.float32)

        self.colors = np.array([
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, 0.0, 1.0]
        ], dtype=np.float32)

        self.normals = np.array([
            [0.0, 0.0, 1.0],
            [0.0, 0.0, 1.0],
            [0.0, 0.0, 1.0]
        ], dtype=np.float32)


class Rectangle(Geometry):
    VERTEX_SHADER = "shaders/color_interp.vert"
    FRAGMENT_SHADER = "shaders/color_interp.frag"

    def __init__(self, width=1.0, height=1.0, vert_shader=None, frag_shader=None):
        self.width = width
        self.height = height
        super().__init__(vert_shader, frag_shader)
        self._generate_geometry()

    def _generate_geometry(self):
        w, h = self.width / 2, self.height / 2
        self.vertices = np.array([
            [-w, -h, 0.0],
            [w, -h, 0.0],
            [w, h, 0.0],
            [-w, h, 0.0]
        ], dtype=np.float32)

        self.colors = np.array([
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, 0.0, 1.0],
            [1.0, 1.0, 0.0]
        ], dtype=np.float32)

        self.normals = np.array([
            [0.0, 0.0, 1.0],
            [0.0, 0.0, 1.0],
            [0.0, 0.0, 1.0],
            [0.0, 0.0, 1.0]
        ], dtype=np.float32)

        self.indices = np.array([0, 1, 2, 0, 2, 3], dtype=np.int32)


class Pentagon(Geometry):
    VERTEX_SHADER = "shaders/color_interp.vert"
    FRAGMENT_SHADER = "shaders/color_interp.frag"

    def __init__(self, radius=0.5, vert_shader=None, frag_shader=None):
        self.radius = radius
        super().__init__(vert_shader, frag_shader)
        self._generate_geometry()

    def _generate_geometry(self):
        n = 5
        vertices = []
        colors = []
        normals = []

        vertices.append([0.0, 0.0, 0.0])
        colors.append([0.5, 0.5, 0.5])
        normals.append([0.0, 0.0, 1.0])

        for i in range(n):
            angle = 2 * math.pi * i / n - math.pi / 2
            x = self.radius * math.cos(angle)
            y = self.radius * math.sin(angle)
            vertices.append([x, y, 0.0])
            colors.append([math.cos(angle), math.sin(angle), 0.5])
            normals.append([0.0, 0.0, 1.0])

        self.vertices = np.array(vertices, dtype=np.float32)
        self.colors = np.array(colors, dtype=np.float32)
        self.normals = np.array(normals, dtype=np.float32)

        indices = []
        for i in range(1, n + 1):
            indices.extend([0, i, i % n + 1])
        self.indices = np.array(indices, dtype=np.int32)


class Hexagon(Geometry):
    VERTEX_SHADER = "shaders/color_interp.vert"
    FRAGMENT_SHADER = "shaders/color_interp.frag"

    def __init__(self, radius=0.5, vert_shader=None, frag_shader=None):
        self.radius = radius
        super().__init__(vert_shader, frag_shader)
        self._generate_geometry()

    def _generate_geometry(self):
        n = 6
        vertices = []
        colors = []
        normals = []

        vertices.append([0.0, 0.0, 0.0])
        colors.append([0.5, 0.5, 0.5])
        normals.append([0.0, 0.0, 1.0])

        for i in range(n):
            angle = 2 * math.pi * i / n
            x = self.radius * math.cos(angle)
            y = self.radius * math.sin(angle)
            vertices.append([x, y, 0.0])
            colors.append([math.cos(angle), math.sin(angle), 0.5])
            normals.append([0.0, 0.0, 1.0])

        self.vertices = np.array(vertices, dtype=np.float32)
        self.colors = np.array(colors, dtype=np.float32)
        self.normals = np.array(normals, dtype=np.float32)

        indices = []
        for i in range(1, n + 1):
            indices.extend([0, i, i % n + 1])
        self.indices = np.array(indices, dtype=np.int32)


class Circle(Geometry):
    VERTEX_SHADER = "shaders/color_interp.vert"
    FRAGMENT_SHADER = "shaders/color_interp.frag"

    def __init__(self, radius=0.5, segments=32, vert_shader=None, frag_shader=None):
        self.radius = radius
        self.segments = segments
        super().__init__(vert_shader, frag_shader)
        self._generate_geometry()

    def _generate_geometry(self):
        n = self.segments
        vertices = []
        colors = []
        normals = []

        vertices.append([0.0, 0.0, 0.0])
        colors.append([0.5, 0.5, 0.5])
        normals.append([0.0, 0.0, 1.0])

        for i in range(n):
            angle = 2 * math.pi * i / n
            x = self.radius * math.cos(angle)
            y = self.radius * math.sin(angle)
            vertices.append([x, y, 0.0])
            colors.append([math.cos(angle), math.sin(angle), 0.5])
            normals.append([0.0, 0.0, 1.0])

        self.vertices = np.array(vertices, dtype=np.float32)
        self.colors = np.array(colors, dtype=np.float32)
        self.normals = np.array(normals, dtype=np.float32)

        indices = []
        for i in range(1, n + 1):
            indices.extend([0, i, i % n + 1])
        self.indices = np.array(indices, dtype=np.int32)


class Ellipse(Geometry):
    VERTEX_SHADER = "shaders/color_interp.vert"
    FRAGMENT_SHADER = "shaders/color_interp.frag"

    def __init__(self, radius_x=0.5, radius_y=0.3, segments=32, vert_shader=None, frag_shader=None):
        self.radius_x = radius_x
        self.radius_y = radius_y
        self.segments = segments
        super().__init__(vert_shader, frag_shader)
        self._generate_geometry()

    def _generate_geometry(self):
        n = self.segments
        vertices = []
        colors = []
        normals = []

        vertices.append([0.0, 0.0, 0.0])
        colors.append([0.5, 0.5, 0.5])
        normals.append([0.0, 0.0, 1.0])

        for i in range(n):
            angle = 2 * math.pi * i / n
            x = self.radius_x * math.cos(angle)
            y = self.radius_y * math.sin(angle)
            vertices.append([x, y, 0.0])
            colors.append([math.cos(angle), math.sin(angle), 0.5])
            normals.append([0.0, 0.0, 1.0])

        self.vertices = np.array(vertices, dtype=np.float32)
        self.colors = np.array(colors, dtype=np.float32)
        self.normals = np.array(normals, dtype=np.float32)

        indices = []
        for i in range(1, n + 1):
            indices.extend([0, i, i % n + 1])
        self.indices = np.array(indices, dtype=np.int32)


class Trapezoid(Geometry):
    VERTEX_SHADER = "shaders/color_interp.vert"
    FRAGMENT_SHADER = "shaders/color_interp.frag"

    def __init__(self, top_width=0.3, bottom_width=0.6, height=0.5, vert_shader=None, frag_shader=None):
        self.top_width = top_width
        self.bottom_width = bottom_width
        self.height = height
        super().__init__(vert_shader, frag_shader)
        self._generate_geometry()

    def _generate_geometry(self):
        tw, bw, h = self.top_width / 2, self.bottom_width / 2, self.height / 2
        self.vertices = np.array([
            [-tw, h, 0.0],
            [tw, h, 0.0],
            [-bw, -h, 0.0],
            [bw, -h, 0.0]
        ], dtype=np.float32)

        self.colors = np.array([
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, 0.0, 1.0],
            [1.0, 1.0, 0.0]
        ], dtype=np.float32)

        self.normals = np.array([
            [0.0, 0.0, 1.0],
            [0.0, 0.0, 1.0],
            [0.0, 0.0, 1.0],
            [0.0, 0.0, 1.0]
        ], dtype=np.float32)

        self.indices = np.array([0, 1, 2, 1, 3, 2], dtype=np.int32)


class Star(Geometry):
    VERTEX_SHADER = "shaders/color_interp.vert"
    FRAGMENT_SHADER = "shaders/color_interp.frag"

    def __init__(self, outer_radius=0.5, inner_radius=0.2, points=5, vert_shader=None, frag_shader=None):
        self.outer_radius = outer_radius
        self.inner_radius = inner_radius
        self.points = points
        super().__init__(vert_shader, frag_shader)
        self._generate_geometry()

    def _generate_geometry(self):
        n = self.points * 2
        vertices = []
        colors = []
        normals = []

        vertices.append([0.0, 0.0, 0.0])
        colors.append([0.5, 0.5, 0.5])
        normals.append([0.0, 0.0, 1.0])

        for i in range(n):
            angle = math.pi * i / n - math.pi / 2
            radius = self.outer_radius if i % 2 == 0 else self.inner_radius
            x = radius * math.cos(angle)
            y = radius * math.sin(angle)
            vertices.append([x, y, 0.0])
            colors.append([math.cos(angle), math.sin(angle), 0.5])
            normals.append([0.0, 0.0, 1.0])

        self.vertices = np.array(vertices, dtype=np.float32)
        self.colors = np.array(colors, dtype=np.float32)
        self.normals = np.array(normals, dtype=np.float32)

        indices = []
        for i in range(1, n + 1):
            indices.extend([0, i, i % n + 1])
        self.indices = np.array(indices, dtype=np.int32)


class Arrow(Geometry):
    VERTEX_SHADER = "shaders/color_interp.vert"
    FRAGMENT_SHADER = "shaders/color_interp.frag"

    def __init__(self, length=0.8, width=0.2, head_ratio=0.3, vert_shader=None, frag_shader=None):
        self.length = length
        self.width = width
        self.head_ratio = head_ratio
        super().__init__(vert_shader, frag_shader)
        self._generate_geometry()

    def _generate_geometry(self):
        l, w, hr = self.length, self.width, self.head_ratio
        shaft_end = l * (1 - hr)

        self.vertices = np.array([
            [-w/2, -l/2, 0.0],
            [w/2, -l/2, 0.0],
            [w/2, -shaft_end, 0.0],
            [w/2 + hr * 0.3, -shaft_end, 0.0],
            [0.0, l/2, 0.0],
            [-w/2 - hr * 0.3, -shaft_end, 0.0],
            [-w/2, -shaft_end, 0.0]
        ], dtype=np.float32)

        self.colors = np.array([
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, 0.0, 1.0],
            [1.0, 1.0, 0.0],
            [0.0, 1.0, 1.0],
            [1.0, 0.0, 1.0],
            [0.5, 0.5, 0.5]
        ], dtype=np.float32)

        self.normals = np.array([
            [0.0, 0.0, 1.0],
            [0.0, 0.0, 1.0],
            [0.0, 0.0, 1.0],
            [0.0, 0.0, 1.0],
            [0.0, 0.0, 1.0],
            [0.0, 0.0, 1.0],
            [0.0, 0.0, 1.0]
        ], dtype=np.float32)

        self.indices = np.array([0, 1, 2, 0, 2, 6, 6, 2, 3, 6, 3, 4, 4, 3, 5, 5, 3, 2, 5, 2, 6], dtype=np.int32)
