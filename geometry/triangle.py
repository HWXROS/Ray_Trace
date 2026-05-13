"""
三角形图元 + OBJ 模型加载
"""

import numpy as np
import taichi as ti

try:
    import trimesh
    HAS_TRIMESH = True
except ImportError:
    HAS_TRIMESH = False

vec3 = ti.types.vector(3, ti.f32)

# Taichi 三角形结构体
Triangle = ti.types.struct(
    v0=vec3, v1=vec3, v2=vec3,    # 三个顶点
    n0=vec3, n1=vec3, n2=vec3,    # 顶点法线（可选）
    mat_type=ti.i32,
    albedo=vec3,
    fuzz=ti.f32,
    ir=ti.f32,
)


def load_obj_model(filepath, mat_type=0, albedo=(0.7,0.7,0.7), fuzz=0.0, ir=1.5):
    """
    加载 OBJ 模型文件，返回三角形列表
    
    返回: list of dict，每个dict包含三角形的顶点、法线、材质信息
    """
    if not HAS_TRIMESH:
        print("警告: trimesh 未安装，无法加载 OBJ 模型")
        print("请运行: pip install trimesh")
        return []
    
    try:
        mesh = trimesh.load(filepath, force='mesh')
    except Exception as e:
        print(f"加载模型失败: {e}")
        return []
    
    triangles = []
    
    # 获取顶点和面
    vertices = mesh.vertices.astype(np.float32)
    faces = mesh.faces
    
    # 计算顶点法线（如果有）
    if hasattr(mesh, 'vertex_normals') and mesh.vertex_normals is not None:
        vertex_normals = mesh.vertex_normals.astype(np.float32)
    else:
        vertex_normals = None
    
    for face in faces:
        v0 = vertices[face[0]]
        v1 = vertices[face[1]]
        v2 = vertices[face[2]]
        
        if vertex_normals is not None:
            n0 = vertex_normals[face[0]]
            n1 = vertex_normals[face[1]]
            n2 = vertex_normals[face[2]]
        else:
            # 计算面法线
            edge1 = v1 - v0
            edge2 = v2 - v0
            normal = np.cross(edge1, edge2)
            norm = np.linalg.norm(normal)
            if norm > 0:
                normal = normal / norm
            else:
                normal = np.array([0, 1, 0], dtype=np.float32)
            n0 = n1 = n2 = normal
        
        triangles.append({
            'v0': v0, 'v1': v1, 'v2': v2,
            'n0': n0, 'n1': n1, 'n2': n2,
            'mat_type': mat_type,
            'albedo': np.array(albedo, dtype=np.float32),
            'fuzz': fuzz,
            'ir': ir,
        })
    
    print(f"加载模型: {filepath}")
    print(f"  顶点数: {len(vertices)}, 三角形数: {len(triangles)}")
    
    return triangles


def create_cube_triangles(center=(0,0,0), size=1.0, mat_type=0, albedo=(0.7,0.7,0.7), fuzz=0.0, ir=1.5):
    """
    程序化生成立方体的三角形
    """
    cx, cy, cz = center
    s = size / 2.0
    
    # 8个顶点
    verts = np.array([
        [cx-s, cy-s, cz-s], [cx+s, cy-s, cz-s], [cx+s, cy+s, cz-s], [cx-s, cy+s, cz-s],  # 后面
        [cx-s, cy-s, cz+s], [cx+s, cy-s, cz+s], [cx+s, cy+s, cz+s], [cx-s, cy+s, cz+s],  # 前面
    ], dtype=np.float32)
    
    # 6个面，每个面2个三角形
    faces = [
        [0,1,2], [0,2,3],  # 后面 (z=-s)
        [4,6,5], [4,7,6],  # 前面 (z=+s)
        [0,4,5], [0,5,1],  # 底面 (y=-s)
        [2,6,7], [2,7,3],  # 顶面 (y=+s)
        [0,3,7], [0,7,4],  # 左面 (x=-s)
        [1,5,6], [1,6,2],  # 右面 (x=+s)
    ]
    
    # 面法线
    normals = [
        [0,0,-1], [0,0,-1],
        [0,0,1], [0,0,1],
        [0,-1,0], [0,-1,0],
        [0,1,0], [0,1,0],
        [-1,0,0], [-1,0,0],
        [1,0,0], [1,0,0],
    ]
    
    triangles = []
    for i, face in enumerate(faces):
        n = np.array(normals[i], dtype=np.float32)
        triangles.append({
            'v0': verts[face[0]], 'v1': verts[face[1]], 'v2': verts[face[2]],
            'n0': n, 'n1': n, 'n2': n,
            'mat_type': mat_type,
            'albedo': np.array(albedo, dtype=np.float32),
            'fuzz': fuzz,
            'ir': ir,
        })
    
    return triangles
