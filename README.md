# Assignment 1.1: Basic Shapes
## Computer Graphics - CO3059 - HCMUT

A comprehensive OpenGL-based 3D rendering application demonstrating basic 2D/3D shapes, multiple shading modes, lighting, and camera controls.

---

## Table of Contents
1. [Installation](#installation)
2. [Running the Application](#running-the-application)
3. [Controls & Keymap](#controls--keymap)
4. [Technical Documentation](#technical-documentation)
   - [Rendering Pipeline](#rendering-pipeline)
   - [Shaders](#shaders)
   - [Geometry Generation](#geometry-generation)
   - [Camera System](#camera-system)
5. [Features](#features)
6. [Project Structure](#project-structure)

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
| **A** | Add new cube at offset position |
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

### Rendering Modes
| Key | Action |
|-----|--------|
| **W** | Toggle wireframe/fill/point mode |
| **D** | Toggle RGB rendering ↔ Depth Map |
| **R** | Reset scene to default state |

### Exit
| Key | Action |
|-----|--------|
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
│     - Model Matrix: Object's local transformation              │
│     - View Matrix: Camera transformation                       │
│     - Projection Matrix: Perspective/Orthographic              │
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

#### Vertex Shader Structure
```glsl
#version 330 core
layout (location = 0) in vec3 aPos;      // Vertex position
layout (location = 1) in vec3 aColor;    // Vertex color
layout (location = 2) in vec3 aNormal;   // Vertex normal

uniform mat4 model;      // Model matrix
uniform mat4 view;      // View matrix  
uniform mat4 projection; // Projection matrix

void main() {
    gl_Position = projection * view * model * vec4(aPos, 1.0);
}
```

#### Fragment Shader (Phong)
```glsl
#version 330 core
// Calculates ambient + diffuse + specular lighting
// I_light * (K_ambient + K_diffuse * NdotL + K_specular * (RdotV)^shininess)
```

### Geometry Generation

#### 2D Shapes
- **Triangle**: 3 vertices
- **Rectangle**: 4 vertices + 2 triangles
- **Pentagon/Hexagon**: n vertices using triangle fan
- **Circle/Ellipse**: Many vertices using triangle fan
- **Trapezoid**: Custom 4 vertices
- **Star**: 10 vertices (5 outer + 5 inner) using triangle fan
- **Arrow**: Custom polygon

#### 3D Shapes

| Shape | Generation Method |
|-------|-----------------|
| **Cube** | 8 corner vertices, 12 triangles (2 per face) |
| **Sphere (UV)** | Grid projection: theta/phi loops → normalize to sphere |
| **Sphere (Subdivision)** | Start with tetrahedron, recursively subdivide triangles, normalize vertices to sphere surface |
| **Sphere (Lat-Long)** | Latitude/longitude grid, similar to UV sphere |
| **Cylinder** | Circle at y=bottom + circle at y=top + side triangles |
| **Cone** | Circle at base + apex point + side triangles |
| **Truncated Cone** | Two circles at different radii + side triangles |
| **Tetrahedron** | 4 vertices, 4 faces |
| **Torus** | Major circle + minor circle revolution |
| **Prism** | n-sided polygon extrude + caps |
| **Parametric Surface** | Grid mesh where z = f(x,y) |

### Camera System

The application uses a **Trackball Camera** implementation:

```
Trackball Camera Parameters:
- yaw: rotation around Y axis (horizontal)
- pitch: rotation around X axis (vertical)  
- roll: rotation around Z axis (roll)
- distance: distance from target point
- pos2d: 2D panning offset
```

#### Projection Matrix (Perspective)
```
fov = 35 degrees (default)
aspect = width / height
near = 0.1 * distance
far = 100 * distance
```

#### View Matrix
Computed using quaternion-based rotation + translation.

### Lighting Model

The application supports Phong lighting model:

```
I = I_ambient * K_ambient 
  + I_diffuse * K_diffuse * max(0, N·L)
  + I_specular * K_specular * max(0, R·V)^shininess
```

Where:
- **N**: Surface normal
- **L**: Light direction
- **V**: View direction
- **R**: Reflection direction

### Depth Map Rendering

When pressing **D** to toggle depth map mode:

1. Objects are rendered with a custom depth shader
2. The depth shader calculates linear depth from view space Z coordinate
3. Depth is normalized and displayed as grayscale:
   - White = near (closest to camera)
   - Black = far (furthest from camera)

---

## Features

### ✅ Implemented Features

**2D Shapes:**
- Triangle, Rectangle, Pentagon, Hexagon
- Circle, Ellipse, Trapezoid, Star, Arrow

**3D Shapes:**
- Cube, Sphere (3 methods), Cylinder
- Cone, Truncated Cone, Tetrahedron
- Torus, Prism, Parametric Surface

**Shading Modes:**
- (A) Flat color
- (B) Vertex color interpolation
- (C) Phong/Gouraud shading
- (D) Texture mapping
- (E) Combined
- (F) Wireframe mode

**Lighting:**
- Multiple light sources (2 lights)

**Camera:**
- Multiple cameras (3 cameras)
- Orbit rotation (mouse drag)
- Pan (right mouse drag)
- Zoom (scroll wheel)

**Display:**
- RGB rendering
- Depth map visualization

---

## Project Structure

```
assignment_1_1/
├── libs/                       # Core utilities (from Sample)
│   ├── shader.py              # Shader compilation
│   ├── buffer.py              # VAO, VBO, EBO management
│   ├── transform.py           # Matrix operations
│   ├── camera.py              # Camera class
│   └── lighting.py            # Lighting management
│
├── geometry/                   # Geometry generators
│   ├── base.py               # Base Geometry class
│   ├── shapes_2d.py          # 2D shape classes
│   └── shapes_3d.py         # 3D shape classes
│
├── shaders/                    # GLSL shaders
│   ├── flat.vert/frag
│   ├── color_interp.vert/frag
│   ├── phong.vert/frag
│   ├── gouraud.vert/frag
│   ├── texture.vert/frag
│   └── depth.vert/frag
│
├── scene.py                    # Scene management
├── viewer.py                   # Main window & event handling
├── app.py                     # Entry point
├── requirements.txt
└── README.md
```

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
