"""
光线追踪器 - 主程序
基于 Peter Shirley 的 Ray Tracing in One Weekend
"""

import sys
import math
import time
import numpy as np
from PIL import Image

# 添加项目根目录到路径
sys.path.insert(0, __file__.rsplit('\\', 1)[0])

from core.vec3 import Vec3, Color, Point3, dot, unit_vector
from core.ray import Ray
from core.camera import Camera
from hittables.hittable import HitRecord, HittableList
from hittables.sphere import Sphere
from materials.material import Lambertian, Metal, Dielectric


def ray_color(r: Ray, world: HittableList, depth: int) -> Color:
    """
    计算光线颜色（递归路径追踪）
    depth: 最大递归深度，防止无限递归
    """
    # 超过最大深度，返回黑色
    if depth <= 0:
        return Color(0, 0, 0)
    
    rec = HitRecord()
    
    # 检测光线与场景中物体的相交
    # t_min=0.001 避免浮点精度问题导致的自相交
    if world.hit(r, 0.001, float('inf'), rec):
        attenuation = Color()
        scattered = Ray(Point3(), Vec3())
        
        if rec.material.scatter(r, rec, attenuation, scattered):
            # 递归追踪散射光线
            return attenuation * ray_color(scattered, world, depth - 1)
        
        return Color(0, 0, 0)
    
    # 没有击中物体，返回天空背景色（线性渐变）
    unit_dir = unit_vector(r.direction())
    t = 0.5 * (unit_dir.y + 1.0)
    return (1.0 - t) * Color(1.0, 1.0, 1.0) + t * Color(0.5, 0.7, 1.0)


def write_color(pixel_color: Color, samples_per_pixel: int) -> np.ndarray:
    """将颜色值转换为像素值，并进行伽马校正"""
    r = pixel_color.x
    g = pixel_color.y
    b = pixel_color.z
    
    # 除以采样数（取平均）
    scale = 1.0 / samples_per_pixel
    r *= scale
    g *= scale
    b *= scale
    
    # Gamma 2.0 校正（平方根）
    r = math.sqrt(r)
    g = math.sqrt(g)
    b = math.sqrt(b)
    
    # 映射到 [0, 255]
    ir = int(256 * np.clip(r, 0.0, 0.999))
    ig = int(256 * np.clip(g, 0.0, 0.999))
    ib = int(256 * np.clip(b, 0.0, 0.999))
    
    return np.array([ir, ig, ib], dtype=np.uint8)


def render_scene(world: HittableList, camera: Camera,
                 image_width: int, image_height: int,
                 samples_per_pixel: int = 100, max_depth: int = 50) -> np.ndarray:
    """
    渲染场景
    返回 shape 为 (height, width, 3) 的 numpy 数组
    """
    image = np.zeros((image_height, image_width, 3), dtype=np.uint8)
    total_pixels = image_width * image_height
    processed = 0
    start_time = time.time()
    
    print(f"开始渲染: {image_width}x{image_height}, 每像素采样 {samples_per_pixel} 次, 最大深度 {max_depth}")
    
    for j in range(image_height):
        for i in range(image_width):
            pixel_color = Color(0, 0, 0)
            
            # 对每个像素进行多次采样（抗锯齿）
            for s in range(samples_per_pixel):
                u = (i + np.random.random()) / (image_width - 1)
                v = ((image_height - 1 - j) + np.random.random()) / (image_height - 1)
                r = camera.get_ray(u, v)
                pixel_color += ray_color(r, world, max_depth)
            
            image[j, i] = write_color(pixel_color, samples_per_pixel)
            processed += 1
        
        # 每完成一行打印进度
        elapsed = time.time() - start_time
        eta = (elapsed / processed) * (total_pixels - processed) if processed > 0 else 0
        print(f"\r进度: {processed}/{total_pixels} ({100*processed/total_pixels:.1f}%) | 已用 {elapsed:.1f}s | 预计剩余 {eta:.1f}s", end='')
    
    print(f"\n渲染完成！总耗时 {time.time() - start_time:.1f} 秒")
    return image


def create_demo_scene() -> tuple:
    """
    创建演示场景（经典的三个球场景）
    返回: (world, camera)
    """
    world = HittableList()
    
    # 地面（巨大的球体）
    material_ground = Lambertian(Color(0.8, 0.8, 0.0))
    world.add(Sphere(Point3(0, -100.5, -1), 100.0, material_ground))
    
    # 中心球 - 漫反射红色
    material_center = Lambertian(Color(0.7, 0.3, 0.3))
    world.add(Sphere(Point3(0, 0, -1), 0.5, material_center))
    
    # 左侧球 - 金属
    material_left = Metal(Color(0.8, 0.8, 0.8), 0.3)
    world.add(Sphere(Point3(-1.0, 0, -1), 0.5, material_left))
    
    # 右侧球 - 玻璃
    material_right = Dielectric(1.5)
    world.add(Sphere(Point3(1.0, 0, -1), 0.5, material_right))
    
    # 相机参数
    aspect_ratio = 16.0 / 9.0
    image_width = 400
    image_height = int(image_width / aspect_ratio)
    
    lookfrom = Point3(-2, 2, 1)
    lookat = Point3(0, 0, -1)
    vup = Vec3(0, 1, 0)
    vfov = 20.0
    
    camera = Camera(lookfrom, lookat, vup, vfov, aspect_ratio)
    
    return world, camera, image_width, image_height


def create_complex_scene() -> tuple:
    """
    创建复杂场景（随机小球场景）
    这是 Ray Tracing in One Weekend 中的经典最终场景
    """
    world = HittableList()
    
    # 地面
    material_ground = Lambertian(Color(0.5, 0.5, 0.5))
    world.add(Sphere(Point3(0, -1000, 0), 1000, material_ground))
    
    # 随机生成大量小球
    np.random.seed(42)
    for a in range(-11, 11):
        for b in range(-11, 11):
            choose_mat = np.random.random()
            center = Point3(a + 0.9 * np.random.random(), 
                           0.2, 
                           b + 0.9 * np.random.random())
            
            if (center - Point3(4, 0.2, 0)).length() > 0.9:
                if choose_mat < 0.8:
                    # 漫反射
                    albedo = Color(np.random.random() * np.random.random(),
                                  np.random.random() * np.random.random(),
                                  np.random.random() * np.random.random())
                    world.add(Sphere(center, 0.2, Lambertian(albedo)))
                elif choose_mat < 0.95:
                    # 金属
                    albedo = Color(0.5 * (1 + np.random.random()),
                                  0.5 * (1 + np.random.random()),
                                  0.5 * (1 + np.random.random()))
                    fuzz = 0.5 * np.random.random()
                    world.add(Sphere(center, 0.2, Metal(albedo, fuzz)))
                else:
                    # 玻璃
                    world.add(Sphere(center, 0.2, Dielectric(1.5)))
    
    # 三个大球
    world.add(Sphere(Point3(0, 1, 0), 1.0, Dielectric(1.5)))
    world.add(Sphere(Point3(-4, 1, 0), 1.0, Lambertian(Color(0.4, 0.2, 0.1))))
    world.add(Sphere(Point3(4, 1, 0), 1.0, Metal(Color(0.7, 0.6, 0.5), 0.0)))
    
    # 相机参数
    aspect_ratio = 16.0 / 9.0
    image_width = 800
    image_height = int(image_width / aspect_ratio)
    
    lookfrom = Point3(13, 2, 3)
    lookat = Point3(0, 0, 0)
    vup = Vec3(0, 1, 0)
    vfov = 20.0
    aperture = 0.1
    focus_dist = 10.0
    
    camera = Camera(lookfrom, lookat, vup, vfov, aspect_ratio, aperture, focus_dist)
    
    return world, camera, image_width, image_height


def main():
    print("=" * 50)
    print("  光线追踪器 v1.0")
    print("  高级图形学与增强现实 - 课程设计")
    print("=" * 50)
    
    # 选择场景: 'demo' 或 'complex'
    scene_name = 'demo'  # 先跑 demo 场景验证
    
    if scene_name == 'demo':
        world, camera, image_width, image_height = create_demo_scene()
        samples_per_pixel = 100
        max_depth = 50
        output_file = 'outputs/demo_scene.png'
    else:
        world, camera, image_width, image_height = create_complex_scene()
        samples_per_pixel = 100
        max_depth = 50
        output_file = 'outputs/complex_scene.png'
    
    # 渲染
    image = render_scene(world, camera, image_width, image_height,
                        samples_per_pixel, max_depth)
    
    # 保存图片
    img = Image.fromarray(image)
    img.save(output_file)
    print(f"图片已保存到: {output_file}")


if __name__ == '__main__':
    main()
