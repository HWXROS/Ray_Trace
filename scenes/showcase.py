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
    参考创新港校区中轴线对称布局:
    - 红棕色回字形教学楼 (力行楼/躬行楼)
    - 中央玻璃建筑 (涵英楼)
    - 北部大型教学楼 (泓理楼)
    - 南部宿舍区
    """
    r = TaichiRenderer(max_spheres=80, max_cubes=150, max_triangles=10)
    np.random.seed(2024)

    # ========== 大地与道路 ==========
    # 整个校园绿地
    r.add_cube((-28, -0.5, -32), (28, 0, 22), MAT_LAMBERTIAN, (0.38, 0.62, 0.32))
    # 中央景观大道 (灰色)
    r.add_cube((-4.5, 0.01, -28), (4.5, 0.06, 18), MAT_LAMBERTIAN, (0.62, 0.60, 0.57))
    # 横向道路 (北)
    r.add_cube((-25, 0.01, -16), (25, 0.06, -14), MAT_LAMBERTIAN, (0.62, 0.60, 0.57))
    # 横向道路 (中)
    r.add_cube((-25, 0.01, -5), (25, 0.06, -3), MAT_LAMBERTIAN, (0.62, 0.60, 0.57))
    # 横向道路 (南)
    r.add_cube((-25, 0.01, 5), (25, 0.06, 7), MAT_LAMBERTIAN, (0.62, 0.60, 0.57))

    # ========== 北部 - 泓理楼区域 ==========
    # 主楼体 (红棕色)
    r.add_cube((-12, 0, -24), (12, 3.0, -17), MAT_LAMBERTIAN, (0.72, 0.30, 0.20))
    # 屋顶 (深红色)
    r.add_cube((-12.2, 3.0, -24.2), (12.2, 3.3, -16.8), MAT_LAMBERTIAN, (0.65, 0.25, 0.18))
    # 两侧配楼
    r.add_cube((-16, 0, -23), (-13, 2.0, -18), MAT_LAMBERTIAN, (0.70, 0.32, 0.22))
    r.add_cube((13, 0, -23), (16, 2.0, -18), MAT_LAMBERTIAN, (0.70, 0.32, 0.22))

    # ========== 中北部 - B区小建筑群 ==========
    for i in range(4):
        x = -10 + i * 2.8
        r.add_cube((x, 0, -15), (x+1.8, 1.0, -13), MAT_LAMBERTIAN, (0.75, 0.55, 0.50))
        r.add_cube((-x-1.8, 0, -15), (-x, 1.0, -13), MAT_LAMBERTIAN, (0.75, 0.55, 0.50))

    # ========== 中部 - 力行楼 & 躬行楼 (回字形对称) ==========
    # 左侧回字形 - 躬行楼
    # 上边
    r.add_cube((-16, 0, -12), (-4, 2.2, -10), MAT_LAMBERTIAN, (0.72, 0.30, 0.20))
    # 下边
    r.add_cube((-16, 0, -6), (-4, 2.2, -4), MAT_LAMBERTIAN, (0.72, 0.30, 0.20))
    # 左边
    r.add_cube((-16, 0, -10), (-14, 2.2, -6), MAT_LAMBERTIAN, (0.72, 0.30, 0.20))
    # 右边
    r.add_cube((-6, 0, -10), (-4, 2.2, -6), MAT_LAMBERTIAN, (0.72, 0.30, 0.20))
    # 屋顶
    r.add_cube((-16.2, 2.2, -12.2), (-3.8, 2.5, -3.8), MAT_LAMBERTIAN, (0.65, 0.25, 0.18))

    # 右侧回字形 - 力行楼
    r.add_cube((4, 0, -12), (16, 2.2, -10), MAT_LAMBERTIAN, (0.72, 0.30, 0.20))
    r.add_cube((4, 0, -6), (16, 2.2, -4), MAT_LAMBERTIAN, (0.72, 0.30, 0.20))
    r.add_cube((4, 0, -10), (6, 2.2, -6), MAT_LAMBERTIAN, (0.72, 0.30, 0.20))
    r.add_cube((14, 0, -10), (16, 2.2, -6), MAT_LAMBERTIAN, (0.72, 0.30, 0.20))
    r.add_cube((3.8, 2.2, -12.2), (16.2, 2.5, -3.8), MAT_LAMBERTIAN, (0.65, 0.25, 0.18))

    # 中央 - 涵英楼 (蓝色玻璃建筑)
    r.add_cube((-2.5, 0, -11), (2.5, 2.8, -5), MAT_DIELECTRIC, ir=1.5)
    # 玻璃底座
    r.add_cube((-3.0, 0, -11.5), (3.0, 0.3, -4.5), MAT_METAL, (0.5, 0.5, 0.55), fuzz=0.1)

    # ========== 中南部 - C区 + 阅览中心 ==========
    # 左侧C区
    for i in range(3):
        x = -11 + i * 2.5
        r.add_cube((x, 0, -2), (x+1.8, 1.2, 0), MAT_LAMBERTIAN, (0.78, 0.58, 0.52))
    # 右侧C区
    for i in range(3):
        x = 5.5 + i * 2.5
        r.add_cube((x, 0, -2), (x+1.8, 1.2, 0), MAT_LAMBERTIAN, (0.78, 0.58, 0.52))
    # 阅览中心 (东)
    r.add_cube((10, 0, -2), (15, 1.5, 1), MAT_LAMBERTIAN, (0.70, 0.65, 0.55))

    # ========== 南部 - 敏行楼 ==========
    r.add_cube((-14, 0, 3), (14, 2.5, 10), MAT_LAMBERTIAN, (0.72, 0.30, 0.20))
    r.add_cube((-14.2, 2.5, 2.8), (14.2, 2.8, 10.2), MAT_LAMBERTIAN, (0.65, 0.25, 0.18))

    # ========== 最南部 - 学生宿舍区 ==========
    # 左侧宿舍 (Y形简化 - 用3个立方体)
    for row in range(3):
        z = 12 + row * 2.5
        for col in range(4):
            x = -20 + col * 2.0
            r.add_cube((x, 0, z), (x+1.5, 1.3, z+1.8), MAT_LAMBERTIAN, (0.85, 0.60, 0.58))
    # 右侧宿舍
    for row in range(3):
        z = 12 + row * 2.5
        for col in range(4):
            x = 8 + col * 2.0
            r.add_cube((x, 0, z), (x+1.5, 1.3, z+1.8), MAT_LAMBERTIAN, (0.85, 0.60, 0.58))

    # ========== 绿化 - 树木 (绿色小球) ==========
    for _ in range(60):
        x = np.random.uniform(-26, 26)
        z = np.random.uniform(-30, 20)
        # 避开道路和建筑区域 (粗略)
        if abs(x) < 5.5 and -28 < z < 18:  # 中央大道
            continue
        if -5 < z < -3 or -16 < z < -14 or 5 < z < 7:  # 横向道路
            continue
        if -12 < x < 12 and -24 < z < -17:  # 泓理楼
            continue
        if -16 < x < -4 and -12 < z < -4:  # 躬行楼
            continue
        if 4 < x < 16 and -12 < z < -4:  # 力行楼
            continue
        if -14 < x < 14 and 3 < z < 10:  # 敏行楼
            continue
        r.add_sphere((x, 0.25, z), np.random.uniform(0.2, 0.4),
                     MAT_LAMBERTIAN, (0.15, 0.40 + np.random.random()*0.15, 0.15))

    # ========== 光源 ==========
    # 主光源 (模拟阳光)
    r.add_light((-8, 12, -5), 0.6, (6.0, 5.5, 4.5))
    # 辅助光源
    r.add_light((10, 8, -15), 0.4, (4.0, 4.0, 5.0))

    # ========== 相机 - 鸟瞰航拍视角 (更高更俯) ==========
    r.set_camera((3, 32, 12), (0, -4, -8), (0, 1, 0), 58, 16.0/9.0, 0.0)
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
