import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
from geometry.shapes_2d import *
from geometry.shapes_3d import *
from geometry.model_loader import load_model


class Scene:
    def __init__(self):
        self.objects = []
        self.selected_index = 0
        self.wireframe_mode = False

    def add(self, obj):
        self.objects.append(obj)
        return len(self.objects) - 1

    def remove(self, index):
        if 0 <= index < len(self.objects):
            self.objects.pop(index)
            if self.selected_index >= len(self.objects):
                self.selected_index = max(0, len(self.objects) - 1)

    def clear(self):
        self.objects.clear()
        self.selected_index = 0

    def get_selected(self):
        if 0 <= self.selected_index < len(self.objects):
            return self.objects[self.selected_index]
        return None

    def select_next(self):
        if self.objects:
            self.selected_index = (self.selected_index + 1) % len(self.objects)

    def select_prev(self):
        if self.objects:
            self.selected_index = (self.selected_index - 1) % len(self.objects)

    def draw(self, projection, view, custom_shader=None):
        for obj in self.objects:
            obj.draw(projection, view, None, custom_shader)

    def toggle_wireframe(self):
        self.wireframe_mode = not self.wireframe_mode
        import OpenGL.GL as GL
        if self.wireframe_mode:
            GL.glPolygonMode(GL.GL_FRONT_AND_BACK, GL.GL_LINE)
        else:
            GL.glPolygonMode(GL.GL_FRONT_AND_BACK, GL.GL_FILL)


class SceneBuilder:
    SHAPES_2D = {
        'triangle': Triangle,
        'rectangle': Rectangle,
        'pentagon': Pentagon,
        'hexagon': Hexagon,
        'circle': Circle,
        'ellipse': Ellipse,
        'trapezoid': Trapezoid,
        'star': Star,
        'arrow': Arrow,
    }

    SHAPES_3D = {
        'cube': Cube,
        'sphere_sub': SphereSubdivision,
        'sphere_uv': UVSphere,
        'sphere_latlong': LatLongSphere,
        'cylinder': Cylinder,
        'cone': Cone,
        'truncated_cone': TruncatedCone,
        'tetrahedron': Tetrahedron,
        'torus': Torus,
        'prism': Prism,
        'parametric': ParametricSurface,
    }

    @staticmethod
    def create_2d(shape_name, **kwargs):
        if shape_name.lower() in SceneBuilder.SHAPES_2D:
            return SceneBuilder.SHAPES_2D[shape_name.lower()](**kwargs)
        return None

    @staticmethod
    def create_3d(shape_name, **kwargs):
        if shape_name.lower() in SceneBuilder.SHAPES_3D:
            return SceneBuilder.SHAPES_3D[shape_name.lower()](**kwargs)
        return None

    @staticmethod
    def create_parametric(func_name, **kwargs):
        funcs = {
            'himmelblau': himmelblau,
            'rosenbrock': rosenbrock,
            'booth': booth,
            'quadratic': quadratic,
        }
        if func_name.lower() in funcs:
            return ParametricSurface(func=funcs[func_name.lower()], **kwargs)
        return None

    @staticmethod
    def load_model(filepath, **kwargs):
        """Load a 3D model from OBJ or PLY file."""
        return load_model(filepath, **kwargs)
