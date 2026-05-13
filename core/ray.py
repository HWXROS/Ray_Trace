from .vec3 import Point3, Vec3

class Ray:
    """光线类：origin + t * direction"""
    
    def __init__(self, origin: Point3, direction: Vec3):
        self.orig = origin
        self.dir = direction
    
    def origin(self) -> Point3:
        return self.orig
    
    def direction(self) -> Vec3:
        return self.dir
    
    def at(self, t: float) -> Point3:
        return self.orig + t * self.dir
    
    def __repr__(self):
        return f"Ray(orig={self.orig}, dir={self.dir})"
