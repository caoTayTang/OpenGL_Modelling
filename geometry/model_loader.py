"""
Model loading utilities for OBJ and PLY formats.
"""
import numpy as np
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from geometry.base import Geometry


class OBJModel(Geometry):
    """Load and render 3D models from OBJ files."""

    def __init__(self, filepath, **kwargs):
        self.filepath = filepath
        vert_shader = kwargs.get('vert_shader', 'shaders/phong.vert')
        frag_shader = kwargs.get('frag_shader', 'shaders/phong.frag')
        super().__init__(vert_shader, frag_shader)
        self._load_obj(filepath)

    def _load_obj(self, filepath):
        """Load vertices, normals, and indices from OBJ file."""
        # First pass: read all vertices and normals
        obj_vertices = []
        obj_normals = []

        # Second pass: read faces and build indexed geometry
        face_data = []  # List of (v_idx, vn_idx) tuples per face

        vertex_map = {}  # (v_idx, vn_idx) -> new_vert_index
        new_vertices = []  # Position + Normal interleaved
        indices = []
        current_idx = 0

        with open(filepath, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue

                parts = line.split()
                if not parts:
                    continue

                prefix = parts[0]

                if prefix == 'v':
                    obj_vertices.extend([float(x) for x in parts[1:4]])
                elif prefix == 'vn':
                    obj_normals.extend([float(x) for x in parts[1:4]])
                elif prefix == 'f':
                    face_verts = []
                    for vert_spec in parts[1:]:
                        spec = vert_spec.split('/')
                        v_idx = int(spec[0]) - 1
                        vn_idx = int(spec[2]) - 1 if len(spec) > 2 and spec[2] else v_idx
                        face_verts.append((v_idx, vn_idx))

                    # Fan triangulation for n-gon
                    for i in range(1, len(face_verts) - 1):
                        v0, vn0 = face_verts[0]
                        v1, vn1 = face_verts[i]
                        v2, vn2 = face_verts[i + 1]

                        # Add v0
                        if (v0, vn0) not in vertex_map:
                            vertex_map[(v0, vn0)] = current_idx
                            # Get position
                            px, py, pz = obj_vertices[v0*3:v0*3+3]
                            # Get normal
                            if vn0 < len(obj_normals) // 3:
                                nx, ny, nz = obj_normals[vn0*3:vn0*3+3]
                            else:
                                nx, ny, nz = 0, 1, 0
                            new_vertices.extend([px, py, pz, nx, ny, nz])
                            current_idx += 1
                        i0 = vertex_map[(v0, vn0)]

                        # Add v1
                        if (v1, vn1) not in vertex_map:
                            vertex_map[(v1, vn1)] = current_idx
                            px, py, pz = obj_vertices[v1*3:v1*3+3]
                            if vn1 < len(obj_normals) // 3:
                                nx, ny, nz = obj_normals[vn1*3:vn1*3+3]
                            else:
                                nx, ny, nz = 0, 1, 0
                            new_vertices.extend([px, py, pz, nx, ny, nz])
                            current_idx += 1
                        i1 = vertex_map[(v1, vn1)]

                        # Add v2
                        if (v2, vn2) not in vertex_map:
                            vertex_map[(v2, vn2)] = current_idx
                            px, py, pz = obj_vertices[v2*3:v2*3+3]
                            if vn2 < len(obj_normals) // 3:
                                nx, ny, nz = obj_normals[vn2*3:vn2*3+3]
                            else:
                                nx, ny, nz = 0, 1, 0
                            new_vertices.extend([px, py, pz, nx, ny, nz])
                            current_idx += 1
                        i2 = vertex_map[(v2, vn2)]

                        indices.extend([i0, i1, i2])

        if new_vertices:
            # Extract positions and normals into SEPARATE arrays (not interleaved)
            num_vertices = len(new_vertices) // 6  # 6 floats per vertex (px,py,pz,nx,ny,nz)

            # Extract positions (vec3)
            positions = []
            for i in range(num_vertices):
                positions.extend([new_vertices[i*6], new_vertices[i*6+1], new_vertices[i*6+2]])
            self.vertices = np.array(positions, dtype=np.float32)

            # Extract normals (vec3)
            normals = []
            for i in range(num_vertices):
                normals.extend([new_vertices[i*6+3], new_vertices[i*6+4], new_vertices[i*6+5]])
            self.normals = np.array(normals, dtype=np.float32)
        else:
            self.vertices = None
            self.normals = None

        if indices:
            self.indices = np.array(indices, dtype=np.uint32)
        else:
            self.indices = None

        # Generate colors
        if self.vertices is not None:
            num_vertices = len(self.vertices) // 3
            colors = []
            for i in range(num_vertices):
                # Rainbow colors based on position
                r = (np.sin(i * 0.1) + 1) / 2
                g = (np.sin(i * 0.1 + 2) + 1) / 2
                b = (np.sin(i * 0.1 + 4) + 1) / 2
                colors.extend([r, g, b])
            self.colors = np.array(colors, dtype=np.float32)

    def _compute_normals(self):
        """Compute vertex normals from faces."""
        if self.vertices is None or self.indices is None:
            return None

        num_vertices = len(self.vertices) // 3
        normals = np.zeros(num_vertices * 3, dtype=np.float32)

        for i in range(0, len(self.indices), 3):
            i0, i1, i2 = self.indices[i], self.indices[i + 1], self.indices[i + 2]

            v0 = self.vertices[i0*3:i0*3+3]
            v1 = self.vertices[i1*3:i1*3+3]
            v2 = self.vertices[i2*3:i2*3+3]

            edge1 = v1 - v0
            edge2 = v2 - v0
            face_normal = np.cross(edge1, edge2)

            normals[i0*3:i0*3+3] += face_normal
            normals[i1*3:i1*3+3] += face_normal
            normals[i2*3:i2*3+3] += face_normal

        # Normalize
        for i in range(num_vertices):
            n = normals[i*3:i*3+3]
            length = np.linalg.norm(n)
            if length > 0:
                normals[i*3:i*3+3] /= length

        return normals


class PLYModel(Geometry):
    """Load and render 3D models from PLY files."""

    def __init__(self, filepath, **kwargs):
        self.filepath = filepath
        vert_shader = kwargs.get('vert_shader', 'shaders/phong.vert')
        frag_shader = kwargs.get('frag_shader', 'shaders/phong.frag')
        super().__init__(vert_shader, frag_shader)
        self._load_ply(filepath)

    def _load_ply(self, filepath):
        """Load vertices, normals, colors, and indices from PLY file."""
        # First, read the file in binary mode to check format and parse header
        with open(filepath, 'rb') as f:
            header_bytes = f.read(2000)  # Read enough for header

        # Decode header to find format and structure
        header_text = header_bytes.decode('latin-1')
        header_lines = header_text.split('\n')

        # Check format
        is_binary = False
        if 'format binary_little_endian' in header_text:
            is_binary = True
        elif 'format binary_big_endian' in header_text:
            is_binary = True

        # Parse header
        vertex_count = 0
        face_count = 0
        has_colors = False
        is_big_endian = False

        header_end = 0
        for i, line in enumerate(header_lines):
            if line.strip() == 'end_header':
                header_end = i + 1
                break
            if line.startswith('element vertex'):
                vertex_count = int(line.split()[2])
            elif line.startswith('element face'):
                face_count = int(line.split()[2])
            elif 'red' in line.lower() and 'green' in line.lower() and 'blue' in line.lower():
                has_colors = True
            if 'binary_big_endian' in line:
                is_big_endian = True

        if is_binary:
            # Binary PLY loading
            with open(filepath, 'rb') as f:
                # Skip header
                f.seek(0)
                data = f.read()

            # Find end of header
            header_end_pos = data.find(b'end_header\n')
            if header_end_pos == -1:
                header_end_pos = data.find(b'end_header\r\n')
            data_start = header_end_pos + len(b'end_header\n') if b'\n' in data[header_end_pos:] else header_end_pos + len(b'end_header')

            # Parse vertices - each vertex is 12 bytes (3 floats) + optionally 12 bytes (3 colors)
            import struct
            vertices = []
            colors = []

            pos = data_start
            for _ in range(vertex_count):
                # Read 3 floats for position (x, y, z)
                if is_big_endian:
                    x, y, z = struct.unpack('>fff', data[pos:pos+12])
                else:
                    x, y, z = struct.unpack('<fff', data[pos:pos+12])
                vertices.extend([x, y, z])
                pos += 12

                # Read colors if present (3 uchars)
                if has_colors:
                    if is_big_endian:
                        r, g, b = struct.unpack('>BBB', data[pos:pos+3])
                    else:
                        r, g, b = struct.unpack('<BBB', data[pos:pos+3])
                    colors.extend([r/255.0, g/255.0, b/255.0])
                    pos += 3

            # Parse faces - each face starts with a uchar (num_verts) followed by num_verts ints
            indices = []
            for _ in range(face_count):
                num_verts = struct.unpack('B', data[pos:pos+1])[0]
                pos += 1

                face_vertices = []
                if is_big_endian:
                    for _ in range(num_verts):
                        v = struct.unpack('>I', data[pos:pos+4])[0]
                        face_vertices.append(v)
                        pos += 4
                else:
                    for _ in range(num_verts):
                        v = struct.unpack('<I', data[pos:pos+4])[0]
                        face_vertices.append(v)
                        pos += 4

                # Fan triangulation
                for j in range(1, num_verts - 1):
                    indices.extend([face_vertices[0], face_vertices[j], face_vertices[j + 1]])
        else:
            # ASCII PLY loading (existing code)
            with open(filepath, 'r') as f:
                lines = f.readlines()

            header_end = 0
            for i, line in enumerate(lines):
                if line.strip() == 'end_header':
                    header_end = i + 1
                    break

            # Parse vertices
            vertices = []
            colors = []

            for i in range(header_end, header_end + vertex_count):
                parts = lines[i].strip().split()
                if len(parts) >= 3:
                    vertices.extend([float(x) for x in parts[:3]])
                if has_colors and len(parts) >= 6:
                    colors.extend([int(parts[3])/255.0, int(parts[4])/255.0, int(parts[5])/255.0])

            # Parse faces
            indices = []
            for i in range(header_end + vertex_count, header_end + vertex_count + face_count):
                parts = lines[i].strip().split()
                if len(parts) >= 4:
                    num_verts = int(parts[0])
                    face_vertices = [int(x) for x in parts[1:1 + num_verts]]
                    for j in range(1, num_verts - 1):
                        indices.extend([face_vertices[0], face_vertices[j], face_vertices[j + 1]])
                face_vertices = [int(x) for x in parts[1:1 + num_verts]]

                # Fan triangulation: turn n-gon into n-2 triangles
                # Triangle fan: (v0, v1, v2), (v0, v2, v3), (v0, v3, v4), ...
                for j in range(1, num_verts - 1):
                    indices.extend([face_vertices[0], face_vertices[j], face_vertices[j + 1]])

        if vertices:
            self.vertices = np.array(vertices, dtype=np.float32)
        if indices:
            self.indices = np.array(indices, dtype=np.uint32)
        if colors:
            self.colors = np.array(colors, dtype=np.float32)
        else:
            # Generate colors
            if self.vertices is not None:
                num_vertices = len(self.vertices) // 3
                colors = []
                for i in range(num_vertices):
                    r = (np.sin(i * 0.1) + 1) / 2
                    g = (np.sin(i * 0.1 + 2) + 1) / 2
                    b = (np.sin(i * 0.1 + 4) + 1) / 2
                    colors.extend([r, g, b])
                self.colors = np.array(colors, dtype=np.float32)

        # Compute normals
        self.normals = self._compute_normals()

    def _compute_normals(self):
        """Compute vertex normals from faces."""
        if self.vertices is None or self.indices is None:
            return None

        num_vertices = len(self.vertices) // 3
        normals = np.zeros(num_vertices * 3, dtype=np.float32)

        for i in range(0, len(self.indices), 3):
            i0, i1, i2 = self.indices[i], self.indices[i + 1], self.indices[i + 2]

            v0 = self.vertices[i0*3:i0*3+3]
            v1 = self.vertices[i1*3:i1*3+3]
            v2 = self.vertices[i2*3:i2*3+3]

            edge1 = v1 - v0
            edge2 = v2 - v0
            face_normal = np.cross(edge1, edge2)

            normals[i0*3:i0*3+3] += face_normal
            normals[i1*3:i1*3+3] += face_normal
            normals[i2*3:i2*3+3] += face_normal

        # Normalize
        for i in range(num_vertices):
            n = normals[i*3:i*3+3]
            length = np.linalg.norm(n)
            if length > 0:
                normals[i*3:i*3+3] /= length

        return normals


def load_model(filepath, **kwargs):
    """Load a 3D model from file based on extension.

    Args:
        filepath: Path to the model file (.obj or .ply)
        **kwargs: Additional arguments passed to the model class

    Returns:
        Geometry object with loaded data, or None if loading fails
    """
    if not os.path.exists(filepath):
        print(f"Error: File not found: {filepath}")
        return None

    ext = os.path.splitext(filepath)[1].lower()

    if ext == '.obj':
        return OBJModel(filepath, **kwargs)
    elif ext == '.ply':
        return PLYModel(filepath, **kwargs)
    else:
        print(f"Error: Unsupported file format: {ext}")
        return None