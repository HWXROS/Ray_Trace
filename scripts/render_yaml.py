"""
YAML 场景配置渲染入口
用法:
    python scripts/render_yaml.py scenes/demo_scene.yaml -o outputs/from_yaml.png
    python scripts/render_yaml.py scenes/demo_scene.yaml --anim -o outputs/anim/frame
"""

import sys
import os
import argparse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from renderer import (
    load_scene_from_yaml,
    build_renderer_from_config,
    render_animation,
    init_taichi_perlin,
)


def main():
    parser = argparse.ArgumentParser(description='从 YAML 配置文件渲染场景')
    parser.add_argument('config', help='YAML 配置文件路径')
    parser.add_argument('-o', '--output', default='outputs/yaml_render.png',
                        help='输出图片路径 (默认: outputs/yaml_render.png)')
    parser.add_argument('--anim', action='store_true',
                        help='渲染动画序列')
    parser.add_argument('--spp', type=int, default=None,
                        help='覆盖配置中的采样数')
    parser.add_argument('--width', type=int, default=None,
                        help='覆盖配置中的宽度')
    parser.add_argument('--height', type=int, default=None,
                        help='覆盖配置中的高度')
    
    args = parser.parse_args()
    
    # 初始化
    init_taichi_perlin(seed=42)
    
    # 加载配置
    config = load_scene_from_yaml(args.config)
    
    # 覆盖参数
    if args.spp is not None:
        config['render']['samples'] = args.spp
    if args.width is not None:
        config['render']['width'] = args.width
    if args.height is not None:
        config['render']['height'] = args.height
    
    if args.anim:
        # 动画渲染
        frames = render_animation(config, output_prefix=args.output)
        print(f"\n动画渲染完成: {frames} 帧")
    else:
        # 单帧渲染
        renderer = build_renderer_from_config(config)
        rc = config['render']
        img = renderer.render(
            rc['width'], rc['height'],
            samples_per_pixel=rc['samples'],
            max_depth=rc['max_depth'],
            use_bvh=rc.get('use_bvh', True),
            use_nee=rc.get('use_nee', True),
        )
        
        from PIL import Image
        Image.fromarray(img).save(args.output)
        print(f"\n渲染完成，已保存: {args.output}")


if __name__ == '__main__':
    main()
