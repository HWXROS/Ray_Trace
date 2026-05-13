import math
import numpy as np
from core.vec3 import Vec3, Color, Point3, dot, reflect, refract, reflectance, random_unit_vector, random_in_unit_sphere, unit_vector
from core.ray import Ray
from hittables.hittable import HitRecord

class Material:
    """材质基类"""
    
    def scatter(self, r_in: Ray, rec: HitRecord, attenuation, scattered: Ray) -> bool:
        raise NotImplementedError


class Lambertian(Material):
    """漫反射材质（Lambertian）"""
    
    def __init__(self, albedo: Color):
        self.albedo = albedo
    
    def scatter(self, r_in: Ray, rec: HitRecord, attenuation, scattered: Ray) -> bool:
        scatter_direction = rec.normal + random_unit_vector()
        
        # 防止随机方向恰好与法线相反
        if scatter_direction.near_zero():
            scatter_direction = rec.normal
        
        scattered.orig = rec.p
        scattered.dir = scatter_direction
        attenuation.e = self.albedo.e.copy()
        return True


class Metal(Material):
    """金属材质（镜面反射）"""
    
    def __init__(self, albedo: Color, fuzz: float = 0.0):
        self.albedo = albedo
        self.fuzz = min(fuzz, 1.0)
    
    def scatter(self, r_in: Ray, rec: HitRecord, attenuation, scattered: Ray) -> bool:
        reflected = reflect(unit_vector(r_in.direction()), rec.normal)
        scattered.orig = rec.p
        scattered.dir = reflected + self.fuzz * random_in_unit_sphere()
        attenuation.e = self.albedo.e.copy()
        
        return dot(scattered.direction(), rec.normal) > 0


class Dielectric(Material):
    """电介质/玻璃材质（折射）"""
    
    def __init__(self, index_of_refraction: float):
        self.ir = index_of_refraction
    
    def scatter(self, r_in: Ray, rec: HitRecord, attenuation, scattered: Ray) -> bool:
        attenuation.e = np.array([1.0, 1.0, 1.0])
        
        refraction_ratio = (1.0 / self.ir) if rec.front_face else self.ir
        
        unit_direction = unit_vector(r_in.direction())
        cos_theta = min(dot(-unit_direction, rec.normal), 1.0)
        sin_theta = math.sqrt(1.0 - cos_theta * cos_theta)
        
        cannot_refract = refraction_ratio * sin_theta > 1.0
        direction = Vec3()
        
        if cannot_refract or reflectance(cos_theta, refraction_ratio) > np.random.random():
            direction = reflect(unit_direction, rec.normal)
        else:
            direction = refract(unit_direction, rec.normal, refraction_ratio)
        
        scattered.orig = rec.p
        scattered.dir = direction
        return True
