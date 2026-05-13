import math
import numpy as np

class Vec3:
    """3D向量类，支持各种向量运算"""
    
    def __init__(self, e0=0.0, e1=0.0, e2=0.0):
        self.e = np.array([float(e0), float(e1), float(e2)])
    
    @property
    def x(self): return self.e[0]
    @property
    def y(self): return self.e[1]
    @property
    def z(self): return self.e[2]
    
    def __neg__(self):
        return Vec3(-self.e[0], -self.e[1], -self.e[2])
    
    def __getitem__(self, i):
        return self.e[i]
    
    def __add__(self, v):
        return Vec3(self.e[0] + v.e[0], self.e[1] + v.e[1], self.e[2] + v.e[2])
    
    def __sub__(self, v):
        return Vec3(self.e[0] - v.e[0], self.e[1] - v.e[1], self.e[2] - v.e[2])
    
    def __mul__(self, t):
        if isinstance(t, Vec3):
            return Vec3(self.e[0] * t.e[0], self.e[1] * t.e[1], self.e[2] * t.e[2])
        return Vec3(self.e[0] * t, self.e[1] * t, self.e[2] * t)
    
    def __rmul__(self, t):
        return self * t
    
    def __truediv__(self, t):
        return self * (1.0 / t)
    
    def length(self):
        return math.sqrt(self.length_squared())
    
    def length_squared(self):
        return self.e[0]**2 + self.e[1]**2 + self.e[2]**2
    
    def near_zero(self):
        s = 1e-8
        return abs(self.e[0]) < s and abs(self.e[1]) < s and abs(self.e[2]) < s
    
    def __repr__(self):
        return f"Vec3({self.e[0]:.3f}, {self.e[1]:.3f}, {self.e[2]:.3f})"

def dot(u, v):
    return u.e[0] * v.e[0] + u.e[1] * v.e[1] + u.e[2] * v.e[2]

def cross(u, v):
    return Vec3(
        u.e[1] * v.e[2] - u.e[2] * v.e[1],
        u.e[2] * v.e[0] - u.e[0] * v.e[2],
        u.e[0] * v.e[1] - u.e[1] * v.e[0]
    )

def unit_vector(v):
    return v / v.length()

def random_vec3():
    return Vec3(np.random.random(), np.random.random(), np.random.random())

def random_vec3_range(min_val, max_val):
    return Vec3(
        np.random.uniform(min_val, max_val),
        np.random.uniform(min_val, max_val),
        np.random.uniform(min_val, max_val)
    )

def random_in_unit_sphere():
    while True:
        p = random_vec3_range(-1, 1)
        if p.length_squared() < 1:
            return p

def random_unit_vector():
    return unit_vector(random_in_unit_sphere())

def random_in_hemisphere(normal):
    in_unit_sphere = random_in_unit_sphere()
    if dot(in_unit_sphere, normal) > 0.0:
        return in_unit_sphere
    else:
        return -in_unit_sphere

def random_in_unit_disk():
    while True:
        p = Vec3(np.random.uniform(-1, 1), np.random.uniform(-1, 1), 0)
        if p.length_squared() < 1:
            return p

def reflect(v, n):
    return v - 2 * dot(v, n) * n

def refract(uv, n, etai_over_etat):
    cos_theta = min(dot(-uv, n), 1.0)
    r_out_perp = etai_over_etat * (uv + cos_theta * n)
    r_out_parallel = -math.sqrt(abs(1.0 - r_out_perp.length_squared())) * n
    return r_out_perp + r_out_parallel

def reflectance(cosine, ref_idx):
    # Schlick's approximation
    r0 = (1 - ref_idx) / (1 + ref_idx)
    r0 = r0 * r0
    return r0 + (1 - r0) * math.pow((1 - cosine), 5)

# 别名
Color = Vec3
Point3 = Vec3
