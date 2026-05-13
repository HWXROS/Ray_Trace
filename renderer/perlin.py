"""
Perlin 噪声 - 用于生成程序化纹理
课程设计要求: "利用Perlin噪声生成非朗伯表面材质"
"""

import numpy as np
import taichi as ti

vec3 = ti.types.vector(3, ti.f32)


class PerlinNoise:
    """Python 端 Perlin 噪声生成器"""
    
    def __init__(self, seed=42):
        np.random.seed(seed)
        self.point_count = 256
        
        # 随机梯度向量
        self.ranvec = np.random.uniform(-1, 1, (self.point_count, 3)).astype(np.float32)
        # 归一化
        norms = np.linalg.norm(self.ranvec, axis=1, keepdims=True)
        self.ranvec /= norms
        
        # 置换表
        self.perm_x = np.random.permutation(self.point_count).astype(np.int32)
        self.perm_y = np.random.permutation(self.point_count).astype(np.int32)
        self.perm_z = np.random.permutation(self.point_count).astype(np.int32)
    
    def noise(self, p):
        """
        3D Perlin 噪声
        p: numpy array of shape (3,)
        返回值: [-1, 1]
        """
        u = p[0] - np.floor(p[0])
        v = p[1] - np.floor(p[1])
        w = p[2] - np.floor(p[2])
        
        # Hermite 插值（平滑）
        u = u * u * (3 - 2 * u)
        v = v * v * (3 - 2 * v)
        w = w * w * (3 - 2 * w)
        
        i = int(np.floor(p[0]))
        j = int(np.floor(p[1]))
        k = int(np.floor(p[2]))
        
        c = np.zeros((2, 2, 2, 3), dtype=np.float32)
        for di in range(2):
            for dj in range(2):
                for dk in range(2):
                    idx = self.perm_x[(i + di) & 255] ^ self.perm_y[(j + dj) & 255] ^ self.perm_z[(k + dk) & 255]
                    c[di, dj, dk] = self.ranvec[idx]
        
        accum = 0.0
        for di in range(2):
            for dj in range(2):
                for dk in range(2):
                    weight_v = np.array([u - di, v - dj, w - dk], dtype=np.float32)
                    accum += ((di * u + (1 - di) * (1 - u)) *
                             (dj * v + (1 - dj) * (1 - v)) *
                             (dk * w + (1 - dk) * (1 - w)) *
                             np.dot(c[di, dj, dk], weight_v))
        
        return accum
    
    def turb(self, p, depth=7):
        """
        湍流噪声（多频段叠加）
        返回值: [0, 1]
        """
        accum = 0.0
        temp_p = p.copy()
        weight = 1.0
        
        for i in range(depth):
            accum += weight * self.noise(temp_p)
            weight *= 0.5
            temp_p *= 2
        
        return abs(accum)
    
    def marble_texture(self, p, scale=4.0):
        """大理石纹理"""
        return 0.5 * (1 + np.sin(scale * p[2] + 10 * self.turb(p)))
    
    def wood_texture(self, p, scale=10.0):
        """木纹纹理"""
        return 0.5 * (1 + np.sin(scale * self.turb(p)))
    
    def noise_color(self, p, color1=(0.8, 0.3, 0.1), color2=(0.2, 0.1, 0.05)):
        """基于噪声的颜色混合"""
        t = self.turb(p)
        c1 = np.array(color1)
        c2 = np.array(color2)
        return c1 * t + c2 * (1 - t)


# ========== Taichi 端 Perlin 噪声 ==========

# 预计算的 Perlin 数据（延迟初始化）
perlin_ranvec = None
perlin_perm_x = None
perlin_perm_y = None
perlin_perm_z = None

_perlin_initialized = False

def init_taichi_perlin(perlin: PerlinNoise = None, seed=42):
    """初始化 Taichi Perlin 噪声数据"""
    global _perlin_initialized, perlin_ranvec, perlin_perm_x, perlin_perm_y, perlin_perm_z
    if _perlin_initialized:
        return
    
    if perlin is None:
        perlin = PerlinNoise(seed)
    
    # 创建 Taichi fields
    perlin_ranvec = ti.Vector.field(3, dtype=ti.f32, shape=(256,))
    perlin_perm_x = ti.field(dtype=ti.i32, shape=(256,))
    perlin_perm_y = ti.field(dtype=ti.i32, shape=(256,))
    perlin_perm_z = ti.field(dtype=ti.i32, shape=(256,))
    
    # 拷贝数据到 Taichi field
    for i in range(256):
        perlin_ranvec[i] = vec3(perlin.ranvec[i])
        perlin_perm_x[i] = int(perlin.perm_x[i])
        perlin_perm_y[i] = int(perlin.perm_y[i])
        perlin_perm_z[i] = int(perlin.perm_z[i])
    
    _perlin_initialized = True
    print("[Perlin] Taichi Perlin 噪声已初始化")


@ti.func
def taichi_perlin_noise(p: vec3) -> ti.f32:
    """Taichi 端 3D Perlin 噪声"""
    u = p[0] - ti.floor(p[0])
    v = p[1] - ti.floor(p[1])
    w = p[2] - ti.floor(p[2])
    
    u = u * u * (3.0 - 2.0 * u)
    v = v * v * (3.0 - 2.0 * v)
    w = w * w * (3.0 - 2.0 * w)
    
    i = ti.cast(ti.floor(p[0]), ti.i32)
    j = ti.cast(ti.floor(p[1]), ti.i32)
    k = ti.cast(ti.floor(p[2]), ti.i32)
    
    accum = 0.0
    for di in range(2):
        for dj in range(2):
            for dk in range(2):
                idx = perlin_perm_x[(i + di) & 255] ^ perlin_perm_y[(j + dj) & 255] ^ perlin_perm_z[(k + dk) & 255]
                weight_v = vec3(u - di, v - dj, w - dk)
                accum += ((di * u + (1 - di) * (1 - u)) *
                         (dj * v + (1 - dj) * (1 - v)) *
                         (dk * w + (1 - dk) * (1 - w)) *
                         perlin_ranvec[idx].dot(weight_v))
    
    return accum


@ti.func
def taichi_perlin_turb(p: vec3, depth: ti.i32 = 7) -> ti.f32:
    """Taichi 端湍流噪声"""
    accum = 0.0
    temp_p = p
    weight = 1.0
    
    for i in range(depth):
        accum += weight * taichi_perlin_noise(temp_p)
        weight *= 0.5
        temp_p *= 2.0
    
    return ti.abs(accum)
