# GPU 光线追踪器 - 高级图形学课程设计

基于 **Taichi** + **CUDA** 的高性能 GPU 光线追踪器，可在 RTX 4060Ti 8G 显存上实现照片级真实感渲染。

## 项目概述

| 项目 | 内容 |
|------|------|
| 选题 | 参考7：光线跟踪器 |
| 技术栈 | Python + Taichi + CUDA |
| GPU | NVIDIA RTX 4060Ti 8G |
| 渲染性能 | ~25M 采样/秒 (500球场景) |

## 已实现功能

### 核心光追算法
- [x] 光线生成与图元相交（球体 / 立方体 / 三角形）
- [x] **BVH 加速结构**（Bounding Volume Hierarchy，GPU 无栈遍历）
- [x] Lambert 漫反射材质（Cosine-weighted 采样）
- [x] **Phong 金属材质**（镜面反射 + 模糊）
- [x] **Fresnel 折射**（玻璃/电介质）
- [x] **Perlin 噪声程序化纹理**
- [x] **发光材质**（区域光源，支持 NEE 直接采样）
- [x] **NEE 直接光源采样**（Next Event Estimation）

### 高级特性
- [x] **OBJ 模型加载**（trimesh，支持缩放/平移）
- [x] **HDRI 环境贴图**（equirectangular 球形映射）
- [x] **YAML 场景配置驱动**
- [x] **动画渲染**（相机路径插值）
- [x] **交互式渐进预览**（ti.GUI 实时显示）

### 真实感效果
- [x] 路径追踪（Path Tracing + Russian Roulette）
- [x] 软阴影（通过区域光源 + NEE 实现）
- [x] 景深效果（Defocus Blur）
- [x] 抗锯齿（超采样）
- [x] Gamma 校正
- [x] 环境光/天空盒 / HDRI

### GPU 加速
- [x] Taichi CUDA Kernel 并行渲染
- [x] 每个像素独立 GPU 线程
- [x] BVH 加速遍历（skip-link 无栈策略）
- [x] 相比 CPU 版本加速 **~150 倍**

## 项目结构

```
raytracer/
├── renderer/               # GPU 渲染核心
│   ├── taichi_renderer.py  # 主渲染器（Taichi CUDA Kernel）
│   ├── perlin.py          # Perlin 噪声
│   └── config.py          # YAML 场景解析 + 动画渲染
│
├── scenes/                 # 场景预设与配置
│   ├── presets.py         # Python 预设场景
│   ├── showcase.py        # 展示场景批量渲染
│   └── *.yaml            # YAML 场景配置文件
│
├── scripts/                # 运行入口
│   ├── run.py             # 统一命令行入口
│   ├── render_yaml.py     # YAML 场景渲染入口
│   └── make_showcase_grid.py  # 展示图拼图
│
├── experiments/            # 消融实验
│   ├── ablation_study.py      # 分辨率/采样/光圈
│   ├── ablation_enclosed.py   # 封闭空间采样/光源/封闭程度
│   ├── ablation_bvh_nee.py    # BVH/NEE 性能分析
│   ├── benchmark.py
│   └── test_primitives.py
│
├── cpu/                    # CPU 参考实现
│   ├── main.py
│   └── bvh.py
│
├── core/                   # CPU 核心数学库
│   ├── vec3.py
│   ├── ray.py
│   └── camera.py
│
├── hittables/              # CPU 可相交物体
│   ├── hittable.py
│   └── sphere.py
│
├── materials/              # CPU 材质
│   └── material.py
│
├── geometry/               # 几何工具
│   └── triangle.py        # OBJ 加载 + 程序化立方体
│
├── models/                # 3D 模型文件
├── outputs/               # 渲染输出（见下方详细说明）
└── README.md
```

---

## 渲染输出说明 (`outputs/`)

### 一、基础演示场景

#### `taichi_demo.png`
**基础三球场景**，本项目 GPU 渲染的入门示例。包含：
- 左侧红色 Lambertian 漫反射球
- 中央银色金属球（高反射）
- 右侧玻璃球（Fresnel 折射，ir=1.5）
- 黄色漫反射地面
- 分辨率 400×225，100 spp

#### `taichi_complex.png`
**复杂随机场景**，展示大规模场景渲染与景深效果。包含：
- 486 个随机散布的球体（Lambertian / Metal / Dielectric 混合）
- 前景大银球（完美镜面反射）
- 玻璃球（可看到内部折射和后方景物）
- 大地面球体作为地平线
- 相机带光圈（aperture=0.1），产生景深虚化效果
- 分辨率 800×450，100 spp

---

### 二、展示场景集 (`showcase_01` ~ `showcase_07`)

7 个独立场景，分别展示不同图元、材质和复杂度。所有场景均通过 `scenes/showcase.py` 批量渲染生成，分辨率 800×450 或 800×800，200~300 spp。

#### `showcase_01_materials.png` — 材质博览馆
**目的**：展示渲染器支持的全部 5 种材质 + 3 种图元。

场景布局为 3 行 × 3 列：
- **第1行（Lambertian 漫反射）**：红色球、绿色立方体、蓝色三角形
- **第2行（Metal 金属）**：银色球（fuzz=0）、铜色立方体（fuzz=0.1）、金色三角形（fuzz=0.3）
- **第3行（特殊材质）**：玻璃球（Dielectric, ir=1.5）、白色发光立方体（Emissive, 强度 3.0）、Perlin 噪声球（程序化大理石纹理）

#### `showcase_02_metals.png` — 金属工坊
**目的**：展示不同金属的反射效果与模糊度（fuzz）参数。

- 中央大银球（完美镜面，fuzz=0）
- 周围金属立方体：金（fuzz=0.05）、铜（fuzz=0.15）、铁（fuzz=0.1）
- 金属三角形装饰
- 小银球散落
- 主光源 + 辅助蓝色光源，产生冷暖对比

#### `showcase_03_glass.png` — 水晶宫
**目的**：展示玻璃/电介质材质的折射效果与不同折射率。

- 深色反光地面（Metal, fuzz=0.05）
- 中央大玻璃立方体（ir=1.5，普通玻璃）
- 左侧玻璃球（ir=1.5）
- 右侧玻璃球（ir=1.77，蓝宝石折射率）
- 玻璃金字塔（4个三角形组成，ir=2.42，钻石折射率）
- 小玻璃球（ir=1.33，水折射率）
- 背光设计，让折射效果更明显

#### `showcase_04_neon.png` — 霓虹展台
**目的**：展示发光材质（Emissive）与软阴影效果。

- 深色地面
- 中央银色金属球（反射周围环境）
- 红色 Lambertian 立方体、绿色三角形
- **霓虹灯管**：左侧红色发光立方体、右侧蓝色发光立方体、上方绿色发光三角形
- 远处暖色发光球
- 发光体产生的柔和阴影与彩色反光

#### `showcase_05_forest.png` — 几何森林
**目的**：展示大量混合图元随机散布的渲染能力。

- 绿色地面
- 30 个随机散布的几何体（球体/立方体/三角形混合）
- 金属物体点缀（金色立方体、银球）
- 自然光照

#### `showcase_06_cornell.png` — Cornell Box
**目的**：经典封闭空间全局光照测试场景，用立方体建造真正的 Cornell Box。

- 白色地板/天花板/后墙
- 左墙红色、右墙绿色（产生间接光照颜色渗透）
- 天花板区域光源（发光立方体）
- 中央物体：白色 Lambertian 球、金色金属立方体、玻璃三角形
- 展示封闭空间中的多次反弹全局光照与颜色渗透

#### `showcase_07_innovation_harbor.png` — 创新港微缩模型
**目的**：参照西安交通大学创新港校区平面图 (`../data/6.png`) 搭建的简化版校园沙盘。

- **扇形倒三角整体布局**，北部宽南部窄
- **西迁大道**中轴线 + 棋盘格道路系统
- **黄色**=教学科研楼：泓理楼（北部大长条）、躬行楼/力行楼（中部对称矩形）、涵英楼（中央 U 形）、敏行楼（南部大矩形）
- **粉色**=学生宿舍：B区、C区、A区、南部 Y 形宿舍区
- **绿色**=绿地广场，**深绿**=运动场地
- 东侧弘德楼群、西侧核能研究院按位置摆放
- 45° 沙盘视角，800×450，300 spp

#### `showcase_grid.png`
**7 个展示场景的 4×2 网格拼图**，由 `scripts/make_showcase_grid.py` 自动生成。每格 500×500 像素，方便整体浏览项目展示能力。

---

### 三、消融实验 (Ablation Study)

消融实验用于验证各渲染参数和技术对画质与性能的影响。

#### `ablation_study.png` / `ablation_study_v2.png`
**分辨率 / 采样数 / 光圈消融实验**（`experiments/ablation_study.py` 生成，v2 为新版代码渲染）。

包含 3 行对比：

| 行 | 变量 | 固定参数 | 说明 |
|---|---|---|---|
| 第1行 | 分辨率 | aperture=0, spp=100 | 200×200 → 800×800，展示分辨率对清晰度的影响 |
| 第2行 | 采样数 (spp) | 400×400, aperture=0 | 10 → 500 spp，展示 Monte Carlo 采样数对噪点的影响。10spp 严重噪点，500spp 几乎纯净 |
| 第3行 | 光圈 (aperture) | 400×400, spp=100 | 0 → 2.0，展示 Defocus Blur 景深效果。aperture=0 全清晰，aperture=2.0 前景红球和背景绿球严重虚化，中景金属球保持清晰（焦点距离=4.0）|

#### `ablation_enclosed.png` / `ablation_enclosed_v2.png`
**封闭空间消融实验**（`experiments/ablation_enclosed.py` 生成，v2 为新版代码渲染）。

包含 3 行对比：

| 行 | 变量 | 固定参数 | 说明 |
|---|---|---|---|
| 第1行 | 采样数 | 封闭 Cornell Box, 光源 1.5×1.5 | 50 → 1000 spp，封闭空间需要更多采样才能收敛 |
| 第2行 | 光源面积 | 500 spp, 封闭空间 | 0.4×0.4 → 3.0×3.0，光源越大软阴影越柔和，但亮度分布更均匀 |
| 第3行 | 封闭程度 | 500 spp, 球形光源 | 1墙(开放) → 6墙(全封闭)，展示封闭程度对全局光照的影响。全封闭时仅靠球光源照明，颜色渗透更明显 |

#### `ablation_bvh_nee.png`
**BVH / NEE 性能消融实验**（`experiments/ablation_bvh_nee.py` 生成）。

测试不同场景复杂度下，BVH 和 NEE 对渲染时间的影响：

| 场景 | 图元数 | BVH+NEE | BVH only | NEE only | None |
|---|---|---|---|---|---|
| Small | ~15 | ~1.17s | ~1.20s | ~0.05s | ~0.05s |
| Medium | ~80 | ~1.54s | ~1.57s | ~0.07s | ~0.01s |
| Large | ~300 | ~3.22s | ~3.58s | ~0.07s | ~0.02s |

**关键发现**：
- **BVH**：当前 skip-link 实现在 GPU 上因 warp divergence 严重，在小/中/大场景下均比线性遍历慢。这是 GPU BVH 遍历的已知挑战，需要在后续工作中优化（如改用栈式遍历或重新排序光线）。
- **NEE**：增加了 shadow ray 开销（小场景约 3-7x），但在封闭空间中能显著降低噪点、提升画质。
- 实验过程中发现并修复了 `build_bvh()` 的 bug：原实现每次创建新 field 替换 `self.bvh_nodes`，导致 `ti.template()` kernel 反复重新编译（每次~17秒）。修复后改为复用已有 field 只复制数据。

---

## 快速开始

### 1. 环境准备

```bash
conda activate graphics_hw
pip install taichi numpy pillow trimesh pyyaml
```

### 2. 渲染场景

```bash
# 渲染默认演示场景
python scripts/run.py demo

# 渲染复杂随机场景（500球）
python scripts/run.py complex

# 高质量模式（500采样/像素）
python scripts/run.py complex --hq

# 批量渲染所有独特场景
python scripts/run.py --all

# 自定义参数
python scripts/run.py cornell -s 200 -w 800 -H 800

# YAML 场景渲染
python scripts/render_yaml.py scenes/demo_scene.yaml -o outputs/scene.png

# YAML 动画渲染
python scripts/render_yaml.py scenes/demo_scene.yaml --anim -o outputs/anim/frame
```

### 3. 可用场景

| 场景 | 说明 | 特色 |
|------|------|------|
| `demo` | 基础三球场景 | 金属/漫反射/玻璃 |
| `complex` | 复杂随机场景 | 486球 + 景深 |
| `cornell` | 开放展示台 | Perlin纹理 + 发光光源 |
| `planets` | 太阳系 | 发光太阳 + 行星 |
| `jewelry` | 珠宝展示 | 钻石折射 + 黄金 |
| `underwater` | 水下气泡 | 大量玻璃气泡 |
| `galaxy` | 螺旋星系 | 发光核心 + 螺旋臂 |

---

## 性能对比

| 版本 | 场景 | 分辨率 | 采样 | 耗时 |
|------|------|--------|------|------|
| CPU (Python) | Demo | 400×225 | 100 | ~127 秒 |
| **GPU (Taichi)** | Demo | 400×225 | 100 | **~0.95 秒** |
| **GPU (Taichi)** | Complex | 800×450 | 100 | **~5.6 秒** |
| **GPU (Taichi)** | Complex | 800×450 | 500 | **~16 秒** |

**加速比：CPU vs GPU ≈ 150 倍**

---

## 技术亮点

### 1. 路径追踪 + NEE
实现了完整的蒙特卡洛路径追踪算法，配合 **Next Event Estimation** 直接光源采样，显著降低封闭空间噪点。

### 2. BVH 加速结构
CPU 端构建 BVH，GPU 端使用 **线性化 skip-link 无栈遍历**，支持球体/立方体/三角形三种图元统一加速。

### 3. Fresnel 折射（Schlick 近似）
玻璃材质根据入射角度自动计算反射/折射比例：
```
R(θ) = R₀ + (1-R₀)(1-cosθ)⁵
```

### 4. HDRI 环境贴图
支持 equirectangular 格式的 HDRI 环境贴图，实现真实的天空光照和背景反射。

### 5. OBJ 模型加载
通过 trimesh 加载 OBJ 模型，自动转换为三角形图元并接入 BVH 加速渲染管线。

### 6. YAML 配置驱动
使用 YAML 文件定义场景、相机、材质和动画路径，无需修改代码即可创建和渲染场景。

---

## 参考文献

1. Peter Shirley, "Ray Tracing in One Weekend"
2. Peter Shirley, "Ray Tracing: The Next Week"
3. Taichi Documentation: https://docs.taichi-lang.org/
4. Ken Perlin, "An Image Synthesizer" (SIGGRAPH 1985)

## 作者信息

- 课程：高级图形学与增强现实
- 日期：2026 年 5 月
