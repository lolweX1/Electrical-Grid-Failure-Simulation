from PyQt6.QtWidgets import (
    QApplication, QGraphicsScene, QGraphicsView, QGraphicsPixmapItem,
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QGraphicsRectItem, QPushButton, QGridLayout,
)
from PyQt6.QtGui import QBrush, QPen, QColor, QPainter, QPixmap
from PyQt6.QtCore import Qt, QSize, QTimer

class Tile(QPushButton):
    def __init__(self, text=""):
        super().__init__(text)

        # allow expansion
        self.setSizePolicy(
            self.sizePolicy().Policy.Expanding,
            self.sizePolicy().Policy.Expanding
        )

        self.setStyleSheet("""
            QPushButton {
                border-radius: 0px;
                border: 1px solid black;
                background-color: lightgray;
            }
            QPushButton:hover {
                background-color: gray;
            }
        """)

    # force square shape
    def resizeEvent(self, event):
        size = min(self.width(), self.height())
        self.setFixedSize(QSize(size, size))
        super().resizeEvent(event)

class options(QGraphicsRectItem):
    def __init__(self, width, height):
        super().__init__(0, 0, width, height)

        self.setBrush(QBrush(QColor(200, 200, 200, 220))) # Semi-transparent white
        self.setZValue(1000)
        self.visible = False
        self.setVisible(False)

    def setText(self, txt = []):
        pass
    
    def set_vis(self, vis):
        self.visible = vis
        self.setVisible(self.visible)
    
    def toggle_vis(self):
        self.visible = not self.visible
        self.setVisible(self.visible)

class Window(QWidget):
    def __init__(self, name, width, height):
        super().__init__()

        self.setWindowTitle(name)
        self.resize(width, height)

        self.top_left = [0, 0]
        self.zoom = 1
        self.zoom_lim = [0.25, 4]
        self.tile_size = 64
        self.width = width
        self.height = height

        self.hover_tile = QGraphicsRectItem(0, 0, self.tile_size, self.tile_size)
        self.hover_tile.setBrush(QBrush(QColor(0, 0, 0, 80)))  # semi-transparent gray
        #self.hover_tile.setPen(Qt.PenStyle.NoPen)
        self.hover_tile.setZValue(999)  # always on top

        self.choices_menu = options(200, 400)

        self.map = {

        }

        # wires
        self.wires = {

        } # format is: "number": [wire, (start), (end)]
        self.temp_wire = None
        self.temp_wire_pos = None
        self.wires_count = 0

        self.borders = {
            "horizontal": {},
            "vertical": {}
        }

        layout = QVBoxLayout()
        self.setLayout(layout)

        # Scene + View (canvas)
        self.scene = QGraphicsScene()
        self.view = QGraphicsView(self.scene)
        self.scene.setSceneRect(0, 0, width, height)

        self.scene.addItem(self.hover_tile)
        self.scene.addItem(self.choices_menu)

        layout.addWidget(self.view)

        # optional: remove borders/margins
        layout.setContentsMargins(0, 0, 0, 0)

        self.view.setMouseTracking(True)
        self.view.viewport().installEventFilter(self)
        self.view.installEventFilter(self)

        self.view.drawBackground = self.drawBackground
        self.view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.view.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.view.setInteractive(True) # Keep this True so you can click buttons/items
        self.view.setTransformationAnchor(QGraphicsView.ViewportAnchor.NoAnchor)

        self.images = {
            "power_node":QPixmap("power_node.png").scaled(64, 64)
        }

        self.options = "build"

        self.timer = QTimer()
        self.timer.timeout.connect(self.update)

        self.timer.start(33) # 30 fps

    def mousePressEvent(self, event):
        pos = self.view.mapToScene(event.pos())

        if (event.button() == Qt.MouseButton.LeftButton):
            self.choices_menu.set_vis(False)
        elif (event.button() == Qt.MouseButton.RightButton):
            x = (self.top_left[0] + pos.x())//self.tile_size
            y = (self.top_left[1] + pos.y())//self.tile_size
            if (str(y) + "-" + str(x) in self.map): # NOTE there is nothing preventing the user from selecting the same node. Wires buggeds 
                if (self.temp_wire):
                    self.wires[str(self.wires_count)] = [self.temp_wire, (self.temp_wire_pos[0], self.temp_wire_pos[1]), (self.top_left[0] + pos.x(), self.top_left[1] + pos.y())]
                    self.temp_wire = None
                    self.temp_wire_pos = None
                    self.wires_count += 1
                else:
                    match self.map[str(y) + "-" + str(x)][0]:
                        case "power node":
                            self.options = "pn"
            else:
                self.options = "build"

            self.choices_menu.toggle_vis()

    def zoom_change(self):
        pass
    
    def update(self):
        self.view.viewport().update()
        for i in self.map:
            self.map[i][1].setPos(self.map[i][2] * self.tile_size - self.top_left[0], self.map[i][3] * self.tile_size - self.top_left[1])
        for i in self.wires:
            self.wires[i][0].setPos(-self.top_left[0], -self.top_left[1])
        if (self.temp_wire):
            self.temp_wire.setPos(-self.top_left[0], -self.top_left[1])
        
    def eventFilter(self, source, event):
        if event.type() == event.Type.MouseMove:

            pos = self.view.mapToScene(event.position().toPoint())

            # snap to 32px grid
            x = int(pos.x() // self.tile_size) * self.tile_size - self.top_left[0] % self.tile_size
            y = int(pos.y() // self.tile_size) * self.tile_size - self.top_left[1] % self.tile_size

            if (not self.choices_menu.visible):
                self.hover_tile.setPos(x, y)
            
            if (self.temp_wire):
                self.temp_wire.setLine(int(self.temp_wire_pos[0]), int(self.temp_wire_pos[1]), pos.x() + self.top_left[0], pos.y() + self.top_left[1])
        elif event.type() == event.Type.KeyPress:
            self.keyPressEvent(event.key())

        return super().eventFilter(source, event)
    
    # Inside your Window class, or a subclass of QGraphicsView
    def drawBackground(self, painter, rect):
        pen = QPen(Qt.GlobalColor.black)
        painter.setPen(pen)

        # Use the top_left offset to determine where to start drawing
        left = int(rect.left()) - (int(rect.left()) % self.tile_size) - (self.top_left[0] % self.tile_size)
        top = int(rect.top()) - (int(rect.top()) % self.tile_size) - (self.top_left[1] % self.tile_size)
        
        # Draw vertical lines
        x = left
        while x < rect.right() + self.tile_size:
            painter.drawLine(x, int(rect.top()), x, int(rect.bottom()))
            x += self.tile_size

        # Draw horizontal lines
        y = top
        while y < rect.bottom() + self.tile_size:
            painter.drawLine(int(rect.left()), y, int(rect.right()), y)
            y += self.tile_size

    def keyPressEvent(self, key):
        step = 8
        if (key == Qt.Key.Key_Right):
            self.top_left[0] += step
        elif (key == Qt.Key.Key_Left):
            self.top_left[0] -= step
        if (key == Qt.Key.Key_Up):
            self.top_left[1] -= step
        elif (key == Qt.Key.Key_Down):
            self.top_left[1] += step

        if (self.choices_menu.visible):
            tile = self.hover_tile.pos()
            if (self.options == "build"):
                if (key == Qt.Key.Key_1):
                    x = (self.top_left[0] + tile.x())//self.tile_size
                    y = (self.top_left[1] + tile.y())//self.tile_size
                    item = QGraphicsPixmapItem(self.images["power_node"])
                    self.map[f"{y}-{x}"] = ["power node", item, x, y]
                    item.setPos(0, 0)
                    self.scene.addItem(item)
            elif (self.options == "pn"):
                if (key == Qt.Key.Key_1):
                    pen = QPen(Qt.GlobalColor.black)
                    pen.setWidth(5)
                    self.temp_wire_pos = [tile.x() + self.tile_size/2 + self.top_left[0], tile.y() + self.tile_size/2 + self.top_left[1]]
                    self.temp_wire = self.scene.addLine(self.temp_wire_pos[0], self.temp_wire_pos[1], self.temp_wire_pos[0], self.temp_wire_pos[1], pen)

    def display_window(self):
        self.show()