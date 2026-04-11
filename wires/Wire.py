material_resistance = {
    "aluminum": 2.8e-8,
    "copper": 1.68e-8
}

class Wire:
    def __init__(self, material, length, cross_sectional_area, node_heights = None):
        self.material = material
        self.length = length
        self.cross_sectional_area = cross_sectional_area
        self.node_heights = [] if not node_heights else node_heights
    
    def change_material(self, material):
        self.material = material

    def change_cross_sectional_area(self, csa):
        self.cross_sectional_area = csa

    def get_resistance(self):
        return (material_resistance[self.material] * self.length)/self.cross_sectional_area

    def get_conductivity(self):
        return 1/self.get_resistance()