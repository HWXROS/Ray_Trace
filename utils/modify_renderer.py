"""
批量修改 taichi_renderer.py，添加立方体和三角形支持
"""

with open('taichi_renderer.py', 'r', encoding='utf-8') as f:
    content = f.read()

# ========== 1. 添加 Cube 和 Triangle struct ==========
old_sphere_struct = '''# 球体结构体
Sphere = ti.types.struct(
    center=vec3,
    radius=ti.f32,
    mat_type=ti.i32,      # 材质类型
    albedo=vec3,          # 漫反射/金属颜色
    fuzz=ti.f32,          # 金属模糊度
    ir=ti.f32,            # 折射率
)'''

new_structs = '''# 球体结构体
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
)'''

content = content.replace(old_sphere_struct, new_structs)

# ========== 2. 在 hit_sphere 后添加 hit_cube 和 hit_triangle ==========
old_comment = '# ========== 场景相交（遍历所有球体） =========='

new_funcs = '''# ========== 光线-立方体相交 (AABB Slab Method) ==========
@ti.func
def hit_cube(cube: Cube, ray_origin: vec3, ray_dir: vec3,
             t_min: ti.f32, t_max: ti.f32) -> HitResult:
    """
    检测光线与轴对齐立方体(AABB)相交
    """
    res = HitResult(hit=0, t=0.0, p=vec3(0.0,0.0,0.0), normal=vec3(0.0,0.0,0.0),
                   mat_type=0, albedo=vec3(0.0,0.0,0.0), fuzz=0.0, ir=0.0)
    
    t0 = t_min
    t1 = t_max
    
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
            return res
    
    # 找到有效的交点
    if t0 > 0.0 and t0 < t_max:
        res.hit = 1
        res.t = t0
        res.p = ray_origin + t0 * ray_dir
        
        # 计算法线：判断从哪个面进入
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
    """
    res = HitResult(hit=0, t=0.0, p=vec3(0.0,0.0,0.0), normal=vec3(0.0,0.0,0.0),
                   mat_type=0, albedo=vec3(0.0,0.0,0.0), fuzz=0.0, ir=0.0)
    
    edge1 = tri.v1 - tri.v0
    edge2 = tri.v2 - tri.v0
    h = ray_dir.cross(edge2)
    a = edge1.dot(h)
    
    # 光线与三角形平行
    if ti.abs(a) < 1e-6:
        return res
    
    f = 1.0 / a
    s = ray_origin - tri.v0
    u = f * s.dot(h)
    if u < 0.0 or u > 1.0:
        return res
    
    q = s.cross(edge1)
    v = f * ray_dir.dot(q)
    if v < 0.0 or u + v > 1.0:
        return res
    
    t = f * edge2.dot(q)
    if t < t_min or t > t_max:
        return res
    
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


# ========== 场景相交（遍历所有物体） =========='''

content = content.replace(old_comment, new_funcs)

# ========== 3. 修改 hit_world ==========
old_hit_world = '''@ti.func
def hit_world(spheres: ti.template(), num_spheres: ti.i32,
              ray_origin: vec3, ray_dir: vec3, t_min: ti.f32, t_max: ti.f32) -> HitResult:
    """
    检测光线与场景中所有物体的相交，返回最近的交点信息
    """
    closest_so_far = t_max
    rec = HitResult(hit=0, t=0.0, p=vec3(0.0,0.0,0.0), normal=vec3(0.0,0.0,0.0),
                   mat_type=0, albedo=vec3(0.0,0.0,0.0), fuzz=0.0, ir=0.0)
    
    for i in range(num_spheres):
        tmp = hit_sphere(spheres[i], ray_origin, ray_dir, t_min, closest_so_far)
        if tmp.hit:
            rec = tmp
            closest_so_far = tmp.t
    
    return rec'''

new_hit_world = '''@ti.func
def hit_world(spheres: ti.template(), num_spheres: ti.i32,
              cubes: ti.template(), num_cubes: ti.i32,
              triangles: ti.template(), num_triangles: ti.i32,
              ray_origin: vec3, ray_dir: vec3, t_min: ti.f32, t_max: ti.f32) -> HitResult:
    """
    检测光线与场景中所有物体的相交，返回最近的交点信息
    """
    closest_so_far = t_max
    rec = HitResult(hit=0, t=0.0, p=vec3(0.0,0.0,0.0), normal=vec3(0.0,0.0,0.0),
                   mat_type=0, albedo=vec3(0.0,0.0,0.0), fuzz=0.0, ir=0.0)
    
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
    
    return rec'''

content = content.replace(old_hit_world, new_hit_world)

# ========== 4. 修改 ray_color ==========
old_ray_color_sig = '''def ray_color(ray_origin: vec3, ray_dir: vec3, 
              spheres: ti.template(), num_spheres: ti.i32, 
              max_depth: ti.i32) -> vec3:'''

new_ray_color_sig = '''def ray_color(ray_origin: vec3, ray_dir: vec3, 
              spheres: ti.template(), num_spheres: ti.i32,
              cubes: ti.template(), num_cubes: ti.i32,
              triangles: ti.template(), num_triangles: ti.i32,
              max_depth: ti.i32) -> vec3:'''

content = content.replace(old_ray_color_sig, new_ray_color_sig)

old_hitworld_call = '        rec = hit_world(spheres, num_spheres, cur_origin, cur_dir, 0.001, 1e30)'
new_hitworld_call = '        rec = hit_world(spheres, num_spheres, cubes, num_cubes, triangles, num_triangles,\n                        cur_origin, cur_dir, 0.001, 1e30)'

content = content.replace(old_hitworld_call, new_hitworld_call)

# ========== 5. 修改 render_kernel ==========
old_render_sig = '''def render_kernel(
    pixels: ti.types.ndarray(ndim=3),           # 输出像素数组 (w, h, 3)
    spheres: ti.template(),                      # 场景球体列表
    num_spheres: ti.i32,                         # 球体数量
    camera: Camera,                              # 相机
    image_width: ti.i32,                         # 图像宽度
    image_height: ti.i32,                        # 图像高度
    samples_per_pixel: ti.i32,                   # 每像素采样数
    max_depth: ti.i32,                           # 最大递归深度
):'''

new_render_sig = '''def render_kernel(
    pixels: ti.types.ndarray(ndim=3),           # 输出像素数组 (w, h, 3)
    spheres: ti.template(),                      # 场景球体列表
    num_spheres: ti.i32,                         # 球体数量
    cubes: ti.template(),                        # 场景立方体列表
    num_cubes: ti.i32,                           # 立方体数量
    triangles: ti.template(),                    # 场景三角形列表
    num_triangles: ti.i32,                       # 三角形数量
    camera: Camera,                              # 相机
    image_width: ti.i32,                         # 图像宽度
    image_height: ti.i32,                        # 图像高度
    samples_per_pixel: ti.i32,                   # 每像素采样数
    max_depth: ti.i32,                           # 最大递归深度
):'''

content = content.replace(old_render_sig, new_render_sig)

old_raycolor_call = '            pixel_color += ray_color(ray_origin, ray_dir, spheres, num_spheres, max_depth)'
new_raycolor_call = '            pixel_color += ray_color(ray_origin, ray_dir, spheres, num_spheres,\n                                     cubes, num_cubes, triangles, num_triangles, max_depth)'

content = content.replace(old_raycolor_call, new_raycolor_call)

# ========== 6. 修改 TaichiRenderer 类 ==========
old_init = '''class TaichiRenderer:
    """Taichi GPU 渲染器 Python 接口"""
    
    def __init__(self, max_spheres=500):
        self.max_spheres = max_spheres
        # 分配球体 field
        self.spheres = Sphere.field(shape=(max_spheres,))
        self.num_spheres = 0
    
    def clear_scene(self):
        self.num_spheres = 0'''

new_init = '''class TaichiRenderer:
    """Taichi GPU 渲染器 Python 接口"""
    
    def __init__(self, max_spheres=500, max_cubes=100, max_triangles=1000):
        self.max_spheres = max_spheres
        self.max_cubes = max_cubes
        self.max_triangles = max_triangles
        # 分配各图元 field
        self.spheres = Sphere.field(shape=(max_spheres,))
        self.cubes = Cube.field(shape=(max_cubes,))
        self.triangles = Triangle.field(shape=(max_triangles,))
        self.num_spheres = 0
        self.num_cubes = 0
        self.num_triangles = 0
    
    def clear_scene(self):
        self.num_spheres = 0
        self.num_cubes = 0
        self.num_triangles = 0'''

content = content.replace(old_init, new_init)

old_light = '''    def add_light(self, center, radius, color=(10.0, 10.0, 10.0)):
        """添加发光球体光源"""
        self.add_sphere(center, radius, MAT_EMISSIVE, color)
    
    def set_camera('''

new_light = '''    def add_light(self, center, radius, color=(10.0, 10.0, 10.0)):
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
    
    def set_camera('''

content = content.replace(old_light, new_light)

old_render = '''    def render(self, image_width, image_height, samples_per_pixel=100, max_depth=50):
        """渲染场景"""
        print(f"[Taichi GPU] 开始渲染: {image_width}x{image_height}")
        print(f"  球体数量: {self.num_spheres}")
        print(f"  每像素采样: {samples_per_pixel}, 最大深度: {max_depth}")
        
        # 分配像素数组
        pixels = np.zeros((image_width, image_height, 3), dtype=np.uint8)
        pixels_ti = ti.ndarray(ti.u8, shape=(image_width, image_height, 3))
        
        start = time.time()
        
        # 调用 GPU Kernel
        render_kernel(pixels_ti, self.spheres, self.num_spheres, 
                     self.camera, image_width, image_height, 
                     samples_per_pixel, max_depth)'''

new_render = '''    def render(self, image_width, image_height, samples_per_pixel=100, max_depth=50):
        """渲染场景"""
        print(f"[Taichi GPU] 开始渲染: {image_width}x{image_height}")
        print(f"  球体: {self.num_spheres}, 立方体: {self.num_cubes}, 三角形: {self.num_triangles}")
        print(f"  每像素采样: {samples_per_pixel}, 最大深度: {max_depth}")
        
        # 分配像素数组
        pixels = np.zeros((image_width, image_height, 3), dtype=np.uint8)
        pixels_ti = ti.ndarray(ti.u8, shape=(image_width, image_height, 3))
        
        start = time.time()
        
        # 调用 GPU Kernel
        render_kernel(pixels_ti, self.spheres, self.num_spheres,
                     self.cubes, self.num_cubes,
                     self.triangles, self.num_triangles,
                     self.camera, image_width, image_height,
                     samples_per_pixel, max_depth)'''

content = content.replace(old_render, new_render)

# 写回
with open('taichi_renderer.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("修改完成！")
print("主要变更:")
print("  + Cube struct (AABB)")
print("  + Triangle struct")
print("  + hit_cube() / hit_triangle()")
print("  + TaichiRenderer.add_cube() / add_triangle()")
print("  + hit_world() 遍历球体/立方体/三角形")
