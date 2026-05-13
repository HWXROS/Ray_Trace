"""
GPU 渲染器模块
"""

from .taichi_renderer import (
    TaichiRenderer,
    MAT_LAMBERTIAN,
    MAT_METAL,
    MAT_DIELECTRIC,
    MAT_PERLIN,
    MAT_EMISSIVE,
    create_demo_scene_gpu,
    create_complex_scene_gpu,
)
from .perlin import init_taichi_perlin, taichi_perlin_turb
from .config import (
    load_scene_from_yaml,
    build_renderer_from_config,
    render_animation,
)
