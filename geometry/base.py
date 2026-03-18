import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from libs.shader import *
from libs.buffer import *
import numpy as np
import OpenGL.GL as GL


class Geometry:
    VERTEX_SHADER = "shaders/basic.vert"
    FRAGMENT_SHADER = "shaders/basic.frag"

    def __init__(self, vert_shader=None, frag_shader=None):
        self.vert_shader = vert_shader or self.VERTEX_SHADER
        self.frag_shader = frag_shader or self.FRAGMENT_SHADER

        self.vertices = None
        self.colors = None
        self.normals = None
        self.texcoords = None
        self.indices = None

        self.vao = VAO()
        self.shader = Shader(self.vert_shader, self.frag_shader)
        self.uma = UManager(self.shader)

        self.model_matrix = np.identity(4, 'f')
        self.position = np.array([0.0, 0.0, 0.0], dtype=np.float32)
        self.rotation = np.array([0.0, 0.0, 0.0], dtype=np.float32)
        self.scale = np.array([1.0, 1.0, 1.0], dtype=np.float32)

    def setup(self):
        if self.vertices is not None:
            self.vao.add_vbo(0, self.vertices, ncomponents=3)

        if self.colors is not None:
            self.vao.add_vbo(1, self.colors, ncomponents=3)

        if self.normals is not None:
            self.vao.add_vbo(2, self.normals, ncomponents=3)

        if self.texcoords is not None:
            self.vao.add_vbo(3, self.texcoords, ncomponents=2)

        if self.indices is not None:
            self.vao.add_ebo(self.indices)

        return self

    def draw(self, projection, view, model=None, custom_shader=None):
        model_mat = self.model_matrix
        
        if custom_shader:
            GL.glUseProgram(custom_shader.render_idx)
            uma = custom_shader.uma if hasattr(custom_shader, 'uma') else None
            if uma is None:
                from libs.buffer import UManager
                uma = UManager(custom_shader)
            uma.upload_uniform_matrix4fv(projection, 'projection', True)
            uma.upload_uniform_matrix4fv(view @ model_mat, 'modelview', True)
            uma.upload_uniform_matrix4fv(model_mat, 'model', True)
        else:
            GL.glUseProgram(self.shader.render_idx)
            self.uma.upload_uniform_matrix4fv(projection, 'projection', True)
            self.uma.upload_uniform_matrix4fv(view @ model_mat, 'modelview', True)

        self.vao.activate()

        indices = self.indices
        if indices is not None:
            GL.glDrawElements(GL.GL_TRIANGLES, indices.shape[0], GL.GL_UNSIGNED_INT, None)
        elif self.vertices is not None:
            GL.glDrawArrays(GL.GL_TRIANGLES, 0, self.vertices.shape[0])

    def set_position(self, x, y, z):
        self.position = np.array([x, y, z], dtype=np.float32)
        self._update_model_matrix()

    def set_rotation(self, x, y, z):
        self.rotation = np.array([x, y, z], dtype=np.float32)
        self._update_model_matrix()

    def set_scale(self, x, y, z):
        self.scale = np.array([x, y, z], dtype=np.float32)
        self._update_model_matrix()

    def _update_model_matrix(self):
        from libs import transform as T
        self.model_matrix = T.translate(*self.position)
        self.model_matrix = self.model_matrix @ T.rotate(axis=(1, 0, 0), angle=self.rotation[0])
        self.model_matrix = self.model_matrix @ T.rotate(axis=(0, 1, 0), angle=self.rotation[1])
        self.model_matrix = self.model_matrix @ T.rotate(axis=(0, 0, 1), angle=self.rotation[2])
        self.model_matrix = self.model_matrix @ T.scale(*self.scale)

    def key_handler(self, key):
        pass
