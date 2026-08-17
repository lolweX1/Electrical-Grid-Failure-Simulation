import sys
import math
import wires.Sag
import pyqt_simplified.window as pyqs

from PyQt6.QtWidgets import (
    QApplication, QGraphicsScene, QGraphicsView, QGraphicsPixmapItem,
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QGraphicsRectItem, QPushButton, QGridLayout, QScrollArea
)
from PyQt6.QtGui import QBrush, QPen, QColor, QPainter, QPixmap, QIcon
from PyQt6.QtCore import Qt

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = pyqs.Window("eletrical grid", 400, 400)
    window.show()
    sys.exit(app.exec())

# current divider rule, given that the branches are parallel
# https://en.wikipedia.org/wiki/Current_divider

# heat power (how quickly electrical energy is converted to thermal), Joule's heating, returns Joules
def Joules_Law(current=None, voltage = None, resistance=None):
    """
        Uses Joule's law to return power
    """
    if current and resistance:
        return current**2 * resistance
    elif voltage and resistance:
        return voltage ** 2 / resistance
    elif voltage and current:
        return voltage * current
    else:
        raise ValueError("Not enough parameter values to calculate power")

def energy_from_power(Joules_value, time):
    return Joules_value * time

def temperature_change_from_energy(energy, mass, C):
    """
        Q = m * C * (delta t)
        energy: Q
        C: C, specific heat capacity
        mass: m
    """
    return energy/(mass * C)

def new_temperature_from_energy(energy, mass, C, original_temp):
    """
        Q = m * C * (delta t)
        energy: Q
        C: C, specific heat capacity
        mass: m
    """
    return original_temp + (energy/(mass * C))

# https://en.wikipedia.org/wiki/Convection_(heat_transfer)
# heat loss from convection, no wind
def convection_heat_loss(heat_transfer_coefficient, surface_area, surface_temperature, fluid_temperature):
    return heat_transfer_coefficient * surface_area * (surface_temperature - fluid_temperature)

# temperature change
'''
T = temperature, t = time, Q = heat transfered, P = power, C = heat capacity
Q = mC(ΔT)
Qnet (net power) = (Pgain - Ploss)*Δt (power is rate of heat transfer, multiply by time to get total heat transfered)
Qqain = heat_power
Qloss = convection_heat_los
(Pgain - Ploss)*Δt = mC(ΔT) 
ΔT = ((Pgain - Ploss)*Δt)/(mC)
'''
def temperature_change(heat_capacity, mass, time, power_gain, power_loss):
    heat_transferred = (power_gain - power_loss) * time
    return heat_transferred/(mass * heat_capacity)

def change_in_length(linear_expansion_coefficent, temperature_change, length):
    return length * (1 + linear_expansion_coefficent * temperature_change)

def max_safe_temp_for_sag():
    pass

# heat for sun

# newton rahspon solver
def catenary_c_solver(err, total_length, horizontal_dist, vertical_diff, old_c = None, count = 0):
    if old_c is None:
        old_c = horizontal_dist / (2 * math.sqrt(6 * (total_length/horizontal_dist - 1)))
    
    func = 2 * old_c  * math.sinh(horizontal_dist/(2 * old_c)) - math.sqrt(math.pow(total_length, 2) - math.pow(vertical_diff, 2))
    func_deriv = 2 * math.sinh(horizontal_dist/(2 * old_c)) - (horizontal_dist/old_c) * math.cosh(horizontal_dist/(2 * old_c))
    new_val = old_c - func/func_deriv
    if (count > 100):
        raise ValueError("Failed to Converge")

    if (abs(new_val - old_c) > err):
        return catenary_c_solver(err, total_length, horizontal_dist, vertical_diff, new_val, count+1)
    else:
        return new_val
    
def x_of_lowest_point(vertical_diff, total_length, c):
    """
        return the x-position of the lowest point of the wire relative to the middle point
    """
    return c * math.atanh(vertical_diff / total_length)

EPSILON = 1e-8

def get_wire_sag(c, x0, horizontal_dist, x):
    """
        Returns the wire's y-distance (drop) below the tall-pole attachment point,
        at horizontal position x.

        c: catenary parameter
        x0: x-position of the wire's lowest point, relative to the span's midpoint
        horizontal_dist: horizontal distance between the two poles
        x: horizontal position (relative to the span's midpoint) at which to
           evaluate the sag; the tall pole is at x = -horizontal_dist/2
    """
    y_tall = c * math.cosh((horizontal_dist / 2 + x0) / c)  # height at the tall pole, c * math.cosh((x-a)/c)
    y_x = c * math.cosh((x0 - x) / c)                        # height at position x
    return y_tall - y_x

def get_sag_of_lowest_point_of_wire(c, x0, horizontal_dist):
    y_high = c * math.cosh((horizontal_dist / 2 + x0) / c)
    y_lowest = c  # minimum of cosh is 1, so y_min = c*1 = c
    return y_high - y_lowest

def verify_c_cat_param(c, total_length, horizontal_dist, vertical_diff, tolerance=1e-6):
    """
    Verifies that the catenary parameter c satisfies the arc-length equation.
    Returns True if valid, and prints the LHS, RHS, and their difference.
    
    Equation: 2c * sinh(d / 2c) = sqrt(L^2 - dy^2)
    """
    LHS = 2 * c * math.sinh(horizontal_dist / (2 * c))
    RHS = math.sqrt(total_length**2 - vertical_diff**2)
    diff = abs(LHS - RHS)
    valid = diff < tolerance

    print(f"  LHS = 2c*sinh(d/2c) = {LHS:.6f}")
    print(f"  RHS = sqrt(L^2-dy^2) = {RHS:.6f}")
    print(f"  diff = {diff:.2e}")
    print(f"  valid: {valid}")
    return valid

def verify_sag(c, x0, horizontal_dist, vertical_diff):
    """
    The sag difference between the two attachment points should equal vertical_diff.
    sag at tall pole = 0 (by definition, it's the reference)
    sag at short pole = vertical_diff
    """
    sag_tall = c * math.cosh((horizontal_dist/2 + x0)/c) - c
    sag_short = c * math.cosh((-horizontal_dist/2 + x0)/c) - c
    recovered_diff = abs(sag_short - sag_tall)

    print(f"  sag at tall pole end:  {sag_tall:.6f}")
    print(f"  sag at short pole end: {sag_short:.6f}")
    print(f"  recovered vertical_diff: {recovered_diff:.6f}")
    print(f"  expected vertical_diff:  {vertical_diff:.6f}")
    print(f"  valid: {abs(recovered_diff - vertical_diff) < 1e-6}")

print("test case 1 - symmetrical")
span = 100
length = 110
vertical_diff = 0
tall_pole_height = 50
c = catenary_c_solver(EPSILON, length, span, vertical_diff, None)
print("catenary parameter value:")
print(c)
x0 = x_of_lowest_point(vertical_diff, length, c)
print("shift_from_middle")
print(x0)
lowest_point = get_sag_of_lowest_point_of_wire(c, x0, span)
print("the sag of the lowest point is:")
print(lowest_point)
verify_sag(c, x0, span, vertical_diff)


print("test case 2 - different height")
span = 100
length = 120
vertical_diff = 40
tall_pole_height = 60
c = catenary_c_solver(EPSILON, length, span, vertical_diff, None)
print("catenary parameter value:")
print(c)
x0 = x_of_lowest_point(vertical_diff, length, c)
print("shift_from_middle")
print(x0)
lowest_point = get_sag_of_lowest_point_of_wire(c, x0, span)
print("the sag of the lowest point is:")
print(lowest_point)
verify_sag(c, x0, span, vertical_diff)


print("test case 3 - tight symmetrical")
span = 100
length = 101
vertical_diff = 0
tall_pole_height = 60
c = catenary_c_solver(EPSILON, length, span, vertical_diff, None)
print("catenary parameter value:")
print(c)
x0 = x_of_lowest_point(vertical_diff, length, c)
print("shift_from_middle")
print(x0)
lowest_point = get_sag_of_lowest_point_of_wire(c, x0, span)
print("the sag of the lowest point is:")
print(lowest_point)
verify_sag(c, x0, span, vertical_diff)


print("test case 4 - tight different height")
span = 100
length = 108
vertical_diff = 40
tall_pole_height = 60
c = catenary_c_solver(EPSILON, length, span, vertical_diff, None)
print("catenary parameter value:")
print(c)
x0 = x_of_lowest_point(vertical_diff, length, c)
print("shift_from_middle")
print(x0)
lowest_point = get_sag_of_lowest_point_of_wire(c, x0, span)
print("the sag of the lowest point is:")
print(lowest_point)
verify_sag(c, x0, span, vertical_diff)

# Test all 4 cases
print("Test case 1 - symmetrical")
verify_c_cat_param(65.49639476368564, 110, 100, 0)

print("Test case 2 - different height")
verify_c_cat_param(57.39538677623081, 120, 100, 40)

print("Test case 3 - tight symmetrical")
verify_c_cat_param(204.42962365016066, 101, 100, 0)

print("Test case 4 - tight different height")
verify_c_cat_param(361.3049566772255, 108, 100, 40)
