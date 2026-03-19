# Assignment 1.1: Basic Shapes
## Computer Graphics - CO3059 - HCMUT

A comprehensive OpenGL-based 3D rendering application demonstrating basic 2D/3D shapes, multiple shading modes, lighting, and camera controls. Features a beautiful Blender-style UI with ImGui panels.

---

## Table of Contents
1. [Installation](#installation)
2. [Running the Application](#running-the-application)
3. [UI Layout](#ui-layout)
4. [Controls & Keymap](#controls--keymap)
5. [Technical Documentation](#technical-documentation)
   - [Rendering Pipeline](#rendering-pipeline)
   - [OBJ and PLY Model Loading](#obj-and-ply-model-loading)
   - [HiDPI/Retina Display Support](#hidpiretina-display-support)
   - [Shaders](#shaders)
   - [Input Handling](#input-handling)
6. [Implementation Details](#implementation-details)
7. [Features](#features)
8. [Project Structure](#project-structure)

---

## Installation

### Quick Start (Already Configured)
The environment is already set up. To run:

```bash
cd /Users/dai.lechidai/me/BK/HK252/CG/ass
source .venv/bin/activate
cd assignment_1_1
python app.py
```

### Manual Setup (if needed)
```bash
# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # On macOS/Linux
# On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install imgui-bundle (for beautiful UI panels)
pip install imgui-bundle
```

### Requirements
- Python 3.8+
- PyOpenGL
- GLFW
- NumPy
- OpenCV (for texture loading)
- imgui-bundle (for ImGui UI panels)

---

## Running the Application

```bash
cd assignment_1_1
python app.py
```

**Important Notes:**
- The application starts with **NO objects** in the scene (empty scene)
- Use keyboard shortcuts or the UI to add shapes
- All key presses trigger only once per press (no hold-to-repeat for single actions)

---

## UI Layout

The application uses a Blender-style UI with floating panels:

```
┌──────────────────────────────────────────────────────────────────┐
│  TOP TOOLBAR (32px)                                              │
│  [Shader: ▼flat] [Fill] [Wire] [Point]  Light: [☑L1] [☑L2]     │
├────────┬─────────────────────────────────────────────┬───────────┤
│        │                                         │           │
│ LEFT   │         CENTER VIEWPORT                  │  RIGHT    │
│ PANEL  │      (3D Rendering Area)                 │  PANEL    │
│        │                                         │           │
│ Objects│                                         │ Properties│
│ (180px)│                                         │ (up to    │
│        │                                         │  1/3 win) │
│        │                                         │           │
├────────┴─────────────────────────────────────────────┴───────────┤
│  BOTTOM STATUS BAR (32px)                                        │
│  Objects: 0 | Shader: flat | L1:ON | L2:ON | Cam: 1             │
└──────────────────────────────────────────────────────────────────┘
```

### UI Panels Detail

**Top Toolbar:**
- Shader dropdown: Select shading mode (flat, color_interp, phong, gouraud, texture)
- Fill/Wire/Point buttons: Toggle polygon rendering mode
- Light toggles: Enable/disable Light 1 and Light 2

**Left Panel (Objects):**
- Shows count: "Objects (N)"
- List of all objects in scene with type names
- Click to select an object
- Delete button to remove selected object

**Right Panel (Properties):**
- Object section: Shows type and position of selected object
- Camera section: View number and "Next View" button
- Model section: File path input + Load button for OBJ/PLY files
- Shortcuts section: Reference for all keyboard controls

**Bottom Status Bar:**
- Shows: Object count | Current shader | Light status | Camera number

---

## Controls & Keymap

### Camera Controls
| Key | Action |
|-----|--------|
| **Left Mouse Drag** | Rotate camera (orbit around scene center) |
| **Right Mouse Drag** | Pan camera |
| **Scroll Wheel** | Zoom in/out |
| **C** | Switch between 3 cameras |

### Shape Management (Add New)
| Key | Action |
|-----|--------|
| **0** | Add new **Cube** at offset position |

### Shape Management (Replace Selected)
| Key | Action |
|-----|--------|
| **1** | Replace selected shape with **Cube** |
| **2** | Replace selected shape with **UV Sphere** |
| **3** | Replace selected shape with **Cylinder** |
| **4** | Replace selected shape with **Cone** |
| **5** | Replace selected shape with **Torus** |
| **6** | Replace selected shape with **Prism** |
| **7** | Replace selected shape with **Tetrahedron** |
| **8** | Replace selected shape with **Truncated Cone** |
| **9** | Replace selected shape with **Sphere (Subdivision)** |

### Shape Management (Add 2D Shapes)
| Key | Action |
|-----|--------|
| **Shift+1** | Add **Triangle** |
| **Shift+2** | Add **Rectangle** |
| **Shift+3** | Add **Pentagon** |
| **Shift+4** | Add **Hexagon** |
| **Shift+5** | Add **Circle** |
| **Shift+6** | Add **Ellipse** |
| **Shift+7** | Add **Trapezoid** |
| **Shift+8** | Add **Star** |
| **Shift+9** | Add **Arrow** |

### Model Loading
| Method | Action |
|--------|--------|
| **UI Panel** | Type file path in Properties panel → click "Load" |
| **O key** | Enter input mode (type path in terminal) |

**Supported formats:** `.obj`, `.ply`

**Example paths:**
- `/Users/dai.lechidai/me/BK/HK252/CG/ass/3d_sample/suzanne.obj`
- `/Users/dai.lechidai/me/BK/HK252/CG/ass/3d_sample/dragon_stand/dragonStandRight_0.ply`

### Object Selection & Movement
| Key | Action |
|-----|--------|
| **T** | Select next object in scene |
| **Y** | Select previous object in scene |
| **← Arrow** | Move selected object left |
| **→ Arrow** | Move selected object right |
| **↑ Arrow** | Move selected object up |
| **↓ Arrow** | Move selected object down |
| **Page Up** | Move selected object forward (Z+) |
| **Page Down** | Move selected object backward (Z-) |

### Rendering & Shading
| Key | Action |
|-----|--------|
| **W** | Toggle wireframe/fill/point mode |
| **D** | Toggle RGB rendering ↔ Depth Map |
| **[** | Previous shading mode |
| **]** | Next shading mode |

### Lighting
| Key | Action |
|-----|--------|
| **L** | Toggle Light 1 |
| **K** | Toggle Light 2 |

### Scene
| Key | Action |
|-----|--------|
| **R** | Reset scene (clears all objects) |
| **Q** or **Escape** | Quit application |

### Object Deletion
| Key | Action |
|-----|--------|
| **X** | Delete currently selected object |
| **Delete** | Delete currently selected object |

---

## Technical Documentation

### Rendering Pipeline

This application follows the modern OpenGL rendering pipeline:

```
┌─────────────────────────────────────────────────────────────────┐
│                     APPLICATION                                │
├─────────────────────────────────────────────────────────────────┤
│  1. Geometry Generation                                       │
│     - Vertices, Normals, Colors, TexCoords, Indices          │
│     - Stored in numpy arrays                                  │
│                                                                 │
│  2. Buffer Management (VAO/VBO/EBO)                         │
│     - Vertex Array Object (VAO) wraps all buffers            │
│     - Vertex Buffer Object (VBO) stores vertex data          │
│     - Element Buffer Object (EBO) stores indices             │
│                                                                 │
│  3. Shader Program                                            │
│     - Vertex Shader: Transforms positions, passes data        │
│     - Fragment Shader: Calculates colors, lighting            │
│                                                                 │
│  4. Matrix Transformations                                    │
│     - Model Matrix: Object's local transformation            │
│     - View Matrix: Camera transformation                      │
│     - Projection Matrix: Perspective/Orthographic            │
│                                                                 │
│  5. Rasterization                                            │
│     - Primitive assembly (triangles)                          │
│     - Fragment generation                                     │
│                                                                 │
│  6. Fragment Processing                                      │
│     - Depth testing                                          │
│     - Color blending                                         │
│     - Final pixel color output                               │
└─────────────────────────────────────────────────────────────────┘
```

### HiDPI/Retina Display Support

The application properly handles HiDPI displays (including Retina):

```python
# Get both window size (logical) and framebuffer size (pixels)
win_size = glfw.get_window_size(self.win)
fb_size = glfw.get_framebuffer_size(self.win)

# Calculate scale factor
scale_x = fb_size[0] / win_size[0]  # e.g., 2.0 on Retina
scale_y = fb_size[1] / win_size[1]

# Scale viewport coordinates to framebuffer pixels
vp_x = int(left_panel_w * scale_x)
vp_y = int(bottom_bar_h * scale_y)
vp_w = int(viewport_width * scale_x)
vp_h = int(viewport_height * scale_y)

# Set viewport in pixel coordinates
GL.glViewport(vp_x, vp_y, vp_w, vp_h)
```

**Key insight:** `glViewport` expects pixel coordinates, not logical window coordinates. On Retina displays (2x), a 800x600 window has a 1600x1200 framebuffer.

### Shaders

The application includes multiple shader programs:

| Shader | File | Description |
|--------|------|-------------|
| **Flat** | `flat.vert/frag` | Constant color per primitive |
| **Color Interpolation** | `color_interp.vert/frag` | Interpolates vertex colors across face |
| **Phong** | `phong.vert/frag` | Per-fragment Phong lighting |
| **Gouraud** | `gouraud.vert/frag` | Per-vertex lighting |
| **Texture** | `phong_texture.vert/frag` | Phong + texture mapping |
| **Depth** | `depth.vert/frag` | Depth map visualization |

### Input Handling (Polling vs Callbacks)

The application uses **polling** instead of callbacks for keyboard input to avoid conflicts with ImGui:

```python
def _handle_camera_input(self):
    """Handle camera and keyboard input by polling - called each frame."""
    io = imgui.get_io()

    # Track key states to detect single press (not held)
    def just_pressed(key):
        is_pressed = glfw.get_key(self.win, key) == glfw.PRESS
        was_pressed = self._key_state.get(key, False)
        self._key_state[key] = is_pressed
        return is_pressed and not was_pressed

    # Use just_pressed() for single-trigger actions
    if just_pressed(glfw.KEY_0):
        self._add_shape('cube')
```

**Why polling?**
- GlfwRenderer (from imgui-bundle) attaches its own callbacks
- Having two callback systems caused duplicate key events
- Polling avoids this conflict and provides finer control

---

## OBJ and PLY Model Loading

This section details how the application loads 3D models from OBJ and PLY files, including the graphics pipeline considerations and file format parsing.

### Overview

Model loading involves several stages:
```
┌─────────────────────────────────────────────────────────────────┐
│                    MODEL LOADING PIPELINE                      │
├─────────────────────────────────────────────────────────────────┤
│  1. File I/O                                                   │
│     - Read OBJ/PLY file from disk                              │
│     - Detect format (ASCII vs Binary for PLY)                  │
│                                                                 │
│  2. Parsing & Geometry Extraction                              │
│     - Parse vertices (position)                                │
│     - Parse normals (optional)                                 │
│     - Parse faces/indices                                      │
│                                                                 │
│  3. Triangulation                                              │
│     - Convert n-gons (quads, pentagons, etc.) to triangles    │
│     - Uses fan triangulation algorithm                         │
│                                                                 │
│  4. Data Transformation                                        │
│     - Store positions and normals in SEPARATE arrays           │
│     - Generate vertex colors (rainbow gradient)                │
│     - Create index buffer for efficient rendering              │
│                                                                 │
│  5. Buffer Setup (OpenGL)                                      │
│     - Create VAO/VBO/EBO                                       │
│     - Upload data to GPU                                       │
└─────────────────────────────────────────────────────────────────┘
```

### OBJ File Format

The OBJ format is a text-based 3D model format. Key elements:

```
# Vertex positions (x, y, z)
v 1.0 2.0 3.0
v -0.5 0.0 0.5
...

# Vertex normals (nx, ny, nz)
vn 0.0 1.0 0.0
vn 0.707 0.0 0.707
...

# Faces (vertex_index/normal_index)
# format: f v1/vt1/vn1 v2/vt2/vn2 v3/vt3/vn3
f 1//1 2//1 3//1      # triangle with normal 1
f 1/1/1 2/2/2 3/3/3   # triangle with texcoords and normals
f 1//1 2//1 3//1 4//1 # quad - needs triangulation
```

**OBJ Loading Process:**

```python
# 1. First pass: Read all vertices and normals into memory
obj_vertices = []   # [x1, y1, z1, x2, y2, z2, ...]
obj_normals = []    # [nx1, ny1, nz1, nx2, ny2, nz2, ...]

# 2. Second pass: Build indexed geometry
vertex_map = {}     # (v_idx, vn_idx) -> unique_vertex_index
new_vertices = []   # interleaved [px, py, pz, nx, ny, nz, ...]
indices = []

for each face:
    # Parse vertex indices: "1//1" -> (v_idx=0, vn_idx=0)
    face_verts = [(v_idx, vn_idx), ...]

    # Fan triangulation: convert n-gon to n-2 triangles
    # quad (v0,v1,v2,v3) -> triangles: (v0,v1,v2), (v0,v2,v3)
    for i in range(1, len(face_verts) - 1):
        v0, vn0 = face_verts[0]
        v1, vn1 = face_verts[i]
        v2, vn2 = face_verts[i + 1]

        # Add unique vertices to map and vertex array
        for (v_idx, vn_idx) in [(v0,vn0), (v1,vn1), (v2,vn2)]:
            if (v_idx, vn_idx) not in vertex_map:
                vertex_map[(v_idx, vn_idx)] = current_idx
                # Get position from obj_vertices
                # Get normal from obj_normals (or use default 0,1,0)
                new_vertices.extend([px, py, pz, nx, ny, nz])
                current_idx += 1

        indices.extend([i0, i1, i2])

# 3. Extract positions and normals into SEPARATE arrays
# This is crucial for base.py setup() which expects ncomponents=3
positions = []  # [px, py, pz, px, py, pz, ...]
normals = []    # [nx, ny, nz, nx, ny, nz, ...]
for i in range(num_vertices):
    positions.extend([new_vertices[i*6], new_vertices[i*6+1], new_vertices[i*6+2]])
    normals.extend([new_vertices[i*6+3], new_vertices[i*6+4], new_vertices[i*6+5]])
```

**Key insight:** The OBJ loader stores positions and normals in SEPARATE numpy arrays (not interleaved), because the `Geometry.setup()` method in `base.py` expects:
- `vertices`: vec3 (3 components)
- `normals`: vec3 (3 components)
- `colors`: vec3 (3 components)

### PLY File Format

The PLY (Polygon File Format) supports both ASCII and binary formats:

**ASCII PLY:**
```
ply
format ascii 1.0
element vertex 507
property float x
property float y
property float z
property float nx
property float ny
property float nz
element face 968
property list uchar int vertex_indices
end_header
0.5 0.2 0.1 0.0 1.0 0.0
...
3 0 1 2
3 1 3 2
...
```

**Binary PLY:**
```
ply
format binary_little_endian 1.0
element vertex 6613568
property float x
property float y
property float z
element face 13178120
property list uchar int vertex_indices
end_header
[binary data: 12 bytes per vertex, variable per face]
```

**Binary PLY Parsing:**
```python
# Read header as text to detect format and structure
with open(filepath, 'rb') as f:
    header_bytes = f.read(2000)

header_text = header_bytes.decode('latin-1')
is_binary = 'binary' in header_text
is_big_endian = 'binary_big_endian' in header_text

# Parse header to get vertex_count, face_count, has_colors
# ...

if is_binary:
    # Read entire file as binary
    with open(filepath, 'rb') as f:
        data = f.read()

    # Find end of header
    header_end_pos = data.find(b'end_header\n')
    data_start = header_end_pos + len(b'end_header\n')

    # Parse vertices - each is 12 bytes (3 floats)
    import struct
    vertices = []
    for _ in range(vertex_count):
        if is_big_endian:
            x, y, z = struct.unpack('>fff', data[pos:pos+12])
        else:
            x, y, z = struct.unpack('<fff', data[pos:pos+12])
        vertices.extend([x, y, z])
        pos += 12

    # Parse faces - variable length
    for _ in range(face_count):
        num_verts = struct.unpack('B', data[pos:pos+1])[0]  # uchar
        pos += 1
        face_vertices = []
        for _ in range(num_verts):
            if is_big_endian:
                v = struct.unpack('>I', data[pos:pos+4])[0]
            else:
                v = struct.unpack('<I', data[pos:pos+4])[0]
            face_vertices.append(v)
            pos += 4

        # Fan triangulation
        for j in range(1, num_verts - 1):
            indices.extend([face_vertices[0], face_vertices[j], face_vertices[j+1]])
```

### Fan Triangulation

Both OBJ and PLY loaders use **fan triangulation** to convert n-gons to triangles:

```
Original quad:    Triangulated:
    v0                  v0
   /|\                 /|\
  / | \               / | \
 v1--+--v3    =>     v1-+-v3
  \ | /               \ |/
   \|/                 \|
    v2                  v2

Triangles: (v0,v1,v2), (v0,v2,v3)
```

This is the simplest method and works well for convex polygons. For concave polygons, more complex triangulation algorithms would be needed.

### Data Storage Format

The final data stored in each Geometry object:

| Field | Format | Description |
|-------|--------|-------------|
| `vertices` | `np.array[float32]` | Positions only, shape: (N*3,) - 3 floats per vertex |
| `normals` | `np.array[float32]` | Normals only, shape: (N*3,) - 3 floats per vertex |
| `colors` | `np.array[float32]` | RGB colors, shape: (N*3,) - rainbow gradient |
| `indices` | `np.array[uint32]` | Triangle indices, shape: (M*3,) - 3 per triangle |

### OpenGL Buffer Setup

Once data is loaded, `Geometry.setup()` uploads to GPU:

```python
def setup(self):
    if self.vertices is not None:
        self.vao.add_vbo(0, self.vertices, ncomponents=3)
    if self.normals is not None:
        self.vao.add_vbo(2, self.normals, ncomponents=3)
    if self.colors is not None:
        self.vao.add_vbo(1, self.colors, ncomponents=3)
    if self.indices is not None:
        self.vao.add_ebo(self.indices)
```

VBO layout (attribute locations):
- Location 0: Vertex positions (vec3)
- Location 1: Vertex colors (vec3)
- Location 2: Vertex normals (vec3)

---

## Implementation Details

### Geometry Generation

#### 2D Shapes (9 types)
| Shape | Method |
|-------|--------|
| **Triangle** | 3 vertices, GL_TRIANGLES |
| **Rectangle** | 4 vertices, 2 triangles |
| **Pentagon** | 5 vertices, triangle fan |
| **Hexagon** | 6 vertices, triangle fan |
| **Circle** | 32+ segments, triangle fan |
| **Ellipse** | Scaled circle (x radius ≠ y radius) |
| **Trapezoid** | 4 custom vertices |
| **Star** | 10 vertices (5 outer + 5 inner), triangle fan |
| **Arrow** | Custom polygon |

#### 3D Shapes (11+ types)

| Shape | Generation Method |
|-------|-----------------|
| **Cube** | 8 corner vertices, 12 triangles (2 per face) |
| **UV Sphere** | Grid projection: theta/phi loops → normalize to sphere surface |
| **Subdivision Sphere** | Start with icosahedron (12 vertices), recursively subdivide each triangle, normalize to unit sphere |
| **Lat-Long Sphere** | Latitude/longitude grid (similar to UV sphere) |
| **Cylinder** | Two circles (top/bottom) + side triangles |
| **Cone** | Circle at base + apex point + side triangles |
| **Truncated Cone** | Two circles at different radii + side triangles |
| **Tetrahedron** | 4 vertices, 4 equilateral faces |
| **Torus** | Major circle (R) + minor circle (r) revolution |
| **Prism** | n-sided polygon extrusion with top/bottom caps |
| **Parametric Surface** | Grid mesh where z = f(x,y) |

### Camera System

**Trackball Camera** using quaternions:
- Rotation via quaternion multiplication
- Smooth interpolation between orientations
- Distance-based zoom

```python
# Projection (Perspective)
fov = 35 degrees
aspect = width / height
near = max(0.05, 0.1 * distance)
far = max(near * 15, 2.0 * distance)  # ~15:1 ratio for better depth visualization
```

### Depth Map Implementation

1. Render scene normally (populates depth buffer)
2. Use depth shader to compute linearized depth
3. Near/far ratio optimized (~15:1) to prevent depth clustering
4. Gamma correction (pow 0.5) for better visual contrast

### ImGui Integration

This project uses Dear ImGui (via imgui-bundle) for beautiful UI panels, the same library used in Blender.

**UI Components:**
1. **Toolbar Panel** (top): Shader dropdown, Fill/Wire/Point buttons, Light toggles
2. **Objects Panel** (left): List of all objects, clickable to select, Delete button
3. **Properties Panel** (right): Selected object info, Camera controls, Model loading
4. **Status Bar** (bottom): Shows current state

**Implementation:**
```python
# libs/imgui_renderer.py
class ImGuiRenderer:
    def __init__(self, window):
        imgui.create_context()
        self.impl = GlfwRenderer(window, attach_callbacks=True)
        self._setup_style()  # Blender-like dark theme

# In viewer.py run() loop
imgui.new_frame()
self._render_ui()  # Draw all panels
imgui.render()
self.imgui_renderer.render(imgui.get_draw_data())
glfw.swap_buffers(win)
```

**Key Features:**
- Dark theme with Blender-like styling
- Real-time object selection via UI
- Model loading via UI input field
- Position display for selected objects

---

## Features

### ✅ Implemented Features

**2D Shapes (9 types):**
- Triangle, Rectangle, Pentagon, Hexagon
- Circle, Ellipse, Trapezoid, Star, Arrow

**3D Shapes (11+ types):**
- Cube, Sphere (3 methods: UV, Subdivision, Lat-Long)
- Cylinder, Cone, Truncated Cone
- Tetrahedron, Torus, Prism
- Parametric Surface

**Shading Modes (5 types):**
- Flat color
- Vertex color interpolation
- Phong shading (per-fragment)
- Gouraud shading (per-vertex)
- Texture mapping
- Plus: Wireframe/Point modes

**Camera:**
- 3 cameras with different initial positions
- Orbit rotation (mouse drag)
- Pan (right mouse drag)
- Zoom (scroll wheel)

**Display:**
- RGB rendering
- Depth map visualization (linearized)

**Lighting:**
- 2 light sources
- Toggle on/off with L/K keys
- Phong and Gouraud shaders use combined lighting from all enabled lights

**Model Loading:**
- OBJ file support
- PLY file support
- Via UI input field in Properties panel

**UI (ImGui):**
- Beautiful floating panels using Dear ImGui (same library as Blender)
- Object list panel with clickable selection
- Properties panel showing object type, position, camera controls
- Model loading section with file path input
- Toolbar with shader selection and rendering mode buttons
- Status bar showing current state

**Object Management:**
- Delete selected object with X or Delete key
- Click on object in list to select
- Scene starts empty (no default objects)

---

## Project Structure

```
assignment_1_1/
├── libs/                       # Core utilities
│   ├── shader.py              # Shader compilation
│   ├── buffer.py              # VAO, VBO, EBO, UManager
│   ├── transform.py           # Matrix operations, Trackball
│   ├── camera.py              # Camera class
│   ├── lighting.py            # Lighting management
│   └── imgui_renderer.py      # ImGui renderer wrapper
│
├── geometry/                   # Geometry generators
│   ├── base.py               # Base Geometry class
│   ├── shapes_2d.py          # 2D shape classes (9)
│   └── shapes_3d.py          # 3D shape classes (11+)
│
├── shaders/                    # GLSL shaders
│   ├── flat.vert/frag
│   ├── color_interp.vert/frag
│   ├── phong.vert/frag
│   ├── gouraud.vert/frag
│   ├── phong_texture.vert/frag
│   └── depth.vert/frag
│
├── scene.py                    # Scene management
├── viewer.py                   # Main window & event handling (POLLING-BASED INPUT)
├── app.py                     # Entry point
├── requirements.txt
└── README.md
```

---

## Key Implementation Details

### Single-Press Key Handling

Keys are tracked using a state dictionary to ensure single-trigger behavior:

```python
# In __init__
self._key_state = {}  # key -> True if was held last frame

# In _handle_camera_input
def just_pressed(key):
    is_pressed = glfw.get_key(self.win, key) == glfw.PRESS
    was_pressed = self._key_state.get(key, False)
    self._key_state[key] = is_pressed
    return is_pressed and not was_pressed
```

This prevents holding a key from triggering multiple actions.

### Viewport Layout Calculation

The viewport is calculated to fill the space between panels:

```python
# Panel dimensions
left_panel_w = 180
right_panel_w = min(320, win_size[0] // 3)
top_bar_h = 32
bottom_bar_h = 32

# Viewport in window coordinates
vp_x_win = left_panel_w
vp_y_win = bottom_bar_h
vp_w_win = win_size[0] - left_panel_w - right_panel_w
vp_h_win = win_size[1] - top_bar_h - bottom_bar_h

# Scale to framebuffer pixels (HiDPI)
scale_x = fb_size[0] / win_size[0]
scale_y = fb_size[1] / win_size[1]
vp_x = int(vp_x_win * scale_x)
# ... etc
```

---

## References

- [Learn OpenGL](https://learnopengl.com/)
- [OpenGL Documentation](https://www.khronos.org/opengl/)
- [GLFW Documentation](https://www.glfw.org/docs/latest/)
- [PyOpenGL Documentation](https://pyopengl.sourceforge.net/)
- [imgui-bundle](https://github.com/ocornut/imgui)

---

**Course:** CO3059 - Computer Graphics
**Instructor:** TS. Lê Thanh Sách
**University:** HCMUT - Khoa Khoa học Máy tính