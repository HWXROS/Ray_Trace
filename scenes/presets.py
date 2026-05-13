"""
独特场景定义
满足课程设计要求: "使用独特的模型及材质（不能重复）"
"""

import numpy as np
from renderer import TaichiRenderer, MAT_LAMBERTIAN, MAT_METAL, MAT_DIELECTRIC, MAT_PERLIN


def scene_cornell_box():
    """
    开放展示台场景 - 类似 Cornell Box 但开放顶部
    包含: 漫反射墙、金属球、玻璃球、Perlin噪声球、区域光源
    """
    renderer = TaichiRenderer(max_spheres=20)
    
    # 地面 - 浅灰色
    renderer.add_sphere((0, -1000.3, -1), 1000.0, MAT_LAMBERTIAN, (0.7, 0.7, 0.7))
    
    # 左墙 - 红色（只保留下半部分，用偏移实现）
    renderer.add_sphere((-1001, 0.5, -1), 1000.0, MAT_LAMBERTIAN, (0.8, 0.2, 0.2))
    # 右墙 - 绿色
    renderer.add_sphere((1001, 0.5, -1), 1000.0, MAT_LAMBERTIAN, (0.2, 0.8, 0.2))
    # 后墙 - 浅蓝色
    renderer.add_sphere((0, 0.5, -1002), 1000.0, MAT_LAMBERTIAN, (0.7, 0.8, 0.9))
    
    # 区域光源 - 顶部发光板（用多个发光球近似）
    renderer.add_light((-0.3, 1.5, -1.5), 0.2, (4.0, 4.0, 4.0))
    renderer.add_light((0.3, 1.5, -1.5), 0.2, (4.0, 4.0, 4.0))
    renderer.add_light((0, 1.5, -1.0), 0.2, (4.0, 4.0, 4.0))
    
    # 中心球 - Perlin噪声大理石纹理
    renderer.add_perlin_sphere((0, 0.4, -1.5), 0.4)
    
    # 左侧球 - 金色金属
    renderer.add_sphere((-0.7, 0.25, -1.0), 0.25, MAT_METAL, (1.0, 0.84, 0.0), fuzz=0.1)
    
    # 右侧球 - 蓝宝石玻璃
    renderer.add_sphere((0.7, 0.25, -1.0), 0.25, MAT_DIELECTRIC, ir=1.77)
    
    # 相机
    renderer.set_camera(
        lookfrom=(0, 0.8, 1.5),
        lookat=(0, 0.3, -1.2),
        vup=(0, 1, 0),
        vfov=50.0,
        aspect_ratio=1.0,
        aperture=0.02,
        focus_dist=2.5,
    )
    
    return renderer, 500, 500


def scene_planets():
    """
    太阳系场景 - 三个行星
    太阳(发光/金色)、地球(蓝色漫反射+海洋)、月球(灰色Perlin噪声)
    """
    renderer = TaichiRenderer(max_spheres=20)
    
    # 深空背景 - 深蓝色（不挡光，只提供微弱环境）
    # 不添加大球体，让天空盒自然显示
    
    # 太阳 - 发光球体
    renderer.add_light((0, 0, -5), 1.5, (3.0, 2.8, 1.5))
    
    # 地球 - 蓝色漫反射
    renderer.add_sphere((-2.5, 0.2, -3), 0.6, MAT_LAMBERTIAN, (0.2, 0.4, 0.8))
    
    # 月球 - Perlin噪声（陨石坑效果）
    renderer.add_perlin_sphere((-1.8, 0.5, -2.5), 0.25)
    
    # 火星 - 红色漫反射
    renderer.add_sphere((2.0, -0.1, -4), 0.5, MAT_LAMBERTIAN, (0.8, 0.3, 0.1))
    
    # 小行星带（几个小球）
    np.random.seed(123)
    for _ in range(15):
        x = np.random.uniform(-4, 4)
        z = np.random.uniform(-6, -2)
        r = np.random.uniform(0.05, 0.15)
        renderer.add_sphere((x, 0, z), r, MAT_LAMBERTIAN, 
                          (0.4 + np.random.random()*0.3, 0.3, 0.2))
    
    renderer.set_camera(
        lookfrom=(0, 2, 4),
        lookat=(0, 0, -4),
        vup=(0, 1, 0),
        vfov=60.0,
        aspect_ratio=16.0/9.0,
        aperture=0.05,
        focus_dist=6.0,
    )
    
    return renderer, 800, 450


def scene_jewelry():
    """
    珠宝展示场景 - 各种宝石和金属
    钻石、红宝石、翡翠、黄金
    """
    renderer = TaichiRenderer(max_spheres=30)
    
    # 展示台 - 黑色天鹅绒
    renderer.add_sphere((0, -1000.3, -1), 1000.0, MAT_LAMBERTIAN, (0.05, 0.05, 0.05))
    
    # 钻石（高折射率）
    renderer.add_sphere((0, 0.4, -1.2), 0.4, MAT_DIELECTRIC, ir=2.42)
    
    # 红宝石
    renderer.add_sphere((-0.6, 0.25, -0.8), 0.25, MAT_DIELECTRIC, ir=1.77)
    
    # 翡翠 - 绿色漫反射
    renderer.add_sphere((0.6, 0.25, -0.8), 0.25, MAT_LAMBERTIAN, (0.2, 0.8, 0.3))
    
    # 黄金戒指（金属环）
    # 用多个小球近似环形
    n_ring = 20
    for i in range(n_ring):
        theta = 2 * np.pi * i / n_ring
        x = 0.5 * np.cos(theta)
        z = -1.2 + 0.5 * np.sin(theta)
        renderer.add_sphere((x, 0.15, z), 0.08, MAT_METAL, (1.0, 0.84, 0.0), fuzz=0.05)
    
    # 银珠
    renderer.add_sphere((-0.3, 0.15, -1.5), 0.15, MAT_METAL, (0.9, 0.9, 0.95), fuzz=0.0)
    
    # Perlin纹理装饰球
    renderer.add_perlin_sphere((0.3, 0.2, -1.6), 0.2)
    
    renderer.set_camera(
        lookfrom=(1.5, 1.5, 2),
        lookat=(0, 0.2, -1.2),
        vup=(0, 1, 0),
        vfov=35.0,
        aspect_ratio=16.0/9.0,
        aperture=0.02,
        focus_dist=3.0,
    )
    
    return renderer, 800, 450


def scene_underwater():
    """
    水下气泡场景
    大量玻璃气泡 + 蓝色水体效果
    """
    renderer = TaichiRenderer(max_spheres=300)
    np.random.seed(789)
    
    # 水底 - 沙色
    renderer.add_sphere((0, -1000, 0), 1000.0, MAT_LAMBERTIAN, (0.76, 0.7, 0.5))
    
    # 大量气泡（玻璃球）
    for _ in range(100):
        x = np.random.uniform(-5, 5)
        y = np.random.uniform(0.1, 4)
        z = np.random.uniform(-5, -1)
        r = np.random.uniform(0.05, 0.3)
        
        # 大部分是水泡（玻璃），少数是彩色气泡
        if np.random.random() < 0.8:
            renderer.add_sphere((x, y, z), r, MAT_DIELECTRIC, ir=1.33)  # 水折射率
        else:
            colors = [
                (0.2, 0.6, 0.9),  # 蓝色
                (0.9, 0.2, 0.6),  # 粉色
                (0.2, 0.9, 0.6),  # 绿色
            ]
            color = colors[np.random.randint(0, 3)]
            renderer.add_sphere((x, y, z), r, MAT_LAMBERTIAN, color)
    
    # 几条小鱼（用彩色金属球表示）
    for i in range(5):
        x = -2 + i * 1.0
        renderer.add_sphere((x, 1.5 + 0.3*np.sin(i), -2), 0.15, 
                          MAT_METAL, (1.0, 0.5, 0.0), fuzz=0.2)
        renderer.add_sphere((x-0.2, 1.5, -2), 0.08, 
                          MAT_METAL, (1.0, 0.5, 0.0), fuzz=0.2)
    
    renderer.set_camera(
        lookfrom=(3, 2, 4),
        lookat=(0, 1.5, -2),
        vup=(0, 1, 0),
        vfov=50.0,
        aspect_ratio=16.0/9.0,
        aperture=0.0,
    )
    
    return renderer, 800, 450


def scene_spiral_galaxy():
    """
    螺旋星系场景
    中心黑洞 + 螺旋臂上的彩色恒星
    """
    renderer = TaichiRenderer(max_spheres=500)
    np.random.seed(999)
    
    # 中心黑洞 - 发光核心（模拟吸积盘）
    renderer.add_light((0, 0, -3), 0.6, (2.0, 1.5, 1.0))
    
    # 螺旋臂
    n_arms = 3
    n_stars_per_arm = 60
    
    for arm in range(n_arms):
        arm_offset = arm * 2 * np.pi / n_arms
        for i in range(n_stars_per_arm):
            t = i / n_stars_per_arm
            angle = arm_offset + t * 4 * np.pi
            radius = 0.5 + t * 3.0
            
            x = radius * np.cos(angle)
            z = -3 + radius * np.sin(angle)
            y = np.random.uniform(-0.1, 0.1)
            
            # 恒星颜色根据距离变化
            if t < 0.3:
                color = (0.9, 0.9, 0.5)  # 黄色（靠近中心）
            elif t < 0.6:
                color = (0.9, 0.5, 0.5)  # 红色
            else:
                color = (0.5, 0.5, 0.9)  # 蓝色（远离中心）
            
            star_r = 0.03 + np.random.uniform(0, 0.08)
            
            if np.random.random() < 0.3:
                renderer.add_sphere((x, y, z), star_r, MAT_METAL, color, fuzz=0.0)
            else:
                renderer.add_sphere((x, y, z), star_r, MAT_LAMBERTIAN, color)
    
    # 一些随机分布的恒星
    for _ in range(50):
        x = np.random.uniform(-4, 4)
        z = np.random.uniform(-6, 0)
        y = np.random.uniform(-0.5, 0.5)
        color = np.random.random(3) * 0.5 + 0.5
        renderer.add_sphere((x, y, z), 0.03 + np.random.random()*0.05, 
                          MAT_METAL, color, fuzz=0.0)
    
    renderer.set_camera(
        lookfrom=(0, 4, 3),
        lookat=(0, 0, -3),
        vup=(0, 0, -1),
        vfov=60.0,
        aspect_ratio=16.0/9.0,
        aperture=0.0,
    )
    
    return renderer, 800, 450


# 场景注册表
SCENES = {
    'demo': ('taichi_demo.png', None),  # 内置的demo场景
    'complex': ('taichi_complex.png', None),  # 内置的complex场景
    'cornell': ('scene_cornell.png', scene_cornell_box),
    'planets': ('scene_planets.png', scene_planets),
    'jewelry': ('scene_jewelry.png', scene_jewelry),
    'underwater': ('scene_underwater.png', scene_underwater),
    'galaxy': ('scene_spiral_galaxy.png', scene_spiral_galaxy),
}
