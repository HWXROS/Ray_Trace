"""
新图元测试：立方体 + 三角形
"""

import sys
sys.path.insert(0, __file__.rsplit('\\', 2)[0])

import numpy as np
from PIL import Image
from renderer import (
    TaichiRenderer, MAT_LAMBERTIAN, MAT_METAL, MAT_DIELECTRIC, MAT_EMISSIVE,
    init_taichi_perlin,
)

init_taichi_perlin(seed=42)


def create_primitives_scene():
    """创建立方体和三角形展示场景"""
    renderer = TaichiRenderer(max_spheres=10, max_cubes=20, max_triangles=20)
    
    # === 地面：用大立方体代替大球 ===
    # 地面是一个扁平的 AABB
    renderer.add_cube(
        min_point=(-10, -1.0, -10),
        max_point=(10, 0.0, 10),
        mat_type=MAT_LAMBERTIAN,
        albedo=(0.7, 0.7, 0.7),
    )
    
    # === 中心：金属立方体 ===
    renderer.add_cube(
        min_point=(-0.5, 0.2, -2.5),
        max_point=(0.5, 1.2, -1.5),
        mat_type=MAT_METAL,
        albedo=(0.9, 0.7, 0.3),  # 金色
        fuzz=0.05,
    )
    
    # === 左侧：红色漫反射立方体 ===
    renderer.add_cube(
        min_point=(-2.0, 0.0, -2.0),
        max_point=(-1.0, 1.0, -1.0),
        mat_type=MAT_LAMBERTIAN,
        albedo=(0.8, 0.2, 0.2),
    )
    
    # === 右侧：玻璃球（作为材质对比）===
    renderer.add_sphere(
        center=(1.5, 0.5, -2.0),
        radius=0.5,
        mat_type=MAT_DIELECTRIC,
        ir=1.5,
    )
    
    # === 前方：三角形金字塔（4个三角形组成）===
    # 金字塔顶点
    apex = (0.0, 1.5, -0.5)
    base_v0 = (-0.5, 0.3, 0.0)
    base_v1 = (0.5, 0.3, 0.0)
    base_v2 = (0.0, 0.3, 0.8)
    
    # 4个面
    renderer.add_triangle(apex, base_v0, base_v1, MAT_LAMBERTIAN, (0.2, 0.6, 0.8))
    renderer.add_triangle(apex, base_v1, base_v2, MAT_LAMBERTIAN, (0.2, 0.6, 0.8))
    renderer.add_triangle(apex, base_v2, base_v0, MAT_LAMBERTIAN, (0.2, 0.6, 0.8))
    # 底面
    renderer.add_triangle(base_v0, base_v2, base_v1, MAT_LAMBERTIAN, (0.2, 0.6, 0.8))
    
    # === 小三角形装饰 ===
    renderer.add_triangle(
        (-1.5, 0.5, -1.0), (-1.0, 1.2, -1.5), (-0.5, 0.5, -1.0),
        MAT_METAL, (0.8, 0.8, 0.9), fuzz=0.1,
    )
    
    # === 区域光源 ===
    renderer.add_light((-2, 3, 0), 0.3, (5.0, 5.0, 5.0))
    renderer.add_light((2, 3, -1), 0.3, (4.0, 4.0, 4.0))
    
    # 相机
    renderer.set_camera(
        lookfrom=(0, 2, 3),
        lookat=(0, 0.5, -1.5),
        vup=(0, 1, 0),
        vfov=40.0,
        aspect_ratio=16.0/9.0,
        aperture=0.0,
        focus_dist=5.0,
    )
    
    return renderer


if __name__ == '__main__':
    print("=" * 50)
    print("  新图元测试：立方体 + 三角形")
    print("=" * 50)
    
    renderer = create_primitives_scene()
    
    # 高分辨率渲染
    image = renderer.render(
        image_width=1200,
        image_height=675,
        samples_per_pixel=200,
        max_depth=50,
    )
    
    img = Image.fromarray(image)
    output_path = 'outputs/scene_primitives.png'
    img.save(output_path)
    print(f"图片已保存到: {output_path}")
