import math
from .vec3 import Point3, Vec3, unit_vector, cross

class Camera:
    """透视相机"""
    
    def __init__(self, lookfrom: Point3, lookat: Point3, vup: Vec3,
                 vfov: float, aspect_ratio: float,
                 aperture: float = 0.0, focus_dist: float = None):
        theta = math.radians(vfov)
        h = math.tan(theta / 2)
        viewport_height = 2.0 * h
        viewport_width = aspect_ratio * viewport_height
        
        self.w = unit_vector(lookfrom - lookat)
        self.u = unit_vector(cross(vup, self.w))
        self.v = cross(self.w, self.u)
        
        if focus_dist is None:
            focus_dist = (lookfrom - lookat).length()
        
        self.origin = lookfrom
        self.horizontal = focus_dist * viewport_width * self.u
        self.vertical = focus_dist * viewport_height * self.v
        self.lower_left_corner = (self.origin 
                                  - self.horizontal / 2 
                                  - self.vertical / 2 
                                  - focus_dist * self.w)
        
        self.lens_radius = aperture / 2
    
    def get_ray(self, s: float, t: float):
        from .vec3 import random_in_unit_disk
        rd = self.lens_radius * random_in_unit_disk()
        offset = self.u * rd.x + self.v * rd.y
        
        orig = self.origin + offset
        direction = (self.lower_left_corner 
                     + s * self.horizontal 
                     + t * self.vertical 
                     - self.origin - offset)
        
        from .ray import Ray
        return Ray(orig, direction)
