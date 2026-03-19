import OpenGL.GL as GL
import glfw
import numpy as np
from itertools import cycle
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from libs.transform import Trackball
from libs.shader import Shader
from libs.imgui_renderer import ImGuiRenderer
from scene import Scene, SceneBuilder
from geometry.shapes_2d import *
from geometry.shapes_3d import *
from libs.lighting import LightingManager, Light, Material
from libs.buffer import UManager
from imgui_bundle import imgui


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
        self.scroll_y = 0  # For scroll zoom polling
        self._is_dragging = False  # Track if mouse is being dragged

        # Track key states to detect single press (not held)
        self._key_state = {}  # key -> True if was held last frame
        
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
        self._pending_model_path = None
        
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

        # Model path input mode
        self.input_mode = False
        self.input_string = ""

        # Initialize ImGui renderer
        self.imgui_renderer = ImGuiRenderer(self.win)

        # Set ImGui display size and framebuffer scale for HiDPI
        io = imgui.get_io()
        io.display_size = (width, height)
        fb_size = glfw.get_framebuffer_size(self.win)
        io.display_framebuffer_scale = (fb_size[0] / width, fb_size[1] / height)

        # Start with empty scene (no default objects)

        # Setup window callbacks (scroll handled by renderer, we poll for camera)
        glfw.set_window_size_callback(self.win, self.on_window_size)
        glfw.set_scroll_callback(self.win, self.on_scroll)

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
            # Process ImGui inputs FIRST (updates display_size, etc.)
            self.imgui_renderer.impl.process_inputs()

            # Get sizes AFTER processing inputs
            win_size = glfw.get_window_size(self.win)
            fb_size = glfw.get_framebuffer_size(self.win)

            # Calculate viewport area (between left and right panels)
            left_panel_w = 180
            right_panel_w = min(320, win_size[0] // 3)
            top_bar_h = 32
            bottom_bar_h = 32

            # Calculate viewport in window coordinates
            vp_x_win = left_panel_w
            vp_y_win = bottom_bar_h
            vp_w_win = win_size[0] - left_panel_w - right_panel_w
            vp_h_win = win_size[1] - top_bar_h - bottom_bar_h

            # Scale to framebuffer coordinates (HiDPI/Retina)
            scale_x = fb_size[0] / win_size[0] if win_size[0] > 0 else 1
            scale_y = fb_size[1] / win_size[1] if win_size[1] > 0 else 1
            vp_x = int(vp_x_win * scale_x)
            vp_y = int(vp_y_win * scale_y)
            vp_w = int(vp_w_win * scale_x)
            vp_h = int(vp_h_win * scale_y)

            # Update ImGui display size and framebuffer scale for HiDPI
            io = imgui.get_io()
            io.display_size = (win_size[0], win_size[1])
            io.display_framebuffer_scale = (fb_size[0] / win_size[0] if win_size[0] > 0 else 1,
                                             fb_size[1] / win_size[1] if win_size[1] > 0 else 1)

            # Set viewport to center area (no scissor needed - viewport clips)
            GL.glViewport(vp_x, vp_y, vp_w, vp_h)
            GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)

            cam = self.cameras[self.current_camera]
            view = cam.view_matrix()
            # Use viewport dimensions for correct aspect ratio
            projection = cam.projection_matrix((vp_w_win, vp_h_win))

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
                current_shader = self.shaders[self.shader_modes[self.shader_mode]]
                self._setup_lighting(current_shader)
                self.scene.draw(projection, view, current_shader)

            # Reset viewport to full window for ImGui rendering
            GL.glViewport(0, 0, fb_size[0], fb_size[1])

            # Render ImGui UI (after scene, before swap)
            imgui.new_frame()
            self._render_ui()
            imgui.render()
            self.imgui_renderer.render(imgui.get_draw_data())

            glfw.swap_buffers(self.win)
            glfw.poll_events()

            # Handle pending model load from UI input
            if self._pending_model_path:
                path = self._pending_model_path
                self._pending_model_path = None
                # Validate extension
                if path.lower().endswith('.obj') or path.lower().endswith('.ply'):
                    if os.path.exists(path):
                        obj = SceneBuilder.load_model(path)
                        if obj:
                            obj.setup()
                            offset = len(self.scene.objects) * 0.8
                            obj.set_position(offset, 0, 0)
                            self.scene.add(obj)
                            print(f"Loaded: {os.path.basename(path)}")
                        else:
                            print(f"Failed to load: {path}")
                    else:
                        print(f"File not found: {path}")
                else:
                    print(f"Unsupported format. Use .obj or .ply")

            # Handle camera input via polling (after events are processed)
            self._handle_camera_input()

            self._update_title()

    def _setup_lighting(self, shader):
        """Setup lighting uniforms for the given shader."""
        shader_name = self.shader_modes[self.shader_mode]

        # Only setup lighting for shaders that support it
        if shader_name not in ['phong', 'gouraud', 'texture']:
            return

        GL.glUseProgram(shader.render_idx)
        uma = UManager(shader)

        # Compute combined light from all enabled lights
        combined_diffuse = np.array([0.0, 0.0, 0.0], dtype=np.float32)
        combined_specular = np.array([0.0, 0.0, 0.0], dtype=np.float32)
        combined_ambient = np.array([0.0, 0.0, 0.0], dtype=np.float32)
        combined_position = np.array([0.0, 0.0, 0.0], dtype=np.float32)

        for i, (light, enabled) in enumerate(zip(self.lights, self.light_enabled)):
            if enabled:
                combined_diffuse += light.diffuse
                combined_specular += light.specular
                combined_ambient += light.ambient
                combined_position += light.position

        # Default material (will be same for all objects for now)
        material = Material(
            diffuse=(0.6, 0.4, 0.7),
            specular=(0.6, 0.4, 0.7),
            ambient=(0.6, 0.4, 0.7),
            shininess=100.0
        )

        # Create I_light matrix: [diffuse, specular, ambient]
        I_light = np.array([
            combined_diffuse,
            combined_specular,
            combined_ambient
        ], dtype=np.float32)

        # Create K_materials matrix: [diffuse, specular, ambient]
        K_materials = np.array([
            material.diffuse,
            material.specular,
            material.ambient
        ], dtype=np.float32)

        # Upload uniforms
        uma.upload_uniform_matrix3fv(I_light, 'I_light', False)
        uma.upload_uniform_vector3fv(combined_position, 'light_pos')
        uma.upload_uniform_matrix3fv(K_materials, 'K_materials', False)
        uma.upload_uniform_scalar1f(material.shininess, 'shininess')

        # For texture shader, also set mode
        if shader_name == 'texture':
            uma.upload_uniform_scalar1i(1, 'mode')
            uma.upload_uniform_scalar1i(0, 'has_texture')

    def _render_ui(self):
        """Render Blender-style compact UI panels."""
        win_w, win_h = glfw.get_window_size(self.win)

        # Compact panel dimensions
        top_bar_h = 32
        left_panel_w = 180
        right_panel_w = min(320, win_w // 3)  # Can take up to 1/3 of screen
        bottom_bar_h = 32

        # === Top Toolbar (Blender menu style) ===
        imgui.set_next_window_pos(imgui.ImVec2(0, 0), imgui.Cond_.always)
        imgui.set_next_window_size(imgui.ImVec2(win_w, top_bar_h), imgui.Cond_.always)

        flags = (imgui.WindowFlags_.no_title_bar | imgui.WindowFlags_.no_resize |
                 imgui.WindowFlags_.no_move | imgui.WindowFlags_.no_scrollbar)
        imgui.begin("TopBar", flags=flags)

        # Set cursor to start of window with small offset
        imgui.set_cursor_pos(imgui.ImVec2(4, 4))

        imgui.same_line(spacing=15)

        imgui.same_line(spacing=15)

        # Shader dropdown (outside menu bar)
        imgui.text("Shader:")
        imgui.same_line()
        result = imgui.combo("##shader", self.shader_mode, self.shader_modes)
        # combo returns (bool,) or just bool depending on version
        if hasattr(result, '__iter__'):
            changed = result[0]
            if changed:
                self.shader_mode = result[1]
        else:
            changed = result
        if changed:
            print(f"Shading: {self.shader_modes[self.shader_mode]}")

        imgui.same_line(spacing=10)

        # Wireframe mode button
        if imgui.button("Fill"):
            GL.glPolygonMode(GL.GL_FRONT_AND_BACK, GL.GL_FILL)
        imgui.same_line()
        if imgui.button("Wire"):
            GL.glPolygonMode(GL.GL_FRONT_AND_BACK, GL.GL_LINE)
        imgui.same_line()
        if imgui.button("Point"):
            GL.glPolygonMode(GL.GL_FRONT_AND_BACK, GL.GL_POINT)

        imgui.same_line(spacing=10)

        # Lighting toggles
        imgui.text("Light:")
        imgui.same_line()
        changed, self.light_enabled[0] = imgui.checkbox("L1##1", self.light_enabled[0])
        imgui.same_line()
        changed, self.light_enabled[1] = imgui.checkbox("L2##2", self.light_enabled[1])

        imgui.end()

        # === Left Sidebar (Objects) ===
        imgui.set_next_window_pos(imgui.ImVec2(0, top_bar_h), imgui.Cond_.always)
        imgui.set_next_window_size(imgui.ImVec2(left_panel_w, win_h - top_bar_h - bottom_bar_h), imgui.Cond_.always)

        flags = (imgui.WindowFlags_.no_title_bar | imgui.WindowFlags_.no_resize |
                 imgui.WindowFlags_.no_move)
        imgui.begin("Objects", flags=flags)

        imgui.text(f"Objects ({len(self.scene.objects)})")
        imgui.separator()

        # Scrollable object list
        for i, obj in enumerate(self.scene.objects):
            is_selected = (i == self.scene.selected_index)
            label = f"{obj.__class__.__name__}##{i}"

            if imgui.selectable(label, is_selected)[0]:
                self.scene.selected_index = i

        imgui.separator()

        if imgui.button("Delete"):
            if self.scene.objects:
                self.scene.remove(self.scene.selected_index)

        imgui.end()

        # === Right Sidebar (Properties & Help) ===
        props_x = win_w - right_panel_w

        imgui.set_next_window_pos(imgui.ImVec2(props_x, top_bar_h), imgui.Cond_.always)
        imgui.set_next_window_size(imgui.ImVec2(right_panel_w, win_h - top_bar_h - bottom_bar_h), imgui.Cond_.always)

        flags = (imgui.WindowFlags_.no_title_bar | imgui.WindowFlags_.no_resize |
                 imgui.WindowFlags_.no_move)
        imgui.begin("Properties", flags=flags)

        # === Object Properties ===
        imgui.text("Object")
        imgui.separator()

        selected_obj = self.scene.get_selected()
        if selected_obj:
            imgui.text(f"Type: {selected_obj.__class__.__name__}")
            pos = selected_obj.position
            imgui.text(f"Pos: ({pos[0]:.2f}, {pos[1]:.2f}, {pos[2]:.2f})")
            imgui.separator()
        else:
            imgui.text_disabled("No object selected")
            imgui.separator()

        # === Camera Controls ===
        imgui.text("Camera")
        imgui.separator()
        imgui.text(f"View: {self.current_camera + 1}/3")
        if imgui.button("Next View"):
            self.current_camera = (self.current_camera + 1) % len(self.cameras)
            print(f"Switched to camera {self.current_camera + 1}")

        imgui.separator()

        # === Model Loading ===
        imgui.text("Model")
        imgui.separator()
        # Input field for model path
        changed, self.input_string = imgui.input_text("Path##model", self.input_string, 256)
        imgui.same_line()
        if imgui.button("Load##model"):
            if self.input_string.strip():
                # Store the path and trigger load
                self._pending_model_path = self.input_string.strip()
        if imgui.is_item_hovered():
            imgui.set_tooltip("Enter OBJ/PLY file path")

        imgui.separator()

        # === Keyboard Shortcuts ===
        imgui.text("Shortcuts")
        imgui.separator()
        imgui.text_disabled("Navigation:")
        imgui.text("  L-Drag: Rotate")
        imgui.text("  R-Drag: Pan")
        imgui.text("  Scroll: Zoom")
        imgui.separator()
        imgui.text_disabled("Selection:")
        imgui.text("  T/Y: Next/Prev")
        imgui.text("  Arrows: Move")
        imgui.text("  X/Del: Delete")
        imgui.separator()
        imgui.text_disabled("View:")
        imgui.text("  W: Wireframe")
        imgui.text("  C: Cycle Camera")
        imgui.text("  [: Prev Shader")
        imgui.text("  ]: Next Shader")
        imgui.text("  R: Reset Scene")
        imgui.text("  D: Depth Mode")
        imgui.text("  O: Load Model")

        imgui.end()

        # === Bottom Status Bar ===
        imgui.set_next_window_pos(imgui.ImVec2(0, win_h - bottom_bar_h), imgui.Cond_.always)
        imgui.set_next_window_size(imgui.ImVec2(win_w, bottom_bar_h), imgui.Cond_.always)

        flags = (imgui.WindowFlags_.no_title_bar | imgui.WindowFlags_.no_resize |
                 imgui.WindowFlags_.no_move | imgui.WindowFlags_.no_scrollbar)
        imgui.begin("StatusBar", flags=flags)

        imgui.text(f"Objects: {len(self.scene.objects)} | Shader: {self.shader_modes[self.shader_mode]} | L1:{'ON' if self.light_enabled[0] else 'OFF'} | L2:{'ON' if self.light_enabled[1] else 'OFF'} | Cam: {self.current_camera+1}")

        imgui.end()

    def _update_title(self):
        obj_count = len(self.scene.objects)
        light_status = '|'.join(['ON' if e else 'OFF' for e in self.light_enabled])
        if self.input_mode:
            title = f'CG Assignment 1.1 | Enter path: {self.input_string}_'
        else:
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

    def on_key(self, _win, key, scancode, action, mods):
        # Key handling is now done via polling in _handle_camera_input
        # This callback is kept for potential future use but does nothing now
        pass

    def on_char(self, _win, char):
        """Handle character input for model path."""
        if self.input_mode:
            self.input_string += chr(char)

    def on_scroll(self, win, deltax, deltay):
        """Handle scroll for camera zoom."""
        io = imgui.get_io()
        if not io.want_capture_mouse:
            self.cameras[self.current_camera].zoom(deltay, glfw.get_window_size(win)[1])

    def on_window_size(self, win, width, height):
        fb_size = glfw.get_framebuffer_size(win)
        GL.glViewport(0, 0, fb_size[0], fb_size[1])
        io = imgui.get_io()
        io.display_size = (width, height)
        io.display_framebuffer_scale = (fb_size[0] / width, fb_size[1] / height)

    def _load_model_from_input_path(self):
        """Load model from user-typed path."""
        path = self.input_string.strip()
        if not path:
            print("No path entered")
            return

        # Validate extension
        if not (path.lower().endswith('.obj') or path.lower().endswith('.ply')):
            print(f"Unsupported format. Use .obj or .ply")
            return

        # Validate file exists
        if not os.path.exists(path):
            print(f"File not found: {path}")
            return

        obj = SceneBuilder.load_model(path)
        if obj:
            obj.setup()
            offset = len(self.scene.objects) * 0.8
            obj.set_position(offset, 0, 0)
            self.scene.add(obj)
            print(f"Loaded: {os.path.basename(path)}")
        else:
            print(f"Failed to load: {path}")

    def _add_shape(self, shape_name):
        obj = SceneBuilder.create_3d(shape_name)
        if obj:
            obj.setup()
            offset = len(self.scene.objects) * 0.8
            obj.set_position(offset, 0, 0)
            self.scene.add(obj)

    def _add_2d_shape(self, shape_name):
        """Add a 2D shape to the scene."""
        obj = SceneBuilder.create_2d(shape_name)
        if obj:
            obj.setup()
            offset = len(self.scene.objects) * 0.8
            # 2D shapes are placed at z=0
            obj.set_position(offset, 0, 0)
            self.scene.add(obj)

    def _load_model_from_path(self):
        """Load model from 3d_sample folder - cycles through available models."""
        # Predefined models from 3d_sample (just use one dragon as example)
        search_paths = [
            '/Users/dai.lechidai/me/BK/HK252/CG/ass/3d_sample/suzanne.obj',
            # '/Users/dai.lechidai/me/BK/HK252/CG/ass/3d_sample/utah_teapot.obj',

            # '/Users/dai.lechidai/me/BK/HK252/CG/ass/3d_sample/dragon_stand/dragonStandRight_0.ply',
            # '/Users/dai.lechidai/me/BK/HK252/CG/ass/3d_sample/Armadillo_scans/ArmadilloSide_0.ply',
        ]
        loaded = False
        for path in search_paths:
            if os.path.exists(path):
                obj = SceneBuilder.load_model(path)
                if obj:
                    obj.setup()
                    offset = len(self.scene.objects) * 0.8
                    obj.set_position(offset, 0, 0)
                    self.scene.add(obj)
                    print(f"Loaded model: {os.path.basename(path)}")
                    loaded = True
                    break

        if not loaded:
            print("No model files found in 3d_sample/")
            print("Supported formats: .obj, .ply")

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

    def _handle_camera_input(self):
        """Handle camera and keyboard input by polling - called each frame."""
        io = imgui.get_io()

        # Helper to check if key was just pressed (trigger once per press)
        def just_pressed(key):
            is_pressed = glfw.get_key(self.win, key) == glfw.PRESS
            was_pressed = self._key_state.get(key, False)
            self._key_state[key] = is_pressed
            return is_pressed and not was_pressed

        # Handle keyboard shortcuts (only when ImGui doesn't want text input)
        if not io.want_text_input:
            # Input mode for model path
            if self.input_mode:
                if just_pressed(glfw.KEY_ENTER):
                    self._load_model_from_input_path()
                    self.input_mode = False
                    self.input_string = ""
                elif just_pressed(glfw.KEY_ESCAPE):
                    self.input_mode = False
                    self.input_string = ""
                return  # Don't process other keys in input mode

            if just_pressed(glfw.KEY_ESCAPE) or just_pressed(glfw.KEY_Q):
                glfw.set_window_should_close(self.win, True)
            if just_pressed(glfw.KEY_W):
                GL.glPolygonMode(GL.GL_FRONT_AND_BACK, next(self.fill_modes))
                print("Wireframe mode toggled")
            if just_pressed(glfw.KEY_C):
                self.current_camera = (self.current_camera + 1) % len(self.cameras)
                print(f"Switched to camera {self.current_camera + 1}")
            if just_pressed(glfw.KEY_R):
                self._reset_scene()
                print("Scene reset")
            if just_pressed(glfw.KEY_LEFT_BRACKET):
                self.shader_mode = (self.shader_mode - 1) % len(self.shader_modes)
                print(f"Shading: {self.shader_modes[self.shader_mode]}")
            if just_pressed(glfw.KEY_RIGHT_BRACKET):
                self.shader_mode = (self.shader_mode + 1) % len(self.shader_modes)
                print(f"Shading: {self.shader_modes[self.shader_mode]}")
            if just_pressed(glfw.KEY_D):
                self.display_mode = (self.display_mode + 1) % 2
                print(f"Display mode: {'RGB' if self.display_mode == 0 else 'Depth Map'}")
            if just_pressed(glfw.KEY_T):
                self.scene.select_next()
                print(f"Selected object: {self.scene.selected_index}")
            if just_pressed(glfw.KEY_Y):
                self.scene.select_prev()
                print(f"Selected object: {self.scene.selected_index}")
            if just_pressed(glfw.KEY_X) or just_pressed(glfw.KEY_DELETE):
                if self.scene.objects:
                    removed_idx = self.scene.selected_index
                    self.scene.remove(self.scene.selected_index)
                    print(f"Deleted object {removed_idx}. Remaining: {len(self.scene.objects)}")
            # Arrow keys for moving selected object - allow hold for continuous movement
            if glfw.get_key(self.win, glfw.KEY_LEFT) == glfw.PRESS:
                self._move_selected(-0.1, 0, 0)
                print("Moved left")
            if glfw.get_key(self.win, glfw.KEY_RIGHT) == glfw.PRESS:
                self._move_selected(0.1, 0, 0)
                print("Moved right")
            if glfw.get_key(self.win, glfw.KEY_UP) == glfw.PRESS:
                self._move_selected(0, 0.1, 0)
                print("Moved up")
            if glfw.get_key(self.win, glfw.KEY_DOWN) == glfw.PRESS:
                self._move_selected(0, -0.1, 0)
                print("Moved down")
            if glfw.get_key(self.win, glfw.KEY_PAGE_UP) == glfw.PRESS:
                self._move_selected(0, 0, 0.1)
                print("Moved forward")
            if glfw.get_key(self.win, glfw.KEY_PAGE_DOWN) == glfw.PRESS:
                self._move_selected(0, 0, -0.1)
                print("Moved backward")
            # Number keys for object insertion
            if just_pressed(glfw.KEY_0):
                self._add_shape('cube')
                print(f"Added cube. Total objects: {len(self.scene.objects)}")
            if just_pressed(glfw.KEY_1):
                if glfw.get_key(self.win, glfw.KEY_LEFT_SHIFT) == glfw.PRESS or glfw.get_key(self.win, glfw.KEY_RIGHT_SHIFT) == glfw.PRESS:
                    self._add_2d_shape('triangle')
                    print(f"Added triangle. Total objects: {len(self.scene.objects)}")
                else:
                    self._replace_shape('cube')
                    print(f"Shape replaced with cube")
            if just_pressed(glfw.KEY_2):
                if glfw.get_key(self.win, glfw.KEY_LEFT_SHIFT) == glfw.PRESS or glfw.get_key(self.win, glfw.KEY_RIGHT_SHIFT) == glfw.PRESS:
                    self._add_2d_shape('rectangle')
                    print(f"Added rectangle. Total objects: {len(self.scene.objects)}")
                else:
                    self._replace_shape('sphere_uv')
                    print(f"Shape replaced with sphere_uv")
            if just_pressed(glfw.KEY_3):
                if glfw.get_key(self.win, glfw.KEY_LEFT_SHIFT) == glfw.PRESS or glfw.get_key(self.win, glfw.KEY_RIGHT_SHIFT) == glfw.PRESS:
                    self._add_2d_shape('pentagon')
                    print(f"Added pentagon. Total objects: {len(self.scene.objects)}")
                else:
                    self._replace_shape('cylinder')
                    print(f"Shape replaced with cylinder")
            if just_pressed(glfw.KEY_4):
                if glfw.get_key(self.win, glfw.KEY_LEFT_SHIFT) == glfw.PRESS or glfw.get_key(self.win, glfw.KEY_RIGHT_SHIFT) == glfw.PRESS:
                    self._add_2d_shape('hexagon')
                    print(f"Added hexagon. Total objects: {len(self.scene.objects)}")
                else:
                    self._replace_shape('cone')
                    print(f"Shape replaced with cone")
            if just_pressed(glfw.KEY_5):
                if glfw.get_key(self.win, glfw.KEY_LEFT_SHIFT) == glfw.PRESS or glfw.get_key(self.win, glfw.KEY_RIGHT_SHIFT) == glfw.PRESS:
                    self._add_2d_shape('circle')
                    print(f"Added circle. Total objects: {len(self.scene.objects)}")
                else:
                    self._replace_shape('torus')
                    print(f"Shape replaced with torus")
            if just_pressed(glfw.KEY_6):
                if glfw.get_key(self.win, glfw.KEY_LEFT_SHIFT) == glfw.PRESS or glfw.get_key(self.win, glfw.KEY_RIGHT_SHIFT) == glfw.PRESS:
                    self._add_2d_shape('ellipse')
                    print(f"Added ellipse. Total objects: {len(self.scene.objects)}")
                else:
                    self._replace_shape('prism')
                    print(f"Shape replaced with prism")
            if just_pressed(glfw.KEY_7):
                if glfw.get_key(self.win, glfw.KEY_LEFT_SHIFT) == glfw.PRESS or glfw.get_key(self.win, glfw.KEY_RIGHT_SHIFT) == glfw.PRESS:
                    self._add_2d_shape('trapezoid')
                    print(f"Added trapezoid. Total objects: {len(self.scene.objects)}")
                else:
                    self._replace_shape('tetrahedron')
                    print(f"Shape replaced with tetrahedron")
            if just_pressed(glfw.KEY_8):
                if glfw.get_key(self.win, glfw.KEY_LEFT_SHIFT) == glfw.PRESS or glfw.get_key(self.win, glfw.KEY_RIGHT_SHIFT) == glfw.PRESS:
                    self._add_2d_shape('star')
                    print(f"Added star. Total objects: {len(self.scene.objects)}")
                else:
                    self._replace_shape('truncated_cone')
                    print(f"Shape replaced with truncated_cone")
            if just_pressed(glfw.KEY_9):
                if glfw.get_key(self.win, glfw.KEY_LEFT_SHIFT) == glfw.PRESS or glfw.get_key(self.win, glfw.KEY_RIGHT_SHIFT) == glfw.PRESS:
                    self._add_2d_shape('arrow')
                    print(f"Added arrow. Total objects: {len(self.scene.objects)}")
                else:
                    self._replace_shape('sphere_sub')
                    print(f"Shape replaced with sphere_sub")

        # Handle mouse camera controls (only when ImGui doesn't want mouse)
        if io.want_capture_mouse:
            self._is_dragging = False
            return

        win_size = glfw.get_window_size(self.win)
        mouse_pos = glfw.get_cursor_pos(self.win)

        # Convert to GL coordinates (Y inverted)
        current_mouse = (mouse_pos[0], win_size[1] - mouse_pos[1])

        # Polling-based camera controls - use delta movement
        left_pressed = glfw.get_mouse_button(self.win, glfw.MOUSE_BUTTON_LEFT) == glfw.PRESS
        right_pressed = glfw.get_mouse_button(self.win, glfw.MOUSE_BUTTON_RIGHT) == glfw.PRESS

        if left_pressed:
            if not self._is_dragging:
                # First frame of drag - start from current position to avoid jump
                self._is_dragging = True
                self.mouse = current_mouse
            self.cameras[self.current_camera].drag(self.mouse, current_mouse, win_size)
        elif right_pressed:
            if not self._is_dragging:
                self._is_dragging = True
                self.mouse = current_mouse
            self.cameras[self.current_camera].pan(self.mouse, current_mouse)
        else:
            # Mouse button released
            self._is_dragging = False

        # Always update stored mouse position for next frame
        self.mouse = current_mouse

        # Scroll zoom is handled by on_scroll callback


def main():
    viewer = Viewer()
    viewer.run()


if __name__ == '__main__':
    glfw.init()
    main()
    glfw.terminate()
