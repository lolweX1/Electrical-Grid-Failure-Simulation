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

map = [
    ["."] * 60
] * 20

pix_to_meter = 1

def max_sag(weight_of_1m, length, tension):
    complete_weight =  weight_of_1m * (length ** 2)
    return complete_weight/tension

# current divider rule, given that the branches are parallel
# https://en.wikipedia.org/wiki/Current_divider
def line_split_current_transfer(total_current, resistance_of_all_lines):
    line_currents = []
    total_resistance = sum(resistance_of_all_lines)
    for i in resistance_of_all_lines:
        line_currents.append((total_resistance-i)/total_resistance * total_current)
    return line_currents

# heat power (how quickly electrical energy is converted to thermal), Joule's heating, returns Joules
def heat_power(current, resistance):
    return current**2 * resistance

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

def caternary_equation(weight_of_1m, horizontal_tension, length, distance_from_middle): # calculates the height from the ground at x-position
    a = max_sag(weight_of_1m, horizontal_tension, length) # a is lowest point of the sag
    return a * math.cosh(distance_from_middle/a)

def max_safe_temp_for_sag():
    pass