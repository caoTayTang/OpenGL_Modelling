import OpenGL.GL as GL
import glfw
import numpy as np
from itertools import cycle
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from libs.transform import Trackball
from libs.shader import Shader
from scene import Scene, SceneBuilder
from geometry.shapes_2d import *
from geometry.shapes_3d import *
from libs.lighting import LightingManager, Light, Material


class Viewer:
    def __init__(self, width=800, height=600):
        self.width = width
        self.height = height
        self.fill_modes = cycle([GL.GL_FILL, GL.GL_LINE, GL.GL_POINT])
        
        glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
        glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
        glfw.window_hint(glfw.OPENGL_FORWARD_COMPAT, GL.GL_TRUE)
        glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
        glfw.window_hint(glfw.RESIZABLE, True)
        self.win = glfw.create_window(width, height, 'Computer Graphics - Assignment 1.1', None, None)
        
        glfw.make_context_current(self.win)
        
        self.trackball = Trackball(distance=3.0)
        self.mouse = (0, 0)
        
        glfw.set_key_callback(self.win, self.on_key)
        glfw.set_cursor_pos_callback(self.win, self.on_mouse_move)
        glfw.set_scroll_callback(self.win, self.on_scroll)
        glfw.set_window_size_callback(self.win, self.on_window_size)
        
        print('OpenGL', GL.glGetString(GL.GL_VERSION).decode() + ', GLSL',
              GL.glGetString(GL.GL_SHADING_LANGUAGE_VERSION).decode() +
              ', Renderer', GL.glGetString(GL.GL_RENDERER).decode())
        
        GL.glClearColor(0.1, 0.1, 0.1, 1.0)
        GL.glEnable(GL.GL_DEPTH_TEST)
        GL.glDepthFunc(GL.GL_LESS)
        
        self.depth_shader = Shader("shaders/depth.vert", "shaders/depth.frag")
        
        # Fullscreen quad shader for depth display
        self.quad_shader = self._create_quad_shader()
        self.quad_vao = self._create_quad_vao()
        
        # Load all shading mode shaders
        self.shaders = {
            'flat': Shader("shaders/flat.vert", "shaders/flat.frag"),
            'color_interp': Shader("shaders/color_interp.vert", "shaders/color_interp.frag"),
            'phong': Shader("shaders/phong.vert", "shaders/phong.frag"),
            'gouraud': Shader("shaders/gouraud.vert", "shaders/gouraud.frag"),
            'texture': Shader("shaders/phong_texture.vert", "shaders/phong_texture.frag"),
        }
        
        self.scene = Scene()
        self.current_camera = 0
        self.cameras = self._create_cameras()
        
        self.lights = [
            Light(diffuse=(0.9, 0.4, 0.6), specular=(0.9, 0.4, 0.6), ambient=(0.2, 0.2, 0.2), position=(0, 0.5, 0.9)),
            Light(diffuse=(0.4, 0.4, 0.9), specular=(0.4, 0.4, 0.9), ambient=(0.1, 0.1, 0.1), position=(0.5, 0.5, -0.5)),
        ]
        self.light_enabled = [True, True]
        self.display_mode = 0
        self.near = 0.1
        self.far = 100.0
        
        # Shading modes: A-F keys
        self.shader_mode = 0
        self.shader_modes = ['flat', 'color_interp', 'phong', 'gouraud', 'texture']
        
        self._add_default_shapes()

    def _create_cameras(self):
        cameras = []
        for i in range(3):
            tb = Trackball(distance=3.0 + i * 0.5)
            if i == 0:
                tb = Trackball(yaw=0, pitch=0, distance=3.0)
            elif i == 1:
                tb = Trackball(yaw=45, pitch=30, distance=4.0)
            elif i == 2:
                tb = Trackball(yaw=-45, pitch=-20, distance=5.0)
            cameras.append(tb)
        return cameras

    def _add_default_shapes(self):
        cube = Cube(size=0.5)
        cube.setup()
        cube.set_position(0, 0, 0)
        self.scene.add(cube)
        
        sphere = UVSphere(radius=0.4)
        sphere.setup()
        sphere.set_position(1.5, 0, 0)
        self.scene.add(sphere)

    def run(self):
        while not glfw.window_should_close(self.win):
            GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)
            
            win_size = glfw.get_window_size(self.win)
            cam = self.cameras[self.current_camera]
            view = cam.view_matrix()
            projection = cam.projection_matrix(win_size)
            
            if self.display_mode == 1:
                # Render depth map using depth shader directly
                GL.glUseProgram(self.depth_shader.render_idx)
                from libs.buffer import UManager
                uma = UManager(self.depth_shader)
                
                # Pass projection and near/far
                uma.upload_uniform_matrix4fv(projection, 'projection', True)
                uma.upload_uniform_scalar1f(cam.near, 'near')
                uma.upload_uniform_scalar1f(cam.far, 'far')
                
                # Draw all objects with depth shader
                for obj in self.scene.objects:
                    GL.glUseProgram(self.depth_shader.render_idx)
                    uma.upload_uniform_matrix4fv(view @ obj.model_matrix, 'modelview', True)
                    obj.vao.activate()
                    if obj.indices is not None:
                        GL.glDrawElements(GL.GL_TRIANGLES, obj.indices.shape[0], GL.GL_UNSIGNED_INT, None)
                    elif obj.vertices is not None:
                        GL.glDrawArrays(GL.GL_TRIANGLES, 0, obj.vertices.shape[0])
            else:
                # Render with selected shading mode
                self._setup_lighting()
                current_shader = self.shaders[self.shader_modes[self.shader_mode]]
                self.scene.draw(projection, view, current_shader)
            
            self._render_ui()
            
            glfw.swap_buffers(self.win)
            glfw.poll_events()
            
            self._update_title()

    def _setup_lighting(self):
        # Fixed-function lighting is deprecated in Core Profile
        # Lighting is handled in the shaders (phong, gouraud)
        pass

    def _render_ui(self):
        pass

    def _update_title(self):
        obj_count = len(self.scene.objects)
        light_status = '|'.join(['ON' if e else 'OFF' for e in self.light_enabled])
        title = f'CG Assignment 1.1 | Objects: {obj_count} | Cam: {self.current_camera+1} | Lights: [{light_status}]'
        glfw.set_window_title(self.win, title)

    def _create_quad_shader(self):
        vert_src = """#version 330 core
        layout(location = 0) in vec2 aPos;
        out vec2 texCoord;
        void main() {
            gl_Position = vec4(aPos, 0.0, 1.0);
            texCoord = aPos * 0.5 + 0.5;
        }"""
        frag_src = """#version 330 core
        in vec2 texCoord;
        out vec4 fragColor;
        uniform sampler2D depthTexture;
        void main() {
            float d = texture(depthTexture, texCoord).r;
            fragColor = vec4(vec3(d), 1.0);
        }"""
        return Shader(vert_src, frag_src)

    def _create_quad_vao(self):
        vao = GL.glGenVertexArrays(1)
        GL.glBindVertexArray(vao)
        vbo = GL.glGenBuffers(1)
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, vbo)
        vertices = np.array([-1,-1, 1,-1, -1,1, 1,1], dtype=np.float32)
        GL.glBufferData(GL.GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL.GL_STATIC_DRAW)
        GL.glEnableVertexAttribArray(0)
        GL.glVertexAttribPointer(0, 2, GL.GL_FLOAT, GL.GL_FALSE, 0, None)
        GL.glBindVertexArray(0)
        return vao

    def _render_depth_overlay(self, depth_array, screen_width, screen_height):
        """Render depth buffer as grayscale on top of existing render"""
        from libs.buffer import UManager
        
        height, width = depth_array.shape
        
        # Create texture from depth
        tex_id = GL.glGenTextures(1)
        GL.glBindTexture(GL.GL_TEXTURE_2D, tex_id)
        GL.glTexImage2D(GL.GL_TEXTURE_2D, 0, GL.GL_R8, width, height, 0, GL.GL_RED, GL.GL_UNSIGNED_BYTE, depth_array)
        GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER, GL.GL_NEAREST)
        GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MAG_FILTER, GL.GL_NEAREST)
        
        # Render fullscreen quad without changing viewport
        GL.glDisable(GL.GL_DEPTH_TEST)
        GL.glUseProgram(self.quad_shader.render_idx)
        
        GL.glActiveTexture(GL.GL_TEXTURE0)
        GL.glBindTexture(GL.GL_TEXTURE_2D, tex_id)
        uma = UManager(self.quad_shader)
        uma.upload_uniform_scalar1i(0, 'depthTexture')
        
        GL.glBindVertexArray(self.quad_vao)
        GL.glDrawArrays(GL.GL_TRIANGLE_STRIP, 0, 4)
        
        GL.glDeleteTextures([tex_id])
        GL.glEnable(GL.GL_DEPTH_TEST)

    def on_key(self, _win, key, _scancode, action, _mods):
        if action == glfw.PRESS or action == glfw.REPEAT:
            if key == glfw.KEY_ESCAPE or key == glfw.KEY_Q:
                glfw.set_window_should_close(self.win, True)
            
            elif key == glfw.KEY_W:
                GL.glPolygonMode(GL.GL_FRONT_AND_BACK, next(self.fill_modes))
                print("Wireframe mode toggled")
            
            elif key == glfw.KEY_C:
                self.current_camera = (self.current_camera + 1) % len(self.cameras)
                print(f"Switched to camera {self.current_camera + 1}")
            
            elif key == glfw.KEY_0:
                self._add_shape('cube')
                print(f"Added cube. Total objects: {len(self.scene.objects)}")
            
            elif key == glfw.KEY_1:
                self._replace_shape('cube')
                print(f"Shape replaced with cube")
            elif key == glfw.KEY_2:
                self._replace_shape('sphere_uv')
                print(f"Shape replaced with sphere_uv")
            elif key == glfw.KEY_3:
                self._replace_shape('cylinder')
                print(f"Shape replaced with cylinder")
            elif key == glfw.KEY_4:
                self._replace_shape('cone')
            elif key == glfw.KEY_5:
                self._replace_shape('torus')
            elif key == glfw.KEY_6:
                self._replace_shape('prism')
            elif key == glfw.KEY_7:
                self._replace_shape('tetrahedron')
            elif key == glfw.KEY_8:
                self._replace_shape('truncated_cone')
            elif key == glfw.KEY_9:
                self._replace_shape('sphere_sub')
            
            elif key == glfw.KEY_T:
                self.scene.select_next()
                print(f"Selected object: {self.scene.selected_index}")
            elif key == glfw.KEY_Y:
                self.scene.select_prev()
                print(f"Selected object: {self.scene.selected_index}")
            
            elif key == glfw.KEY_LEFT:
                self._move_selected(-0.1, 0, 0)
                print("Moved left")
            elif key == glfw.KEY_RIGHT:
                self._move_selected(0.1, 0, 0)
                print("Moved right")
            elif key == glfw.KEY_UP:
                self._move_selected(0, 0.1, 0)
                print("Moved up")
            elif key == glfw.KEY_DOWN:
                self._move_selected(0, -0.1, 0)
                print("Moved down")
            elif key == glfw.KEY_PAGE_UP:
                self._move_selected(0, 0, 0.1)
                print("Moved forward")
            elif key == glfw.KEY_PAGE_DOWN:
                self._move_selected(0, 0, -0.1)
                print("Moved backward")
            
            elif key == glfw.KEY_D:
                self.display_mode = (self.display_mode + 1) % 2
                mode_name = "RGB" if self.display_mode == 0 else "Depth Map"
                print(f"Display mode: {mode_name}")
            
            # Shading mode - cycle with [ and ]
            elif key == glfw.KEY_LEFT_BRACKET:
                self.shader_mode = (self.shader_mode - 1) % len(self.shader_modes)
                print(f"Shading: {self.shader_modes[self.shader_mode]}")
            elif key == glfw.KEY_RIGHT_BRACKET:
                self.shader_mode = (self.shader_mode + 1) % len(self.shader_modes)
                print(f"Shading: {self.shader_modes[self.shader_mode]}")
            
            # Light toggle (for future shader support)
            elif key == glfw.KEY_L:
                self.light_enabled[0] = not self.light_enabled[0]
                status = "ON" if self.light_enabled[0] else "OFF"
                print(f"Light 1: {status}")
            elif key == glfw.KEY_K:
                self.light_enabled[1] = not self.light_enabled[1]
                status = "ON" if self.light_enabled[1] else "OFF"
                print(f"Light 2: {status}")
            
            elif key == glfw.KEY_R:
                self._reset_scene()
                print("Scene reset")

    def _add_shape(self, shape_name):
        obj = SceneBuilder.create_3d(shape_name)
        if obj:
            obj.setup()
            offset = len(self.scene.objects) * 0.8
            obj.set_position(offset, 0, 0)
            self.scene.add(obj)

    def _replace_shape(self, shape_name):
        obj = SceneBuilder.create_3d(shape_name)
        if obj:
            obj.setup()
            if self.scene.objects:
                self.scene.objects[self.scene.selected_index] = obj
            else:
                self.scene.add(obj)

    def _move_selected(self, dx, dy, dz):
        obj = self.scene.get_selected()
        if obj:
            obj.position[0] += dx
            obj.position[1] += dy
            obj.position[2] += dz
            obj._update_model_matrix()

    def _reset_scene(self):
        self.scene.clear()
        self._add_default_shapes()

    def on_mouse_move(self, win, xpos, ypos):
        old = self.mouse
        self.mouse = (xpos, glfw.get_window_size(win)[1] - ypos)
        if glfw.get_mouse_button(win, glfw.MOUSE_BUTTON_LEFT):
            self.cameras[self.current_camera].drag(old, self.mouse, glfw.get_window_size(win))
        if glfw.get_mouse_button(win, glfw.MOUSE_BUTTON_RIGHT):
            self.cameras[self.current_camera].pan(old, self.mouse)

    def on_scroll(self, win, _deltax, deltay):
        self.cameras[self.current_camera].zoom(deltay, glfw.get_window_size(win)[1])

    def on_window_size(self, win, width, height):
        GL.glViewport(0, 0, width, height)


def main():
    viewer = Viewer()
    viewer.run()


if __name__ == '__main__':
    glfw.init()
    main()
    glfw.terminate()
