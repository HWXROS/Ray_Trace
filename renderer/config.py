"""
YAML/JSON 场景配置驱动 + 动画渲染
"""

import yaml
import numpy as np
from .taichi_renderer import (
    TaichiRenderer, MAT_LAMBERTIAN, MAT_METAL, MAT_DIELECTRIC,
    MAT_PERLIN, MAT_EMISSIVE, init_hdri
)

MATERIAL_MAP = {
    'lambertian': MAT_LAMBERTIAN,
    'metal': MAT_METAL,
    'dielectric': MAT_DIELECTRIC,
    'glass': MAT_DIELECTRIC,
    'perlin': MAT_PERLIN,
    'emissive': MAT_EMISSIVE,
    'light': MAT_EMISSIVE,
}


def load_scene_from_yaml(filepath):
    """从 YAML 文件加载场景配置"""
    with open(filepath, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    return config


def build_renderer_from_config(config, renderer=None):
    """
    根据配置构建 TaichiRenderer
    
    Args:
        config: YAML/字典配置
        renderer: 可选的现有 renderer（用于复用）
    
    Returns:
        TaichiRenderer 实例
    """
    if renderer is None:
        # 统计需要的容量
        obj_counts = {'sphere': 0, 'cube': 0, 'triangle': 0, 'obj': 0}
        for obj in config.get('objects', []):
            t = obj.get('type', 'sphere')
            obj_counts[t] = obj_counts.get(t, 0) + 1
            if t == 'obj':
                # 粗略估计 OBJ 的三角形数
                try:
                    from geometry.triangle import load_obj_model
                    tris = load_obj_model(obj.get('path', ''), mat_type=0)
                    obj_counts['triangle'] += len(tris)
                except:
                    pass
        
        max_spheres = max(obj_counts['sphere'] + obj_counts.get('light', 0) + 10, 100)
        max_cubes = max(obj_counts['cube'] + 10, 50)
        max_triangles = max(obj_counts['triangle'] + 10, 1000)
        
        renderer = TaichiRenderer(
            max_spheres=max_spheres,
            max_cubes=max_cubes,
            max_triangles=max_triangles,
        )
    else:
        renderer.clear_scene()
    
    # HDRI
    hdri_cfg = config.get('hdri')
    if hdri_cfg and hdri_cfg.get('path'):
        init_hdri(
            hdri_cfg['path'],
            width=hdri_cfg.get('width'),
            height=hdri_cfg.get('height')
        )
    
    # 添加物体
    for obj in config.get('objects', []):
        obj_type = obj.get('type', 'sphere')
        mat_name = obj.get('material', 'lambertian')
        mat_type = MATERIAL_MAP.get(mat_name, MAT_LAMBERTIAN)
        albedo = tuple(obj.get('albedo', [0.7, 0.7, 0.7]))
        fuzz = obj.get('fuzz', 0.0)
        ir = obj.get('ir', 1.5)
        
        if obj_type == 'sphere':
            center = tuple(obj.get('center', [0, 0, 0]))
            radius = obj.get('radius', 1.0)
            renderer.add_sphere(center, radius, mat_type, albedo, fuzz, ir)
        
        elif obj_type == 'cube':
            min_p = tuple(obj.get('min', [-1, -1, -1]))
            max_p = tuple(obj.get('max', [1, 1, 1]))
            renderer.add_cube(min_p, max_p, mat_type, albedo, fuzz, ir)
        
        elif obj_type == 'triangle':
            v0 = tuple(obj.get('v0', [0, 0, 0]))
            v1 = tuple(obj.get('v1', [1, 0, 0]))
            v2 = tuple(obj.get('v2', [0, 1, 0]))
            renderer.add_triangle(v0, v1, v2, mat_type, albedo, fuzz, ir)
        
        elif obj_type == 'obj':
            path = obj.get('path', '')
            scale = obj.get('scale', 1.0)
            offset = tuple(obj.get('offset', [0, 0, 0]))
            if path:
                renderer.add_obj_model(path, mat_type, albedo, fuzz, ir, scale, offset)
        
        elif obj_type == 'light':
            center = tuple(obj.get('center', [0, 0, 0]))
            radius = obj.get('radius', 1.0)
            color = tuple(obj.get('color', [10.0, 10.0, 10.0]))
            renderer.add_light(center, radius, color)
    
    # 相机
    cam_cfg = config.get('camera', {})
    renderer.set_camera(
        lookfrom=cam_cfg.get('lookfrom', [0, 0, 1]),
        lookat=cam_cfg.get('lookat', [0, 0, 0]),
        vup=cam_cfg.get('vup', [0, 1, 0]),
        vfov=cam_cfg.get('vfov', 40.0),
        aspect_ratio=cam_cfg.get('aspect_ratio', 16.0/9.0),
        aperture=cam_cfg.get('aperture', 0.0),
        focus_dist=cam_cfg.get('focus_dist'),
    )
    
    return renderer


def lerp(a, b, t):
    """线性插值"""
    return a * (1 - t) + b * t


def render_animation(config, output_prefix='outputs/frame', renderer=None):
    """
    渲染动画序列
    
    Args:
        config: 包含 animation 字段的配置
        output_prefix: 输出文件前缀
        renderer: 可选的现有 renderer
    
    Returns:
        渲染的帧数
    """
    anim_cfg = config.get('animation')
    if not anim_cfg or not anim_cfg.get('enabled', False):
        return 0
    
    frames = anim_cfg.get('frames', 60)
    path = anim_cfg.get('camera_path', [])
    
    if len(path) < 2:
        print("[Anim] 相机路径点不足，跳过动画渲染")
        return 0
    
    render_cfg = config.get('render', {})
    width = render_cfg.get('width', 800)
    height = render_cfg.get('height', 450)
    samples = render_cfg.get('samples', 50)
    max_depth = render_cfg.get('max_depth', 50)
    use_bvh = render_cfg.get('use_bvh', True)
    use_nee = render_cfg.get('use_nee', True)
    
    import os
    from PIL import Image
    
    # 确保输出目录存在
    out_dir = os.path.dirname(output_prefix)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    
    # 排序路径点
    path = sorted(path, key=lambda p: p['frame'])
    
    # 为每一帧插值相机位置
    rendered = 0
    for frame_idx in range(frames):
        # 找到当前帧所在的区间
        seg_start = None
        seg_end = None
        for i in range(len(path) - 1):
            if path[i]['frame'] <= frame_idx <= path[i+1]['frame']:
                seg_start = path[i]
                seg_end = path[i+1]
                break
        
        if seg_start is None:
            # 超出路径范围，使用最后一个点
            seg_start = path[-1]
            seg_end = path[-1]
            t = 0.0
        else:
            t = (frame_idx - seg_start['frame']) / (seg_end['frame'] - seg_start['frame'])
        
        # 插值相机参数
        lookfrom = [
            lerp(seg_start.get('lookfrom', [0,0,0])[i], seg_end.get('lookfrom', [0,0,0])[i], t)
            for i in range(3)
        ]
        lookat = [
            lerp(seg_start.get('lookat', [0,0,0])[i], seg_end.get('lookat', [0,0,0])[i], t)
            for i in range(3)
        ]
        
        # 更新配置并渲染
        config['camera']['lookfrom'] = lookfrom
        config['camera']['lookat'] = lookat
        
        renderer = build_renderer_from_config(config, renderer)
        img = renderer.render(width, height, samples, max_depth, use_bvh, use_nee)
        
        out_path = f"{output_prefix}_{frame_idx:04d}.png"
        Image.fromarray(img).save(out_path)
        print(f"[Anim] 帧 {frame_idx}/{frames} 已保存: {out_path}")
        rendered += 1
    
    return rendered
