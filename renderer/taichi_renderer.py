"""
Taichi GPU 加速光线追踪器
利用 4060Ti 的 CUDA 核心进行并行渲染
"""

import taichi as ti
import numpy as np
from PIL import Image
import time
from .perlin import init_taichi_perlin, taichi_perlin_turb
from geometry.triangle import load_obj_model

# 初始化 Taichi，使用 CUDA GPU
ti.init(arch=ti.cuda, random_seed=42)

# ========== HDRI 环境贴图（全局可选） ==========
MAX_HDRI_WIDTH = 2048
MAX_HDRI_HEIGHT = 1024
_hdri_enabled = False
hdri_field = ti.Vector.field(3, dtype=ti.f32, shape=(MAX_HDRI_WIDTH, MAX_HDRI_HEIGHT))
hdri_size = ti.field(ti.i32, shape=(2,))  # [width, height]

def init_hdri(image_path, width=None, height=None):
    """加载 HDRI/equirectangular 环境贴图"""
    global _hdri_enabled
    from PIL import Image
    img = Image.open(image_path).convert('RGB')
    if width is None:
        width = min(img.width, MAX_HDRI_WIDTH)
    if height is None:
        height = min(img.height, MAX_HDRI_HEIGHT)
    img = img.resize((width, height), Image.LANCZOS)
    arr = np.array(img).astype(np.float32) / 255.0
    full_arr = np.zeros((MAX_HDRI_WIDTH, MAX_HDRI_HEIGHT, 3), dtype=np.float32)
    full_arr[:width, :height, :] = arr.transpose(1, 0, 2)
    hdri_field.from_numpy(full_arr)
    hdri_size[0] = width
    hdri_size[1] = height
    _hdri_enabled = True
    print(f"[HDRI] 已加载: {image_path} ({width}x{height})")

# ========== 数据类型定义 ==========
vec3 = ti.types.vector(3, ti.f32)

@ti.func
def sample_hdri(direction: vec3) -> vec3:
    """从 equirectangular HDRI field 采样颜色"""
    phi = ti.atan2(direction[2], direction[0])
    theta = ti.acos(ti.min(ti.max(direction[1], -1.0), 1.0))
    u = (phi + 3.14159265) / (2.0 * 3.14159265)
    v = theta / 3.14159265
    w = hdri_size[0]
    h = hdri_size[1]
    i = ti.cast(u * w, ti.i32) % w
    j = ti.cast(v * h, ti.i32) % h
    return hdri_field[i, j]

# 材质类型枚举
MAT_LAMBERTIAN = 0
MAT_METAL = 1
MAT_DIELECTRIC = 2
MAT_PERLIN = 3  # Perlin噪声纹理材质
MAT_EMISSIVE = 4  # 发光材质（直接发光，不散射）

# 球体结构体
Sphere = ti.types.struct(
    center=vec3,
    radius=ti.f32,
    mat_type=ti.i32,      # 材质类型
    albedo=vec3,          # 漫反射/金属颜色
    fuzz=ti.f32,          # 金属模糊度
    ir=ti.f32,            # 折射率
)

# 立方体结构体 (AABB - Axis Aligned Bounding Box)
Cube = ti.types.struct(
    min=vec3,
    max=vec3,
    mat_type=ti.i32,
    albedo=vec3,
    fuzz=ti.f32,
    ir=ti.f32,
)

# 三角形结构体
Triangle = ti.types.struct(
    v0=vec3,
    v1=vec3,
    v2=vec3,
    normal=vec3,
    mat_type=ti.i32,
    albedo=vec3,
    fuzz=ti.f32,
    ir=ti.f32,
)

# 相交结果结构体
HitResult = ti.types.struct(
    hit=ti.i32,
    t=ti.f32,
    p=vec3,
    normal=vec3,
    mat_type=ti.i32,
    albedo=vec3,
    fuzz=ti.f32,
    ir=ti.f32,
)

# 散射结果结构体
ScatterResult = ti.types.struct(
    ok=ti.i32,
    attenuation=vec3,
    direction=vec3,
)

# 相机结构体
Camera = ti.types.struct(
    origin=vec3,
    lower_left_corner=vec3,
    horizontal=vec3,
    vertical=vec3,
    u=vec3,
    v=vec3,
    w=vec3,
    lens_radius=ti.f32,
)

# BVH 加速结构节点
BVHNode = ti.types.struct(
    aabb_min=vec3,
    aabb_max=vec3,
    skip=ti.i32,       # 跳过整个子树后的下一个节点索引（线性化遍历）
    left=ti.i32,
    right=ti.i32,
    prim_type=ti.i32,  # -1=内部节点, 0=sphere, 1=cube, 2=triangle
    prim_idx=ti.i32,   # 图元在对应数组中的索引（叶子节点）
)

# 光源结构体（用于 NEE 直接采样）
Light = ti.types.struct(
    center=vec3,
    radius=ti.f32,
    color=vec3,
)


# ========== Taichi 数学函数 ==========
@ti.func
def random_vec3() -> vec3:
    return vec3(ti.random(), ti.random(), ti.random())

@ti.func
def random_vec3_range(min_val: ti.f32, max_val: ti.f32) -> vec3:
    return vec3(
        ti.random() * (max_val - min_val) + min_val,
        ti.random() * (max_val - min_val) + min_val,
        ti.random() * (max_val - min_val) + min_val,
    )

@ti.func
def random_in_unit_sphere() -> vec3:
    p = vec3(0.0, 0.0, 0.0)
    while True:
        p = random_vec3_range(-1.0, 1.0)
        if p.dot(p) < 1.0:
            break
    return p

@ti.func
def random_unit_vector() -> vec3:
    return random_in_unit_sphere().normalized()

@ti.func
def random_in_hemisphere(normal: vec3) -> vec3:
    in_unit_sphere = random_in_unit_sphere()
    if in_unit_sphere.dot(normal) > 0.0:
        return in_unit_sphere
    else:
        return -in_unit_sphere

@ti.func
def random_in_unit_disk() -> vec3:
    p = vec3(0.0, 0.0, 0.0)
    while True:
        p = vec3(ti.random() * 2.0 - 1.0, ti.random() * 2.0 - 1.0, 0.0)
        if p.dot(p) < 1.0:
            break
    return p

@ti.func
def reflect(v: vec3, n: vec3) -> vec3:
    return v - 2.0 * v.dot(n) * n

@ti.func
def refract(uv: vec3, n: vec3, etai_over_etat: ti.f32) -> vec3:
    cos_theta = ti.min((-uv).dot(n), 1.0)
    r_out_perp = etai_over_etat * (uv + cos_theta * n)
    r_out_parallel = -ti.sqrt(ti.abs(1.0 - r_out_perp.dot(r_out_perp))) * n
    return r_out_perp + r_out_parallel

@ti.func
def reflectance(cosine: ti.f32, ref_idx: ti.f32) -> ti.f32:
    r0 = (1.0 - ref_idx) / (1.0 + ref_idx)
    r0 = r0 * r0
    return r0 + (1.0 - r0) * ti.pow((1.0 - cosine), 5)


# ========== 光线-球体相交 ==========
@ti.func
def hit_sphere(sphere: Sphere, ray_origin: vec3, ray_dir: vec3, 
               t_min: ti.f32, t_max: ti.f32) -> HitResult:
    """
    检测光线与球体相交
    """
    oc = ray_origin - sphere.center
    a = ray_dir.dot(ray_dir)
    half_b = oc.dot(ray_dir)
    c = oc.dot(oc) - sphere.radius * sphere.radius
    
    discriminant = half_b * half_b - a * c
    
    res = HitResult(hit=0, t=0.0, p=vec3(0.0,0.0,0.0), normal=vec3(0.0,0.0,0.0),
                   mat_type=0, albedo=vec3(0.0,0.0,0.0), fuzz=0.0, ir=0.0)
    
    if discriminant > 0.0:
        sqrtd = ti.sqrt(discriminant)
        root = (-half_b - sqrtd) / a
        
        if root < t_min or t_max < root:
            root = (-half_b + sqrtd) / a
            if root < t_min or t_max < root:
                root = -1.0
        
        if root > 0.0:
            res.hit = 1
            res.t = root
            res.p = ray_origin + root * ray_dir
            outward_normal = (res.p - sphere.center) / sphere.radius
            front_face = ray_dir.dot(outward_normal) < 0.0
            res.normal = outward_normal if front_face else -outward_normal
            res.mat_type = sphere.mat_type
            res.albedo = sphere.albedo
            res.fuzz = sphere.fuzz
            res.ir = sphere.ir
    
    return res


# ========== 光线-立方体相交 (AABB Slab Method) ==========
@ti.func
def hit_cube(cube: Cube, ray_origin: vec3, ray_dir: vec3,
             t_min: ti.f32, t_max: ti.f32) -> HitResult:
    """
    检测光线与轴对齐立方体(AABB)相交
    Taichi 限制：不能在 for/if 内部 return，只能在函数末尾 return
    """
    res = HitResult(hit=0, t=0.0, p=vec3(0.0,0.0,0.0), normal=vec3(0.0,0.0,0.0),
                   mat_type=0, albedo=vec3(0.0,0.0,0.0), fuzz=0.0, ir=0.0)
    
    t0 = t_min
    t1 = t_max
    hit_ok = 1
    
    # 三个轴上的 slab 求交
    for i in range(3):
        inv_d = 1.0 / ray_dir[i]
        t_near = (cube.min[i] - ray_origin[i]) * inv_d
        t_far = (cube.max[i] - ray_origin[i]) * inv_d
        
        if inv_d < 0.0:
            t_near, t_far = t_far, t_near
        
        t0 = max(t_near, t0)
        t1 = min(t_far, t1)
        
        if t1 <= t0:
            hit_ok = 0
    
    # 找到有效的交点（只在函数末尾 return）
    if hit_ok == 1:
        # 如果光线起点在 AABB 内部，t0 可能 < 0，此时有效交点是 t1（出口）
        hit_t = t0
        if hit_t < 0.0 and t1 > 0.0:
            hit_t = t1
        
        if hit_t > 0.0 and hit_t < t_max:
            res.hit = 1
            res.t = hit_t
            res.p = ray_origin + hit_t * ray_dir
            
            # 计算法线：判断从哪个面进入/离开
            epsilon = 1e-3
            if ti.abs(res.p[0] - cube.min[0]) < epsilon:
                res.normal = vec3(-1.0, 0.0, 0.0)
            elif ti.abs(res.p[0] - cube.max[0]) < epsilon:
                res.normal = vec3(1.0, 0.0, 0.0)
            elif ti.abs(res.p[1] - cube.min[1]) < epsilon:
                res.normal = vec3(0.0, -1.0, 0.0)
            elif ti.abs(res.p[1] - cube.max[1]) < epsilon:
                res.normal = vec3(0.0, 1.0, 0.0)
            elif ti.abs(res.p[2] - cube.min[2]) < epsilon:
                res.normal = vec3(0.0, 0.0, -1.0)
            else:
                res.normal = vec3(0.0, 0.0, 1.0)
            
            # 确保法线朝外（与入射方向相反）
            if ray_dir.dot(res.normal) > 0.0:
                res.normal = -res.normal
            
            res.mat_type = cube.mat_type
            res.albedo = cube.albedo
            res.fuzz = cube.fuzz
            res.ir = cube.ir
    
    return res


# ========== 光线-三角形相交 (Möller–Trumbore) ==========
@ti.func
def hit_triangle(tri: Triangle, ray_origin: vec3, ray_dir: vec3,
                 t_min: ti.f32, t_max: ti.f32) -> HitResult:
    """
    检测光线与三角形相交
    Möller–Trumbore 算法
    Taichi 限制：不能在 if 内部 return，只能在函数末尾 return
    """
    res = HitResult(hit=0, t=0.0, p=vec3(0.0,0.0,0.0), normal=vec3(0.0,0.0,0.0),
                   mat_type=0, albedo=vec3(0.0,0.0,0.0), fuzz=0.0, ir=0.0)
    
    edge1 = tri.v1 - tri.v0
    edge2 = tri.v2 - tri.v0
    h = ray_dir.cross(edge2)
    a = edge1.dot(h)
    
    hit_ok = 1
    
    # 光线与三角形平行
    if ti.abs(a) < 1e-6:
        hit_ok = 0
    
    if hit_ok == 1:
        f = 1.0 / a
        s = ray_origin - tri.v0
        u = f * s.dot(h)
        if u < 0.0 or u > 1.0:
            hit_ok = 0
        
        if hit_ok == 1:
            q = s.cross(edge1)
            v = f * ray_dir.dot(q)
            if v < 0.0 or u + v > 1.0:
                hit_ok = 0
            
            if hit_ok == 1:
                t = f * edge2.dot(q)
                if t < t_min or t > t_max:
                    hit_ok = 0
                
                if hit_ok == 1:
                    # 命中
                    res.hit = 1
                    res.t = t
                    res.p = ray_origin + t * ray_dir
                    res.normal = tri.normal
                    if ray_dir.dot(res.normal) > 0.0:
                        res.normal = -res.normal
                    res.mat_type = tri.mat_type
                    res.albedo = tri.albedo
                    res.fuzz = tri.fuzz
                    res.ir = tri.ir
    
    return res


# ========== AABB 相交测试 ==========
@ti.func
def hit_aabb(aabb_min: vec3, aabb_max: vec3, ray_origin: vec3, ray_dir: vec3,
             t_min: ti.f32, t_max: ti.f32) -> ti.i32:
    """检测光线与 AABB 相交（Slab Method）"""
    res = 1
    t0 = t_min
    t1 = t_max
    
    for i in range(3):
        inv_d = 1.0 / ray_dir[i]
        t_near = (aabb_min[i] - ray_origin[i]) * inv_d
        t_far = (aabb_max[i] - ray_origin[i]) * inv_d
        
        if inv_d < 0.0:
            t_near, t_far = t_far, t_near
        
        t0 = max(t_near, t0)
        t1 = min(t_far, t1)
        
        if t1 <= t0:
            res = 0
    
    return res


# ========== BVH 遍历（线性化无栈遍历） ==========
@ti.func
def hit_bvh(bvh_nodes: ti.template(), num_bvh_nodes: ti.i32,
            spheres: ti.template(), num_spheres: ti.i32,
            cubes: ti.template(), num_cubes: ti.i32,
            triangles: ti.template(), num_triangles: ti.i32,
            ray_origin: vec3, ray_dir: vec3, t_min: ti.f32, t_max: ti.f32) -> HitResult:
    """
    使用线性化 BVH（skip-link）遍历场景，无需栈
    """
    closest_so_far = t_max
    rec = HitResult(hit=0, t=0.0, p=vec3(0.0,0.0,0.0), normal=vec3(0.0,0.0,0.0),
                   mat_type=0, albedo=vec3(0.0,0.0,0.0), fuzz=0.0, ir=0.0)
    
    node_idx = 0
    while node_idx < num_bvh_nodes and node_idx >= 0:
        node = bvh_nodes[node_idx]
        
        # AABB 快速剔除
        if hit_aabb(node.aabb_min, node.aabb_max, ray_origin, ray_dir, t_min, closest_so_far) == 0:
            node_idx = node.skip
            continue
        
        if node.prim_type >= 0:
            # 叶子节点：测试对应图元
            tmp = HitResult(hit=0, t=0.0, p=vec3(0.0,0.0,0.0), normal=vec3(0.0,0.0,0.0),
                           mat_type=0, albedo=vec3(0.0,0.0,0.0), fuzz=0.0, ir=0.0)
            if node.prim_type == 0 and node.prim_idx < num_spheres:
                tmp = hit_sphere(spheres[node.prim_idx], ray_origin, ray_dir, t_min, closest_so_far)
            elif node.prim_type == 1 and node.prim_idx < num_cubes:
                tmp = hit_cube(cubes[node.prim_idx], ray_origin, ray_dir, t_min, closest_so_far)
            elif node.prim_type == 2 and node.prim_idx < num_triangles:
                tmp = hit_triangle(triangles[node.prim_idx], ray_origin, ray_dir, t_min, closest_so_far)
            
            if tmp.hit:
                rec = tmp
                closest_so_far = tmp.t
        
        # 继续深度优先遍历（下一个节点就是左子树或下一个兄弟）
        node_idx += 1
    
    return rec


# ========== 场景相交（BVH 加速 / 线性回退） ==========
@ti.func
def hit_world(spheres: ti.template(), num_spheres: ti.i32,
              cubes: ti.template(), num_cubes: ti.i32,
              triangles: ti.template(), num_triangles: ti.i32,
              bvh_nodes: ti.template(), num_bvh_nodes: ti.i32,
              ray_origin: vec3, ray_dir: vec3, t_min: ti.f32, t_max: ti.f32) -> HitResult:
    """
    检测光线与场景中所有物体的相交，返回最近的交点信息
    如果 BVH 已构建则使用 BVH 加速，否则线性遍历
    """
    rec = HitResult(hit=0, t=0.0, p=vec3(0.0,0.0,0.0), normal=vec3(0.0,0.0,0.0),
                   mat_type=0, albedo=vec3(0.0,0.0,0.0), fuzz=0.0, ir=0.0)
    
    if num_bvh_nodes > 0:
        rec = hit_bvh(bvh_nodes, num_bvh_nodes,
                      spheres, num_spheres, cubes, num_cubes,
                      triangles, num_triangles,
                      ray_origin, ray_dir, t_min, t_max)
    else:
        # 无 BVH 时线性遍历（小场景或调试）
        closest_so_far = t_max
        
        for i in range(num_spheres):
            tmp = hit_sphere(spheres[i], ray_origin, ray_dir, t_min, closest_so_far)
            if tmp.hit:
                rec = tmp
                closest_so_far = tmp.t
        
        for i in range(num_cubes):
            tmp = hit_cube(cubes[i], ray_origin, ray_dir, t_min, closest_so_far)
            if tmp.hit:
                rec = tmp
                closest_so_far = tmp.t
        
        for i in range(num_triangles):
            tmp = hit_triangle(triangles[i], ray_origin, ray_dir, t_min, closest_so_far)
            if tmp.hit:
                rec = tmp
                closest_so_far = tmp.t
    
    return rec


# ========== 材质散射 ==========
@ti.func
def scatter(mat_type: ti.i32, albedo: vec3, fuzz: ti.f32, ir: ti.f32,
            ray_dir: vec3, normal: vec3, front_face: ti.i32, hit_p: vec3) -> ScatterResult:
    """
    计算材质的散射方向
    """
    res = ScatterResult(ok=0, attenuation=vec3(0.0,0.0,0.0), direction=vec3(0.0,0.0,0.0))
    
    if mat_type == MAT_LAMBERTIAN:
        # 漫反射
        scatter_direction = normal + random_unit_vector()
        if scatter_direction.dot(scatter_direction) < 1e-8:
            scatter_direction = normal
        res.direction = scatter_direction
        res.attenuation = albedo
        res.ok = 1
        
    elif mat_type == MAT_METAL:
        # 金属
        reflected = reflect(ray_dir.normalized(), normal)
        res.direction = reflected + fuzz * random_in_unit_sphere()
        res.attenuation = albedo
        res.ok = 1 if res.direction.dot(normal) > 0.0 else 0
        
    elif mat_type == MAT_DIELECTRIC:
        # 玻璃/电介质
        res.attenuation = vec3(1.0, 1.0, 1.0)
        refraction_ratio = 1.0 / ir if front_face else ir
        
        unit_direction = ray_dir.normalized()
        cos_theta = ti.min((-unit_direction).dot(normal), 1.0)
        sin_theta = ti.sqrt(1.0 - cos_theta * cos_theta)
        
        cannot_refract = refraction_ratio * sin_theta > 1.0
        
        if cannot_refract or reflectance(cos_theta, refraction_ratio) > ti.random():
            res.direction = reflect(unit_direction, normal)
        else:
            res.direction = refract(unit_direction, normal, refraction_ratio)
        
        res.ok = 1
    
    elif mat_type == MAT_PERLIN:
        # Perlin噪声纹理
        scatter_direction = normal + random_unit_vector()
        if scatter_direction.dot(scatter_direction) < 1e-8:
            scatter_direction = normal
        res.direction = scatter_direction
        
        # 基于噪声的颜色
        noise_val = taichi_perlin_turb(hit_p * 4.0, 7)
        noise_color = vec3(0.5, 0.3, 0.1) * noise_val + vec3(0.2, 0.1, 0.05) * (1.0 - noise_val)
        res.attenuation = noise_color
        res.ok = 1
    
    elif mat_type == MAT_EMISSIVE:
        # 发光材质 - 直接返回发光颜色，不继续散射
        res.ok = 2  # 特殊标记: 发光
        res.attenuation = albedo
        res.direction = vec3(0.0, 0.0, 0.0)
    
    return res


# ========== NEE 直接光源采样 ==========
@ti.func
def sample_direct_light(hit_p: vec3, normal: vec3,
                        lights: ti.template(), num_lights: ti.i32,
                        spheres: ti.template(), num_spheres: ti.i32,
                        cubes: ti.template(), num_cubes: ti.i32,
                        triangles: ti.template(), num_triangles: ti.i32,
                        bvh_nodes: ti.template(), num_bvh_nodes: ti.i32) -> vec3:
    """
    简化版 NEE：向随机光源球面采样并发送 Shadow Ray
    返回直接光照贡献（已含 BRDF*cos/pdf 的蒙特卡洛权重）
    """
    contribution = vec3(0.0, 0.0, 0.0)
    
    if num_lights > 0:
        # 随机选一个光源
        idx = ti.cast(ti.random() * ti.cast(num_lights, ti.f32), ti.i32) % num_lights
        light = lights[idx]
        
        # 在光源球面上均匀采样一点
        sample_dir = random_unit_vector()
        light_point = light.center + light.radius * sample_dir
        to_light = light_point - hit_p
        dist_sq = to_light.dot(to_light)
        dist = ti.sqrt(dist_sq)
        
        valid = 1
        if dist < 1e-4:
            valid = 0
        
        if valid == 1:
            to_light = to_light / dist
            
            # 光源必须在表面正面
            cos_theta = normal.dot(to_light)
            if cos_theta <= 0.0:
                valid = 0
            
            if valid == 1:
                # Shadow ray（排除光源自身，所以终点在光源表面之前）
                shadow = hit_world(spheres, num_spheres, cubes, num_cubes,
                                   triangles, num_triangles, bvh_nodes, num_bvh_nodes,
                                   hit_p, to_light, 0.001, dist - 0.001)
                
                if shadow.hit:
                    valid = 0
                
                if valid == 1:
                    # 计算 PDF（球面均匀采样 -> solid angle）
                    cos_theta_light = max(-to_light.dot(sample_dir), 0.0)
                    if cos_theta_light <= 1e-6:
                        valid = 0
                    
                    if valid == 1:
                        pdf_area = 1.0 / (4.0 * 3.14159265 * light.radius * light.radius)
                        pdf_omega = pdf_area * dist_sq / cos_theta_light
                        pdf = pdf_omega / ti.cast(num_lights, ti.f32)
                        if pdf > 1e-8:
                            # Lambertian BRDF = 1/pi
                            brdf = 1.0 / 3.14159265
                            contribution = light.color * brdf * cos_theta / pdf
    
    return contribution


# ========== 光线颜色计算（路径追踪 + NEE） ==========
@ti.func
def ray_color(ray_origin: vec3, ray_dir: vec3, 
              spheres: ti.template(), num_spheres: ti.i32,
              cubes: ti.template(), num_cubes: ti.i32,
              triangles: ti.template(), num_triangles: ti.i32,
              bvh_nodes: ti.template(), num_bvh_nodes: ti.i32,
              lights: ti.template(), num_lights: ti.i32,
              use_nee: ti.i32,
              use_hdri: ti.i32,
              max_depth: ti.i32) -> vec3:
    """
    路径追踪 + NEE（Next Event Estimation）
    throughput/final_color 分离，避免在衰减链上乘发光颜色
    """
    throughput = vec3(1.0, 1.0, 1.0)
    final_color = vec3(0.0, 0.0, 0.0)
    cur_origin = ray_origin
    cur_dir = ray_dir
    
    for depth in range(max_depth):
        rec = hit_world(spheres, num_spheres, cubes, num_cubes, triangles, num_triangles,
                        bvh_nodes, num_bvh_nodes,
                        cur_origin, cur_dir, 0.001, 1e30)
        
        if rec.hit:
            # 发光材质：直接累加（仅在未启用 NEE 或主光线直接命中时）
            if rec.mat_type == MAT_EMISSIVE:
                if use_nee == 0 or depth == 0:
                    final_color += throughput * rec.albedo
                break
            
            # 判断 front_face
            front_face = 1 if cur_dir.dot(rec.normal) < 0.0 else 0
            sres = scatter(rec.mat_type, rec.albedo, rec.fuzz, rec.ir,
                           cur_dir, rec.normal, front_face, rec.p)
            
            if sres.ok == 1:
                # NEE：对非镜面/非玻璃材质做直接光源采样
                # 只对 Lambertian/Perlin 做 NEE（金属和玻璃的路径连续性重要）
                if use_nee == 1 and num_lights > 0 and (rec.mat_type == MAT_LAMBERTIAN or rec.mat_type == MAT_PERLIN):
                    direct = sample_direct_light(rec.p, rec.normal,
                                                  lights, num_lights,
                                                  spheres, num_spheres, cubes, num_cubes,
                                                  triangles, num_triangles,
                                                  bvh_nodes, num_bvh_nodes)
                    final_color += throughput * sres.attenuation * direct
                
                throughput *= sres.attenuation
                cur_origin = rec.p
                cur_dir = sres.direction
                
                # Russian Roulette（depth > 3 时）
                if depth > 3:
                    p = max(throughput[0], max(throughput[1], throughput[2]))
                    if p < 1e-4:
                        break
                    if ti.random() > p:
                        break
                    throughput /= p
            else:
                break
        else:
            # 天空背景 / HDRI
            unit_dir = cur_dir.normalized()
            sky_color_val = vec3(0.0, 0.0, 0.0)
            if use_hdri == 1:
                sky_color_val = sample_hdri(unit_dir)
            else:
                t_sky = 0.5 * (unit_dir[1] + 1.0)
                sky_color_val = (1.0 - t_sky) * vec3(1.0, 1.0, 1.0) + t_sky * vec3(0.5, 0.7, 1.0)
            final_color += throughput * sky_color_val
            break
    
    return final_color


# ========== 主渲染 Kernel ==========
@ti.kernel
def render_kernel(
    pixels: ti.types.ndarray(ndim=3),           # 输出像素数组 (w, h, 3)
    spheres: ti.template(),                      # 场景球体列表
    num_spheres: ti.i32,                         # 球体数量
    cubes: ti.template(),                        # 场景立方体列表
    num_cubes: ti.i32,                           # 立方体数量
    triangles: ti.template(),                    # 场景三角形列表
    num_triangles: ti.i32,                       # 三角形数量
    bvh_nodes: ti.template(),                    # BVH 节点数组
    num_bvh_nodes: ti.i32,                       # BVH 节点数量
    lights: ti.template(),                       # 光源数组
    num_lights: ti.i32,                          # 光源数量
    use_nee: ti.i32,                             # 是否启用 NEE
    use_hdri: ti.i32,                            # 是否启用 HDRI
    camera: Camera,                              # 相机
    image_width: ti.i32,                         # 图像宽度
    image_height: ti.i32,                        # 图像高度
    samples_per_pixel: ti.i32,                   # 每像素采样数
    max_depth: ti.i32,                           # 最大递归深度
):
    """
    GPU 并行渲染 Kernel
    每个线程处理一个像素
    """
    for i, j in ti.ndrange(image_width, image_height):
        # i 是列（x），j 是行（y）
        col = i
        row = image_height - 1 - j  # 翻转y轴
        
        pixel_color = vec3(0.0, 0.0, 0.0)
        
        for s in range(samples_per_pixel):
            u = (ti.cast(col, ti.f32) + ti.random()) / ti.cast(image_width - 1, ti.f32)
            v = (ti.cast(row, ti.f32) + ti.random()) / ti.cast(image_height - 1, ti.f32)
            
            # 生成光线（考虑景深）
            rd = camera.lens_radius * random_in_unit_disk()
            offset = camera.u * rd[0] + camera.v * rd[1]
            
            ray_origin = camera.origin + offset
            ray_dir = (camera.lower_left_corner 
                      + u * camera.horizontal 
                      + v * camera.vertical 
                      - camera.origin - offset)
            
            pixel_color += ray_color(ray_origin, ray_dir, spheres, num_spheres,
                                     cubes, num_cubes, triangles, num_triangles,
                                     bvh_nodes, num_bvh_nodes,
                                     lights, num_lights, use_nee, use_hdri, max_depth)
        
        # 取平均并 Gamma 校正
        scale = 1.0 / ti.cast(samples_per_pixel, ti.f32)
        r = ti.sqrt(scale * pixel_color[0])
        g = ti.sqrt(scale * pixel_color[1])
        b = ti.sqrt(scale * pixel_color[2])
        
        # 写入像素
        pixels[i, j, 0] = ti.cast(256.0 * ti.min(r, 0.999), ti.u8)
        pixels[i, j, 1] = ti.cast(256.0 * ti.min(g, 0.999), ti.u8)
        pixels[i, j, 2] = ti.cast(256.0 * ti.min(b, 0.999), ti.u8)


# ========== 渐进式渲染 Kernel ==========
@ti.kernel
def render_kernel_accum(
    accum: ti.types.ndarray(ndim=3),            # float32 线性累积 buffer (w, h, 3)
    display: ti.types.ndarray(ndim=3),          # uint8 显示 buffer (w, h, 3)
    spheres: ti.template(),
    num_spheres: ti.i32,
    cubes: ti.template(),
    num_cubes: ti.i32,
    triangles: ti.template(),
    num_triangles: ti.i32,
    bvh_nodes: ti.template(),
    num_bvh_nodes: ti.i32,
    lights: ti.template(),
    num_lights: ti.i32,
    use_nee: ti.i32,
    use_hdri: ti.i32,
    camera: Camera,
    image_width: ti.i32,
    image_height: ti.i32,
    batch_spp: ti.i32,                          # 本次批次采样数
    current_spp: ti.i32,                        # 已累积采样数
    max_depth: ti.i32,
):
    """
    渐进式渲染 Kernel：在线性空间累积，只渲染 batch_spp 个新采样
    """
    for i, j in ti.ndrange(image_width, image_height):
        col = i
        row = image_height - 1 - j
        
        pixel_color = vec3(0.0, 0.0, 0.0)
        
        for s in range(batch_spp):
            u = (ti.cast(col, ti.f32) + ti.random()) / ti.cast(image_width - 1, ti.f32)
            v = (ti.cast(row, ti.f32) + ti.random()) / ti.cast(image_height - 1, ti.f32)
            
            rd = camera.lens_radius * random_in_unit_disk()
            offset = camera.u * rd[0] + camera.v * rd[1]
            
            ray_origin = camera.origin + offset
            ray_dir = (camera.lower_left_corner 
                      + u * camera.horizontal 
                      + v * camera.vertical 
                      - camera.origin - offset)
            
            pixel_color += ray_color(ray_origin, ray_dir, spheres, num_spheres,
                                     cubes, num_cubes, triangles, num_triangles,
                                     bvh_nodes, num_bvh_nodes,
                                     lights, num_lights, use_nee, use_hdri, max_depth)
        
        # 新采样的线性平均值
        new_avg = pixel_color / ti.cast(batch_spp, ti.f32)
        
        # 读取旧累积值
        old_r = accum[i, j, 0]
        old_g = accum[i, j, 1]
        old_b = accum[i, j, 2]
        
        # 加权更新（线性空间）
        total = current_spp + batch_spp
        accum[i, j, 0] = (old_r * ti.cast(current_spp, ti.f32) + new_avg[0] * ti.cast(batch_spp, ti.f32)) / ti.cast(total, ti.f32)
        accum[i, j, 1] = (old_g * ti.cast(current_spp, ti.f32) + new_avg[1] * ti.cast(batch_spp, ti.f32)) / ti.cast(total, ti.f32)
        accum[i, j, 2] = (old_b * ti.cast(current_spp, ti.f32) + new_avg[2] * ti.cast(batch_spp, ti.f32)) / ti.cast(total, ti.f32)
        
        # Gamma 校正到显示 buffer
        r = ti.sqrt(accum[i, j, 0])
        g = ti.sqrt(accum[i, j, 1])
        b = ti.sqrt(accum[i, j, 2])
        display[i, j, 0] = ti.cast(256.0 * ti.min(r, 0.999), ti.u8)
        display[i, j, 1] = ti.cast(256.0 * ti.min(g, 0.999), ti.u8)
        display[i, j, 2] = ti.cast(256.0 * ti.min(b, 0.999), ti.u8)


# ========== BVH 构建器（CPU 端） ==========
class BVHBuilder:
    """
    CPU 端 BVH 构建器：支持球体、立方体、三角形三种图元
    使用 DFS 前序遍历线性化存储，配合 skip 指针实现 GPU 无栈遍历
    """
    
    def __init__(self, renderer):
        self.renderer = renderer
        self.nodes = []  # Python 端临时节点列表
    
    def build(self):
        """构建 BVH，返回 Taichi field"""
        prims = []
        
        # 收集所有球体
        for i in range(self.renderer.num_spheres):
            s = self.renderer.spheres[i]
            c = s.center
            r = s.radius
            prims.append({
                'type': 0,
                'idx': i,
                'aabb_min': [c[0] - r, c[1] - r, c[2] - r],
                'aabb_max': [c[0] + r, c[1] + r, c[2] + r],
                'center': [c[0], c[1], c[2]],
            })
        
        # 收集所有立方体
        for i in range(self.renderer.num_cubes):
            c = self.renderer.cubes[i]
            mn = c.min
            mx = c.max
            prims.append({
                'type': 1,
                'idx': i,
                'aabb_min': [mn[0], mn[1], mn[2]],
                'aabb_max': [mx[0], mx[1], mx[2]],
                'center': [(mn[0] + mx[0]) * 0.5, (mn[1] + mx[1]) * 0.5, (mn[2] + mx[2]) * 0.5],
            })
        
        # 收集所有三角形
        for i in range(self.renderer.num_triangles):
            t = self.renderer.triangles[i]
            v0, v1, v2 = t.v0, t.v1, t.v2
            prims.append({
                'type': 2,
                'idx': i,
                'aabb_min': [min(v0[0], v1[0], v2[0]), min(v0[1], v1[1], v2[1]), min(v0[2], v1[2], v2[2])],
                'aabb_max': [max(v0[0], v1[0], v2[0]), max(v0[1], v1[1], v2[1]), max(v0[2], v1[2], v2[2])],
                'center': [(v0[0] + v1[0] + v2[0]) / 3.0, (v0[1] + v1[1] + v2[1]) / 3.0, (v0[2] + v1[2] + v2[2]) / 3.0],
            })
        
        if len(prims) == 0:
            return None, 0
        
        self._build_recursive(prims)
        
        # 转换为 Taichi field
        n_nodes = len(self.nodes)
        nodes_field = BVHNode.field(shape=(n_nodes,))
        for i, node in enumerate(self.nodes):
            nodes_field[i] = BVHNode(
                aabb_min=vec3(node['aabb_min']),
                aabb_max=vec3(node['aabb_max']),
                skip=node['skip'],
                left=node['left'],
                right=node['right'],
                prim_type=node['prim_type'],
                prim_idx=node['prim_idx'],
            )
        
        return nodes_field, n_nodes
    
    def _build_recursive(self, prims):
        """递归构建 BVH 节点，返回 (node_idx, skip_idx)"""
        node_idx = len(self.nodes)
        self.nodes.append({
            'aabb_min': [1e30, 1e30, 1e30],
            'aabb_max': [-1e30, -1e30, -1e30],
            'skip': -1,
            'left': -1,
            'right': -1,
            'prim_type': -1,
            'prim_idx': -1,
        })
        
        # 计算当前节点的 AABB
        aabb_min = [1e30, 1e30, 1e30]
        aabb_max = [-1e30, -1e30, -1e30]
        for p in prims:
            for j in range(3):
                aabb_min[j] = min(aabb_min[j], p['aabb_min'][j])
                aabb_max[j] = max(aabb_max[j], p['aabb_max'][j])
        
        self.nodes[node_idx]['aabb_min'] = aabb_min
        self.nodes[node_idx]['aabb_max'] = aabb_max
        
        n = len(prims)
        if n == 1:
            # 叶子节点
            self.nodes[node_idx]['prim_type'] = prims[0]['type']
            self.nodes[node_idx]['prim_idx'] = prims[0]['idx']
            self.nodes[node_idx]['skip'] = node_idx + 1
            return node_idx, node_idx + 1
        
        # 找到最长轴
        extent = [aabb_max[j] - aabb_min[j] for j in range(3)]
        axis = int(np.argmax(extent))
        
        # 按中心点排序并中点分割
        prims.sort(key=lambda p: p['center'][axis])
        mid = n // 2
        
        # 递归构建左子树
        left_idx, left_skip = self._build_recursive(prims[:mid])
        self.nodes[node_idx]['left'] = left_idx
        
        # 递归构建右子树
        right_idx, right_skip = self._build_recursive(prims[mid:])
        self.nodes[node_idx]['right'] = right_idx
        
        # skip = 右子树结束后的下一个位置
        self.nodes[node_idx]['skip'] = right_skip
        
        return node_idx, right_skip


# ========== Python 接口 ==========
class TaichiRenderer:
    """Taichi GPU 渲染器 Python 接口"""
    
    def __init__(self, max_spheres=500, max_cubes=100, max_triangles=1000, max_bvh_nodes=8192):
        self.max_spheres = max_spheres
        self.max_cubes = max_cubes
        self.max_triangles = max_triangles
        self.max_bvh_nodes = max_bvh_nodes
        # 分配各图元 field
        self.spheres = Sphere.field(shape=(max_spheres,))
        self.cubes = Cube.field(shape=(max_cubes,))
        self.triangles = Triangle.field(shape=(max_triangles,))
        self.bvh_nodes = BVHNode.field(shape=(max_bvh_nodes,))
        self.lights = Light.field(shape=(max_spheres,))  # 光源数不超过球体数
        self.num_spheres = 0
        self.num_cubes = 0
        self.num_triangles = 0
        self.num_bvh_nodes = 0
        self.num_lights = 0
    
    def clear_scene(self):
        self.num_spheres = 0
        self.num_cubes = 0
        self.num_triangles = 0
        self.num_bvh_nodes = 0
        self.num_lights = 0
    
    def add_sphere(self, center, radius, mat_type, albedo=(1,1,1), fuzz=0.0, ir=1.5):
        if self.num_spheres >= self.max_spheres:
            raise RuntimeError(f"球体数量超过最大值 {self.max_spheres}")
        
        self.spheres[self.num_spheres] = Sphere(
            center=vec3(center),
            radius=radius,
            mat_type=mat_type,
            albedo=vec3(albedo),
            fuzz=fuzz,
            ir=ir,
        )
        # 如果是发光材质，同时加入光源列表（供 NEE 使用）
        if mat_type == MAT_EMISSIVE and self.num_lights < self.max_spheres:
            self.lights[self.num_lights] = Light(
                center=vec3(center),
                radius=radius,
                color=vec3(albedo),
            )
            self.num_lights += 1
        self.num_spheres += 1
    
    def add_perlin_sphere(self, center, radius):
        """添加 Perlin 噪声纹理球体"""
        self.add_sphere(center, radius, MAT_PERLIN)
    
    def add_light(self, center, radius, color=(10.0, 10.0, 10.0)):
        """添加发光球体光源"""
        self.add_sphere(center, radius, MAT_EMISSIVE, color)
    
    def add_cube(self, min_point, max_point, mat_type, albedo=(1,1,1), fuzz=0.0, ir=1.5):
        """添加轴对齐立方体"""
        if self.num_cubes >= self.max_cubes:
            raise RuntimeError(f"立方体数量超过最大值 {self.max_cubes}")
        
        self.cubes[self.num_cubes] = Cube(
            min=vec3(min_point),
            max=vec3(max_point),
            mat_type=mat_type,
            albedo=vec3(albedo),
            fuzz=fuzz,
            ir=ir,
        )
        self.num_cubes += 1
    
    def add_triangle(self, v0, v1, v2, mat_type, albedo=(1,1,1), fuzz=0.0, ir=1.5):
        """添加三角形"""
        if self.num_triangles >= self.max_triangles:
            raise RuntimeError(f"三角形数量超过最大值 {self.max_triangles}")
        
        # 计算面法线
        e1 = vec3(v1) - vec3(v0)
        e2 = vec3(v2) - vec3(v0)
        n = e1.cross(e2).normalized()
        
        self.triangles[self.num_triangles] = Triangle(
            v0=vec3(v0),
            v1=vec3(v1),
            v2=vec3(v2),
            normal=n,
            mat_type=mat_type,
            albedo=vec3(albedo),
            fuzz=fuzz,
            ir=ir,
        )
        self.num_triangles += 1
    
    def add_obj_model(self, filepath, mat_type=0, albedo=(0.7,0.7,0.7),
                      fuzz=0.0, ir=1.5, scale=1.0, offset=(0,0,0)):
        """
        加载 OBJ 模型并批量添加三角形到场景
        
        Args:
            filepath: OBJ 文件路径
            mat_type: 材质类型
            albedo: 漫反射颜色
            fuzz: 金属模糊度
            ir: 折射率
            scale: 缩放因子
            offset: 平移偏移
        """
        tris = load_obj_model(filepath, mat_type, albedo, fuzz, ir)
        if not tris:
            return 0
        
        ox, oy, oz = offset
        added = 0
        for tri_data in tris:
            if self.num_triangles >= self.max_triangles:
                print(f"[OBJ] 警告: 三角形数量超过最大值，仅加载前 {added} 个")
                break
            
            v0 = (tri_data['v0'][0] * scale + ox, tri_data['v0'][1] * scale + oy, tri_data['v0'][2] * scale + oz)
            v1 = (tri_data['v1'][0] * scale + ox, tri_data['v1'][1] * scale + oy, tri_data['v1'][2] * scale + oz)
            v2 = (tri_data['v2'][0] * scale + ox, tri_data['v2'][1] * scale + oy, tri_data['v2'][2] * scale + oz)
            
            self.add_triangle(v0, v1, v2, mat_type, albedo, fuzz, ir)
            added += 1
        
        print(f"[OBJ] 已加载 {added} 个三角形到场景")
        return added
    
    def set_camera(self, lookfrom, lookat, vup, vfov, aspect_ratio, aperture=0.0, focus_dist=None):
        """设置相机参数"""
        if focus_dist is None:
            focus_dist = (vec3(lookfrom) - vec3(lookat)).norm()
        
        theta = np.radians(vfov)
        h = np.tan(theta / 2)
        viewport_height = 2.0 * h
        viewport_width = aspect_ratio * viewport_height
        
        w = (vec3(lookfrom) - vec3(lookat)).normalized()
        u = (vec3(vup).cross(w)).normalized()
        v = w.cross(u)
        
        origin = vec3(lookfrom)
        horizontal = focus_dist * viewport_width * u
        vertical = focus_dist * viewport_height * v
        lower_left_corner = origin - horizontal / 2 - vertical / 2 - focus_dist * w
        
        self.camera = Camera(
            origin=origin,
            lower_left_corner=lower_left_corner,
            horizontal=horizontal,
            vertical=vertical,
            u=u,
            v=v,
            w=w,
            lens_radius=aperture / 2,
        )
    
    def build_bvh(self):
        """为当前场景构建 BVH 加速结构"""
        builder = BVHBuilder(self)
        field, n = builder.build()
        if field is not None:
            if n > self.max_bvh_nodes:
                print(f"[BVH] 警告: BVH 节点数 {n} 超过最大值 {self.max_bvh_nodes}，禁用 BVH")
                self.num_bvh_nodes = 0
            else:
                self.bvh_nodes = field
                self.num_bvh_nodes = n
                print(f"[BVH] 构建完成: {n} 个节点 ({self.num_spheres} 球 + {self.num_cubes} 立方体 + {self.num_triangles} 三角形)")
        else:
            self.num_bvh_nodes = 0
    
    def render(self, image_width, image_height, samples_per_pixel=100, max_depth=50,
               use_bvh=True, use_nee=True, use_hdri=None):
        """渲染场景"""
        print(f"[Taichi GPU] 开始渲染: {image_width}x{image_height}")
        print(f"  球体: {self.num_spheres}, 立方体: {self.num_cubes}, 三角形: {self.num_triangles}, 光源: {self.num_lights}")
        print(f"  每像素采样: {samples_per_pixel}, 最大深度: {max_depth}, NEE: {'开' if use_nee else '关'}")
        
        # 构建 BVH
        if use_bvh:
            self.build_bvh()
        else:
            self.num_bvh_nodes = 0
        
        # 自动判断 HDRI
        if use_hdri is None:
            use_hdri = _hdri_enabled
        
        # 分配像素数组 (PIL 需要 height×width，但 Taichi ndarray 用 width×height)
        pixels = np.zeros((image_height, image_width, 3), dtype=np.uint8)
        pixels_ti = ti.ndarray(ti.u8, shape=(image_width, image_height, 3))
        
        start = time.time()
        
        # 调用 GPU Kernel
        nee_flag = 1 if use_nee else 0
        hdri_flag = 1 if use_hdri else 0
        render_kernel(pixels_ti, self.spheres, self.num_spheres,
                     self.cubes, self.num_cubes,
                     self.triangles, self.num_triangles,
                     self.bvh_nodes, self.num_bvh_nodes,
                     self.lights, self.num_lights, nee_flag, hdri_flag,
                     self.camera, image_width, image_height,
                     samples_per_pixel, max_depth)
        
        # 同步并拷贝回 CPU，转置为 PIL 需要的 (H, W, C)
        ti.sync()
        pixels = np.transpose(pixels_ti.to_numpy(), (1, 0, 2))
        
        elapsed = time.time() - start
        print(f"[Taichi GPU] 渲染完成! 耗时: {elapsed:.2f} 秒")
        print(f"  性能: {image_width * image_height * samples_per_pixel / elapsed / 1e6:.2f} M 采样/秒")
        
        return pixels
    
    def render_interactive(self, image_width=800, image_height=450, 
                           max_spp=1000, batch_spp=4, max_depth=50,
                           use_nee=True, use_hdri=None, save_path='outputs/preview.png'):
        """
        交互式渐进渲染预览
        使用 ti.GUI 实时显示渲染进度，按 ESC 退出，S 保存当前图像
        """
        gui = ti.GUI("Ray Tracer Preview", (image_width, image_height))
        
        # 构建 BVH
        self.build_bvh()
        
        # 分配 GPU buffer（Taichi ndarray）
        accum_ti = ti.ndarray(ti.f32, shape=(image_width, image_height, 3))
        display_ti = ti.ndarray(ti.u8, shape=(image_width, image_height, 3))
        
        # 清零 accum
        arr = np.zeros((image_width, image_height, 3), dtype=np.float32)
        accum_ti.from_numpy(arr)
        
        spp_done = 0
        last_save = 0
        nee_flag = 1 if use_nee else 0
        if use_hdri is None:
            use_hdri = _hdri_enabled
        hdri_flag = 1 if use_hdri else 0
        
        print(f"[Preview] 交互式预览启动: {image_width}x{image_height}")
        print(f"  目标 spp: {max_spp}, 每批: {batch_spp}, NEE: {'开' if use_nee else '关'}")
        print("  按键: ESC=退出, S=保存, R=重置")
        
        while gui.running and spp_done < max_spp:
            # 渲染一批采样
            render_kernel_accum(accum_ti, display_ti,
                               self.spheres, self.num_spheres,
                               self.cubes, self.num_cubes,
                               self.triangles, self.num_triangles,
                               self.bvh_nodes, self.num_bvh_nodes,
                               self.lights, self.num_lights, nee_flag, hdri_flag,
                               self.camera, image_width, image_height,
                               batch_spp, spp_done, max_depth)
            ti.sync()
            
            spp_done += batch_spp
            
            # 拷贝到 CPU 并转置为 (H, W, 3) 供 GUI 显示
            display_np = np.transpose(display_ti.to_numpy(), (1, 0, 2))
            
            # GUI 显示（归一化到 0-1）
            gui.set_image(display_np.astype(np.float32) / 255.0)
            gui.show()
            
            # 处理按键
            if gui.is_pressed('s'):
                if spp_done > last_save:
                    from PIL import Image
                    Image.fromarray(display_np).save(save_path)
                    print(f"[Preview] 已保存 {save_path} ({spp_done} spp)")
                    last_save = spp_done
            
            if gui.is_pressed('r'):
                # 重置累积
                arr = np.zeros((image_width, image_height, 3), dtype=np.float32)
                accum_ti.from_numpy(arr)
                spp_done = 0
                print(f"[Preview] 已重置")
        
        gui.close()
        
        # 返回最终图像
        final = np.transpose(display_ti.to_numpy(), (1, 0, 2))
        return final


# ========== 便捷函数 ==========
def create_demo_scene_gpu():
    """创建 GPU 版本的演示场景"""
    renderer = TaichiRenderer(max_spheres=100)
    
    # 地面
    renderer.add_sphere(
        center=(0, -100.5, -1), radius=100.0,
        mat_type=MAT_LAMBERTIAN, albedo=(0.8, 0.8, 0.0)
    )
    # 中心球 - 红色漫反射
    renderer.add_sphere(
        center=(0, 0, -1), radius=0.5,
        mat_type=MAT_LAMBERTIAN, albedo=(0.7, 0.3, 0.3)
    )
    # 左侧球 - 金属
    renderer.add_sphere(
        center=(-1.0, 0, -1), radius=0.5,
        mat_type=MAT_METAL, albedo=(0.8, 0.8, 0.8), fuzz=0.3
    )
    # 右侧球 - 玻璃
    renderer.add_sphere(
        center=(1.0, 0, -1), radius=0.5,
        mat_type=MAT_DIELECTRIC, ir=1.5
    )
    
    # 相机
    renderer.set_camera(
        lookfrom=(-2, 2, 1),
        lookat=(0, 0, -1),
        vup=(0, 1, 0),
        vfov=20.0,
        aspect_ratio=16.0/9.0,
    )
    
    return renderer


def create_complex_scene_gpu():
    """创建 GPU 版本的复杂随机场景"""
    renderer = TaichiRenderer(max_spheres=600)
    np.random.seed(42)
    
    # 地面
    renderer.add_sphere(
        center=(0, -1000, 0), radius=1000.0,
        mat_type=MAT_LAMBERTIAN, albedo=(0.5, 0.5, 0.5)
    )
    
    # 随机小球
    for a in range(-11, 11):
        for b in range(-11, 11):
            choose_mat = np.random.random()
            center = (a + 0.9 * np.random.random(), 0.2, b + 0.9 * np.random.random())
            
            if np.sqrt((center[0]-4)**2 + (center[2]-0)**2) > 0.9:
                if choose_mat < 0.8:
                    albedo = (np.random.random() * np.random.random(),
                             np.random.random() * np.random.random(),
                             np.random.random() * np.random.random())
                    renderer.add_sphere(center=center, radius=0.2,
                                       mat_type=MAT_LAMBERTIAN, albedo=albedo)
                elif choose_mat < 0.95:
                    albedo = (0.5*(1+np.random.random()),
                             0.5*(1+np.random.random()),
                             0.5*(1+np.random.random()))
                    fuzz = 0.5 * np.random.random()
                    renderer.add_sphere(center=center, radius=0.2,
                                       mat_type=MAT_METAL, albedo=albedo, fuzz=fuzz)
                else:
                    renderer.add_sphere(center=center, radius=0.2,
                                       mat_type=MAT_DIELECTRIC, ir=1.5)
    
    # 三个大球
    renderer.add_sphere(center=(0, 1, 0), radius=1.0, mat_type=MAT_DIELECTRIC, ir=1.5)
    renderer.add_sphere(center=(-4, 1, 0), radius=1.0, mat_type=MAT_LAMBERTIAN, albedo=(0.4, 0.2, 0.1))
    renderer.add_sphere(center=(4, 1, 0), radius=1.0, mat_type=MAT_METAL, albedo=(0.7, 0.6, 0.5), fuzz=0.0)
    
    # 相机
    renderer.set_camera(
        lookfrom=(13, 2, 3),
        lookat=(0, 0, 0),
        vup=(0, 1, 0),
        vfov=20.0,
        aspect_ratio=16.0/9.0,
        aperture=0.1,
        focus_dist=10.0,
    )
    
    return renderer


if __name__ == '__main__':
    print("=" * 50)
    print("  Taichi GPU 光线追踪器")
    print("=" * 50)
    
    # 演示场景
    renderer = create_demo_scene_gpu()
    image = renderer.render(image_width=400, image_height=225, 
                           samples_per_pixel=100, max_depth=50)
    
    img = Image.fromarray(image)
    img.save('outputs/taichi_demo.png')
    print("图片已保存到: outputs/taichi_demo.png")
