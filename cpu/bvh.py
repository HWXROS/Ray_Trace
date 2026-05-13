"""
BVH (Bounding Volume Hierarchy) 加速结构
在 CPU 端构建，然后传给 Taichi GPU 进行遍历
"""

import numpy as np
import taichi as ti

vec3 = ti.types.vector(3, ti.f32)

# Taichi AABB 结构体
AABB = ti.types.struct(
    min=vec3,
    max=vec3,
)

# Taichi BVH 节点结构体
BVHNode = ti.types.struct(
    aabb_min=vec3,
    aabb_max=vec3,
    left=ti.i32,       # 左子节点索引（-1表示叶子）
    right=ti.i32,      # 右子节点索引（-1表示叶子）
    sphere_idx=ti.i32, # 叶子节点对应的球体索引（-1表示内部节点）
)


class AABB_py:
    """Python 端的 AABB 类"""
    
    def __init__(self, min_point=None, max_point=None):
        self.min = np.array(min_point if min_point is not None else [1e30, 1e30, 1e30], dtype=np.float32)
        self.max = np.array(max_point if max_point is not None else [-1e30, -1e30, -1e30], dtype=np.float32)
    
    def expand(self, point):
        """扩展AABB以包含一个点"""
        self.min = np.minimum(self.min, point)
        self.max = np.maximum(self.max, point)
    
    def merge(self, other):
        """合并两个AABB"""
        self.min = np.minimum(self.min, other.min)
        self.max = np.maximum(self.max, other.max)
    
    def center(self):
        return (self.min + self.max) / 2.0
    
    def surface_area(self):
        """表面积（用于SAH）"""
        diag = self.max - self.min
        return 2.0 * (diag[0]*diag[1] + diag[1]*diag[2] + diag[2]*diag[0])
    
    def to_taichi(self):
        return AABB(min=vec3(self.min), max=vec3(self.max))


def aabb_hit(aabb_min, aabb_max, ray_origin, ray_dir, t_min, t_max):
    """
    检测光线与AABB相交（Python端，用于BVH构建时）
    """
    for a in range(3):
        inv_d = 1.0 / ray_dir[a]
        t0 = (aabb_min[a] - ray_origin[a]) * inv_d
        t1 = (aabb_max[a] - ray_origin[a]) * inv_d
        if inv_d < 0:
            t0, t1 = t1, t0
        t_min = max(t0, t_min)
        t_max = min(t1, t_max)
        if t_max <= t_min:
            return False
    return True


class BVHBuilder:
    """
    BVH 构建器
    使用简单的中点分割策略（易于实现，效果良好）
    """
    
    def __init__(self, sphere_centers, sphere_radii):
        """
        sphere_centers: numpy array of shape (N, 3)
        sphere_radii: numpy array of shape (N,)
        """
        self.centers = sphere_centers
        self.radii = radii = sphere_radii
        self.n = len(radii)
        
        # 预计算每个球体的AABB
        self.sphere_aabbs = []
        for i in range(self.n):
            center = centers[i]
            r = radii[i]
            aabb = AABB_py(center - r, center + r)
            self.sphere_aabbs.append(aabb)
        
        # BVH 节点列表（扁平化表示）
        self.nodes = []
        # 叶子节点到球体索引的映射
        self.leaf_sphere_indices = []
    
    def build(self):
        """构建BVH，返回节点列表"""
        # 初始时所有球体都在根节点
        indices = list(range(self.n))
        self._build_recursive(indices)
        return self.nodes
    
    def _build_recursive(self, indices):
        """递归构建BVH节点"""
        node_idx = len(self.nodes)
        self.nodes.append({
            'aabb': AABB_py(),
            'left': -1,
            'right': -1,
            'sphere_idx': -1,
        })
        
        # 计算当前节点的AABB
        node_aabb = AABB_py()
        for i in indices:
            node_aabb.merge(self.sphere_aabbs[i])
        self.nodes[node_idx]['aabb'] = node_aabb
        
        n = len(indices)
        
        if n == 1:
            # 叶子节点
            self.nodes[node_idx]['sphere_idx'] = indices[0]
            return node_idx
        
        # 找到分割轴（最长轴）
        extent = node_aabb.max - node_aabb.min
        axis = int(np.argmax(extent))
        
        # 按中心点坐标排序
        indices.sort(key=lambda i: self.centers[i][axis])
        
        # 中点分割
        mid = n // 2
        left_indices = indices[:mid]
        right_indices = indices[mid:]
        
        # 递归构建子树
        left_child = self._build_recursive(left_indices)
        right_child = self._build_recursive(right_indices)
        
        self.nodes[node_idx]['left'] = left_child
        self.nodes[node_idx]['right'] = right_child
        
        return node_idx
    
    def to_taichi_fields(self):
        """将BVH转换为Taichi field"""
        n_nodes = len(self.nodes)
        nodes_field = BVHNode.field(shape=(n_nodes,))
        
        for i, node in enumerate(self.nodes):
            aabb = node['aabb']
            nodes_field[i] = BVHNode(
                aabb_min=vec3(aabb.min),
                aabb_max=vec3(aabb.max),
                left=node['left'],
                right=node['right'],
                sphere_idx=node['sphere_idx'],
            )
        
        return nodes_field, n_nodes


def build_bvh_for_spheres(sphere_centers, sphere_radii):
    """
    便捷函数：为球体列表构建BVH
    返回: (nodes_field, num_nodes)
    """
    builder = BVHBuilder(sphere_centers, sphere_radii)
    builder.build()
    return builder.to_taichi_fields()
