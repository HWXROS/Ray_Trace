"""
光线追踪器 展示场景集
6 个独立场景，分别展示不同图元、材质和复杂度
"""

import sys
sys.path.insert(0, __file__.rsplit('\\', 2)[0])

import numpy as np
from PIL import Image
from renderer import (
    TaichiRenderer, MAT_LAMBERTIAN, MAT_METAL, MAT_DIELECTRIC,
    MAT_PERLIN, MAT_EMISSIVE, init_taichi_perlin,
)
import time

init_taichi_perlin(seed=42)


def scene_material_showcase():
    """场景1: 材质博览馆 —— 所有材质并排展示"""
    r = TaichiRenderer(max_spheres=10, max_cubes=20, max_triangles=20)
    
    # 地面
    r.add_cube((-4, -0.5, -6), (4, 0, 4), MAT_LAMBERTIAN, (0.8, 0.8, 0.8))
    
    # === 第1行: 漫反射 Lambertian ===
    r.add_sphere((-2, 0.5, -2), 0.4, MAT_LAMBERTIAN, (0.9, 0.1, 0.1))  # 红球
    r.add_cube((-0.6, 0.1, -2.4), (0.2, 0.9, -1.6), MAT_LAMBERTIAN, (0.1, 0.9, 0.1))  # 绿立方
    r.add_triangle((1.0, 0.1, -2.3), (1.8, 0.1, -2.3), (1.4, 0.9, -1.7),
                   MAT_LAMBERTIAN, (0.1, 0.1, 0.9))  # 蓝三角
    
    # === 第2行: 金属 Metal ===
    r.add_sphere((-2, 0.5, -3.5), 0.4, MAT_METAL, (0.9, 0.9, 0.9), fuzz=0.0)   # 银球
    r.add_cube((-0.6, 0.1, -3.9), (0.2, 0.9, -3.1), MAT_METAL, (0.8, 0.5, 0.2), fuzz=0.1)  # 铜立方
    r.add_triangle((1.0, 0.1, -3.8), (1.8, 0.1, -3.8), (1.4, 0.9, -3.2),
                   MAT_METAL, (1.0, 0.84, 0.0), fuzz=0.3)  # 金三角
    
    # === 第3行: 玻璃/发光/Perlin ===
    r.add_sphere((-2, 0.5, -5), 0.4, MAT_DIELECTRIC, ir=1.5)  # 玻璃球
    r.add_cube((-0.6, 0.1, -5.4), (0.2, 0.9, -4.6), MAT_EMISSIVE, (3.0, 3.0, 3.0))  # 发光立方
    r.add_sphere((1.4, 0.5, -5), 0.4, MAT_PERLIN)  # Perlin 球
    
    r.set_camera((0, 3, 2.5), (0, 0.5, -3.5), (0, 1, 0), 50, 1.0, 0.0)
    return r, "showcase_01_materials"


def scene_metallic_studio():
    """场景2: 金属工坊 —— 各种金属反射效果"""
    r = TaichiRenderer(max_spheres=20, max_cubes=20, max_triangles=10)
    
    # 深色地面
    r.add_cube((-5, -0.5, -5), (5, 0, 5), MAT_LAMBERTIAN, (0.1, 0.1, 0.12))
    
    # 中央大银球
    r.add_sphere((0, 0.8, -2), 0.8, MAT_METAL, (0.95, 0.95, 0.97), fuzz=0.0)
    
    # 周围金属立方体
    r.add_cube((-1.8, 0.0, -1.5), (-0.8, 0.8, -0.5), MAT_METAL, (0.9, 0.7, 0.3), fuzz=0.05)   # 金
    r.add_cube((1.0, 0.0, -1.2), (1.8, 0.6, -0.4), MAT_METAL, (0.7, 0.3, 0.2), fuzz=0.15)    # 铜
    r.add_cube((-1.2, 0.0, -3.0), (-0.4, 0.5, -2.2), MAT_METAL, (0.5, 0.5, 0.55), fuzz=0.1)  # 铁
    
    # 金属三角形装饰
    r.add_triangle((0.5, 0.2, -3.0), (1.5, 0.2, -3.0), (1.0, 1.0, -2.5),
                   MAT_METAL, (0.8, 0.8, 0.9), fuzz=0.05)
    r.add_triangle((-0.5, 0.2, -0.5), (-1.5, 0.2, -0.5), (-1.0, 1.0, -1.0),
                   MAT_METAL, (0.6, 0.8, 0.7), fuzz=0.2)
    
    # 小银球散落
    r.add_sphere((-0.5, 0.25, -1.8), 0.25, MAT_METAL, (0.9, 0.9, 0.9), fuzz=0.0)
    r.add_sphere((0.8, 0.2, -2.5), 0.2, MAT_METAL, (0.8, 0.8, 0.8), fuzz=0.05)
    
    # 主光源
    r.add_light((0, 3, 0), 0.4, (6.0, 6.0, 6.0))
    r.add_light((-2, 2, -1), 0.2, (2.0, 2.0, 3.0))
    
    r.set_camera((0, 2, 3.5), (0, 0.5, -1.5), (0, 1, 0), 45, 1.0, 0.0)
    return r, "showcase_02_metals"


def scene_glass_gallery():
    """场景3: 水晶宫 —— 玻璃与折射效果"""
    r = TaichiRenderer(max_spheres=15, max_cubes=15, max_triangles=10)
    
    # 深色反光地面
    r.add_cube((-5, -0.5, -5), (5, 0, 5), MAT_METAL, (0.15, 0.15, 0.2), fuzz=0.05)
    
    # 大玻璃立方体
    r.add_cube((-0.8, 0.0, -2.5), (0.8, 1.2, -1.0), MAT_DIELECTRIC, ir=1.5)
    
    # 玻璃球
    r.add_sphere((-1.5, 0.5, -1.5), 0.5, MAT_DIELECTRIC, ir=1.5)
    r.add_sphere((1.2, 0.4, -2.0), 0.4, MAT_DIELECTRIC, ir=1.77)  # 蓝宝石折射率
    
    # 玻璃金字塔（4个三角形）
    apex = (0.0, 1.2, -3.5)
    base = [(-0.5, 0.1, -3.8), (0.5, 0.1, -3.8), (0.0, 0.1, -3.0)]
    r.add_triangle(apex, base[0], base[1], MAT_DIELECTRIC, ir=2.42)  # 钻石
    r.add_triangle(apex, base[1], base[2], MAT_DIELECTRIC, ir=2.42)
    r.add_triangle(apex, base[2], base[0], MAT_DIELECTRIC, ir=2.42)
    
    # 小玻璃装饰
    r.add_sphere((0.5, 0.2, -1.0), 0.2, MAT_DIELECTRIC, ir=1.33)  # 水
    
    # 背光（让折射更明显）
    r.add_light((0, 2, -4), 0.5, (5.0, 5.0, 5.0))
    r.add_light((2, 1, 0), 0.3, (3.0, 3.0, 4.0))
    
    r.set_camera((0, 1.5, 3), (0, 0.5, -2), (0, 1, 0), 50, 1.0, 0.0)
    return r, "showcase_03_glass"


def scene_neon_night():
    """场景4: 霓虹展台 —— 发光材质与软阴影"""
    r = TaichiRenderer(max_spheres=15, max_cubes=20, max_triangles=10)
    
    # 深色地面
    r.add_cube((-5, -0.5, -5), (5, 0, 5), MAT_LAMBERTIAN, (0.05, 0.05, 0.08))
    
    # 被照亮的物体
    r.add_sphere((0, 0.5, -2), 0.5, MAT_METAL, (0.9, 0.9, 0.9), fuzz=0.02)  # 银球
    r.add_cube((-1.5, 0.0, -1.5), (-0.7, 0.6, -0.7), MAT_LAMBERTIAN, (0.8, 0.3, 0.3))  # 红立方
    r.add_triangle((0.8, 0.1, -1.5), (1.6, 0.1, -1.5), (1.2, 0.7, -0.8),
                   MAT_LAMBERTIAN, (0.3, 0.8, 0.3))  # 绿三角
    
    # 霓虹灯管（发光立方体和三角形）
    r.add_cube((-2.5, 0.2, -3), (-2.3, 1.5, -2.8), MAT_EMISSIVE, (5.0, 0.5, 0.5))   # 红灯管
    r.add_cube((2.3, 0.2, -3), (2.5, 1.5, -2.8), MAT_EMISSIVE, (0.5, 0.5, 5.0))     # 蓝灯管
    r.add_triangle((-0.5, 1.8, -2.5), (0.5, 1.8, -2.5), (0, 2.2, -2),
                   MAT_EMISSIVE, (0.5, 5.0, 0.5))  # 绿灯（三角形）
    
    # 远处发光球
    r.add_light((0, 0.3, -4), 0.3, (4.0, 3.0, 2.0))  # 暖光球
    
    r.set_camera((0, 1.5, 3.5), (0, 0.8, -2), (0, 1, 0), 55, 1.0, 0.0)
    return r, "showcase_04_neon"


def scene_geometric_forest():
    """场景5: 几何森林 —— 大量混合图元随机散布"""
    r = TaichiRenderer(max_spheres=50, max_cubes=50, max_triangles=50)
    np.random.seed(42)
    
    # 绿色地面
    r.add_cube((-8, -0.5, -8), (8, 0, 8), MAT_LAMBERTIAN, (0.3, 0.6, 0.3))
    
    # 随机散布几何体
    for _ in range(30):
        x = np.random.uniform(-4, 4)
        z = np.random.uniform(-6, -1)
        mat = np.random.random()
        
        if mat < 0.4:
            # 球体
            col = np.random.random(3) * 0.5 + 0.3
            r.add_sphere((x, 0.2, z), np.random.uniform(0.1, 0.3),
                        MAT_LAMBERTIAN, tuple(col))
        elif mat < 0.7:
            # 立方体
            col = np.random.random(3) * 0.5 + 0.3
            s = np.random.uniform(0.2, 0.5)
            r.add_cube((x, 0.0, z), (x+s, s, z+s), MAT_LAMBERTIAN, tuple(col))
        else:
            # 三角形
            col = np.random.random(3) * 0.5 + 0.3
            h = np.random.uniform(0.2, 0.5)
            r.add_triangle((x, 0.0, z), (x+0.4, 0.0, z), (x+0.2, h, z+0.2),
                          MAT_LAMBERTIAN, tuple(col))
    
    # 几个金属物体点缀
    r.add_cube((-1, 0.0, -3), (0.5, 0.8, -2), MAT_METAL, (0.9, 0.8, 0.4), fuzz=0.05)
    r.add_sphere((2, 0.4, -4), 0.4, MAT_METAL, (0.7, 0.7, 0.8), fuzz=0.1)
    
    # 光源
    r.add_light((0, 5, 0), 0.5, (5.0, 5.0, 5.0))
    
    r.set_camera((0, 3, 5), (0, 0, -3), (0, 1, 0), 60, 1.0, 0.0)
    return r, "showcase_05_forest"


def scene_cornell_real():
    """场景6: 真正的 Cornell Box —— 用立方体建造"""
    r = TaichiRenderer(max_spheres=10, max_cubes=20, max_triangles=10)
    
    # Cornell Box 墙壁（用真正的立方体，而不是大球）
    # 地板 - 白色
    r.add_cube((-2, -1, -3), (2, -0.9, 1), MAT_LAMBERTIAN, (0.9, 0.9, 0.9))
    # 天花板 - 白色
    r.add_cube((-2, 1.9, -3), (2, 2.0, 1), MAT_LAMBERTIAN, (0.9, 0.9, 0.9))
    # 左墙 - 红色
    r.add_cube((-2, -1, -3), (-1.9, 2, 1), MAT_LAMBERTIAN, (0.8, 0.2, 0.2))
    # 右墙 - 绿色
    r.add_cube((1.9, -1, -3), (2, 2, 1), MAT_LAMBERTIAN, (0.2, 0.8, 0.2))
    # 后墙 - 白色
    r.add_cube((-2, -1, -3), (2, 2, -2.9), MAT_LAMBERTIAN, (0.9, 0.9, 0.9))
    
    # 天花板光源（发光立方体）
    r.add_cube((-0.5, 1.85, -1.5), (0.5, 1.9, -0.5), MAT_EMISSIVE, (5.0, 5.0, 5.0))
    
    # 中央物体
    r.add_sphere((0, -0.4, -1.5), 0.5, MAT_LAMBERTIAN, (0.9, 0.9, 0.9))  # 白球
    r.add_cube((-0.6, -0.9, -1.0), (-0.1, -0.4, -0.5), MAT_METAL, (0.9, 0.7, 0.3), fuzz=0.05)  # 金立方
    r.add_triangle((0.3, -0.9, -1.5), (0.8, -0.9, -1.5), (0.55, -0.4, -1.5),
                   MAT_DIELECTRIC, ir=1.5)  # 玻璃三角
    
    # 相机在盒子前方
    r.set_camera((0, 1, 2.5), (0, 0.5, -1.5), (0, 1, 0), 60, 1.0, 0.0)
    return r, "showcase_06_cornell"


def scene_innovation_harbor():
    """
    场景7: 西安交通大学创新港微缩模型
    严格按照平面图 (../data/6.png) 布局:
    - 扇形倒三角，北部宽南部窄
    - 西迁大道中轴线
    - 黄色=教学科研，粉色=宿舍，绿色=绿地
    """
    r = TaichiRenderer(max_spheres=100, max_cubes=250, max_triangles=10)
    np.random.seed(2024)

    C_YELLOW = (0.78, 0.68, 0.42)
    C_PINK   = (0.88, 0.58, 0.58)
    C_GREEN  = (0.42, 0.68, 0.38)
    C_ROAD   = (0.72, 0.70, 0.67)
    C_SPORT  = (0.35, 0.55, 0.30)

    # ========== 大地 (绿地) ==========
    r.add_cube((-32, -0.5, -28), (32, 0, 22), MAT_LAMBERTIAN, C_GREEN)

    # ========== 道路网格 ==========
    # 纵向 - 西迁大道 (中央)
    r.add_cube((-1.5, 0.01, -26), (1.5, 0.06, 20), MAT_LAMBERTIAN, C_ROAD)
    # 纵向 - 西侧
    r.add_cube((-10, 0.01, -26), (-8, 0.06, 20), MAT_LAMBERTIAN, C_ROAD)
    r.add_cube((-18, 0.01, -26), (-16, 0.06, 20), MAT_LAMBERTIAN, C_ROAD)
    r.add_cube((-26, 0.01, -26), (-24, 0.06, 20), MAT_LAMBERTIAN, C_ROAD)
    # 纵向 - 东侧
    r.add_cube((8, 0.01, -26), (10, 0.06, 20), MAT_LAMBERTIAN, C_ROAD)
    r.add_cube((16, 0.01, -26), (18, 0.06, 20), MAT_LAMBERTIAN, C_ROAD)
    r.add_cube((24, 0.01, -26), (26, 0.06, 20), MAT_LAMBERTIAN, C_ROAD)
    # 横向
    for z in [-20, -14, -8, -2, 4, 10, 16]:
        r.add_cube((-32, 0.01, z-0.4), (32, 0.06, z+0.4), MAT_LAMBERTIAN, C_ROAD)

    # ========== 最北部 - 泓理楼 ==========
    r.add_cube((-22, 0, 14), (22, 2.5, 19), MAT_LAMBERTIAN, C_YELLOW)

    # ========== B区宿舍 (粉色，泓理楼下方) ==========
    for i in range(6):
        x = -20 + i*2.4
        r.add_cube((x, 0, 8), (x+1.6, 1.0, 10), MAT_LAMBERTIAN, C_PINK)
        r.add_cube((x, 0, 10.5), (x+1.6, 1.0, 12.5), MAT_LAMBERTIAN, C_PINK)
    for i in range(6):
        x = 4 + i*2.4
        r.add_cube((x, 0, 8), (x+1.6, 1.0, 10), MAT_LAMBERTIAN, C_PINK)
        r.add_cube((x, 0, 10.5), (x+1.6, 1.0, 12.5), MAT_LAMBERTIAN, C_PINK)

    # ========== 涵英楼 (U形，黄色) + 通英楼 ==========
    r.add_cube((-10, 0, 2), (10, 2.0, 4), MAT_LAMBERTIAN, C_YELLOW)
    r.add_cube((-10, 0, -2), (10, 2.0, 0), MAT_LAMBERTIAN, C_YELLOW)
    r.add_cube((-10, 0, -2), (-7, 2.0, 4), MAT_LAMBERTIAN, C_YELLOW)
    r.add_cube((7, 0, -2), (10, 2.0, 4), MAT_LAMBERTIAN, C_YELLOW)
    r.add_cube((-16, 0, 0), (-11, 1.8, 3), MAT_LAMBERTIAN, C_YELLOW)
    r.add_cube((11, 0, 0), (16, 1.8, 3), MAT_LAMBERTIAN, C_YELLOW)

    # ========== 躬行楼(西) & 力行楼(东) ==========
    r.add_cube((-18, 0, -8), (-4, 2.5, -4), MAT_LAMBERTIAN, C_YELLOW)
    r.add_cube((4, 0, -8), (18, 2.5, -4), MAT_LAMBERTIAN, C_YELLOW)

    # ========== 中下部 - 米兰楼/思源楼/博物馆/阅览中心/C区 ==========
    r.add_cube((-16, 0, -14), (-10, 1.5, -11), MAT_LAMBERTIAN, C_YELLOW)
    r.add_cube((-9, 0, -14), (-5, 1.5, -11), MAT_LAMBERTIAN, C_YELLOW)
    r.add_cube((-4, 0, -14), (4, 1.8, -11), MAT_LAMBERTIAN, C_YELLOW)
    r.add_cube((5, 0, -14), (10, 1.5, -11), MAT_LAMBERTIAN, C_YELLOW)
    r.add_cube((11, 0, -14), (16, 1.5, -11), MAT_LAMBERTIAN, C_YELLOW)
    for i in range(5):
        x = -18 + i*2.2
        r.add_cube((x, 0, -17), (x+1.5, 1.0, -15.5), MAT_LAMBERTIAN, C_PINK)
    for i in range(5):
        x = 5 + i*2.2
        r.add_cube((x, 0, -17), (x+1.5, 1.0, -15.5), MAT_LAMBERTIAN, C_PINK)

    # ========== 南部 - 敏行楼 ==========
    r.add_cube((-20, 0, -22), (20, 2.5, -18), MAT_LAMBERTIAN, C_YELLOW)

    # ========== A区宿舍 (粉色) ==========
    for i in range(5):
        x = -16 + i*2.2
        r.add_cube((x, 0, -26), (x+1.5, 1.0, -24), MAT_LAMBERTIAN, C_PINK)
    for i in range(5):
        x = 4 + i*2.2
        r.add_cube((x, 0, -26), (x+1.5, 1.0, -24), MAT_LAMBERTIAN, C_PINK)

    # ========== 最南部 - Y形宿舍 ==========
    r.add_cube((-2, 0, -28), (2, 1.2, -25), MAT_LAMBERTIAN, C_PINK)
    r.add_cube((-8, 0, -26), (-2, 1.2, -24), MAT_LAMBERTIAN, C_PINK)
    r.add_cube((2, 0, -26), (8, 1.2, -24), MAT_LAMBERTIAN, C_PINK)
    r.add_cube((-6, 0, -24), (-3, 1.0, -22), MAT_LAMBERTIAN, C_PINK)
    r.add_cube((3, 0, -24), (6, 1.0, -22), MAT_LAMBERTIAN, C_PINK)

    # ========== 东侧建筑群 ==========
    r.add_cube((22, 0, -6), (29, 2.0, -3), MAT_LAMBERTIAN, C_YELLOW)
    r.add_cube((22, 0, -11), (29, 2.0, -8), MAT_LAMBERTIAN, C_YELLOW)
    r.add_cube((22, 0, 2), (29, 2.0, 5), MAT_LAMBERTIAN, C_YELLOW)
    r.add_cube((22, 0, 8), (29, 2.0, 12), MAT_LAMBERTIAN, C_YELLOW)

    # ========== 西侧 - 核能研究院 ==========
    r.add_cube((-29, 0, 8), (-22, 2.0, 14), MAT_LAMBERTIAN, C_YELLOW)

    # ========== 运动场地 ==========
    r.add_cube((20, 0.01, -20), (28, 0.05, -16), MAT_LAMBERTIAN, C_SPORT)
    r.add_cube((-28, 0.01, -20), (-20, 0.05, -16), MAT_LAMBERTIAN, C_SPORT)

    # ========== 树木 ==========
    for _ in range(100):
        x = np.random.uniform(-30, 30)
        z = np.random.uniform(-27, 20)
        road_skip = False
        for rz in [-20, -14, -8, -2, 4, 10, 16]:
            if abs(z - rz) < 0.6:
                road_skip = True; break
        for rx in [-26, -18, -10, -1.5, 1.5, 8, 16, 24]:
            if abs(x - rx) < 1.8:
                road_skip = True; break
        if road_skip:
            continue
        r.add_sphere((x, 0.25, z), np.random.uniform(0.2, 0.35),
                     MAT_LAMBERTIAN, (0.12, 0.38, 0.12))

    # ========== 光源 ==========
    r.add_light((-12, 15, 5), 0.5, (5.5, 5.0, 4.0))
    r.add_light((12, 12, -8), 0.4, (4.0, 4.0, 5.0))

    # ========== 相机 - 45度沙盘视角 ==========
    r.set_camera((22, 32, 18), (0, 0, -6), (0, 1, 0), 58, 16.0/9.0, 0.0)
    return r, "showcase_07_innovation_harbor"


# ========== 批量渲染 ==========
SCENES = [
    scene_material_showcase,
    scene_metallic_studio,
    scene_glass_gallery,
    scene_neon_night,
    scene_geometric_forest,
    scene_cornell_real,
    scene_innovation_harbor,
]

if __name__ == '__main__':
    print("=" * 60)
    print("  光线追踪器 展示场景集")
    print("=" * 60)
    
    for scene_func in SCENES:
        print(f"\n--- 渲染: {scene_func.__name__} ---")
        t0 = time.time()
        
        renderer, filename = scene_func()
        img = renderer.render(800, 800, samples_per_pixel=200, max_depth=50)
        
        output = f'outputs/{filename}.png'
        Image.fromarray(img).save(output)
        
        print(f"  已保存: {output} (耗时 {time.time()-t0:.1f}s)")
    
    print(f"\n{'=' * 60}")
    print("全部完成！")
