"""
性能基准测试 - CPU vs GPU 对比
用于课程设计实验结果部分
"""

import time
import sys
sys.path.insert(0, __file__.rsplit('\\', 2)[0])

from cpu.main import create_demo_scene, render_scene as render_cpu
from renderer import create_demo_scene_gpu
from PIL import Image
import numpy as np


def benchmark_cpu(samples_list=[10, 50, 100]):
    """CPU 版本性能测试"""
    print("=" * 60)
    print("CPU 版本性能测试")
    print("=" * 60)
    
    world, camera, w, h = create_demo_scene()
    
    results = []
    for samples in samples_list:
        print(f"\n测试: {w}x{h}, {samples} 采样/像素")
        start = time.time()
        image = render_cpu(world, camera, w, h, samples_per_pixel=samples, max_depth=10)
        elapsed = time.time() - start
        
        m_samples = w * h * samples / 1e6
        throughput = m_samples / elapsed
        
        print(f"  耗时: {elapsed:.2f} 秒")
        print(f"  总采样: {m_samples:.2f} M")
        print(f"  吞吐量: {throughput:.2f} M 采样/秒")
        
        results.append({
            'samples': samples,
            'time': elapsed,
            'throughput': throughput,
        })
    
    return results


def benchmark_gpu(samples_list=[100, 500, 1000]):
    """GPU 版本性能测试"""
    print("\n" + "=" * 60)
    print("GPU 版本性能测试 (Taichi CUDA)")
    print("=" * 60)
    
    renderer = create_demo_scene_gpu()
    w, h = 400, 225
    
    results = []
    for samples in samples_list:
        print(f"\n测试: {w}x{h}, {samples} 采样/像素")
        
        # 预热（第一次编译较慢）
        if samples == samples_list[0]:
            print("  编译中...")
        
        start = time.time()
        image = renderer.render(image_width=w, image_height=h, 
                               samples_per_pixel=samples, max_depth=50)
        elapsed = time.time() - start
        
        m_samples = w * h * samples / 1e6
        throughput = m_samples / elapsed
        
        print(f"  耗时: {elapsed:.2f} 秒")
        print(f"  总采样: {m_samples:.2f} M")
        print(f"  吞吐量: {throughput:.2f} M 采样/秒")
        
        results.append({
            'samples': samples,
            'time': elapsed,
            'throughput': throughput,
        })
    
    return results


def print_comparison(cpu_results, gpu_results):
    """打印对比结果"""
    print("\n" + "=" * 60)
    print("性能对比总结")
    print("=" * 60)
    
    # 取相近采样数对比
    cpu_100 = [r for r in cpu_results if r['samples'] == 100]
    gpu_100 = [r for r in gpu_results if r['samples'] == 100]
    
    if cpu_100 and gpu_100:
        speedup = cpu_100[0]['time'] / gpu_100[0]['time']
        print(f"\n100 采样/像素:")
        print(f"  CPU: {cpu_100[0]['time']:.2f} 秒")
        print(f"  GPU: {gpu_100[0]['time']:.2f} 秒")
        print(f"  加速比: {speedup:.1f}x")
    
    print(f"\nGPU 峰值吞吐量: {max(r['throughput'] for r in gpu_results):.2f} M 采样/秒")
    print(f"CPU 峰值吞吐量: {max(r['throughput'] for r in cpu_results):.2f} M 采样/秒")
    
    if cpu_results and gpu_results:
        max_speedup = max(r['throughput'] for r in gpu_results) / max(r['throughput'] for r in cpu_results)
        print(f"峰值加速比: {max_speedup:.1f}x")


def main():
    print("光线追踪器 - CPU vs GPU 性能基准测试")
    print("硬件: NVIDIA RTX 4060Ti 8G")
    
    # CPU 测试（采样数较少，否则太慢）
    cpu_results = benchmark_cpu(samples_list=[10, 50, 100])
    
    # GPU 测试
    gpu_results = benchmark_gpu(samples_list=[100, 500, 1000])
    
    # 对比
    print_comparison(cpu_results, gpu_results)
    
    # 保存结果
    print("\n" + "=" * 60)
    print("测试完成!")
    print("=" * 60)


if __name__ == '__main__':
    main()
