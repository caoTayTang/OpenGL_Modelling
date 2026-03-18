# Assignment 1.1: Basic Shapes
## Computer Graphics - CO3059 - HCMUT

A comprehensive OpenGL-based 3D rendering application demonstrating basic 2D/3D shapes, multiple shading modes, lighting, and camera controls.

---

## Table of Contents
1. [Installation](#installation)
2. [Running the Application](#running-the-application)
3. [Controls & Keymap](#controls--keymap)
4. [Technical Documentation](#technical-documentation)
5. [Implementation Details](#implementation-details)
6. [Features](#features)
7. [Project Structure](#project-structure)

---

## Installation

```bash
pip install -r requirements.txt
```

### Requirements
- Python 3.8+
- PyOpenGL / PyOpenGL_accelerate
- GLFW
- NumPy
- OpenCV (for texture loading)

---

## Running the Application

```bash
cd assignment_1_1
python app.py
```

---

## Controls & Keymap

### Camera Controls
| Key | Action |
|-----|--------|
| **Left Mouse Drag** | Rotate camera (orbit around scene center) |
| **Right Mouse Drag** | Pan camera |
| **Scroll Wheel** | Zoom in/out |
| **C** | Switch between multiple cameras |

### Shape Management
| Key | Action |
|-----|--------|
| **0** | Add new cube at offset position |
| **1** | Replace selected shape with **Cube** |
| **2** | Replace selected shape with **UV Sphere** |
| **3** | Replace selected shape with **Cylinder** |
| **4** | Replace selected shape with **Cone** |
| **5** | Replace selected shape with **Torus** |
| **6** | Replace selected shape with **Prism** |
| **7** | Replace selected shape with **Tetrahedron** |
| **8** | Replace selected shape with **Truncated Cone** |
| **9** | Replace selected shape with **Sphere (Subdivision)** |

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
| **L** | Toggle Light 1 |
| **K** | Toggle Light 2 |

### Scene
| Key | Action |
|-----|--------|
| **R** | Reset scene to default state |
| **Q** or **Escape** | Quit application |

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

#### Vertex Shader Example (Color Interpolation)
```glsl
#version 330 core

layout(location = 0) in vec3 position;
layout(location = 1) in vec3 color;

uniform mat4 projection, modelview;
out vec3 fragment_color;

void main(){
    fragment_color = color;
    gl_Position = projection * modelview * vec4(position, 1.0);
}
```

#### Fragment Shader Example (Phong)
```glsl
#version 330 core

precision mediump float;
in vec3 normal_interp;  // Surface normal
in vec3 vertPos;       // Vertex position
in vec3 colorInterp;

uniform mat3 K_materials;
uniform mat3 I_light;
uniform float shininess;
uniform vec3 light_pos;

out vec4 fragColor;

void main() {
  vec3 N = normalize(normal_interp);
  vec3 L = normalize(light_pos - vertPos);
  vec3 R = reflect(-L, N);
  vec3 V = normalize(-vertPos);

  float specAngle = max(dot(R, V), 0.0);
  float specular = pow(specAngle, shininess);
  vec3 g = vec3(max(dot(L, N), 0.0), specular, 1.0);
  vec3 rgb = 0.5*matrixCompMult(K_materials, I_light) * g + 0.5*colorInterp;

  fragColor = vec4(rgb, 1.0);
}
```

#### Depth Shader (Linearized Depth)
```glsl
// Vertex Shader
#version 330 core
layout(location = 0) in vec3 position;
layout(location = 1) in vec3 color;

uniform mat4 projection, modelview;

void main(){
    gl_Position = projection * modelview * vec4(position, 1.0);
}

// Fragment Shader
#version 330 core
out vec4 outColor;

uniform float near;
uniform float far;

float linearizeDepth(float depth) {
    float z = depth * 2.0 - 1.0; // NDC
    return (2.0 * near * far) / (far + near - z * (far - near));
}

void main() {
    float linearDepth = linearizeDepth(gl_FragCoord.z);
    float depth = (linearDepth - near) / (far - near);
    depth = clamp(depth, 0.0, 1.0);
    depth = pow(depth, 0.5); // Gamma correction
    outColor = vec4(vec3(depth), 1.0);
}
```

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

### Sphere Generation Algorithms

**1. UV Sphere:**
```python
for ring in range(rings + 1):
    theta = pi * ring / rings
    for seg in range(segments + 1):
        phi = 2 * pi * seg / segments
        x = cos(phi) * sin(theta)
        y = cos(theta)
        z = sin(phi) * sin(theta)
```

**2. Subdivision Sphere:**
- Start with icosahedron (12 vertices, 20 faces)
- For each subdivision level:
  - Find midpoints of all edges
  - Normalize to unit sphere: `v = normalize(v) * radius`
  - Replace each triangle with 4 triangles
- Time complexity: O(4^n) where n = subdivision level

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

**Shading Modes (6 types):**
- Flat color
- Vertex color interpolation
- Phong shading (per-fragment)
- Gouraud shading (per-vertex)
- Texture mapping
- Wireframe mode

**Camera:**
- 3 cameras with different initial positions
- Orbit rotation (mouse drag)
- Pan (right mouse drag)
- Zoom (scroll wheel)

**Display:**
- RGB rendering
- Depth map visualization (linearized)

---

## ⚠️ Notes & Known Issues

### Lighting
- Light toggle keys (L/K) are implemented but **not fully functional** with current shaders
- The Phong/Gouraud shaders compute lighting internally (hardcoded light position)
- Fixed-function pipeline (glEnable(GL_LIGHTING)) is deprecated in OpenGL Core Profile

### Shader Status
| Shader | Status | Notes |
|--------|--------|-------|
| **Flat** | ✅ Working | Simple color output |
| **Color Interp** | ✅ Working | Vertex color interpolation |
| **Depth** | ✅ Working | Linearized depth with gamma |
| **Phong** | ⚠️ May have issues | Needs proper light uniforms |
| **Gouraud** | ⚠️ May have issues | Needs proper light uniforms |
| **Texture** | ⚠️ May have issues | Needs texture setup |

### Future Improvements
1. Implement proper light uniforms in shaders
2. Add texture loading and binding
3. Fix Phong/Gouraud shading calculations
4. Add OBJ/PLY model loading

---

## Project Structure

```
assignment_1_1/
├── libs/                       # Core utilities (from Sample)
│   ├── shader.py              # Shader compilation
│   ├── buffer.py              # VAO, VBO, EBO, UManager
│   ├── transform.py           # Matrix operations, Trackball
│   ├── camera.py              # Camera class
│   └── lighting.py            # Lighting management
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
├── viewer.py                   # Main window & event handling
├── app.py                     # Entry point
├── requirements.txt
└── README.md
```

---

## Key Algorithms

1. **Quaternion Rotation** - For smooth camera orbit
2. **Triangle Subdivision** - For subdivision sphere
3. **Linear Depth** - For depth map visualization: `linearDepth = (2*near*far)/(far+near-z*(far-near))`
4. **Parametric Surface** - For custom surfaces: z = f(x,y)

---

## References

- [Learn OpenGL](https://learnopengl.com/)
- [OpenGL Documentation](https://www.khronos.org/opengl/)
- [GLFW Documentation](https://www.glfw.org/docs/latest/)
- [PyOpenGL Documentation](https://pyopengl.sourceforge.net/)

---

**Course:** CO3059 - Computer Graphics  
**Instructor:** TS. Lê Thanh Sách  
**University:** HCMUT - Khoa Khoa học Máy tính
