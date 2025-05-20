import sys
import psutil
import subprocess
import json
import os
from PyQt6.QtCore import Qt, QTimer, QPoint, QEvent, QObject, QRect, QRectF
from PyQt6.QtGui import QFont, QColor, QPainter, QGuiApplication, QPainterPath, QIcon, QAction
from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QLineEdit, QPushButton, QDialog, QMenu
from PyQt6.QtWidgets import QVBoxLayout, QHBoxLayout, QCheckBox, QColorDialog, QFileDialog, QSlider
from PyQt6.QtWidgets import QSystemTrayIcon, QComboBox
from PyQt6.QtCore import QPropertyAnimation, QEasingCurve, QPointF, QTimer, QSequentialAnimationGroup
from PyQt6.QtGui import QPainterPath, QPainter, QColor, QBrush, QPen

import ctypes
from datetime import datetime

user32 = ctypes.windll.user32
VK_MEDIA_PLAY_PAUSE = 0xB3  # 播放/暂停媒体键
VK_MEDIA_NEXT_TRACK = 0xB0  # 下一曲媒体键
VK_MEDIA_PREV_TRACK = 0xB1  # 上一曲媒体键

# 设置文件路径
SETTINGS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "wallpaper_settings.json")

# 默认设置
DEFAULT_SETTINGS = {
    "netease_music_path": "D:\\CloudMusic\\cloudmusic.exe",
    "everything_path": "D:\\BaiscTools\\Everything\\Everything.exe",
    "browser_path": "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe",
    "bg_color": {
        "r": 0,
        "g": 0,
        "b": 0,
        "a": 120
    },
    "autostart": False,
    "default_search_engine": "everything"
}

def save_settings(settings):
    """保存设置到JSON文件"""
    try:
        with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(settings, f, ensure_ascii=False, indent=4)
        return True
    except Exception as e:
        print(f"保存设置失败: {e}")
        return False

def load_settings():
    """从JSON文件加载设置"""
    try:
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        return DEFAULT_SETTINGS
    except Exception as e:
        print(f"加载设置失败: {e}")
        return DEFAULT_SETTINGS


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
        
        # 添加悬浮动画
        self.hover_animation = QPropertyAnimation(self, b"geometry")
        self.hover_animation.setDuration(200)
        
        # 原始大小
        self.original_geometry = None
    
    def enterEvent(self, event):
        """鼠标进入事件"""
        if not self.original_geometry:
            self.original_geometry = self.geometry()
        
        # 计算放大后的几何形状
        center = self.original_geometry.center()
        new_size = self.original_geometry.size() * 1.1
        new_rect = QRect(0, 0, new_size.width(), new_size.height())
        new_rect.moveCenter(center)
        
        # 设置动画
        self.hover_animation.setStartValue(self.geometry())
        self.hover_animation.setEndValue(new_rect)
        self.hover_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.hover_animation.start()
        
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        """鼠标离开事件"""
        if self.original_geometry:
            # 设置动画
            self.hover_animation.setStartValue(self.geometry())
            self.hover_animation.setEndValue(self.original_geometry)
            self.hover_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
            self.hover_animation.start()
        
        super().leaveEvent(event)

class EventFilter(QObject):
    def eventFilter(self, obj, event):
        # 检查是否是窗口状态改变事件
        if event.type() == QEvent.Type.WindowStateChange:
            # 如果窗口被最小化，阻止最小化并恢复窗口
            if obj.windowState() & Qt.WindowState.WindowMinimized:
                obj.setWindowState(Qt.WindowState.WindowNoState)
                return True
        return super().eventFilter(obj, event)

class CustomLineEdit(QLineEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrame(False)  # 移除默认边框
        
        # 焦点状态
        self.has_focus = False
        
        # 动画效果
        self.focus_animation = QPropertyAnimation(self, b"geometry")
        self.focus_animation.setDuration(300)
        self.focus_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        # 原始几何形状
        self.original_geometry = None

    def focusInEvent(self, event):
        """获得焦点事件"""
        self.has_focus = True
        
        if not self.original_geometry:
            self.original_geometry = self.geometry()
        
        # 计算扩展后的几何形状
        center = self.original_geometry.center()
        new_width = self.original_geometry.width() + 10
        new_rect = QRect(0, 0, new_width, self.original_geometry.height())
        new_rect.moveCenter(center)
        
        # 设置动画
        self.focus_animation.setStartValue(self.geometry())
        self.focus_animation.setEndValue(new_rect)
        self.focus_animation.start()
        
        super().focusInEvent(event)
        self.update()
    
    def focusOutEvent(self, event):
        """失去焦点事件"""
        self.has_focus = False
        
        if self.original_geometry:
            # 设置动画
            self.focus_animation.setStartValue(self.geometry())
            self.focus_animation.setEndValue(self.original_geometry)
            self.focus_animation.start()
        
        super().focusOutEvent(event)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # 绘制背景
        path = QPainterPath()
        path.addRoundedRect(QRectF(self.rect()), 12, 12)
        
        # 根据焦点状态设置不同的背景颜色
        if self.has_focus:
            painter.fillPath(path, QColor(255, 255, 255, 130))
            
            # 绘制发光边框
            glow_pen = QPen(QColor(0, 191, 255, 100), 2)
            painter.setPen(glow_pen)
            painter.drawPath(path)
        else:
            # 半透明背景
            painter.fillPath(path, QColor(255, 255, 255, 100))
        
        # 调用原始绘制方法来绘制文本
        super().paintEvent(event)

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

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("设置")
        self.setFixedSize(400, 400)  # 增加高度以容纳透明度滑动条
        
        # 设置窗口样式
        self.setStyleSheet("""
            QDialog {
                background-color: #2c2c2c;
                color: white;
            }
            QLabel {
                color: white;
            }
            QPushButton {
                background-color: #3a3a3a;
                color: white;
                border: none;
                padding: 5px 10px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #4a4a4a;
            }
            QCheckBox {
                color: white;
            }
            QSlider::groove:horizontal {
                border: 1px solid #999999;
                height: 8px;
                background: #4a4a4a;
                margin: 2px 0;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: #5f9ea0;
                border: 1px solid #5f9ea0;
                width: 18px;
                margin: -2px 0;
                border-radius: 9px;
            }
            QSlider::handle:horizontal:hover {
                background: #7fb1b3;
            }
        """)
        
        layout = QVBoxLayout()
        
        # 开机自启动选项
        self.autostart_checkbox = QCheckBox("开机自动启动")
        layout.addWidget(self.autostart_checkbox)
        
        # 背景颜色设置
        color_layout = QHBoxLayout()
        color_layout.addWidget(QLabel("背景颜色:"))
        self.color_button = QPushButton("选择颜色")
        self.color_button.clicked.connect(self.choose_color)
        color_layout.addWidget(self.color_button)
        layout.addLayout(color_layout)
        
        # 添加透明度滑动条
        transparency_layout = QHBoxLayout()
        transparency_layout.addWidget(QLabel("透明度:"))
        self.transparency_slider = QSlider(Qt.Orientation.Horizontal)
        self.transparency_slider.setMinimum(0)
        self.transparency_slider.setMaximum(255)
        self.transparency_slider.setValue(120)  # 默认值
        self.transparency_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.transparency_slider.setTickInterval(25)
        self.transparency_value_label = QLabel("120")
        transparency_layout.addWidget(self.transparency_slider)
        transparency_layout.addWidget(self.transparency_value_label)
        layout.addLayout(transparency_layout)
        
        # 连接滑动条的值变化信号
        self.transparency_slider.valueChanged.connect(self.update_transparency_value)
        
        # 路径设置
        path_layout = QHBoxLayout()
        path_layout.addWidget(QLabel("网易云音乐路径:"))
        self.music_path_button = QPushButton("选择路径")
        self.music_path_button.clicked.connect(self.choose_music_path)
        path_layout.addWidget(self.music_path_button)
        layout.addLayout(path_layout)
        
        # Everything路径设置
        everything_layout = QHBoxLayout()
        everything_layout.addWidget(QLabel("Everything路径:"))
        self.everything_path_button = QPushButton("选择路径")
        self.everything_path_button.clicked.connect(self.choose_everything_path)
        everything_layout.addWidget(self.everything_path_button)
        layout.addLayout(everything_layout)
        
        # 浏览器路径设置
        browser_layout = QHBoxLayout()
        browser_layout.addWidget(QLabel("浏览器路径:"))
        self.browser_path_button = QPushButton("选择路径")
        self.browser_path_button.clicked.connect(self.choose_browser_path)
        browser_layout.addWidget(self.browser_path_button)
        layout.addLayout(browser_layout)
        
        # 默认搜索引擎设置
        search_engine_layout = QHBoxLayout()
        search_engine_layout.addWidget(QLabel("默认搜索引擎:"))
        self.search_engine_combo = QComboBox()
        self.search_engine_combo.addItems(["Everything", "Bing", "ChatGPT"])
        search_engine_layout.addWidget(self.search_engine_combo)
        layout.addLayout(search_engine_layout)
        
        # 确定取消按钮
        button_layout = QHBoxLayout()
        self.ok_button = QPushButton("确定")
        self.ok_button.clicked.connect(self.accept)
        self.cancel_button = QPushButton("取消")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.ok_button)
        button_layout.addWidget(self.cancel_button)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def choose_browser_path(self):
        path, _ = QFileDialog.getOpenFileName(self, "选择浏览器程序", "", "可执行文件 (*.exe)")
        if path:
            self.browser_path = path
            self.browser_path_button.setText(path.split("/")[-1])

    def update_transparency_value(self, value):
        """更新透明度值显示"""
        self.transparency_value_label.setText(str(value))
        # 如果已经选择了颜色，更新颜色的透明度
        if hasattr(self, 'selected_color'):
            self.selected_color.setAlpha(value)
            self.color_button.setStyleSheet(f"background-color: {self.selected_color.name()}")
    
    def choose_color(self):
        """选择背景颜色"""
        # 创建颜色对话框并明确设置父窗口
        color_dialog = QColorDialog(self)
        color_dialog.setWindowTitle("选择背景颜色")
        
        # 使用exec()方法模态显示对话框
        if color_dialog.exec() == QDialog.DialogCode.Accepted:
            color = color_dialog.currentColor()
            if color.isValid():
                # 保存颜色设置，并应用当前的透明度值
                self.selected_color = color
                self.selected_color.setAlpha(self.transparency_slider.value())
                self.color_button.setStyleSheet(f"background-color: {self.selected_color.name()}")
    
    def set_autostart(self, enable):
        """设置开机自启动"""
        import winreg
        
        app_path = os.path.abspath(sys.argv[0])
        key_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run"
        
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE) as key:
                if enable:
                    winreg.SetValueEx(key, "WallpaperET", 0, winreg.REG_SZ, f'"{app_path}"')
                else:
                    try:
                        winreg.DeleteValue(key, "WallpaperET")
                    except FileNotFoundError:
                        pass
            return True
        except Exception as e:
            print(f"设置开机自启动失败: {e}")
            return False

    def is_autostart(self):
        """检查是否设置了开机自启动"""
        import winreg
        
        key_path = r"SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run"
        
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_READ) as key:
                try:
                    winreg.QueryValueEx(key, "WallpaperET")
                    return True
                except FileNotFoundError:
                    return False
        except Exception:
            return False

    def choose_music_path(self):
        path, _ = QFileDialog.getOpenFileName(self, "选择网易云音乐程序", "", "可执行文件 (*.exe)")
        if path:
            self.music_path = path
            self.music_path_button.setText(path.split("/")[-1])
    
    def choose_everything_path(self):
        path, _ = QFileDialog.getOpenFileName(self, "选择Everything程序", "", "可执行文件 (*.exe)")
        if path:
            self.everything_path = path
            self.everything_path_button.setText(path.split("/")[-1])


class AcrylicWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.is_playing = False  # 添加播放状态变量
        
        # 加载设置
        self.settings = load_settings()
        
        # 设置默认路径和颜色
        self.netease_music_path = self.settings["netease_music_path"]
        self.everything_path = self.settings["everything_path"]
        self.browser_path = self.settings["browser_path"]
        
        # 从设置中加载颜色
        color_settings = self.settings["bg_color"]
        self.bg_color = QColor(
            color_settings["r"],
            color_settings["g"],
            color_settings["b"],
            color_settings["a"]
        )
        
        # 搜索引擎设置
        self.search_engines = {
            "everything": {"name": "Everything", "icon": "🔍", "action": self.search_everything},
            "bing": {"name": "Bing", "icon": "🌐", "action": self.search_bing},
            "chatgpt": {"name": "ChatGPT", "icon": "🤖", "action": self.search_chatgpt}
        }
        
        # 当前搜索引擎
        self.current_search_engine = self.settings.get("default_search_engine", "everything")

        self.init_ui()
        self.init_tray_icon()  # 初始化系统托盘图标
        
        # 安装事件过滤器
        self.event_filter = EventFilter()
        self.installEventFilter(self.event_filter)

    def init_tray_icon(self):
        """初始化系统托盘图标"""
        # 创建托盘图标
        self.tray_icon = QSystemTrayIcon(self)
        
        try:
            self.tray_icon.setIcon(QIcon("./icon.ico"))  # 如果有自定义图标
        except:
            self.tray_icon.setIcon(QApplication.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon))
        
        # 创建托盘菜单
        tray_menu = QMenu()
        
        # 添加菜单项
        show_action = QAction("显示", self)
        show_action.triggered.connect(self.show)
        
        hide_action = QAction("隐藏", self)
        hide_action.triggered.connect(self.hide)
        
        settings_action = QAction("设置", self)
        settings_action.triggered.connect(self.open_settings)
        
        exit_action = QAction("退出", self)
        exit_action.triggered.connect(self.close_app)
        
        # 添加到菜单
        tray_menu.addAction(show_action)
        tray_menu.addAction(hide_action)
        tray_menu.addSeparator()
        tray_menu.addAction(settings_action)
        tray_menu.addSeparator()
        tray_menu.addAction(exit_action)
        
        # 设置托盘图标的菜单
        self.tray_icon.setContextMenu(tray_menu)
        
        # 设置托盘图标的提示文本
        self.tray_icon.setToolTip("eve desktop")
        
        # 连接托盘图标的激活信号
        self.tray_icon.activated.connect(self.tray_icon_activated)
        
        # 显示托盘图标
        self.tray_icon.show()
    
    def tray_icon_activated(self, reason):
        """处理托盘图标的激活事件"""
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            # 单击托盘图标
            if self.isVisible():
                self.hide()
            else:
                self.show()
                self.activateWindow()  # 激活窗口
    
    def close_app(self):
        """完全关闭应用程序"""
        self.tray_icon.hide()  # 隐藏托盘图标
        QApplication.quit()  # 退出应用程序
    
    def closeEvent(self, event):
        """重写关闭事件，使窗口关闭时只是隐藏而不是退出"""
        if self.tray_icon.isVisible():
            self.hide()
            event.ignore()  # 忽略关闭事件
        else:
            event.accept()  # 接受关闭事件，关闭应用程序

    def init_ui(self):
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool | Qt.WindowType.MSWindowsFixedSizeDialogHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(300, 200)  # 增加宽度以提供更多空间
        
        # 设置字体
        font_time = QFont("Caveat", 36, QFont.Weight.Bold)
        font_info = QFont("Caveat", 24)
        font_search = QFont("Caveat", 14)

        # 时间显示
        self.time_label = QLabel(self)
        self.time_label.setFont(font_time)
        self.time_label.setStyleSheet("color: rgba(0, 191, 255, 230);")
        self.time_label.move(20, 20)

        # 日期显示
        self.date_label = QLabel(self)
        self.date_label.setFont(font_info)
        self.date_label.setStyleSheet("color: rgba(180, 220, 255, 180);")
        self.date_label.move(20, 70)

        # 电池信息
        self.battery_label = QLabel(self)
        self.battery_label.setFont(font_info)
        self.battery_label.setStyleSheet("color: rgba(255, 160, 255, 200);")
        self.battery_label.move(20, 100)

        # 添加搜索图标按钮（替换原来的标签和下拉菜单）
        current_engine = self.search_engines[self.current_search_engine]
        self.search_icon_button = QPushButton(current_engine["icon"], self)
        self.search_icon_button.setFont(QFont("Segoe UI", 14))
        self.search_icon_button.setStyleSheet("""
            QPushButton {
                color: rgba(255, 255, 255, 200);
                background-color: transparent;
                border: none;
                padding: 2px;
            }
            QPushButton:hover {
                color: rgba(255, 255, 255, 230);
                background-color: rgba(255, 255, 255, 40);
                border-radius: 12px;
            }
        """)
        self.search_icon_button.setFixedSize(30, 30)
        self.search_icon_button.move(20, 160)
        self.search_icon_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.search_icon_button.setToolTip(f"当前搜索引擎: {current_engine['name']}")
        
        # 创建搜索引擎菜单
        self.search_engine_menu = QMenu(self)
        self.search_engine_menu.setStyleSheet("""
            QMenu {
                background-color: rgba(40, 40, 40, 220);
                color: white;
                border: 1px solid rgba(100, 100, 100, 150);
                border-radius: 5px;
            }
            QMenu::item {
                padding: 5px 20px 5px 20px;
            }
            QMenu::item:selected {
                background-color: rgba(0, 191, 255, 150);
            }
        """)
        
        # 添加搜索引擎选项到菜单
        for key, engine in self.search_engines.items():
            action = QAction(f"{engine['icon']} {engine['name']}", self)
            action.setData(key)
            self.search_engine_menu.addAction(action)
        
        # 连接菜单动作信号
        self.search_engine_menu.triggered.connect(self.change_search_engine_from_menu)
        
        # 连接按钮点击信号，显示菜单
        self.search_icon_button.clicked.connect(self.show_search_engine_menu)
        
        # 搜索输入框
        self.search_input = CustomLineEdit(self)
        self.search_input.setFont(font_search)
        self.search_input.setStyleSheet("""
            border: none;
            color: rgba(255, 255, 255, 220);
            background: transparent;
            padding: 4px 10px;
            selection-background-color: rgba(0, 191, 255, 150);
        """)
        self.search_input.setPlaceholderText(f"Search with {current_engine['name']}...")
        self.search_input.setFixedSize(200, 28)  # 增加宽度
        self.search_input.move(60, 160)  # 调整位置
        self.search_input.returnPressed.connect(self.perform_search)

        
        # 添加网易云音乐按钮 - 移到右上角
        self.music_button = MusicButton(self)
        self.music_button.setFixedSize(30, 30)
        self.music_button.move(260, 20)
        self.music_button.clicked.connect(self.open_netease_music)
        
        # 添加音乐控制按钮 - 竖直排列在右侧，更加紧凑
        # 上一曲按钮
        self.prev_button = MediaControlButton("△", "上一曲", self)
        self.prev_button.move(265, 60)
        self.prev_button.clicked.connect(self.prev_track)
        
        # 播放/暂停按钮
        self.play_pause_button = MediaControlButton("◼", "播放/暂停", self)
        self.play_pause_button.move(265, 90)
        self.play_pause_button.clicked.connect(self.play_pause_music)
        
        # 下一曲按钮
        self.next_button = MediaControlButton("▽", "下一曲", self)
        self.next_button.move(265, 120)
        self.next_button.clicked.connect(self.next_track)

        timer = QTimer(self)
        timer.timeout.connect(self.update_info)
        timer.start(1000)

        self.update_info()
    
    def change_search_engine(self, index):
        """切换搜索引擎"""
        engine_key = list(self.search_engines.keys())[index]
        self.current_search_engine = engine_key
        
        # 更新图标
        self.search_label.setText(self.search_engines[engine_key]["icon"])
        
        # 更新提示文本
        self.search_input.setPlaceholderText(f"Search with {self.search_engines[engine_key]['name']}...")
        
        # 保存设置
        self.settings["default_search_engine"] = engine_key
        save_settings(self.settings)

    def show_search_engine_menu(self):
        """显示搜索引擎菜单"""
        # 计算菜单显示位置
        pos = self.search_icon_button.mapToGlobal(QPoint(0, self.search_icon_button.height()))
        self.search_engine_menu.popup(pos)

    def change_search_engine_from_menu(self, action):
        """从菜单中切换搜索引擎"""
        engine_key = action.data()
        if engine_key in self.search_engines:
            self.current_search_engine = engine_key
            engine = self.search_engines[engine_key]
            
            # 更新按钮图标和提示
            self.search_icon_button.setText(engine["icon"])
            self.search_icon_button.setToolTip(f"当前搜索引擎: {engine['name']}")
            
            # 更新搜索框提示文本
            self.search_input.setPlaceholderText(f"Search with {engine['name']}...")
            
            # 保存设置
            self.settings["default_search_engine"] = engine_key
            save_settings(self.settings)
    
    def perform_search(self):
        """执行搜索操作"""
        # 获取当前搜索引擎的操作
        search_action = self.search_engines[self.current_search_engine]["action"]
        # 执行搜索
        search_action()
    
    def search_everything(self):
        """使用Everything搜索文件"""
        query = self.search_input.text().strip()
        if query and os.path.exists(self.everything_path):
            try:
                subprocess.Popen([self.everything_path, "-search", query])
                self.search_input.clear()
            except Exception as e:
                print(f"启动Everything失败: {e}")
    
    def search_bing(self):
        """使用Bing搜索"""
        query = self.search_input.text().strip()
        if query:
            url = f"https://www.bing.com/search?q={query}"
            self.open_browser(url)
            self.search_input.clear()
    
    # def search_google(self):
    #     """使用Google搜索"""
    #     query = self.search_input.text().strip()
    #     if query:
    #         url = f"https://www.google.com/search?q={query}"
    #         self.open_browser(url)
    #         self.search_input.clear()
    
    def search_chatgpt(self):
        """使用ChatGPT搜索"""
        query = self.search_input.text().strip()
        if query:
            url = f"https://chat.openai.com/?q={query}"
            self.open_browser(url)
            self.search_input.clear()
    
    def open_browser(self, url):
        """打开浏览器并访问指定URL"""
        try:
            if os.path.exists(self.browser_path):
                subprocess.Popen([self.browser_path, url])
            else:
                # 如果浏览器路径不存在，使用默认浏览器打开
                import webbrowser
                webbrowser.open(url)
        except Exception as e:
            print(f"打开浏览器失败: {e}")

    def contextMenuEvent(self, event):
        """处理右键菜单事件"""
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: rgba(40, 40, 40, 220);
                color: white;
                border: 1px solid rgba(100, 100, 100, 150);
                border-radius: 5px;
                padding: 5px;
            }
            QMenu::item {
                padding: 5px 20px;
                border-radius: 3px;
            }
            QMenu::item:selected {
                background-color: rgba(70, 130, 180, 150);
            }
        """)
        
        # 添加菜单项
        show_hide_action = menu.addAction("隐藏到托盘")
        show_hide_action.triggered.connect(self.hide)
        
        settings_action = menu.addAction("设置")
        settings_action.triggered.connect(self.open_settings)
        
        menu.addSeparator()
        
        exit_action = menu.addAction("退出")
        exit_action.triggered.connect(self.close_app)
        
        # 显示菜单
        menu.exec(event.globalPos())
    
    def open_settings(self):
        """打开设置对话框"""
        dialog = SettingsDialog(self)
        
        # 设置当前值
        dialog.autostart_checkbox.setChecked(self.settings.get("autostart", False))
        
        # 设置当前颜色
        dialog.color_button.setStyleSheet(f"background-color: {self.bg_color.name()}")
        
        # 设置当前透明度
        current_alpha = self.bg_color.alpha()
        dialog.transparency_slider.setValue(current_alpha)
        dialog.transparency_value_label.setText(str(current_alpha))
        
        # 设置当前路径
        if os.path.exists(self.netease_music_path):
            dialog.music_path_button.setText(os.path.basename(self.netease_music_path))
        
        if os.path.exists(self.everything_path):
            dialog.everything_path_button.setText(os.path.basename(self.everything_path))
        
        if os.path.exists(self.browser_path):
            dialog.browser_path_button.setText(os.path.basename(self.browser_path))
        
        # 设置当前搜索引擎
        for i in range(dialog.search_engine_combo.count()):
            if dialog.search_engine_combo.itemText(i).lower() == self.search_engines[self.current_search_engine]["name"].lower():
                dialog.search_engine_combo.setCurrentIndex(i)
                break
        
        if dialog.exec():
            # 保存自启动设置
            autostart = dialog.autostart_checkbox.isChecked()
            self.settings["autostart"] = autostart
            dialog.set_autostart(autostart)
            
            # 保存颜色设置
            if hasattr(dialog, 'selected_color'):
                self.bg_color = dialog.selected_color
                self.settings["bg_color"] = {
                    "r": self.bg_color.red(),
                    "g": self.bg_color.green(),
                    "b": self.bg_color.blue(),
                    "a": self.bg_color.alpha()
                }
            
            # 保存路径设置
            if hasattr(dialog, 'music_path'):
                self.netease_music_path = dialog.music_path
                self.settings["netease_music_path"] = dialog.music_path
            
            if hasattr(dialog, 'everything_path'):
                self.everything_path = dialog.everything_path
                self.settings["everything_path"] = dialog.everything_path
            
            # 保存浏览器路径
            if hasattr(dialog, 'browser_path'):
                self.browser_path = dialog.browser_path
                self.settings["browser_path"] = dialog.browser_path
            
            # 保存默认搜索引擎
            selected_engine = dialog.search_engine_combo.currentText().lower()
            for key, engine in self.search_engines.items():
                if engine["name"].lower() == selected_engine:
                    self.current_search_engine = key
                    self.settings["default_search_engine"] = key
                    
                    # 更新搜索图标和提示文本
                    self.search_icon_button.setText(engine["icon"])
                    self.search_icon_button.setToolTip(f"当前搜索引擎: {engine['name']}")
                    self.search_input.setPlaceholderText(f"Search with {engine['name']}...")
                    break
            
            # 保存设置
            save_settings(self.settings)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # 主背景 - 使用设置的颜色
        painter.setBrush(self.bg_color)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(self.rect(), 20, 20)
        
        # 搜索区域背景
        search_rect = QRectF(15, 155, 250, 35)
        search_color = QColor(30, 30, 30, 100)  # 稍微深一点的半透明背景
        painter.setBrush(search_color)
        painter.drawRoundedRect(search_rect, 15, 15)
        
        # 音乐控制区域背景 - 调整位置和大小
        music_rect = QRectF(260, 55, 35, 95)
        music_color = QColor(30, 30, 40, 80)  # 半透明背景
        painter.setBrush(music_color)
        painter.drawRoundedRect(music_rect, 12, 12)
    
    def update_info(self):
        now = datetime.now()
        self.time_label.setText(now.strftime("%H:%M:%S"))
        self.date_label.setText(now.strftime("%Y-%m-%d %A"))
        battery = psutil.sensors_battery()
        if battery:
            level = battery.percent
            charging = battery.power_plugged
            status = "⚡" if charging else "  "
            self.battery_label.setText(f"{status} Battery: {level}%")
        else:
            self.battery_label.setText("Battery: N/A")
    
    def search_everything(self):
        """使用 Everything 搜索输入的内容"""
        search_text = self.search_input.text().strip()
        if search_text:
            try:
                # 使用设置的路径
                subprocess.Popen(f'start "Everything" "{self.everything_path}" -search "{search_text}"', shell=True)
                self.search_input.clear()  # 清空搜索框
            except Exception as e:
                print(f"启动 Everything 搜索失败: {e}")
    
    def open_netease_music(self):
        """打开网易云音乐"""
        try:
            # 使用设置的路径
            subprocess.Popen(f'start "" "{self.netease_music_path}"', shell=True)
        except Exception as e:
            print(f"启动网易云音乐失败: {e}")
            # 尝试其他可能的安装路径
            try:
                subprocess.Popen('start "" "D:\\Program Files\\Netease\\CloudMusic\\cloudmusic.exe"', shell=True)
            except Exception as e2:
                print(f"备用路径启动网易云音乐失败: {e2}")

    def play_pause_music(self):
        """播放/暂停音乐"""
        # 模拟按下媒体播放/暂停键
        user32.keybd_event(VK_MEDIA_PLAY_PAUSE, 0, 0, 0)
        user32.keybd_event(VK_MEDIA_PLAY_PAUSE, 0, 2, 0)  # KEYEVENTF_KEYUP = 0x0002
    
    def next_track(self):
        """下一曲"""
        # 模拟按下媒体下一曲键
        user32.keybd_event(VK_MEDIA_NEXT_TRACK, 0, 0, 0)
        user32.keybd_event(VK_MEDIA_NEXT_TRACK, 0, 2, 0)  # KEYEVENTF_KEYUP = 0x0002
    
    def prev_track(self):
        """上一曲"""
        # 模拟按下媒体上一曲键
        user32.keybd_event(VK_MEDIA_PREV_TRACK, 0, 0, 0)
        user32.keybd_event(VK_MEDIA_PREV_TRACK, 0, 2, 0)  # KEYEVENTF_KEYUP = 0x0002


    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_position = event.globalPosition().toPoint()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton:
            delta = event.globalPosition().toPoint() - self.drag_position
            self.move(self.pos() + delta)
            self.drag_position = event.globalPosition().toPoint()
            event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon("./icon.ico")) 
    widget = AcrylicWidget()
    widget.show()
    sys.exit(app.exec())