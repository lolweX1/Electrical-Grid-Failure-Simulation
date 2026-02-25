import sys
from PyQt5.QtWidgets import QApplication, QWidget, QGridLayout, QPushButton
from PyQt5.QtCore import Qt


class GridApp(QWidget):
    def __init__(self):
        super().__init__()
        self.active_btn = None
        self.init_ui()

    def init_ui(self):
        # Create grid layout
        layout = QGridLayout()
        layout.setSpacing(0)
        
        # Create 20x20 grid of buttons
        for row in range(20):
            for col in range(20):
                button = QPushButton()
                button.setFixedSize(30, 30)
                button.setStyleSheet("""
                    QPushButton {
                        background-color: white;
                        border: 1px solid black;
                        padding: 0px;
                    }
                    QPushButton:hover {
                        background-color: lightgrey;
                    }
                    QPushButton:pressed {
                        background-color: darkgrey;
                    }
                """)
                button.clicked.connect(lambda checked, r=row, c=col: self.on_button_click(r, c))
                layout.addWidget(button, row, col)
        
        # Set window properties
        self.setLayout(layout)
        self.setWindowTitle("20x20 Button Grid - Active: None")
        self.show()

    def on_button_click(self, row, col):
        self.active_btn = f"{row}-{col}"
        self.setWindowTitle(f"20x20 Button Grid - Active: {self.active_btn}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = GridApp()
    sys.exit(app.exec_())
