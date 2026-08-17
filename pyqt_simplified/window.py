from PyQt6.QtWidgets import (
    QApplication, QGraphicsScene, QGraphicsView, QGraphicsPixmapItem,
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QGraphicsRectItem, QPushButton, QGridLayout, QMainWindow
)
from PyQt6.QtGui import QBrush, QPen, QColor, QPainter, QPixmap
from PyQt6.QtCore import Qt, QSize, QTimer
from main import get_wire_sag

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

class options(QWidget):
    def __init__(self, width, height):
        super().__init__()

        self.resize(width, height)

        self.setStyleSheet("background-color: rgba(200, 200, 200, 220);")

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.visible = False
        self.setVisible(False)
    
    def set_vis(self, vis):
        self.visible = vis
        self.setVisible(self.visible)

    def clear_layout(self):
        while self.layout.count():
            item = self.layout.takeAt(0)
            widget = item.widget()
            widget.deleteLater()
    
    def toggle_vis(self):
        self.visible = not self.visible
        if (not self.visible):
            self.clear_layout()
        self.setVisible(self.visible)

class Window(QMainWindow):
    def __init__(self, name, width, height):
        super().__init__()

        self.setWindowTitle(name)
        self.resize(width, height)

        self.top_left = [0, 0]
        self.zoom = 1
        self.zoom_lim = [0.2, 4]
        self.tile_size = 64
        self.default_tile_size = 64
        self.width = width
        self.height = height
        self.curr_item = None
        self.curr_item_name = ""

        self.hover_tile = QGraphicsRectItem(0, 0, self.tile_size, self.tile_size)
        self.hover_tile.setBrush(QBrush(QColor(0, 0, 0, 80)))  # semi-transparent gray
        #self.hover_tile.setPen(Qt.PenStyle.NoPen)
        self.hover_tile.setZValue(999)  # always on top

        self.choices_menu = options(200, 400)

        self.map = {}

        # wires
        self.wires = {} # format is: "number": [wire, (start), (end)]

        self.temp_wire = None
        self.temp_wire_pos = None
        self.wires_count = 0

        self.borders = {
            "horizontal": {},
            "vertical": {}
        }

        self.sub_windows = []

        layout = QVBoxLayout()

        # Scene + View (canvas)
        self.scene = QGraphicsScene()
        self.view = QGraphicsView(self.scene)
        self.scene.setSceneRect(0, 0, width, height)

        self.scene.addItem(self.hover_tile)

        proxy = self.scene.addWidget(self.choices_menu)
        proxy.setZValue(1000)

        layout.addWidget(self.view)

        # buttons
        self.button = QPushButton("Push for Window")
        self.button.clicked.connect(self.show_new_window)
        layout.addWidget(self.button)

        self.house_8_by_4_btn = QPushButton("8 by 4 house")
        self.house_8_by_4_btn.clicked.connect(lambda: self.new_item("8_by_4"))
        layout.addWidget(self.house_8_by_4_btn)

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
            "power_node":QPixmap("power_node.png").scaled(64, 64),
            "8_by_4":QPixmap("house_8_x_4.png")
        }

        self.options = "build"

        self.timer = QTimer()
        self.timer.timeout.connect(self.update)

        self.timer.start(33) # 30 fps

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def new_item(self, obj):
        if (obj == "8_by_4"):
            self.curr_item = QGraphicsPixmapItem(self.images[obj])
            self.curr_item_name = obj
        self.scene.addItem(self.curr_item)

    def mousePressEvent(self, event):
        pos = self.view.mapToScene(event.pos())

        if (event.button() == Qt.MouseButton.LeftButton):
            if (self.curr_item):
                x = (self.top_left[0] + pos.x())//self.tile_size
                y = (self.top_left[1] + pos.y())//self.tile_size
                self.map[f"{x}-{y}"] = [self.curr_item_name, self.curr_item, x, y] # [name, obj, x, y]
                if (self.curr_item_name == "8_by_4"):
                    for y_offset in range(4):
                        for x_offset in range(8):
                            if (not (x_offset == 0 and y_offset == 0)):
                                self.map[f"{x+x_offset}-{y+y_offset}"] = [self.curr_item_name, self.map[f"{x}-{y}"], x, y, "ref"] # [name, reference, origin x, origin y, ref]
                self.curr_item = None
            else:
                self.choices_menu.set_vis(False)
        elif (event.button() == Qt.MouseButton.RightButton):
            if (self.curr_item):
                self.curr_item = None
            else:
                x = (self.top_left[0] + pos.x())//self.tile_size
                y = (self.top_left[1] + pos.y())//self.tile_size
                if (str(x) + "-" + str(y) in self.map): # NOTE there is nothing preventing the user from selecting the same node. Wires buggeds 
                    self.update_menu(self.map[str(x) + "-" + str(y)])
                    self.choices_menu.toggle_vis()

    def update_menu(self, obj):
        print(obj)
        if (obj[0] == "8_by_4"):
            del_button = QPushButton("Delete")
            del_button.clicked.connect(lambda: self.delete_obj_and_references(obj, obj[2], obj[3], 8, 4))
            self.choices_menu.layout.addWidget(del_button)
            print("hi")

    def delete_obj_and_references(self, obj, x, y, width, height):
        if (obj[-1] == "ref"):
            self.scene.removeItem(obj[1][1])
        else:
            self.scene.removeItem(obj[1])
        for d_y in range(height):
            for d_x in range(width):
                del self.map[str(x + d_x) + "-" + str(y + d_y)]
        self.choices_menu.toggle_vis()

    def wheelEvent(self, event):
        delta = event.angleDelta().y()
        change = delta/120 * 0.1 
        if (change != 0):
            self.zoom += change
            if (self.zoom < self.zoom_lim[0]):
                self.zoom = self.zoom_lim[0]
            elif (self.zoom > self.zoom_lim[1]):
                self.zoom = self.zoom_lim[1]
            self.zoom_change()

    def zoom_change(self):
        self.tile_size = int(self.default_tile_size * self.zoom)
        rect = self.hover_tile.rect()
        self.hover_tile.setRect(rect.x(), rect.y(), self.tile_size, self.tile_size)
        if (self.curr_item):
            self.curr_item.setScale(self.tile_size/self.default_tile_size)
        # resize all map items as well
        for block in self.map:
            if (self.map[block][-1] != "ref"):
                self.map[block][1].setScale(self.tile_size/self.default_tile_size)
                    
    
    def update(self):
        self.view.viewport().update()
        for i in self.map:
            if (self.map[i][-1] != "ref"):
                self.map[i][1].setPos(self.map[i][2] * self.tile_size - self.top_left[0], self.map[i][3] * self.tile_size - self.top_left[1])
        for i in self.wires:
            self.wires[i][0].setPos(-self.top_left[0], -self.top_left[1])
        if (self.temp_wire):
            self.temp_wire.setPos(-self.top_left[0], -self.top_left[1])
        
    def eventFilter(self, source, event):
        if event.type() == event.Type.MouseMove:

            pos = self.view.mapToScene(event.position().toPoint())

            # snap to 32px grid
            x = int((pos.x() + self.top_left[0] % self.tile_size) // self.tile_size) * self.tile_size - self.top_left[0] % self.tile_size
            y = int((pos.y() + self.top_left[1] % self.tile_size) // self.tile_size) * self.tile_size - self.top_left[1] % self.tile_size

            if self.curr_item:
                self.curr_item.setPos(x, y)
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
                    self.map[f"{x}-{y}"] = ["power node", item, x, y]
                    item.setPos(0, 0)
                    self.scene.addItem(item)
            elif (self.options == "pn"):
                if (key == Qt.Key.Key_1):
                    pen = QPen(Qt.GlobalColor.black)
                    pen.setWidth(5)
                    self.temp_wire_pos = [tile.x() + self.tile_size/2 + self.top_left[0], tile.y() + self.tile_size/2 + self.top_left[1]]
                    self.temp_wire = self.scene.addLine(self.temp_wire_pos[0], self.temp_wire_pos[1], self.temp_wire_pos[0], self.temp_wire_pos[1], pen)

    def show_new_window(self):
        w = Wire_Window(
            {
                "left-pole": 20, 
                "right-pole": 10,
                "c-param": 10,
                "center-offset": 4.135684508192784,
                "h-dist": 20
             }
            )
        self.sub_windows.append(w)
        w.show()

    def display_window(self):
        self.show()

class Wire_Window(QWidget):
    def __init__(self, wire_data):
        super().__init__()
        layout = QVBoxLayout()
        self.label = QLabel("Wire")
        layout.addWidget(self.label)
        self.setLayout(layout)
        self.wire = wire_data

        self.pixels_to_meters = 20

        self.scene = QGraphicsScene()
        self.view = QGraphicsView(self.scene)
        self.scene.setSceneRect(0, 0, 600, 300)

        layout.addWidget(self.view)

        start_dist = 300-(self.wire["left-pole"]*self.pixels_to_meters)

        first_pole = QGraphicsRectItem(0, start_dist, 20, (self.wire["left-pole"]*self.pixels_to_meters))
        first_pole.setBrush(QBrush(QColor(200, 200, 200)))
        first_pole.setPen(QPen(Qt.GlobalColor.black))
        self.scene.addItem(first_pole)

        second_pole = QGraphicsRectItem(20+self.wire["h-dist"] * self.pixels_to_meters, 300-(self.wire["right-pole"]*self.pixels_to_meters), 20, (self.wire["right-pole"]*self.pixels_to_meters))
        second_pole.setBrush(QBrush(QColor(200, 200, 200)))
        second_pole.setPen(QPen(Qt.GlobalColor.black))
        self.scene.addItem(second_pole)

        self.points = []
        self.point_count = self.wire["h-dist"] * 10
        pen = QPen(QColor(0, 0, 0))
        pen.setWidth(3)
        brush = QBrush(QColor(255, 255, 255))
        brush = QBrush(Qt.BrushStyle.NoBrush)
        for point in range(self.point_count):
            curr_dist = -(self.wire["h-dist"]/2) + (point/self.point_count * self.wire["h-dist"])
            y = get_wire_sag(self.wire["c-param"], self.wire["center-offset"], self.wire["h-dist"], curr_dist)
            self.points.append(self.scene.addEllipse(20+point/self.point_count * self.wire["h-dist"] * self.pixels_to_meters, start_dist + (y * self.pixels_to_meters), 2, 2, pen, brush))