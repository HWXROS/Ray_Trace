"""
光线追踪器 - 统一运行入口
支持多种独特场景、参数配置、批量渲染
"""

import sys
sys.path.insert(0, __file__.rsplit('\\', 2)[0])  # 项目根目录

import argparse
from PIL import Image
from renderer import init_taichi_perlin, create_demo_scene_gpu, create_complex_scene_gpu
from scenes import SCENES


def render_scene(scene_name, samples=100, max_depth=50, width=None, height=None):
    """渲染指定场景"""
    
    if scene_name not in SCENES:
        print(f"错误: 未知场景 '{scene_name}'")
        print(f"可用场景: {', '.join(SCENES.keys())}")
        return None
    
    filename, scene_func = SCENES[scene_name]
    
    # 初始化 Perlin 噪声
    init_taichi_perlin(seed=42)
    
    # 创建场景
    if scene_name == 'demo':
        renderer = create_demo_scene_gpu()
        w, h = width or 400, height or 225
    elif scene_name == 'complex':
        renderer = create_complex_scene_gpu()
        w, h = width or 800, height or 450
    else:
        renderer, default_w, default_h = scene_func()
        w, h = width or default_w, height or default_h
    
    # 渲染
    image = renderer.render(image_width=w, image_height=h, 
                           samples_per_pixel=samples, max_depth=max_depth)
    
    # 保存
    output_path = f'outputs/{filename}'
    img = Image.fromarray(image)
    img.save(output_path)
    print(f"已保存: {output_path}")
    
    return output_path


def render_all(samples=100, max_depth=50):
    """批量渲染所有场景"""
    print("=" * 60)
    print("批量渲染所有独特场景")
    print("=" * 60)
    
    results = []
    for scene_name in SCENES.keys():
        print(f"\n--- 渲染场景: {scene_name} ---")
        try:
            path = render_scene(scene_name, samples, max_depth)
            if path:
                results.append(path)
        except Exception as e:
            print(f"渲染失败: {e}")
    
    print(f"\n{'=' * 60}")
    print(f"完成! 共渲染 {len(results)} 个场景")
    for r in results:
        print(f"  - {r}")
    
    return results


def main():
    parser = argparse.ArgumentParser(description='GPU 光线追踪器')
    parser.add_argument('scene', nargs='?', default='demo',
                       help='场景名称 (demo/complex/cornell/planets/jewelry/underwater/galaxy)')
    parser.add_argument('--samples', '-s', type=int, default=100,
                       help='每像素采样数 (默认: 100)')
    parser.add_argument('--depth', '-d', type=int, default=50,
                       help='最大递归深度 (默认: 50)')
    parser.add_argument('--width', '-w', type=int, default=None,
                       help='图像宽度')
    parser.add_argument('--height', '-H', type=int, default=None,
                       help='图像高度')
    parser.add_argument('--all', '-a', action='store_true',
                       help='渲染所有场景')
    parser.add_argument('--hq', action='store_true',
                       help='高质量模式 (500采样)')
    
    args = parser.parse_args()
    
    samples = 500 if args.hq else args.samples
    
    if args.all:
        render_all(samples=samples, max_depth=args.depth)
    else:
        render_scene(args.scene, samples=samples, max_depth=args.depth, 
                    width=args.width, height=args.height)


if __name__ == '__main__':
    main()
