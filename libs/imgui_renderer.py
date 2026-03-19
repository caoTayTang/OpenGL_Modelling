"""ImGui renderer wrapper for GLFW-based OpenGL applications."""

import glfw
import OpenGL.GL as GL
import imgui_bundle as ib
from imgui_bundle import imgui
from imgui_bundle.python_backends.glfw_backend import GlfwRenderer


class ImGuiRenderer:
    """ImGui renderer wrapper for GLFW window."""

    def __init__(self, window):
        """Initialize ImGui with GLFW renderer.

        Args:
            window: GLFW window handle
        """
        self.window = window
        imgui.create_context()
        # Attach callbacks - let GlfwRenderer handle all input
        self.impl = GlfwRenderer(window, attach_callbacks=True)

        # Style settings - Blender-inspired dark theme
        self._setup_style()

    def _setup_style(self):
        """Setup a beautiful dark theme similar to Blender."""
        style = imgui.get_style()

        # Helper to create ImVec4 color
        def color(r, g, b, a):
            return imgui.ImVec4(r, g, b, a)

        # Blender-like dark gray theme
        imgui.push_style_color(imgui.Col_.window_bg, color(0.18, 0.18, 0.20, 0.95))
        imgui.push_style_color(imgui.Col_.child_bg, color(0.20, 0.20, 0.23, 0.95))
        imgui.push_style_color(imgui.Col_.popup_bg, color(0.22, 0.22, 0.25, 0.95))
        imgui.push_style_color(imgui.Col_.border, color(0.25, 0.25, 0.30, 0.6))

        # Text colors
        imgui.push_style_color(imgui.Col_.text, color(0.80, 0.80, 0.80, 1.0))
        imgui.push_style_color(imgui.Col_.text_disabled, color(0.45, 0.45, 0.45, 1.0))

        # Accent colors (Blender blue theme)
        imgui.push_style_color(imgui.Col_.header, color(0.25, 0.40, 0.55, 0.50))
        imgui.push_style_color(imgui.Col_.header_hovered, color(0.30, 0.48, 0.65, 0.65))
        imgui.push_style_color(imgui.Col_.header_active, color(0.35, 0.52, 0.72, 0.85))

        # Buttons
        imgui.push_style_color(imgui.Col_.button, color(0.25, 0.38, 0.52, 0.70))
        imgui.push_style_color(imgui.Col_.button_hovered, color(0.30, 0.45, 0.60, 0.85))
        imgui.push_style_color(imgui.Col_.button_active, color(0.38, 0.52, 0.70, 1.0))

        # Frame background
        imgui.push_style_color(imgui.Col_.frame_bg, color(0.20, 0.20, 0.23, 0.70))
        imgui.push_style_color(imgui.Col_.frame_bg_hovered, color(0.24, 0.24, 0.28, 0.80))
        imgui.push_style_color(imgui.Col_.frame_bg_active, color(0.28, 0.32, 0.38, 0.90))

        # Title bar
        imgui.push_style_color(imgui.Col_.title_bg, color(0.16, 0.16, 0.20, 0.95))
        imgui.push_style_color(imgui.Col_.title_bg_active, color(0.22, 0.22, 0.28, 0.95))

        # Scrollbar
        imgui.push_style_color(imgui.Col_.scrollbar_bg, color(0.15, 0.15, 0.18, 0.50))
        imgui.push_style_color(imgui.Col_.scrollbar_grab, color(0.32, 0.32, 0.38, 0.60))
        imgui.push_style_color(imgui.Col_.scrollbar_grab_hovered, color(0.38, 0.38, 0.44, 0.80))
        imgui.push_style_color(imgui.Col_.scrollbar_grab_active, color(0.42, 0.42, 0.48, 1.0))

        # Slider
        imgui.push_style_color(imgui.Col_.slider_grab, color(0.28, 0.42, 0.60, 0.85))
        imgui.push_style_color(imgui.Col_.slider_grab_active, color(0.35, 0.52, 0.72, 1.0))

        # Separator
        imgui.push_style_color(imgui.Col_.separator, color(0.28, 0.28, 0.33, 0.5))

        # Apply all style colors
        imgui.pop_style_color(20)

        # Rounding - more subtle
        style.window_rounding = 2.0
        style.child_rounding = 0.0
        style.frame_rounding = 2.0
        style.scrollbar_rounding = 2.0
        style.grab_rounding = 2.0
        style.tab_rounding = 0.0

        # Padding - very tight for compact UI
        style.window_padding = imgui.ImVec2(4, 3)
        style.frame_padding = imgui.ImVec2(4, 2)
        style.item_spacing = imgui.ImVec2(4, 2)
        style.item_inner_spacing = imgui.ImVec2(3, 2)
        style.scrollbar_size = 8.0

        # Set font scale - larger font
        try:
            style.font_scale_main = 1.3
        except Exception:
            pass

        # Smaller text
        imgui.push_style_color(imgui.Col_.text, color(0.85, 0.85, 0.85, 1.0))

    def render(self, draw_data=None):
        """Render ImGui frame.

        Args:
            draw_data: Optional ImGui draw data (auto-generated if not provided)
        """
        self.impl.render(draw_data)

    def shutdown(self):
        """Clean up ImGui resources."""
        self.impl.shutdown()
        imgui.destroy_context()