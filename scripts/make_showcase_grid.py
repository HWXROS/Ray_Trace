"""
将 6 张展示图拼成一张网格大图
"""

from PIL import Image, ImageDraw, ImageFont

scenes = [
    ("01 Material Gallery", "outputs/showcase_01_materials.png"),
    ("02 Metal Studio", "outputs/showcase_02_metals.png"),
    ("03 Crystal Palace", "outputs/showcase_03_glass.png"),
    ("04 Neon Night", "outputs/showcase_04_neon.png"),
    ("05 Geometric Forest", "outputs/showcase_05_forest.png"),
    ("06 Cornell Box", "outputs/showcase_06_cornell.png"),
    ("07 Innovation Harbor", "outputs/showcase_07_innovation_harbor.png"),
]

GRID_W = 500
GRID_H = 500
TITLE_H = 50
LABEL_H = 35
MARGIN = 15
COLS = 4
ROWS = 2

total_w = COLS * GRID_W + (COLS + 1) * MARGIN
total_h = TITLE_H + ROWS * (GRID_H + LABEL_H) + (ROWS + 1) * MARGIN

canvas = Image.new('RGB', (total_w, total_h), (30, 30, 35))
draw = ImageDraw.Draw(canvas)

try:
    font_title = ImageFont.truetype("arial.ttf", 26)
    font_label = ImageFont.truetype("arial.ttf", 18)
except:
    font_title = ImageFont.load_default()
    font_label = ImageFont.load_default()

draw.text((MARGIN, 14), "GPU Ray Tracer — Showcase Scenes", fill=(255, 255, 255), font=font_title)

for idx, (label, path) in enumerate(scenes):
    row = idx // COLS
    col = idx % COLS
    
    x = MARGIN + col * (GRID_W + MARGIN)
    y = TITLE_H + MARGIN + row * (GRID_H + LABEL_H + MARGIN)
    
    img = Image.open(path)
    img = img.resize((GRID_W, GRID_H), Image.LANCZOS)
    canvas.paste(img, (x, y))
    draw.text((x, y + GRID_H + 6), label, fill=(200, 200, 200), font=font_label)

output = "outputs/showcase_grid.png"
canvas.save(output, quality=95)
print(f"Grid saved: {output} | Size: {canvas.size}")
