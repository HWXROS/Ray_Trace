"""
Cornell Box 高质量渲染
增大光源面积 + 提高采样数
"""

import sys
sys.path.insert(0, __file__.rsplit('\\', 2)[0])

from PIL import Image
from renderer import (
    TaichiRenderer, MAT_LAMBERTIAN, MAT_METAL, MAT_DIELECTRIC, MAT_EMISSIVE,
    init_taichi_perlin,
)

init_taichi_perlin(seed=42)

r = TaichiRenderer(max_spheres=10, max_cubes=20, max_triangles=10)

# Cornell Box 墙壁
r.add_cube((-2, -1, -3), (2, -0.9, 1), MAT_LAMBERTIAN, (0.9, 0.9, 0.9))      # 地板
r.add_cube((-2, 1.9, -3), (2, 2.0, 1), MAT_LAMBERTIAN, (0.9, 0.9, 0.9))      # 天花板
r.add_cube((-2, -1, -3), (-1.9, 2, 1), MAT_LAMBERTIAN, (0.8, 0.2, 0.2))      # 左墙 红
r.add_cube((1.9, -1, -3), (2, 2, 1), MAT_LAMBERTIAN, (0.2, 0.8, 0.2))        # 右墙 绿
r.add_cube((-2, -1, -3), (2, 2, -2.9), MAT_LAMBERTIAN, (0.9, 0.9, 0.9))      # 后墙

# 增大发光天花板面积（原来 0.5×0.5 → 现在 1.5×1.5）
r.add_cube((-0.75, 1.85, -1.5), (0.75, 1.9, 0.0), MAT_EMISSIVE, (3.5, 3.5, 3.5))

# 中央物体
r.add_sphere((0, -0.4, -1.2), 0.5, MAT_LAMBERTIAN, (0.9, 0.9, 0.9))
r.add_cube((-0.6, -0.9, -0.8), (-0.1, -0.4, -0.3), MAT_METAL, (0.9, 0.7, 0.3), fuzz=0.05)
r.add_triangle((0.3, -0.9, -1.2), (0.8, -0.9, -1.2), (0.55, -0.4, -1.2),
               MAT_DIELECTRIC, ir=1.5)

r.set_camera((0, 1, 2.5), (0, 0.5, -1.0), (0, 1, 0), 60, 1.0, 0.0)

print("[Cornell HQ] 渲染 800x800 @ 1000 samples...")
img = r.render(800, 800, samples_per_pixel=1000, max_depth=50)
Image.fromarray(img).save('outputs/showcase_06_cornell_hq.png')
print("已保存: outputs/showcase_06_cornell_hq.png")
