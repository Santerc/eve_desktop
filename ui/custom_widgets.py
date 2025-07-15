from PyQt6.QtWidgets import QLineEdit, QPushButton, QWidget
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QRect, QRectF
from PyQt6.QtGui import QFont, QPen, QColor, QPainter, QPainterPath
from datetime import datetime, timedelta

class CustomLineEdit(QLineEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrame(False)
        self.has_focus = False
        self.focus_animation = QPropertyAnimation(self, b"geometry")
        self.focus_animation.setDuration(300)
        self.focus_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.original_geometry = None
    def focusInEvent(self, event):
        self.has_focus = True
        if not self.original_geometry:
            self.original_geometry = self.geometry()
        center = self.original_geometry.center()
        new_width = self.original_geometry.width() + 10
        new_rect = QRect(0, 0, new_width, self.original_geometry.height())
        new_rect.moveCenter(center)
        self.focus_animation.setStartValue(self.geometry())
        self.focus_animation.setEndValue(new_rect)
        self.focus_animation.start()
        super().focusInEvent(event)
        self.update()
    def focusOutEvent(self, event):
        self.has_focus = False
        if self.original_geometry:
            self.focus_animation.setStartValue(self.geometry())
            self.focus_animation.setEndValue(self.original_geometry)
            self.focus_animation.start()
        super().focusOutEvent(event)
        self.update()
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        path = QPainterPath()
        path.addRoundedRect(QRectF(self.rect()), 12, 12)
        if self.has_focus:
            painter.fillPath(path, QColor(255, 255, 255, 130))
            glow_pen = QPen(QColor(0, 191, 255, 100), 2)
            painter.setPen(glow_pen)
            painter.drawPath(path)
        else:
            painter.fillPath(path, QColor(255, 255, 255, 100))
        super().paintEvent(event)

class MediaControlButton(QPushButton):
    def __init__(self, text, tooltip, parent=None):
        super().__init__(parent)
        self.setFlat(True)
        self.setText(text)
        self.setFont(QFont("Caveat", 12))
        self.setStyleSheet("""
            QPushButton {
                color: rgba(100, 200, 255, 200);
                background-color: transparent;
                border: none;
                padding: 2px;
                transition: transform 0.2s;
            }
            QPushButton:hover {
                color: rgba(150, 220, 255, 230);
                background-color: rgba(255, 255, 255, 40);
                border-radius: 12px;
                transform: scale(1.1);
            }
            QPushButton:pressed {
                color: rgba(50, 150, 255, 200);
                background-color: rgba(255, 255, 255, 20);
                transform: scale(0.95);
            }
        """)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip(tooltip)
        self.setFixedSize(30, 30)
        self.hover_animation = QPropertyAnimation(self, b"geometry")
        self.hover_animation.setDuration(200)
        self.original_geometry = None
    def enterEvent(self, event):
        if not self.original_geometry:
            self.original_geometry = self.geometry()
        center = self.original_geometry.center()
        new_size = self.original_geometry.size() * 1.1
        new_rect = QRect(0, 0, new_size.width(), new_size.height())
        new_rect.moveCenter(center)
        self.hover_animation.setStartValue(self.geometry())
        self.hover_animation.setEndValue(new_rect)
        self.hover_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.hover_animation.start()
        super().enterEvent(event)
    def leaveEvent(self, event):
        if self.original_geometry:
            self.hover_animation.setStartValue(self.geometry())
            self.hover_animation.setEndValue(self.original_geometry)
            self.hover_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
            self.hover_animation.start()
        super().leaveEvent(event)

class MusicButton(QPushButton):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFlat(True)
        self.setText("🎵")
        self.setFont(QFont("Caveat", 14))
        self.setStyleSheet("""
            QPushButton {
                color: rgba(255, 100, 100, 200);
                background-color: transparent;
                border: none;
            }
            QPushButton:hover {
                color: rgba(255, 150, 150, 230);
            }
            QPushButton:pressed {
                color: rgba(255, 50, 50, 200);
            }
        """)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip("打开网易云音乐")

class CustomDateTimeEdit(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
    def init_ui(self):
        from PyQt6.QtWidgets import QHBoxLayout, QLineEdit, QPushButton
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        self.time_edit = QLineEdit()
        self.time_edit.setPlaceholderText("2025-06-12 14:30")
        self.time_edit.setFixedWidth(150)
        self.time_edit.setText(datetime.now().strftime("%Y-%m-%d %H:%M"))
        layout.addWidget(self.time_edit)
        quick_layout = QHBoxLayout()
        quick_layout.setSpacing(2)
        btn_5min = QPushButton("5分钟")
        btn_5min.setFixedSize(50, 25)
        btn_5min.clicked.connect(lambda: self.set_quick_time(5))
        quick_layout.addWidget(btn_5min)
        btn_10min = QPushButton("10分钟")
        btn_10min.setFixedSize(50, 25)
        btn_10min.clicked.connect(lambda: self.set_quick_time(10))
        quick_layout.addWidget(btn_10min)
        btn_30min = QPushButton("30分钟")
        btn_30min.setFixedSize(50, 25)
        btn_30min.clicked.connect(lambda: self.set_quick_time(30))
        quick_layout.addWidget(btn_30min)
        btn_1hour = QPushButton("1小时")
        btn_1hour.setFixedSize(50, 25)
        btn_1hour.clicked.connect(lambda: self.set_quick_time(60))
        quick_layout.addWidget(btn_1hour)
        layout.addLayout(quick_layout)
        self.setLayout(layout)
        self.setStyleSheet("""
            QLineEdit {
                background-color: #3a3a3a;
                color: white;
                border: 1px solid #555555;
                border-radius: 3px;
                padding: 5px;
                font-size: 11px;
            }
            QLineEdit:focus {
                border: 1px solid #5f9ea0;
            }
            QPushButton {
                background-color: #4a4a4a;
                color: white;
                border: none;
                border-radius: 3px;
                font-size: 10px;
            }
            QPushButton:hover {
                background-color: #5a5a5a;
            }
            QPushButton:pressed {
                background-color: #3a3a3a;
            }
        """)
    def set_quick_time(self, minutes):
        future_time = datetime.now() + timedelta(minutes=minutes)
        self.time_edit.setText(future_time.strftime("%Y-%m-%d %H:%M"))
    def setDateTime(self, dt):
        self.time_edit.setText(dt.strftime("%Y-%m-%d %H:%M"))
    def dateTime(self):
        try:
            time_str = self.time_edit.text().strip()
            if not time_str:
                return datetime.now()
            if len(time_str) == 16:
                return datetime.strptime(time_str, "%Y-%m-%d %H:%M")
            elif len(time_str) == 19:
                return datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
            else:
                return datetime.now()
        except ValueError:
            return datetime.now()
    def setEnabled(self, enabled):
        super().setEnabled(enabled)
        self.time_edit.setEnabled(enabled)
        for i in range(self.layout().count()):
            item = self.layout().itemAt(i)
            if hasattr(item, 'count'):
                for j in range(item.count()):
                    child_item = item.itemAt(j)
                    if child_item.widget():
                        child_item.widget().setEnabled(enabled) 