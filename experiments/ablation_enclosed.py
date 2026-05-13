"""
封闭空间消融实验
Row1: 采样数对封闭空间的影响 (固定 Cornell Box + 中等光源)
Row2: 光源面积对封闭空间的影响 (固定 Cornell Box + 500spp)
Row3: 封闭程度的影响 (固定 500spp + 中等光源)
"""

import sys
sys.path.insert(0, __file__.rsplit('\\', 2)[0])

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from renderer import (
    TaichiRenderer, MAT_LAMBERTIAN, MAT_METAL, MAT_EMISSIVE, init_taichi_perlin,
)
import time

init_taichi_perlin(seed=42)


def cornell_box(light_half=0.75, samples=500, add_front_wall=False):
    """创建 Cornell Box，可调整光源大小和是否加前墙"""
    r = TaichiRenderer(max_spheres=10, max_cubes=20, max_triangles=10)
    
    # 标准 5 面
    r.add_cube((-2, -1, -3), (2, -0.9, 1), MAT_LAMBERTIAN, (0.9, 0.9, 0.9))      # 地板
    r.add_cube((-2, 1.9, -3), (2, 2.0, 1), MAT_LAMBERTIAN, (0.9, 0.9, 0.9))      # 天花板
    r.add_cube((-2, -1, -3), (-1.9, 2, 1), MAT_LAMBERTIAN, (0.8, 0.2, 0.2))      # 左墙红
    r.add_cube((1.9, -1, -3), (2, 2, 1), MAT_LAMBERTIAN, (0.2, 0.8, 0.2))        # 右墙绿
    r.add_cube((-2, -1, -3), (2, 2, -2.9), MAT_LAMBERTIAN, (0.9, 0.9, 0.9))      # 后墙
    
    if add_front_wall:
        r.add_cube((-2, -1, 0.9), (2, 2, 1.0), MAT_LAMBERTIAN, (0.9, 0.9, 0.9))  # 前墙
    
    # 天花板光源（面积可调）
    intensity = 3.5
    r.add_cube((-light_half, 1.85, -1.5), (light_half, 1.9, 0.0),
               MAT_EMISSIVE, (intensity, intensity, intensity))
    
    # 中央物体
    r.add_sphere((0, -0.4, -1.2), 0.5, MAT_LAMBERTIAN, (0.9, 0.9, 0.9))
    r.add_cube((-0.6, -0.9, -0.8), (-0.1, -0.4, -0.3),
               MAT_METAL, (0.9, 0.7, 0.3), fuzz=0.05)
    
    # 全封闭时相机必须放在盒子内部，否则前墙会挡住所有视线
    if add_front_wall:
        r.set_camera((0, 0.8, 0.5), (0, 0, -1.5), (0, 1, 0), 70, 1.0, 0.0)
    else:
        r.set_camera((0, 1, 2.5), (0, 0.5, -1.0), (0, 1, 0), 60, 1.0, 0.0)
    return r


def enclosure_scene(walls=5, samples=500):
    """
    不同封闭程度的场景
    walls=1: 只有地板
    walls=2: 地板+后墙
    walls=3: 地板+后墙+左红墙+右绿墙
    walls=4: 地板+后墙+左右墙+天花板
    walls=5: 完整 Cornell Box
    """
    r = TaichiRenderer(max_spheres=10, max_cubes=20, max_triangles=10)
    
    # 地板
    r.add_cube((-2, -1, -3), (2, -0.9, 1), MAT_LAMBERTIAN, (0.9, 0.9, 0.9))
    
    if walls >= 2:
        r.add_cube((-2, -1, -3), (2, 2, -2.9), MAT_LAMBERTIAN, (0.9, 0.9, 0.9))  # 后墙
    
    if walls >= 3:
        r.add_cube((-2, -1, -3), (-1.9, 2, 1), MAT_LAMBERTIAN, (0.8, 0.2, 0.2))  # 左墙
        r.add_cube((1.9, -1, -3), (2, 2, 1), MAT_LAMBERTIAN, (0.2, 0.8, 0.2))    # 右墙
    
    if walls >= 4:
        r.add_cube((-2, 1.9, -3), (2, 2.0, 1), MAT_LAMBERTIAN, (0.9, 0.9, 0.9))  # 天花板
    
    if walls >= 5:
        r.add_cube((-2, -1, 0.9), (2, 2, 1.0), MAT_LAMBERTIAN, (0.9, 0.9, 0.9))  # 前墙
    
    # 统一用悬浮发光球（避免天花板面板在不同场景下不一致）
    r.add_light((0, 1.5, -1), 0.35, (6.0, 6.0, 6.0))
    
    # 中央物体
    r.add_sphere((0, -0.4, -1.2), 0.5, MAT_LAMBERTIAN, (0.9, 0.9, 0.9))
    r.add_cube((-0.6, -0.9, -0.8), (-0.1, -0.4, -0.3),
               MAT_METAL, (0.9, 0.7, 0.3), fuzz=0.05)
    
    # 全封闭时相机必须放在盒子内部，否则前墙会挡住所有视线
    if walls >= 5:
        r.set_camera((0, 0.8, 0.5), (0, 0, -1.5), (0, 1, 0), 70, 1.0, 0.0)
    else:
        r.set_camera((0, 1, 2.5), (0, 0.5, -1.0), (0, 1, 0), 60, 1.0, 0.0)
    return r


# ========== 实验配置 ==========
experiments = [
    # Row 1: 采样数 (固定 light_half=0.75)
    ("Samples | Enclosed | Light 1.5x1.5", [
        (50, 0.75, False, "50 spp"),
        (200, 0.75, False, "200 spp"),
        (500, 0.75, False, "500 spp"),
        (1000, 0.75, False, "1000 spp"),
    ]),
    
    # Row 2: 光源面积 (固定 500 spp)
    ("Light Area | Enclosed | 500 spp", [
        (500, 0.2, False, "light 0.4x0.4"),
        (500, 0.5, False, "light 1.0x1.0"),
        (500, 0.75, False, "light 1.5x1.5"),
        (500, 1.5, False, "light 3.0x3.0"),
    ]),
    
    # Row 3: 封闭程度 (固定 500 spp, 悬浮光源)
    ("Enclosure | 500 spp | Sphere Light", [
        (500, 0, False, "Open (1 wall)"),
        (500, 0, False, "Semi (3 walls)"),
        (500, 0, False, "Full (5 walls)"),
        (500, 0, False, "Super (6 walls)"),
    ]),
]


# ========== 渲染 ==========
print("=" * 60)
print("Enclosed Space Ablation Study")
print("=" * 60)

all_rows = []
row_titles = []

for row_idx, (row_title, configs) in enumerate(experiments):
    print(f"\n--- Row {row_idx+1}: {row_title} ---")
    row_images = []
    row_labels = []
    
    for col_idx, (spp, light_half, front, label) in enumerate(configs):
        print(f"  Rendering: {label} ...", end=" ", flush=True)
        t0 = time.time()
        
        if row_idx == 2:  # Row 3: 封闭程度实验
            walls = [1, 3, 4, 5][col_idx]
            renderer = enclosure_scene(walls=walls, samples=spp)
        else:
            renderer = cornell_box(light_half=light_half, samples=spp, add_front_wall=front)
        
        img = renderer.render(400, 400, spp, 50)
        elapsed = time.time() - t0
        print(f"({elapsed:.1f}s)")
        
        row_images.append(Image.fromarray(img))
        row_labels.append(label)
    
    all_rows.append((row_images, row_labels))
    row_titles.append(row_title)


# ========== 拼接 ==========
print("\nAssembling grid...")

GRID_W = 400
GRID_H = 400
TITLE_H = 55
LABEL_H = 35
MARGIN = 12
ROWS = 3
COLS = 4

total_w = COLS * GRID_W + (COLS + 1) * MARGIN
total_h = ROWS * (GRID_H + LABEL_H) + ROWS * TITLE_H + (ROWS + 1) * MARGIN

canvas = Image.new('RGB', (total_w, total_h), (25, 25, 30))
draw = ImageDraw.Draw(canvas)

try:
    font_title = ImageFont.truetype("arial.ttf", 22)
    font_label = ImageFont.truetype("arial.ttf", 18)
except:
    font_title = ImageFont.load_default()
    font_label = ImageFont.load_default()

y_offset = MARGIN
for row_idx, (images, labels) in enumerate(all_rows):
    draw.text((MARGIN, y_offset), row_titles[row_idx], fill=(255, 255, 255), font=font_title)
    y_offset += TITLE_H
    
    x_offset = MARGIN
    for img, label in zip(images, labels):
        canvas.paste(img, (x_offset, y_offset))
        draw.text((x_offset, y_offset + GRID_H + 6), label, fill=(200, 200, 200), font=font_label)
        x_offset += GRID_W + MARGIN
    
    y_offset += GRID_H + LABEL_H + MARGIN

output = "outputs/ablation_enclosed_v2.png"
canvas.save(output, quality=95)
print(f"\nSaved: {output} | Size: {canvas.size}")
