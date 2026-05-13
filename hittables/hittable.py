from core.vec3 import Point3, Vec3, dot
from core.ray import Ray

class HitRecord:
    """记录光线与物体相交的信息"""
    
    def __init__(self):
        self.p = Point3()
        self.normal = Vec3()
        self.t = 0.0
        self.front_face = False
        self.material = None
    
    def set_face_normal(self, r: Ray, outward_normal: Vec3):
        """判断光线是从外部还是内部击中表面"""
        self.front_face = dot(r.direction(), outward_normal) < 0
        self.normal = outward_normal if self.front_face else -outward_normal


class Hittable:
    """可相交物体的抽象基类"""
    
    def hit(self, r: Ray, t_min: float, t_max: float, rec: HitRecord) -> bool:
        raise NotImplementedError


class HittableList(Hittable):
    """物体列表，用于管理场景中的所有物体"""
    
    def __init__(self):
        self.objects = []
    
    def add(self, obj):
        self.objects.append(obj)
    
    def clear(self):
        self.objects.clear()
    
    def hit(self, r: Ray, t_min: float, t_max: float, rec: HitRecord) -> bool:
        temp_rec = HitRecord()
        hit_anything = False
        closest_so_far = t_max
        
        for obj in self.objects:
            if obj.hit(r, t_min, closest_so_far, temp_rec):
                hit_anything = True
                closest_so_far = temp_rec.t
                rec.p = temp_rec.p
                rec.normal = temp_rec.normal
                rec.t = temp_rec.t
                rec.front_face = temp_rec.front_face
                rec.material = temp_rec.material
        
        return hit_anything
