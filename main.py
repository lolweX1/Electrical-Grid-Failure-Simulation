import sys
from PyQt6.QtWidgets import (
    QApplication, QGraphicsScene, QGraphicsView, QGraphicsPixmapItem,
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QGraphicsRectItem, QPushButton
)
from PyQt6.QtGui import QBrush, QPen, QColor, QPainter, QPixmap
from PyQt6.QtCore import Qt

class PaletteItem(QLabel):
    """A QLabel in the sidebar representing an image."""
    def __init__(self, pixmap, scene):
        super().__init__()
        self.setPixmap(pixmap.scaled(50,50, Qt.AspectRatioMode.KeepAspectRatio))
        self.setFrameShape(QFrame.Shape.Box)
        self.setLineWidth(1)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.scene = scene

    def mousePressEvent(self, event):
        # When clicked, create a copy in the scene
        new_item = QGraphicsPixmapItem(self.pixmap())
        new_item.setFlags(QGraphicsPixmapItem.GraphicsItemFlag.ItemIsMovable |
                          QGraphicsPixmapItem.GraphicsItemFlag.ItemIsSelectable)
        # Spawn at a default location in the scene
        new_item.setPos(0,0)
        self.scene.addItem(new_item)

class ZoomableView(QGraphicsView):
    def __init__(self, scene):
        super().__init__(scene)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.zoom_factor = 1.2  # zoom step
        self.max = 2
        self.min = 0.2
        self.current_zoom = 1
        self.pan_step = 20  # pixels per key press
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)

    def wheelEvent(self, event):
        # Check direction of wheel
        if event.angleDelta().y() > 0:
            if (self.current_zoom < self.max):
                self.scale(self.zoom_factor, self.zoom_factor)  # zoom in
                self.current_zoom *= self.zoom_factor
        else:
            if (self.current_zoom > self.min):
                self.scale(1 / self.zoom_factor, 1 / self.zoom_factor)  # zoom out
                self.current_zoom *= 1/self.zoom_factor
    
    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Left:
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - self.pan_step)
        elif event.key() == Qt.Key.Key_Right:
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() + self.pan_step)
        elif event.key() == Qt.Key.Key_Up:
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() - self.pan_step)
        elif event.key() == Qt.Key.Key_Down:
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() + self.pan_step)
        else:
            super().keyPressEvent(event)  # pass other keys normally

class Sandbox(QWidget):
    def __init__(self, width, height):
        super().__init__()

        self.setWindowTitle("Power Grid")
        self.resize(width, height)

        # Layout
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Graphics Scene
        self.scene = QGraphicsScene()
        self.view = ZoomableView(self.scene)
        layout.addWidget(self.view)

        # Add a simple button
        button = QPushButton("Play")
        layout.addWidget(button)

        # Add a 10x10 grid of squares
        self.grid_size = 10
        self.cell_size = 40
        self.cells = []
        for row in range(self.grid_size):
            row_cells = []
            for col in range(self.grid_size):
                rect = QGraphicsRectItem(col*self.cell_size, row*self.cell_size, self.cell_size, self.cell_size)
                rect.setBrush(QBrush(Qt.GlobalColor.white))
                rect.setPen(QPen(Qt.GlobalColor.black))
                # rect.setFlag(QGraphicsRectItem.GraphicsItemFlag.ItemIsSelectable)
                rect.setFlag(QGraphicsRectItem.GraphicsItemFlag.ItemIsMovable)
                self.scene.addItem(rect)
                row_cells.append(rect)
            self.cells.append(row_cells)

        # Sidebar palette
        palette_widget = QWidget()
        palette_layout = QVBoxLayout()
        palette_widget.setLayout(palette_layout)
        layout.addWidget(palette_widget, stretch=1)

        # Add images to the palette
        images = ["power_node.png", "transformer.png", "turbine.png"]
        for img_path in images:
            pixmap = QPixmap(img_path)
            if pixmap.isNull():
                pixmap = QPixmap(50,50)  # placeholder if file missing
                pixmap.fill(Qt.GlobalColor.lightGray)
            label = PaletteItem(pixmap, self.scene)
            palette_layout.addWidget(label)
        palette_layout.addStretch()  # push images to top

        # Connect click event
        self.view.setMouseTracking(True)
        self.view.viewport().installEventFilter(self)

    def eventFilter(self, source, event):
        if event.type() == event.Type.MouseButtonPress and event.button() == Qt.MouseButton.LeftButton:
            pos = self.view.mapToScene(event.position().toPoint())
            print(event.position())
            items = self.scene.items(pos) # all items at that position
            if items:
                cell = items[0]
                # Toggle cell color
                current = cell.brush().color()
                cell.setBrush(QBrush(Qt.GlobalColor.black if current == Qt.GlobalColor.white else Qt.GlobalColor.white))
        return super().eventFilter(source, event)

# if __name__ == "__main__":
    # app = QApplication(sys.argv)
    # window = Sandbox(600, 600)
    # window.show()
    # sys.exit(app.exec())

map = [
    ["."] * 60
] * 20

pix_to_meter = 1

for r in map:
    st = ""
    for c in r:
        st += c + " "
    print(st)

material_resistance = {
    "aluminum": 2.8 * 10^-8,
    "copper": 1.68 * 10^-8
}

def max_sag(weight_of_1m, length, tension):
    complete_weight =  weight_of_1m * (length ** 2)
    return complete_weight/tension

def resistance(material_resistivity, length, cross_sectional_area):
    return (material_resistivity * length)/cross_sectional_area

def conductivity(resistance):
    return 1/resistance

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