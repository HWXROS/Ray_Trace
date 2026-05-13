"""
消融实验 (Ablation Study)
测试：分辨率 / 采样数 / 光圈大小
场景：包含前景、中景(焦点)、背景的球体组合
"""

import sys
sys.path.insert(0, __file__.rsplit('\\', 2)[0])

import numpy as np
from PIL import Image, ImageDraw, ImageFont
import taichi as ti
from renderer import TaichiRenderer, MAT_LAMBERTIAN, MAT_METAL, MAT_DIELECTRIC, init_taichi_perlin
import time

# 必须先初始化 Perlin
try:
    init_taichi_perlin(seed=42)
except:
    pass


def create_ablation_scene(aperture=0.0):
    """创建消融实验场景：前景红球 / 中景金属球(焦点) / 背景蓝球 / 远处绿球"""
    renderer = TaichiRenderer(max_spheres=10)
    
    # 地面
    renderer.add_sphere((0, -100.5, -1), 100.0, MAT_LAMBERTIAN, (0.8, 0.8, 0.0))
    
    # 前景 - 红色漫反射 (z=-0.5, 距相机约 2.5, 会失焦)
    renderer.add_sphere((-0.5, 0.3, -0.5), 0.3, MAT_LAMBERTIAN, (0.8, 0.2, 0.2))
    
    # 中景焦点 - 金属球 (z=-2, 距相机约 4.0, 正好在焦点上)
    renderer.add_sphere((0, 0, -2), 0.5, MAT_METAL, (0.9, 0.9, 0.9), fuzz=0.05)
    
    # 背景 - 蓝色漫反射 (z=-5, 距相机约 7.0, 会失焦)
    renderer.add_sphere((0.5, 0.2, -5), 0.4, MAT_LAMBERTIAN, (0.2, 0.2, 0.8))
    
    # 远处 - 绿色漫反射 (z=-8, 距相机约 10.0, 严重失焦)
    renderer.add_sphere((-1, 0.15, -8), 0.3, MAT_LAMBERTIAN, (0.2, 0.8, 0.2))
    
    # 相机：焦点设在中景球 (distance ≈ 4.0)
    renderer.set_camera(
        lookfrom=(0, 1, 2),
        lookat=(0, 0, -2),
        vup=(0, 1, 0),
        vfov=30.0,
        aspect_ratio=1.0,
        aperture=aperture,
        focus_dist=4.0,
    )
    
    return renderer


# ========== 实验配置 ==========
# 每组实验: (width, height, samples, aperture, 标签)
experiments = [
    # 第1行: 分辨率消融 (固定 aperture=0, samples=100)
    ("Resolution | aperture=0 | spp=100", [
        (200, 200, 100, 0.0, "200×200"),
        (400, 400, 100, 0.0, "400×400"),
        (600, 600, 100, 0.0, "600×600"),
        (800, 800, 100, 0.0, "800×800"),
    ]),
    
    # 第2行: 采样数消融 (固定 400×400, aperture=0)
    ("Samples | 400×400 | aperture=0", [
        (400, 400, 10, 0.0, "10 spp"),
        (400, 400, 50, 0.0, "50 spp"),
        (400, 400, 100, 0.0, "100 spp"),
        (400, 400, 500, 0.0, "500 spp"),
    ]),
    
    # 第3行: 光圈/景深消融 (固定 400×400, samples=100)
    ("Aperture | 400×400 | spp=100", [
        (400, 400, 100, 0.0, "aperture=0"),
        (400, 400, 100, 0.2, "aperture=0.2"),
        (400, 400, 100, 0.8, "aperture=0.8"),
        (400, 400, 100, 2.0, "aperture=2.0"),
    ]),
]


# ========== 渲染 ==========
print("=" * 60)
print("开始消融实验渲染...")
print("=" * 60)

all_rows = []
row_titles = []

for row_idx, (row_title, configs) in enumerate(experiments):
    print(f"\n--- 第 {row_idx+1} 组: {row_title} ---")
    row_images = []
    row_labels = []
    
    for w, h, s, a, label in configs:
        print(f"  渲染: {label} ...", end=" ", flush=True)
        t0 = time.time()
        
        renderer = create_ablation_scene(aperture=a)
        img_np = renderer.render(w, h, s, 50)
        img = Image.fromarray(img_np)
        
        elapsed = time.time() - t0
        print(f"({elapsed:.2f}s)")
        
        row_images.append(img)
        row_labels.append(label)
    
    all_rows.append((row_images, row_labels))
    row_titles.append(row_title)


# ========== 拼接 ==========
print("\n拼接对比图...")

# 统一显示尺寸 (每格显示大小)
GRID_W = 400
GRID_H = 400
TITLE_H = 70      # 行标题高度
LABEL_H = 40      # 图片标签高度
MARGIN = 10

# 计算总尺寸
n_rows = len(all_rows)
n_cols = 4
total_w = n_cols * GRID_W + (n_cols + 1) * MARGIN
total_h = n_rows * (GRID_H + LABEL_H) + n_rows * TITLE_H + (n_rows + 1) * MARGIN

# 创建画布 (白色背景)
canvas = Image.new('RGB', (total_w, total_h), (255, 255, 255))
draw = ImageDraw.Draw(canvas)

# 尝试加载字体
try:
    font_title = ImageFont.truetype("arial.ttf", 22)
    font_label = ImageFont.truetype("arial.ttf", 18)
except:
    font_title = ImageFont.load_default()
    font_label = ImageFont.load_default()

y_offset = MARGIN

for row_idx, (images, labels) in enumerate(all_rows):
    # 绘制行标题
    draw.text((MARGIN, y_offset), row_titles[row_idx], fill=(0, 0, 0), font=font_title)
    y_offset += TITLE_H
    
    # 绘制每张图
    x_offset = MARGIN
    for img, label in zip(images, labels):
        # 统一缩放到显示尺寸（小图放大、大图缩小，对比更强烈）
        img_display = img.resize((GRID_W, GRID_H), Image.LANCZOS)
        
        # 贴图
        canvas.paste(img_display, (x_offset, y_offset))
        
        # 标签
        draw.text((x_offset, y_offset + GRID_H + 5), label, fill=(50, 50, 50), font=font_label)
        
        x_offset += GRID_W + MARGIN
    
    y_offset += GRID_H + LABEL_H + MARGIN

# 保存
output_path = 'outputs/ablation_study_v2.png'
canvas.save(output_path, quality=95)
print(f"\n消融实验对比图已保存: {output_path}")
print(f"尺寸: {canvas.size}")
