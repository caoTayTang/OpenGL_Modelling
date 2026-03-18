import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import math
from .base import Geometry


class Cube(Geometry):
    VERTEX_SHADER = "shaders/color_interp.vert"
    FRAGMENT_SHADER = "shaders/color_interp.frag"

    def __init__(self, size=1.0, vert_shader=None, frag_shader=None):
        self.size = size
        super().__init__(vert_shader, frag_shader)
        self._generate_geometry()

    def _generate_geometry(self):
        s = self.size / 2
        self.vertices = np.array([
            [-s, -s, +s],  # 0: A
            [+s, -s, +s],  # 1: B
            [+s, -s, -s],  # 2: C
            [-s, -s, -s],  # 3: D
            [-s, +s, +s],  # 4: E
            [+s, +s, +s],  # 5: F
            [+s, +s, -s],  # 6: G
            [-s, +s, -s],  # 7: H
        ], dtype=np.float32)

        self.normals = self.vertices.copy()
        self.normals = self.normals / np.linalg.norm(self.normals, axis=1, keepdims=True)

        self.colors = np.array([
            [1.0, 0.0, 0.0],
            [1.0, 0.0, 1.0],
            [0.0, 0.0, 1.0],
            [0.0, 0.0, 0.0],
            [1.0, 1.0, 0.0],
            [1.0, 1.0, 1.0],
            [0.0, 1.0, 1.0],
            [0.0, 1.0, 0.0],
        ], dtype=np.float32)

        self.indices = np.array([
            # Front (0, 1, 4, 4, 1, 5)
            0, 1, 4, 1, 5, 4,
            # Right (1, 2, 5, 5, 2, 6)
            1, 2, 5, 2, 6, 5,
            # Back (2, 3, 6, 6, 3, 7)
            2, 3, 6, 3, 7, 6,
            # Left (3, 0, 7, 7, 0, 4)
            3, 0, 7, 0, 4, 7,
            # Top (4, 5, 7, 7, 5, 6)
            4, 5, 7, 5, 6, 7,
            # Bottom (0, 3, 1, 1, 3, 2)
            0, 3, 1, 1, 3, 2
        ], dtype=np.int32)


class SphereSubdivision(Geometry):
    """Sphere created by subdividing a tetrahedron and normalizing vertices"""
    VERTEX_SHADER = "shaders/color_interp.vert"
    FRAGMENT_SHADER = "shaders/color_interp.frag"

    def __init__(self, radius=0.5, subdivisions=3, vert_shader=None, frag_shader=None):
        self.radius = radius
        self.subdivisions = subdivisions
        super().__init__(vert_shader, frag_shader)
        self._generate_geometry()

    def _generate_geometry(self):
        phi = (1 + math.sqrt(5)) / 2
        vertices = [
            [-1, phi, 0], [1, phi, 0], [-1, -phi, 0], [1, -phi, 0],
            [0, -1, phi], [0, 1, phi], [0, -1, -phi], [0, 1, -phi],
            [phi, 0, -1], [phi, 0, 1], [-phi, 0, -1], [-phi, 0, 1]
        ]
        
        normalized_verts = []
        for v in vertices:
            norm = math.sqrt(sum(x*x for x in v))
            normalized_verts.append([v[0]/norm * self.radius, v[1]/norm * self.radius, v[2]/norm * self.radius])
        vertices = normalized_verts

        faces = [
            [0, 11, 5], [0, 5, 1], [0, 1, 7], [0, 7, 10], [0, 10, 11],
            [1, 5, 9], [5, 11, 4], [11, 10, 2], [10, 7, 6], [7, 1, 8],
            [3, 9, 4], [3, 4, 2], [3, 2, 6], [3, 6, 8], [3, 8, 9],
            [4, 9, 5], [2, 4, 11], [6, 2, 10], [8, 6, 7], [9, 8, 1]
        ]

        for _ in range(self.subdivisions):
            new_faces = []
            midpoint_cache = {}

            def get_midpoint(v1, v2):
                key = tuple(sorted([v1, v2]))
                if key in midpoint_cache:
                    return midpoint_cache[key]
                mid = [(vertices[v1][i] + vertices[v2][i]) / 2 for i in range(3)]
                norm = math.sqrt(sum(m * m for m in mid))
                mid = [m / norm * self.radius for m in mid]
                vertices.append(mid)
                idx = len(vertices) - 1
                midpoint_cache[key] = idx
                return idx

            for face in faces:
                a, b, c = face
                ab = get_midpoint(a, b)
                bc = get_midpoint(b, c)
                ca = get_midpoint(c, a)
                new_faces.extend([
                    [a, ab, ca], [b, bc, ab], [c, ca, bc], [ab, bc, ca]
                ])
            faces = new_faces

        self.vertices = np.array(vertices, dtype=np.float32)
        self.normals = self.vertices.copy()
        self.normals = self.normals / np.linalg.norm(self.normals, axis=1, keepdims=True)

        self.colors = np.zeros((len(vertices), 3), dtype=np.float32)
        for i in range(len(vertices)):
            v = self.vertices[i]
            self.colors[i] = [
                (v[0] / self.radius + 1) / 2,
                (v[1] / self.radius + 1) / 2,
                (v[2] / self.radius + 1) / 2
            ]

        self.indices = np.array(faces, dtype=np.int32).flatten()


class UVSphere(Geometry):
    """Sphere created by UV grid projection"""
    VERTEX_SHADER = "shaders/color_interp.vert"
    FRAGMENT_SHADER = "shaders/color_interp.frag"

    def __init__(self, radius=0.5, segments=32, rings=16, vert_shader=None, frag_shader=None):
        self.radius = radius
        self.segments = segments
        self.rings = rings
        super().__init__(vert_shader, frag_shader)
        self._generate_geometry()

    def _generate_geometry(self):
        vertices = []
        normals = []
        colors = []
        indices = []

        for ring in range(self.rings + 1):
            theta = math.pi * ring / self.rings
            sin_theta = math.sin(theta)
            cos_theta = math.cos(theta)

            for seg in range(self.segments + 1):
                phi = 2 * math.pi * seg / self.segments
                sin_phi = math.sin(phi)
                cos_phi = math.cos(phi)

                x = cos_phi * sin_theta
                y = cos_theta
                z = sin_phi * sin_theta

                vertices.append([x * self.radius, y * self.radius, z * self.radius])
                normals.append([x, y, z])
                colors.append([(x + 1) / 2, (y + 1) / 2, (z + 1) / 2])

        for ring in range(self.rings):
            for seg in range(self.segments):
                current = ring * (self.segments + 1) + seg
                next_row = current + self.segments + 1

                indices.extend([
                    current, next_row, current + 1,
                    next_row, next_row + 1, current + 1
                ])

        self.vertices = np.array(vertices, dtype=np.float32)
        self.normals = np.array(normals, dtype=np.float32)
        self.colors = np.array(colors, dtype=np.float32)
        self.indices = np.array(indices, dtype=np.int32)


class LatLongSphere(Geometry):
    """Sphere created using latitude-longitude coordinates"""
    VERTEX_SHADER = "shaders/color_interp.vert"
    FRAGMENT_SHADER = "shaders/color_interp.frag"

    def __init__(self, radius=0.5, lat_bands=20, long_bands=20, vert_shader=None, frag_shader=None):
        self.radius = radius
        self.lat_bands = lat_bands
        self.long_bands = long_bands
        super().__init__(vert_shader, frag_shader)
        self._generate_geometry()

    def _generate_geometry(self):
        vertices = []
        normals = []
        colors = []
        indices = []

        for lat in range(self.lat_bands + 1):
            theta = math.pi * lat / self.lat_bands
            sin_theta = math.sin(theta)
            cos_theta = math.cos(theta)

            for lon in range(self.long_bands + 1):
                phi = 2 * math.pi * lon / self.long_bands
                sin_phi = math.sin(phi)
                cos_phi = math.cos(phi)

                x = cos_phi * sin_theta
                y = cos_theta
                z = sin_phi * sin_theta

                u = 1 - (lon / self.long_bands)
                v = 1 - (lat / self.lat_bands)

                vertices.append([x * self.radius, y * self.radius, z * self.radius])
                normals.append([x, y, z])
                colors.append([u, v, 1 - (u + v) / 2])

        for lat in range(self.lat_bands):
            for lon in range(self.long_bands):
                first = lat * (self.long_bands + 1) + lon
                second = first + self.long_bands + 1

                indices.extend([
                    first, second, first + 1,
                    second, second + 1, first + 1
                ])

        self.vertices = np.array(vertices, dtype=np.float32)
        self.normals = np.array(normals, dtype=np.float32)
        self.colors = np.array(colors, dtype=np.float32)
        self.indices = np.array(indices, dtype=np.int32)


class Cylinder(Geometry):
    VERTEX_SHADER = "shaders/color_interp.vert"
    FRAGMENT_SHADER = "shaders/color_interp.frag"

    def __init__(self, radius=0.5, height=1.0, segments=32, vert_shader=None, frag_shader=None):
        self.radius = radius
        self.height = height
        self.segments = segments
        super().__init__(vert_shader, frag_shader)
        self._generate_geometry()

    def _generate_geometry(self):
        h = self.height / 2

        vertices = []
        normals = []
        colors = []
        indices = []

        for i in range(self.segments):
            angle = 2 * math.pi * i / self.segments
            x = self.radius * math.cos(angle)
            z = self.radius * math.sin(angle)

            vertices.extend([
                [x, -h, z], [x, h, z]
            ])
            normals.extend([
                [math.cos(angle), 0, math.sin(angle)],
                [math.cos(angle), 0, math.sin(angle)]
            ])
            colors.extend([
                [(x + self.radius) / (2 * self.radius), 0.5, (z + self.radius) / (2 * self.radius)],
                [(x + self.radius) / (2 * self.radius), 0.5, (z + self.radius) / (2 * self.radius)]
            ])

        for i in range(self.segments):
            i0 = i * 2
            i1 = i0 + 1
            i2 = ((i + 1) % self.segments) * 2
            i3 = i2 + 1
            indices.extend([i0, i2, i1, i1, i2, i3])

        center_bottom = len(vertices)
        vertices.append([0, -h, 0])
        normals.append([0, -1, 0])
        colors.append([0.5, 0.5, 0.5])

        for i in range(self.segments):
            angle = 2 * math.pi * i / self.segments
            vertices.append([self.radius * math.cos(angle), -h, self.radius * math.sin(angle)])
            normals.append([0, -1, 0])
            colors.append([(math.cos(angle) + 1) / 2, 0.5, (math.sin(angle) + 1) / 2])

        for i in range(self.segments):
            indices.extend([center_bottom, center_bottom + i + 1, center_bottom + ((i + 1) % self.segments) + 1])

        center_top = len(vertices)
        vertices.append([0, h, 0])
        normals.append([0, 1, 0])
        colors.append([0.5, 0.5, 0.5])

        for i in range(self.segments):
            angle = 2 * math.pi * i / self.segments
            vertices.append([self.radius * math.cos(angle), h, self.radius * math.sin(angle)])
            normals.append([0, 1, 0])
            colors.append([(math.cos(angle) + 1) / 2, 0.5, (math.sin(angle) + 1) / 2])

        for i in range(self.segments):
            indices.extend([center_top, center_top + ((i + 1) % self.segments) + 1, center_top + i + 1])

        self.vertices = np.array(vertices, dtype=np.float32)
        self.normals = np.array(normals, dtype=np.float32)
        self.colors = np.array(colors, dtype=np.float32)
        self.indices = np.array(indices, dtype=np.int32)


class Cone(Geometry):
    VERTEX_SHADER = "shaders/color_interp.vert"
    FRAGMENT_SHADER = "shaders/color_interp.frag"

    def __init__(self, radius=0.5, height=1.0, segments=32, vert_shader=None, frag_shader=None):
        self.radius = radius
        self.height = height
        self.segments = segments
        super().__init__(vert_shader, frag_shader)
        self._generate_geometry()

    def _generate_geometry(self):
        h = self.height / 2

        vertices = []
        normals = []
        colors = []
        indices = []

        for i in range(self.segments):
            angle = 2 * math.pi * i / self.segments
            next_angle = 2 * math.pi * (i + 1) / self.segments

            x1, z1 = self.radius * math.cos(angle), self.radius * math.sin(angle)
            x2, z2 = self.radius * math.cos(next_angle), self.radius * math.sin(next_angle)

            vertices.extend([
                [0, h, 0], [x1, -h, z1], [x2, -h, z2]
            ])

            n1 = math.cos(angle)
            n2 = math.sin(angle)
            n3 = math.cos(next_angle)
            n4 = math.sin(next_angle)

            normals.extend([
                [n1, 0.5, n2], [n1, 0.5, n2], [n3, 0.5, n4]
            ])
            colors.extend([
                [1.0, 0.5, 0.0], [0.0, 0.5, 1.0], [0.5, 1.0, 0.0]
            ])

            indices.extend([len(vertices) - 3, len(vertices) - 2, len(vertices) - 1])

        center_bottom = len(vertices)
        vertices.append([0, -h, 0])
        normals.append([0, -1, 0])
        colors.append([0.5, 0.5, 0.5])

        for i in range(self.segments):
            angle = 2 * math.pi * i / self.segments
            vertices.append([self.radius * math.cos(angle), -h, self.radius * math.sin(angle)])
            normals.append([0, -1, 0])
            colors.append([(math.cos(angle) + 1) / 2, 0.5, (math.sin(angle) + 1) / 2])

        for i in range(self.segments):
            indices.extend([center_bottom, center_bottom + i + 1, center_bottom + ((i + 1) % self.segments) + 1])

        self.vertices = np.array(vertices, dtype=np.float32)
        self.normals = np.array(normals, dtype=np.float32)
        self.colors = np.array(colors, dtype=np.float32)
        self.indices = np.array(indices, dtype=np.int32)


class TruncatedCone(Geometry):
    VERTEX_SHADER = "shaders/color_interp.vert"
    FRAGMENT_SHADER = "shaders/color_interp.frag"

    def __init__(self, radius_top=0.3, radius_bottom=0.5, height=1.0, segments=32, vert_shader=None, frag_shader=None):
        self.radius_top = radius_top
        self.radius_bottom = radius_bottom
        self.height = height
        self.segments = segments
        super().__init__(vert_shader, frag_shader)
        self._generate_geometry()

    def _generate_geometry(self):
        h = self.height / 2

        vertices = []
        normals = []
        colors = []
        indices = []

        for i in range(self.segments):
            angle = 2 * math.pi * i / self.segments
            next_angle = 2 * math.pi * (i + 1) / self.segments

            x1_t, z1_t = self.radius_top * math.cos(angle), self.radius_top * math.sin(angle)
            x2_t, z2_t = self.radius_top * math.cos(next_angle), self.radius_top * math.sin(next_angle)
            x1_b, z1_b = self.radius_bottom * math.cos(angle), self.radius_bottom * math.sin(angle)
            x2_b, z2_b = self.radius_bottom * math.cos(next_angle), self.radius_bottom * math.sin(next_angle)

            vertices.extend([
                [x1_t, h, z1_t], [x1_b, -h, z1_b], [x2_b, -h, z2_b],
                [x1_t, h, z1_t], [x2_b, -h, z2_b], [x2_t, h, z2_t]
            ])

            nx = math.cos(angle)
            nz = math.sin(angle)
            normals.extend([
                [nx, 0.3, nz], [nx, 0.3, nz], [nx, 0.3, nz],
                [nx, 0.3, nz], [nx, 0.3, nz], [nx, 0.3, nz]
            ])
            colors.extend([
                [1, 0, 0], [0, 1, 0], [0, 0, 1],
                [1, 1, 0], [0, 1, 1], [1, 0, 1]
            ])

            indices.extend([
                len(vertices) - 6, len(vertices) - 5, len(vertices) - 4,
                len(vertices) - 3, len(vertices) - 2, len(vertices) - 1
            ])

        center_bottom = len(vertices)
        vertices.append([0, -h, 0])
        normals.append([0, -1, 0])
        colors.append([0.5, 0.5, 0.5])

        for i in range(self.segments):
            angle = 2 * math.pi * i / self.segments
            vertices.append([self.radius_bottom * math.cos(angle), -h, self.radius_bottom * math.sin(angle)])
            normals.append([0, -1, 0])
            colors.append([(math.cos(angle) + 1) / 2, 0.5, (math.sin(angle) + 1) / 2])

        for i in range(self.segments):
            indices.extend([center_bottom, center_bottom + i + 1, center_bottom + ((i + 1) % self.segments) + 1])

        center_top = len(vertices)
        vertices.append([0, h, 0])
        normals.append([0, 1, 0])
        colors.append([0.5, 0.5, 0.5])

        for i in range(self.segments):
            angle = 2 * math.pi * i / self.segments
            vertices.append([self.radius_top * math.cos(angle), h, self.radius_top * math.sin(angle)])
            normals.append([0, 1, 0])
            colors.append([(math.cos(angle) + 1) / 2, 0.5, (math.sin(angle) + 1) / 2])

        for i in range(self.segments):
            indices.extend([center_top, center_top + ((i + 1) % self.segments) + 1, center_top + i + 1])

        self.vertices = np.array(vertices, dtype=np.float32)
        self.normals = np.array(normals, dtype=np.float32)
        self.colors = np.array(colors, dtype=np.float32)
        self.indices = np.array(indices, dtype=np.int32)


class Tetrahedron(Geometry):
    VERTEX_SHADER = "shaders/color_interp.vert"
    FRAGMENT_SHADER = "shaders/color_interp.frag"

    def __init__(self, size=1.0, vert_shader=None, frag_shader=None):
        self.size = size
        super().__init__(vert_shader, frag_shader)
        self._generate_geometry()

    def _generate_geometry(self):
        s = self.size
        a = [s, s, s]
        b = [-s, -s, s]
        c = [-s, s, -s]
        d = [s, -s, -s]

        self.vertices = np.array([a, b, c, d], dtype=np.float32)

        def normalize(v):
            n = math.sqrt(v[0]**2 + v[1]**2 + v[2]**2)
            return [v[0]/n, v[1]/n, v[2]/n]

        def face_normal(v1, v2, v3):
            u = [v2[0]-v1[0], v2[1]-v1[1], v2[2]-v1[2]]
            v = [v3[0]-v1[0], v3[1]-v1[1], v3[2]-v1[2]]
            n = [u[1]*v[2]-u[2]*v[1], u[2]*v[0]-u[0]*v[2], u[0]*v[1]-u[1]*v[0]]
            return normalize(n)

        self.normals = np.array([
            face_normal(a, b, c),
            face_normal(a, b, d),
            face_normal(a, c, d),
            face_normal(b, d, c)
        ], dtype=np.float32)

        self.colors = np.array([
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, 0.0, 1.0],
            [1.0, 1.0, 0.0]
        ], dtype=np.float32)

        self.indices = np.array([0, 1, 2, 0, 1, 3, 0, 2, 3, 1, 3, 2], dtype=np.int32)


class Torus(Geometry):
    VERTEX_SHADER = "shaders/color_interp.vert"
    FRAGMENT_SHADER = "shaders/color_interp.frag"

    def __init__(self, major_radius=0.5, minor_radius=0.2, major_segments=32, minor_segments=16, vert_shader=None, frag_shader=None):
        self.major_radius = major_radius
        self.minor_radius = minor_radius
        self.major_segments = major_segments
        self.minor_segments = minor_segments
        super().__init__(vert_shader, frag_shader)
        self._generate_geometry()

    def _generate_geometry(self):
        vertices = []
        normals = []
        colors = []
        indices = []

        for i in range(self.major_segments):
            theta = 2 * math.pi * i / self.major_segments
            for j in range(self.minor_segments):
                phi = 2 * math.pi * j / self.minor_segments

                x = (self.major_radius + self.minor_radius * math.cos(phi)) * math.cos(theta)
                y = self.minor_radius * math.sin(phi)
                z = (self.major_radius + self.minor_radius * math.cos(phi)) * math.sin(theta)

                nx = math.cos(phi) * math.cos(theta)
                ny = math.sin(phi)
                nz = math.cos(phi) * math.sin(theta)

                vertices.append([x, y, z])
                normals.append([nx, ny, nz])
                colors.append([(nx + 1) / 2, (ny + 1) / 2, (nz + 1) / 2])

        for i in range(self.major_segments):
            for j in range(self.minor_segments):
                current = i * self.minor_segments + j
                next_major = ((i + 1) % self.major_segments) * self.minor_segments + j
                next_minor = i * self.minor_segments + (j + 1) % self.minor_segments
                next_both = ((i + 1) % self.major_segments) * self.minor_segments + (j + 1) % self.minor_segments

                indices.extend([current, next_minor, next_major])
                indices.extend([next_major, next_minor, next_both])

        self.vertices = np.array(vertices, dtype=np.float32)
        self.normals = np.array(normals, dtype=np.float32)
        self.colors = np.array(colors, dtype=np.float32)
        self.indices = np.array(indices, dtype=np.int32)


class Prism(Geometry):
    VERTEX_SHADER = "shaders/color_interp.vert"
    FRAGMENT_SHADER = "shaders/color_interp.frag"

    def __init__(self, sides=5, radius=0.5, height=1.0, vert_shader=None, frag_shader=None):
        self.sides = sides
        self.radius = radius
        self.height = height
        super().__init__(vert_shader, frag_shader)
        self._generate_geometry()

    def _generate_geometry(self):
        h = self.height / 2
        
        vertices = []
        normals = []
        colors = []
        
        # Generate vertices for bottom and top circles
        bottom_verts = []
        top_verts = []
        
        for i in range(self.sides):
            angle = 2 * math.pi * i / self.sides
            x = self.radius * math.cos(angle)
            z = self.radius * math.sin(angle)
            
            # Bottom vertex
            bottom_verts.append([x, -h, z])
            normals.append([0, -1, 0])
            colors.append([(x/self.radius + 1)/2, 0.5, (z/self.radius + 1)/2])
            
            # Top vertex
            top_verts.append([x, h, z])
            normals.append([0, 1, 0])
            colors.append([(x/self.radius + 1)/2, 0.5, (z/self.radius + 1)/2])
        
        # Add bottom center
        bottom_center_idx = len(vertices)
        vertices.append([0, -h, 0])
        normals.append([0, -1, 0])
        colors.append([0.5, 0.5, 0.5])
        
        # Add bottom vertices
        for v in bottom_verts:
            vertices.append(v)
        
        # Add top center
        top_center_idx = len(vertices)
        vertices.append([0, h, 0])
        normals.append([0, 1, 0])
        colors.append([0.5, 0.5, 0.5])
        
        # Add top vertices
        for v in top_verts:
            vertices.append(v)
        
        # Add side vertices (each side has 4 vertices for proper triangles)
        side_start_idx = len(vertices)
        for i in range(self.sides):
            next_i = (i + 1) % self.sides
            
            # Get bottom and top vertices
            b1 = bottom_verts[i]
            b2 = bottom_verts[next_i]
            t1 = top_verts[i]
            t2 = top_verts[next_i]
            
            # Calculate normal for this side
            nx = math.cos(2 * math.pi * (i + 0.5) / self.sides)
            nz = math.sin(2 * math.pi * (i + 0.5) / self.sides)
            
            # Add 4 vertices for this side face (2 triangles)
            vertices.extend([b1, b2, t1, t2])
            for _ in range(4):
                normals.append([nx, 0, nz])
                colors.append([(nx+1)/2, 0.5, (nz+1)/2])
        
        # Generate indices
        indices = []
        
        # Bottom face (triangle fan)
        for i in range(self.sides):
            indices.extend([bottom_center_idx, bottom_center_idx + 1 + i, bottom_center_idx + 1 + (i + 1) % self.sides])
        
        # Top face (triangle fan)
        for i in range(self.sides):
            indices.extend([top_center_idx, top_center_idx + 1 + (i + 1) % self.sides, top_center_idx + 1 + i])
        
        # Side faces
        for i in range(self.sides):
            base = side_start_idx + i * 4
            # Two triangles per side
            indices.extend([base, base + 1, base + 2])
            indices.extend([base + 2, base + 1, base + 3])
        
        self.vertices = np.array(vertices, dtype=np.float32)
        self.normals = np.array(normals, dtype=np.float32)
        self.colors = np.array(colors, dtype=np.float32)
        self.indices = np.array(indices, dtype=np.int32)


class ParametricSurface(Geometry):
    VERTEX_SHADER = "shaders/color_interp.vert"
    FRAGMENT_SHADER = "shaders/color_interp.frag"

    def __init__(self, func=None, x_range=(-1, 1), y_range=(-1, 1), resolution=30, vert_shader=None, frag_shader=None):
        self.func = func or (lambda x, y: x**2 + y**2)
        self.x_range = x_range
        self.y_range = y_range
        self.resolution = resolution
        super().__init__(vert_shader, frag_shader)
        self._generate_geometry()

    def _generate_geometry(self):
        vertices = []
        normals = []
        colors = []
        indices = []

        x_min, x_max = self.x_range
        y_min, y_max = self.y_range
        res = self.resolution

        for i in range(res + 1):
            for j in range(res + 1):
                x = x_min + (x_max - x_min) * i / res
                y = y_min + (y_max - y_min) * j / res
                z = self.func(x, y)

                vertices.append([x, y, z])

                h = 0.001
                dzdx = (self.func(x + h, y) - self.func(x - h, y)) / (2 * h)
                dzdy = (self.func(x, y + h) - self.func(x, y - h)) / (2 * h)
                n = [-dzdx, -dzdy, 1]
                norm = math.sqrt(n[0]**2 + n[1]**2 + n[2]**2)
                n = [ni / norm for ni in n]

                normals.append(n)
                colors.append([(z + 1) / 2, (x + 1) / 2, (y + 1) / 2])

        for i in range(res):
            for j in range(res):
                current = i * (res + 1) + j
                next_row = (i + 1) * (res + 1) + j

                indices.extend([current, next_row, current + 1])
                indices.extend([next_row, next_row + 1, current + 1])

        self.vertices = np.array(vertices, dtype=np.float32)
        self.normals = np.array(normals, dtype=np.float32)
        self.colors = np.array(colors, dtype=np.float32)
        self.indices = np.array(indices, dtype=np.int32)


def himmelblau(x, y):
    return (x**2 + y - 11)**2 + (x + y**2 - 7)**2


def rosenbrock(x, y, a=1, b=100):
    return (a - x)**2 + b * (y - x**2)**2


def booth(x, y):
    return (x + 2*y - 7)**2 + (2*x + y - 5)**2


def quadratic(x, y):
    return x**2 + y**2


class OBJLoader(Geometry):
    VERTEX_SHADER = "shaders/color_interp.vert"
    FRAGMENT_SHADER = "shaders/color_interp.frag"

    def __init__(self, filepath, vert_shader=None, frag_shader=None):
        self.filepath = filepath
        super().__init__(vert_shader, frag_shader)
        self._load_obj()

    def _load_obj(self):
        vertices = []
        normals = []
        texcoords = []
        indices = []
        vertex_normals = {}

        with open(self.filepath, 'r') as f:
            for line in f:
                parts = line.strip().split()
                if not parts:
                    continue

                if parts[0] == 'v':
                    vertices.append([float(parts[1]), float(parts[2]), float(parts[3])])
                elif parts[0] == 'vn':
                    normals.append([float(parts[1]), float(parts[2]), float(parts[3])])
                elif parts[0] == 'vt':
                    texcoords.append([float(parts[1]), float(parts[2])])
                elif parts[0] == 'f':
                    face_indices = []
                    for part in parts[1:]:
                        indices_part = part.split('/')
                        v_idx = int(indices_part[0]) - 1

                        if len(indices_part) > 2 and indices_part[2]:
                            vn_idx = int(indices_part[2]) - 1
                            if v_idx not in vertex_normals:
                                vertex_normals[v_idx] = []
                            vertex_normals[v_idx].append(normals[vn_idx])

                        face_indices.append(v_idx)

                    for i in range(1, len(face_indices) - 1):
                        indices.extend([face_indices[0], face_indices[i], face_indices[i + 1]])

        if not normals and vertex_normals:
            for v_idx, ns in vertex_normals.items():
                n = np.mean(ns, axis=0)
                n = n / np.linalg.norm(n)
                normals.append(list(n))

        while len(normals) < len(vertices):
            normals.append([0, 1, 0])

        self.vertices = np.array(vertices, dtype=np.float32)
        self.normals = np.array(normals, dtype=np.float32)
        self.colors = np.ones((len(vertices), 3), dtype=np.float32) * 0.7
        self.indices = np.array(indices, dtype=np.int32)
