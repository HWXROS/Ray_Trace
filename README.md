# GPU 光线追踪器 - 高级图形学课程设计

基于 **Taichi** + **CUDA** 的高性能 GPU 光线追踪器，可在 4060Ti 8G 显存上实现照片级真实感渲染。

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
│   └── render_yaml.py     # YAML 场景渲染入口
│
├── experiments/            # 消融实验
│   ├── ablation_study.py  # 分辨率/采样/光圈
│   ├── ablation_enclosed.py
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
├── outputs/               # 渲染输出
└── README.md
```

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

## 性能对比

| 版本 | 场景 | 分辨率 | 采样 | 耗时 |
|------|------|--------|------|------|
| CPU (Python) | Demo | 400×225 | 100 | ~127 秒 |
| **GPU (Taichi)** | Demo | 400×225 | 100 | **~0.95 秒** |
| **GPU (Taichi)** | Complex | 800×450 | 100 | **~5.6 秒** |
| **GPU (Taichi)** | Complex | 800×450 | 500 | **~16 秒** |

**加速比：CPU vs GPU ≈ 150 倍**

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

## 参考文献

1. Peter Shirley, "Ray Tracing in One Weekend"
2. Peter Shirley, "Ray Tracing: The Next Week"
3. Taichi Documentation: https://docs.taichi-lang.org/
4. Ken Perlin, "An Image Synthesizer" (SIGGRAPH 1985)

## 作者信息

- 课程：高级图形学与增强现实
- 日期：2026 年 5 月
