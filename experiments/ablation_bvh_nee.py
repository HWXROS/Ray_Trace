"""
BVH / NEE 性能消融实验
消除 Taichi kernel 编译时间，测量纯运行时性能
"""

import sys
sys.path.insert(0, __file__.rsplit('\\', 2)[0])

import numpy as np
from PIL import Image, ImageDraw, ImageFont
import taichi as ti
from renderer import (
    TaichiRenderer, MAT_LAMBERTIAN, MAT_METAL, MAT_DIELECTRIC,
    MAT_EMISSIVE, init_taichi_perlin,
)
import time

try:
    init_taichi_perlin(seed=42)
except:
    pass


def scene_small():
    """小场景 ~15 图元"""
    r = TaichiRenderer(max_spheres=15, max_cubes=15)
    r.add_cube((-2, -1, -3), (2, -0.9, 1), MAT_LAMBERTIAN, (0.9, 0.9, 0.9))
    r.add_cube((-2, 1.9, -3), (2, 2.0, 1), MAT_LAMBERTIAN, (0.9, 0.9, 0.9))
    r.add_cube((-2, -1, -3), (-1.9, 2, 1), MAT_LAMBERTIAN, (0.8, 0.2, 0.2))
    r.add_cube((1.9, -1, -3), (2, 2, 1), MAT_LAMBERTIAN, (0.2, 0.8, 0.2))
    r.add_cube((-2, -1, -3), (2, 2, -2.9), MAT_LAMBERTIAN, (0.9, 0.9, 0.9))
    r.add_cube((-0.5, 1.85, -1.5), (0.5, 1.9, -0.5), MAT_EMISSIVE, (5.0, 5.0, 5.0))
    r.add_sphere((0, -0.4, -1.2), 0.5, MAT_LAMBERTIAN, (0.9, 0.9, 0.9))
    r.add_cube((-0.6, -0.9, -0.8), (-0.1, -0.4, -0.3), MAT_METAL, (0.9, 0.7, 0.3), fuzz=0.05)
    r.add_sphere((0.6, -0.3, -1.5), 0.35, MAT_DIELECTRIC, ir=1.5)
    r.add_sphere((-0.8, -0.65, -0.5), 0.25, MAT_LAMBERTIAN, (0.2, 0.4, 0.8))
    r.add_sphere((0.3, -0.7, -0.3), 0.2, MAT_METAL, (0.8, 0.8, 0.9), fuzz=0.1)
    r.set_camera((0, 1, 2.5), (0, 0.5, -1.0), (0, 1, 0), 60, 1.0, 0.0)
    return r


def scene_medium():
    """中场景 ~80 图元"""
    r = TaichiRenderer(max_spheres=60, max_cubes=30)
    np.random.seed(42)
    r.add_cube((-8, -0.5, -8), (8, 0, 8), MAT_LAMBERTIAN, (0.3, 0.6, 0.3))
    for _ in range(40):
        x = np.random.uniform(-5, 5)
        z = np.random.uniform(-6, -1)
        mat = np.random.random()
        if mat < 0.5:
            col = np.random.random(3) * 0.5 + 0.3
            r.add_sphere((x, 0.2, z), np.random.uniform(0.1, 0.3),
                        MAT_LAMBERTIAN, tuple(col))
        elif mat < 0.8:
            col = np.random.random(3) * 0.5 + 0.3
            s = np.random.uniform(0.2, 0.5)
            r.add_cube((x, 0.0, z), (x+s, s, z+s), MAT_LAMBERTIAN, tuple(col))
        else:
            r.add_sphere((x, 0.2, z), np.random.uniform(0.1, 0.3),
                        MAT_METAL, (0.8, 0.8, 0.8), fuzz=0.1)
    r.add_light((0, 5, 0), 0.5, (5.0, 5.0, 5.0))
    r.set_camera((0, 3, 5), (0, 0, -3), (0, 1, 0), 60, 1.0, 0.0)
    return r


def scene_large():
    """大场景 ~300 图元"""
    r = TaichiRenderer(max_spheres=350)
    np.random.seed(123)
    r.add_sphere((0, -1000, 0), 1000.0, MAT_LAMBERTIAN, (0.76, 0.7, 0.5))
    for _ in range(250):
        x = np.random.uniform(-10, 10)
        z = np.random.uniform(-12, -2)
        y = np.random.uniform(0.1, 3.0)
        radius = np.random.uniform(0.05, 0.25)
        mat = np.random.random()
        if mat < 0.6:
            col = np.random.random(3) * 0.5 + 0.3
            r.add_sphere((x, y, z), radius, MAT_LAMBERTIAN, tuple(col))
        elif mat < 0.85:
            r.add_sphere((x, y, z), radius, MAT_METAL,
                        (0.5+np.random.random()*0.5, 0.5, 0.5), fuzz=0.1)
        else:
            r.add_sphere((x, y, z), radius, MAT_DIELECTRIC, ir=1.5)
    r.add_light((0, 8, -5), 0.6, (6.0, 5.5, 4.5))
    r.set_camera((0, 4, 6), (0, 1, -5), (0, 1, 0), 55, 16.0/9.0, 0.0)
    return r


# 场景列表: (名称, 构建函数, w, h, spp)
SCENES = [
    ("Small ~15 prims", scene_small, 400, 400, 100),
    ("Medium ~80 prims", scene_medium, 400, 400, 50),
    ("Large ~300 prims", scene_large, 400, 400, 20),
]

COMBOS = [
    (True,  True,  "BVH+NEE"),
    (True,  False, "BVH only"),
    (False, True,  "NEE only"),
    (False, False, "None"),
]

print("=" * 70)
print("BVH / NEE Performance Ablation Study")
print("=" * 70)

all_rows = []
row_titles = []

for row_idx, (scene_name, scene_fn, w, h, spp) in enumerate(SCENES):
    print(f"\n--- {scene_name} ({w}x{h}, {spp}spp) ---")
    
    # 统一创建场景一次
    renderer = scene_fn()
    
    # Warm-up: 先编译 kernel（用 BVH+NEE）
    print("  [warm-up] compiling kernel...", end=" ", flush=True)
    t0 = time.time()
    _ = renderer.render(w, h, spp, max_depth=30, use_bvh=True, use_nee=True)
    print(f"done ({time.time()-t0:.1f}s)")
    
    row_images = []
    row_labels = []
    
    for use_bvh, use_nee, combo_name in COMBOS:
        label = combo_name
        times = []
        
        # 每个组合渲染 3 次取平均（消除噪声）
        for run in range(3):
            t0 = time.time()
            img_np = renderer.render(w, h, spp, max_depth=30,
                                     use_bvh=use_bvh, use_nee=use_nee)
            elapsed = time.time() - t0
            times.append(elapsed)
        
        avg_time = sum(times) / len(times)
        print(f"  [{label:10s}] avg={avg_time:.3f}s  (runs={times})")
        
        row_images.append(Image.fromarray(img_np))
        row_labels.append(f"{combo_name}\n{avg_time:.3f}s")
    
    all_rows.append((row_images, row_labels))
    row_titles.append(scene_name)


# ========== 拼接 ==========
print("\nAssembling grid...")

GRID_W = 400
GRID_H = 400
TITLE_H = 55
LABEL_H = 50
MARGIN = 12
ROWS = len(SCENES)
COLS = 4

total_w = COLS * GRID_W + (COLS + 1) * MARGIN
total_h = ROWS * (GRID_H + LABEL_H) + ROWS * TITLE_H + (ROWS + 1) * MARGIN

canvas = Image.new('RGB', (total_w, total_h), (25, 25, 30))
draw = ImageDraw.Draw(canvas)

try:
    font_title = ImageFont.truetype("arial.ttf", 22)
    font_label = ImageFont.truetype("arial.ttf", 16)
except:
    font_title = ImageFont.load_default()
    font_label = ImageFont.load_default()

y_offset = MARGIN
for row_idx, (images, labels) in enumerate(all_rows):
    draw.text((MARGIN, y_offset), row_titles[row_idx], fill=(255, 255, 255), font=font_title)
    y_offset += TITLE_H
    
    x_offset = MARGIN
    for img, label in zip(images, labels):
        img_display = img.resize((GRID_W, GRID_H), Image.LANCZOS)
        canvas.paste(img_display, (x_offset, y_offset))
        draw.text((x_offset, y_offset + GRID_H + 6), label, fill=(200, 200, 200), font=font_label)
        x_offset += GRID_W + MARGIN
    
    y_offset += GRID_H + LABEL_H + MARGIN

output = "outputs/ablation_bvh_nee.png"
canvas.save(output, quality=95)
print(f"\nSaved: {output} | Size: {canvas.size}")
