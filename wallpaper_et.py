import sys
import psutil
import subprocess
import json
import os
from PyQt6.QtCore import Qt, QTimer, QPoint, QEvent, QObject, QRect, QRectF
from PyQt6.QtGui import QFont, QColor, QPainter, QGuiApplication, QPainterPath, QIcon, QAction
from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QLineEdit, QPushButton, QDialog, QMenu
from PyQt6.QtWidgets import QVBoxLayout, QHBoxLayout, QCheckBox, QColorDialog, QFileDialog, QSlider
from PyQt6.QtWidgets import QSystemTrayIcon, QComboBox, QListWidget
from PyQt6.QtCore import QPropertyAnimation, QEasingCurve, QPointF, QTimer, QSequentialAnimationGroup
from PyQt6.QtGui import QPainterPath, QPainter, QColor, QBrush, QPen
from PyQt6.QtWidgets import QTextEdit, QToolButton, QScrollArea, QFrame, QDateTimeEdit, QSpinBox
from datetime import datetime, timedelta

import ctypes

user32 = ctypes.windll.user32
VK_MEDIA_PLAY_PAUSE = 0xB3  # 播放/暂停媒体键
VK_MEDIA_NEXT_TRACK = 0xB0  # 下一曲媒体键
VK_MEDIA_PREV_TRACK = 0xB1  # 上一曲媒体键

# 设置文件路径
SETTINGS_FILE = "./wallpaper_settings.json"


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
    "default_search_engine": "everything",
    "quick_tools": [
        {"name": "VS Code", "path": "C:\\Program Files\\Microsoft VS Code\\Code.exe", "icon": "💻"},
        {"name": "Terminal", "path": "C:\\Windows\\System32\\cmd.exe", "icon": "🖥️"},
        {"name": "计算器", "path": "C:\\Windows\\System32\\calc.exe", "icon": "🧮"},
        {"name": "记事本", "path": "C:\\Windows\\System32\\notepad.exe", "icon": "📝"}
    ],
    "notes": "",  # 用于存储快速笔记内容
    "initial_position": {"x": None, "y": None},  # 添加初始位置配置
    "memos": [],  # 备忘录列表
    "reminder_settings": {
        "advance_minutes": 5,  # 提前提醒时间（分钟）
        "enable_sound": True,  # 是否启用声音提醒
        "enable_popup": True   # 是否启用弹窗提醒
    }
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

class QuickToolsDialog(QDialog):
    def __init__(self, tools, parent=None):
        super().__init__(parent)
        self.setWindowTitle("编辑常用工具")
        self.setFixedSize(500, 400)
        
        # 复制工具列表
        self.tools = tools.copy()
        
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
            QLineEdit {
                background-color: #3a3a3a;
                color: white;
                border: 1px solid #555555;
                border-radius: 3px;
                padding: 3px;
            }
            QListWidget {
                background-color: #3a3a3a;
                color: white;
                border: 1px solid #555555;
                border-radius: 3px;
            }
            QListWidget::item:selected {
                background-color: #5f9ea0;
            }
        """)
        
        layout = QVBoxLayout()
        
        # 工具列表
        self.tools_list = QListWidget()
        self.update_tools_list()
        layout.addWidget(self.tools_list)
        
        # 编辑区域
        edit_layout = QHBoxLayout()
        
        # 名称输入
        name_layout = QVBoxLayout()
        name_layout.addWidget(QLabel("名称:"))
        self.name_edit = QLineEdit()
        name_layout.addWidget(self.name_edit)
        edit_layout.addLayout(name_layout)
        
        # 图标输入
        icon_layout = QVBoxLayout()
        icon_layout.addWidget(QLabel("图标:"))
        self.icon_edit = QLineEdit()
        icon_layout.addWidget(self.icon_edit)
        edit_layout.addLayout(icon_layout)
        
        # 路径输入
        path_layout = QVBoxLayout()
        path_layout.addWidget(QLabel("路径:"))
        path_input_layout = QHBoxLayout()
        self.path_edit = QLineEdit()
        path_input_layout.addWidget(self.path_edit)
        self.browse_button = QPushButton("浏览...")
        self.browse_button.clicked.connect(self.browse_path)
        path_input_layout.addWidget(self.browse_button)
        path_layout.addLayout(path_input_layout)
        edit_layout.addLayout(path_layout)
        
        layout.addLayout(edit_layout)
        
        # 按钮区域
        buttons_layout = QHBoxLayout()
        
        self.add_button = QPushButton("添加")
        self.add_button.clicked.connect(self.add_tool)
        buttons_layout.addWidget(self.add_button)
        
        self.update_button = QPushButton("更新")
        self.update_button.clicked.connect(self.update_tool)
        self.update_button.setEnabled(False)  # 初始禁用
        buttons_layout.addWidget(self.update_button)
        
        self.delete_button = QPushButton("删除")
        self.delete_button.clicked.connect(self.delete_tool)
        self.delete_button.setEnabled(False)  # 初始禁用
        buttons_layout.addWidget(self.delete_button)
        
        self.up_button = QPushButton("上移")
        self.up_button.clicked.connect(self.move_tool_up)
        self.up_button.setEnabled(False)  # 初始禁用
        buttons_layout.addWidget(self.up_button)
        
        self.down_button = QPushButton("下移")
        self.down_button.clicked.connect(self.move_tool_down)
        self.down_button.setEnabled(False)  # 初始禁用
        buttons_layout.addWidget(self.down_button)
        
        layout.addLayout(buttons_layout)
        
        # 确定取消按钮
        dialog_buttons = QHBoxLayout()
        self.ok_button = QPushButton("确定")
        self.ok_button.clicked.connect(self.accept)
        self.cancel_button = QPushButton("取消")
        self.cancel_button.clicked.connect(self.reject)
        dialog_buttons.addWidget(self.ok_button)
        dialog_buttons.addWidget(self.cancel_button)
        layout.addLayout(dialog_buttons)
        
        self.setLayout(layout)
        
        # 连接列表选择信号
        self.tools_list.itemSelectionChanged.connect(self.selection_changed)
        self.tools_list.itemDoubleClicked.connect(self.item_double_clicked)
    
    def update_tools_list(self):
        """更新工具列表显示"""
        self.tools_list.clear()
        for tool in self.tools:
            self.tools_list.addItem(f"{tool['icon']} {tool['name']} - {tool['path']}")
    
    def selection_changed(self):
        """列表选择变化处理"""
        has_selection = len(self.tools_list.selectedItems()) > 0
        self.update_button.setEnabled(has_selection)
        self.delete_button.setEnabled(has_selection)
        
        # 上移按钮仅在非第一项被选中时启用
        self.up_button.setEnabled(has_selection and self.tools_list.currentRow() > 0)
        
        # 下移按钮仅在非最后一项被选中时启用
        self.down_button.setEnabled(has_selection and self.tools_list.currentRow() < self.tools_list.count() - 1)
        
        # 如果有选择，填充编辑区域
        if has_selection:
            index = self.tools_list.currentRow()
            tool = self.tools[index]
            self.name_edit.setText(tool["name"])
            self.icon_edit.setText(tool["icon"])
            self.path_edit.setText(tool["path"])
    
    def item_double_clicked(self, item):
        """双击列表项处理"""
        # 填充编辑区域
        index = self.tools_list.row(item)
        tool = self.tools[index]
        self.name_edit.setText(tool["name"])
        self.icon_edit.setText(tool["icon"])
        self.path_edit.setText(tool["path"])
    
    def browse_path(self):
        """浏览文件路径"""
        path, _ = QFileDialog.getOpenFileName(self, "选择程序", "", "可执行文件 (*.exe)")
        if path:
            self.path_edit.setText(path)
    
    def add_tool(self):
        """添加新工具"""
        name = self.name_edit.text().strip()
        icon = self.icon_edit.text().strip()
        path = self.path_edit.text().strip()
        
        if not name or not path:
            return
        
        # 使用默认图标如果未提供
        if not icon:
            icon = "🔧"
        
        # 添加到列表
        self.tools.append({"name": name, "icon": icon, "path": path})
        self.update_tools_list()
        
        # 清空输入框
        self.name_edit.clear()
        self.icon_edit.clear()
        self.path_edit.clear()
    
    def update_tool(self):
        """更新选中的工具"""
        if not self.tools_list.selectedItems():
            return
        
        index = self.tools_list.currentRow()
        name = self.name_edit.text().strip()
        icon = self.icon_edit.text().strip()
        path = self.path_edit.text().strip()
        
        if not name or not path:
            return
        
        # 使用默认图标如果未提供
        if not icon:
            icon = "🔧"
        
        # 更新工具
        self.tools[index] = {"name": name, "icon": icon, "path": path}
        self.update_tools_list()
    
    def delete_tool(self):
        """删除选中的工具"""
        if not self.tools_list.selectedItems():
            return
        
        index = self.tools_list.currentRow()
        del self.tools[index]
        self.update_tools_list()
        
        # 清空输入框
        self.name_edit.clear()
        self.icon_edit.clear()
        self.path_edit.clear()
    
    def move_tool_up(self):
        """上移选中的工具"""
        if not self.tools_list.selectedItems():
            return
        
        index = self.tools_list.currentRow()
        if index <= 0:
            return
        
        # 交换位置
        self.tools[index], self.tools[index-1] = self.tools[index-1], self.tools[index]
        self.update_tools_list()
        
        # 保持选择
        self.tools_list.setCurrentRow(index-1)
    
    def move_tool_down(self):
        """下移选中的工具"""
        if not self.tools_list.selectedItems():
            return
        
        index = self.tools_list.currentRow()
        if index >= len(self.tools) - 1:
            return
        
        # 交换位置
        self.tools[index], self.tools[index+1] = self.tools[index+1], self.tools[index]
        self.update_tools_list()
        
        # 保持选择
        self.tools_list.setCurrentRow(index+1)

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
        self.search_engine_combo.addItems(["Everything", "Bing", "ChatGPT", "Bilibili"])
        search_engine_layout.addWidget(self.search_engine_combo)
        layout.addLayout(search_engine_layout)
        
        # 提醒设置
        reminder_title = QLabel("提醒设置")
        reminder_title.setFont(QFont("Caveat", 12, QFont.Weight.Bold))
        reminder_title.setStyleSheet("color: #5f9ea0; margin-top: 10px;")
        layout.addWidget(reminder_title)
        
        # 提前提醒时间设置
        advance_layout = QHBoxLayout()
        advance_layout.addWidget(QLabel("提前提醒时间(分钟):"))
        self.advance_slider = QSlider(Qt.Orientation.Horizontal)
        self.advance_slider.setMinimum(1)
        self.advance_slider.setMaximum(60)
        self.advance_slider.setValue(5)  # 默认5分钟
        self.advance_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.advance_slider.setTickInterval(5)
        self.advance_value_label = QLabel("5")
        advance_layout.addWidget(self.advance_slider)
        advance_layout.addWidget(self.advance_value_label)
        layout.addLayout(advance_layout)
        
        # 连接滑动条的值变化信号
        self.advance_slider.valueChanged.connect(self.update_advance_value)
        
        # 提醒选项
        self.enable_sound_checkbox = QCheckBox("启用声音提醒")
        self.enable_sound_checkbox.setChecked(True)
        layout.addWidget(self.enable_sound_checkbox)
        
        self.enable_popup_checkbox = QCheckBox("启用弹窗提醒")
        self.enable_popup_checkbox.setChecked(True)
        layout.addWidget(self.enable_popup_checkbox)
        
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

    def update_advance_value(self, value):
        """更新提前提醒时间值显示"""
        self.advance_value_label.setText(str(value))
        # 如果已经设置了提前提醒时间，更新提醒设置
        if hasattr(self, 'advance_slider'):
            self.settings["reminder_settings"]["advance_minutes"] = value
            save_settings(self.settings)


class AcrylicWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.is_playing = False  # 添加播放状态变量
        
        # 启用拖放
        self.setAcceptDrops(True)
        
        # 加载设置
        self.settings = load_settings()

        # 应用初始位置设置
        initial_pos = self.settings.get("initial_position", {"x": None, "y": None})
        if initial_pos["x"] is not None and initial_pos["y"] is not None:
            self.move(initial_pos["x"], initial_pos["y"])
        
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
            "chatgpt": {"name": "ChatGPT", "icon": "🤖", "action": self.search_chatgpt},
            "bilibili": {"name": "Bilibili", "icon": "📺", "action": self.search_bilibili},
        }
        
        # 当前搜索引擎
        self.current_search_engine = self.settings.get("default_search_engine", "everything")

        # 左侧边栏状态
        self.sidebar_expanded = False

        self.init_ui()
        self.init_tray_icon()  # 初始化系统托盘图标
        
        # 安装事件过滤器
        self.event_filter = EventFilter()
        self.installEventFilter(self.event_filter)
        
        # 初始化提醒管理器
        self.reminder_manager = ReminderManager(self)

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
    
    def closeEvent(self, event):
        """重写关闭事件，使窗口关闭时只是隐藏而不是退出"""
        if self.tray_icon.isVisible():
            self.hide()
            # 如果边栏已展开，也隐藏边栏
            if hasattr(self, 'sidebar_expanded') and self.sidebar_expanded:
                self.sidebar.hide()
            event.ignore()  # 忽略关闭事件
        else:
            event.accept()  # 接受关闭事件，关闭应用程序

    def close_app(self):
        """完全关闭应用程序"""
        # 如果边栏已创建，关闭边栏
        if hasattr(self, 'sidebar'):
            self.sidebar.close()
        self.tray_icon.hide()  # 隐藏托盘图标
        QApplication.quit()  # 退出应用程序

    def init_ui(self):
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool | Qt.WindowType.MSWindowsFixedSizeDialogHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(340, 200)  # 增加宽度以提供更多空间
        
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
        self.music_button.move(self.width() - 40, 20)
        self.music_button.clicked.connect(self.open_netease_music)
        
        # 添加音乐控制按钮 - 竖直排列在右侧，更加紧凑
        # 上一曲按钮
        self.prev_button = MediaControlButton("△", "上一曲", self)
        self.prev_button.move(self.width() - 40, 60)
        self.prev_button.clicked.connect(self.prev_track)
        
        # 播放/暂停按钮
        self.play_pause_button = MediaControlButton("◼", "播放/暂停", self)
        self.play_pause_button.move(self.width() - 40, 90)
        self.play_pause_button.clicked.connect(self.play_pause_music)
        
        # 下一曲按钮
        self.next_button = MediaControlButton("▽", "下一曲", self)
        self.next_button.move(self.width() - 40, 120)
        self.next_button.clicked.connect(self.next_track)

        # 添加下拉按钮
        self.expand_button = QPushButton("▼", self)
        self.expand_button.setFont(QFont("Segoe UI", 10))
        self.expand_button.setStyleSheet("""
            QPushButton {
                color: rgba(200, 200, 255, 200);
                background-color: transparent;
                border: none;
            }
            QPushButton:hover {
                color: rgba(220, 220, 255, 230);
            }
        """)
        self.expand_button.setFixedSize(20, 20)
        self.expand_button.move(self.width() - 35, 165)
        self.expand_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.expand_button.setToolTip("展开/收起拓展功能")
        self.expand_button.clicked.connect(self.toggle_extension_panel)
        

        # 创建拓展功能面板（初始隐藏）
        self.extension_panel = QWidget(self)
        self.extension_panel.setStyleSheet("""
            background-color: rgba(30, 30, 40, 180);
            border-radius: 10px;
        """)
        self.extension_panel.setFixedWidth(self.width() - 20)
        self.extension_panel.setFixedHeight(300)  # 拓展面板高度
        self.extension_panel.move(10, self.height())  # 初始位置在窗口下方（隐藏状态）
        
        # 拓展面板布局
        extension_layout = QVBoxLayout(self.extension_panel)
        extension_layout.setContentsMargins(10, 10, 10, 10)
        extension_layout.setSpacing(10)
        
        # 添加标题
        tools_title = QLabel("常用工具", self.extension_panel)
        tools_title.setFont(QFont("Caveat", 14, QFont.Weight.Bold))
        tools_title.setStyleSheet("color: rgba(200, 220, 255, 220);")
        extension_layout.addWidget(tools_title)
        
        # 常用工具区域
        self.tools_container = QWidget(self.extension_panel)
        tools_layout = QHBoxLayout(self.tools_container)
        tools_layout.setContentsMargins(0, 0, 0, 0)
        tools_layout.setSpacing(10)
        
        # 从设置中加载常用工具
        self.quick_tools = self.settings.get("quick_tools", DEFAULT_SETTINGS["quick_tools"])
        for tool in self.quick_tools:
            tool_button = self.create_tool_button(tool)
            tools_layout.addWidget(tool_button)
        
        # 添加编辑工具按钮
        edit_tools_button = QPushButton("⚙️", self.tools_container)
        edit_tools_button.setToolTip("编辑常用工具")
        edit_tools_button.setFixedSize(40, 40)
        edit_tools_button.setStyleSheet("""
            QPushButton {
                color: rgba(180, 180, 180, 200);
                background-color: rgba(60, 60, 70, 150);
                border-radius: 5px;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: rgba(80, 80, 90, 180);
            }
        """)
        edit_tools_button.clicked.connect(self.edit_quick_tools)
        tools_layout.addWidget(edit_tools_button)
        
        # 添加弹性空间
        tools_layout.addStretch()
        extension_layout.addWidget(self.tools_container)
        
        # 添加分隔线
        separator = QFrame(self.extension_panel)
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet("background-color: rgba(100, 100, 120, 100);")
        extension_layout.addWidget(separator)
        
        # 添加备忘录标题和按钮
        memo_layout = QHBoxLayout()
        memo_title = QLabel("备忘录", self.extension_panel)
        memo_title.setFont(QFont("Caveat", 14, QFont.Weight.Bold))
        memo_title.setStyleSheet("color: rgba(200, 220, 255, 220);")
        memo_layout.addWidget(memo_title)
        
        # 添加备忘录管理按钮
        memo_button = QPushButton("📝", self.extension_panel)
        memo_button.setToolTip("管理备忘录")
        memo_button.setFixedSize(30, 30)
        memo_button.setStyleSheet("""
            QPushButton {
                color: rgba(220, 220, 220, 220);
                background-color: rgba(50, 50, 60, 150);
                border-radius: 5px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: rgba(70, 70, 80, 180);
            }
        """)
        memo_button.clicked.connect(self.manage_memos)
        memo_layout.addWidget(memo_button)
        
        # 添加弹性空间
        memo_layout.addStretch()
        extension_layout.addLayout(memo_layout)
        
        # 添加快速笔记标题
        notes_title = QLabel("快速笔记", self.extension_panel)
        notes_title.setFont(QFont("Caveat", 14, QFont.Weight.Bold))
        notes_title.setStyleSheet("color: rgba(200, 220, 255, 220);")
        extension_layout.addWidget(notes_title)
        
        # 添加快速笔记文本编辑区
        self.notes_edit = QTextEdit(self.extension_panel)
        self.notes_edit.setStyleSheet("""
            QTextEdit {
                background-color: rgba(40, 40, 50, 150);
                color: rgba(220, 220, 220, 220);
                border-radius: 5px;
                padding: 5px;
                selection-background-color: rgba(70, 130, 180, 150);
            }
        """)
        self.notes_edit.setFont(QFont("Consolas", 10))
        self.notes_edit.setPlaceholderText("在这里记录临时想法、代码片段或待办事项...")
        
        # 从设置中加载笔记内容
        self.notes_edit.setText(self.settings.get("notes", ""))
        self.notes_edit.textChanged.connect(self.save_notes)
        
        extension_layout.addWidget(self.notes_edit)
        
        # 拓展面板动画
        self.panel_animation = QPropertyAnimation(self.extension_panel, b"geometry")
        self.panel_animation.setDuration(300)
        self.panel_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        # 面板状态
        self.panel_expanded = False

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

    def search_bilibili(self):
        """使用Bilibili搜索"""
        query = self.search_input.text().strip()
        if query:
            url = f"https://search.bilibili.com/all?keyword={query}"
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

    # 添加窗口移动事件处理，确保边栏跟随主窗口移动
    def moveEvent(self, event):
        """窗口移动事件"""
        super().moveEvent(event)
        
        # 如果边栏已展开，更新边栏位置
        if hasattr(self, 'sidebar_expanded') and self.sidebar_expanded:
            sidebar_x = self.x() - self.sidebar.width() - 10
            sidebar_y = self.y() + 10
            self.sidebar.move(sidebar_x, sidebar_y)

    def toggle_extension_panel(self):
        """切换拓展功能面板的显示/隐藏状态"""
        if self.panel_expanded:
            # 收起面板
            self.collapse_panel()
        else:
            # 展开面板
            self.expand_panel()

    def expand_panel(self):
        """展开拓展功能面板"""
        # 计算展开后的几何形状
        new_height = self.height() + self.extension_panel.height() + 10
        self.setFixedSize(self.width(), new_height)
        
        # 设置面板位置动画
        start_rect = self.extension_panel.geometry()
        end_rect = QRect(10, self.height() - self.extension_panel.height() - 10, 
                        self.extension_panel.width(), self.extension_panel.height())
        
        self.panel_animation.setStartValue(start_rect)
        self.panel_animation.setEndValue(end_rect)
        self.panel_animation.start()
        
        # 更新按钮文本
        self.expand_button.setText("▲")
        self.panel_expanded = True

    def collapse_panel(self):
        """收起拓展功能面板"""
        # 设置面板位置动画
        start_rect = self.extension_panel.geometry()
        end_rect = QRect(10, self.height(), 
                        self.extension_panel.width(), self.extension_panel.height())
        
        self.panel_animation.setStartValue(start_rect)
        self.panel_animation.setEndValue(end_rect)
        self.panel_animation.start()
        
        # 连接动画完成信号
        self.panel_animation.finished.connect(self.resize_after_collapse)
        
        # 更新按钮文本
        self.expand_button.setText("▼")
        self.panel_expanded = False

    def resize_after_collapse(self):
        """面板收起后调整窗口大小"""
        # 断开信号连接，避免重复调用
        self.panel_animation.finished.disconnect(self.resize_after_collapse)
        
        # 恢复原始窗口大小
        self.setFixedSize(self.width(), 200)

    def create_tool_button(self, tool):
        """创建工具快捷按钮"""
        button = QPushButton(tool["icon"], self.tools_container)
        button.setToolTip(tool["name"])
        button.setFixedSize(40, 40)
        button.setStyleSheet("""
            QPushButton {
                color: rgba(220, 220, 220, 220);
                background-color: rgba(50, 50, 60, 150);
                border-radius: 5px;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: rgba(70, 70, 80, 180);
            }
            QPushButton:pressed {
                background-color: rgba(40, 40, 50, 150);
            }
        """)
        
        # 存储工具路径
        button.setProperty("tool_path", tool["path"])
        
        # 连接点击事件
        button.clicked.connect(lambda: self.open_tool(tool["path"]))
        
        return button

    def open_tool(self, path):
        """打开工具"""
        try:
            subprocess.Popen(path)
        except Exception as e:
            print(f"打开工具失败: {e}")

    def edit_quick_tools(self):
        """编辑常用工具"""
        dialog = QuickToolsDialog(self.quick_tools, self)
        if dialog.exec():
            # 更新工具列表
            self.quick_tools = dialog.tools
            self.settings["quick_tools"] = self.quick_tools
            save_settings(self.settings)
            
            # 重新创建工具按钮
            # 清除现有按钮
            for i in reversed(range(self.tools_container.layout().count())):
                item = self.tools_container.layout().itemAt(i)
                if item.widget():
                    item.widget().deleteLater()
            
            # 添加新按钮
            for tool in self.quick_tools:
                tool_button = self.create_tool_button(tool)
                self.tools_container.layout().addWidget(tool_button)
            
            # 添加编辑按钮
            edit_tools_button = QPushButton("⚙️", self.tools_container)
            edit_tools_button.setToolTip("编辑常用工具")
            edit_tools_button.setFixedSize(40, 40)
            edit_tools_button.setStyleSheet("""
                QPushButton {
                    color: rgba(180, 180, 180, 200);
                    background-color: rgba(60, 60, 70, 150);
                    border-radius: 5px;
                    font-size: 16px;
                }
                QPushButton:hover {
                    background-color: rgba(80, 80, 90, 180);
                }
            """)
            edit_tools_button.clicked.connect(self.edit_quick_tools)
            self.tools_container.layout().addWidget(edit_tools_button)
            
            # 添加弹性空间
            self.tools_container.layout().addStretch()

    def save_notes(self):
        """保存笔记内容"""
        self.settings["notes"] = self.notes_edit.toPlainText()
        save_settings(self.settings)

    def manage_memos(self):
        """管理备忘录"""
        memos = self.settings.get("memos", [])
        dialog = MemoDialog(memos, self)
        if dialog.exec():
            # 更新备忘录列表
            self.settings["memos"] = dialog.memos
            save_settings(self.settings)

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

        set_position_action = QAction("记录初始位置", self)
        set_position_action.triggered.connect(self.set_current_position_as_initial)
        menu.addAction(set_position_action)

        settings_action = menu.addAction("设置")
        settings_action.triggered.connect(self.open_settings)
            
        menu.addSeparator()
            
        exit_action = menu.addAction("退出")
        exit_action.triggered.connect(self.close_app)
            
        # 显示菜单
        menu.exec(event.globalPos())
    
    def set_current_position_as_initial(self):
        """设置当前位置为初始位置"""
        current_pos = self.pos()
        self.settings["initial_position"] = {"x": current_pos.x(), "y": current_pos.y()}
        save_settings(self.settings)
        QApplication.beep()

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
        
        # 设置提醒设置
        reminder_settings = self.settings.get("reminder_settings", DEFAULT_SETTINGS["reminder_settings"])
        dialog.advance_slider.setValue(reminder_settings.get("advance_minutes", 5))
        dialog.advance_value_label.setText(str(reminder_settings.get("advance_minutes", 5)))
        dialog.enable_sound_checkbox.setChecked(reminder_settings.get("enable_sound", True))
        dialog.enable_popup_checkbox.setChecked(reminder_settings.get("enable_popup", True))
        
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
            
            # 保存提醒设置
            self.settings["reminder_settings"] = {
                "advance_minutes": dialog.advance_slider.value(),
                "enable_sound": dialog.enable_sound_checkbox.isChecked(),
                "enable_popup": dialog.enable_popup_checkbox.isChecked()
            }
            
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

class MemoDialog(QDialog):
    def __init__(self, memos, parent=None):
        super().__init__(parent)
        self.setWindowTitle("备忘录管理")
        self.setFixedSize(600, 500)
        
        # 复制备忘录列表
        self.memos = memos.copy()
        
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
            QLineEdit, QTextEdit {
                background-color: #3a3a3a;
                color: white;
                border: 1px solid #555555;
                border-radius: 3px;
                padding: 3px;
            }
            QListWidget {
                background-color: #3a3a3a;
                color: white;
                border: 1px solid #555555;
                border-radius: 3px;
            }
            QListWidget::item:selected {
                background-color: #5f9ea0;
            }
            QCheckBox {
                color: white;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
            }
            QCheckBox::indicator:unchecked {
                border: 1px solid #555555;
                background-color: #3a3a3a;
            }
            QCheckBox::indicator:checked {
                border: 1px solid #5f9ea0;
                background-color: #5f9ea0;
            }
        """)
        
        layout = QVBoxLayout()
        
        # 添加使用提示
        tip_label = QLabel("💡 提示：勾选'设置提醒'后可以设置提醒时间，应用会在指定时间前提醒您")
        tip_label.setStyleSheet("color: #5f9ea0; font-size: 10px; padding: 5px;")
        tip_label.setWordWrap(True)
        layout.addWidget(tip_label)
        
        # 备忘录列表
        self.memos_list = QListWidget()
        self.update_memos_list()
        layout.addWidget(self.memos_list)
        
        # 编辑区域
        edit_layout = QVBoxLayout()
        
        # 标题输入
        title_layout = QHBoxLayout()
        title_layout.addWidget(QLabel("标题:"))
        self.title_edit = QLineEdit()
        title_layout.addWidget(self.title_edit)
        edit_layout.addLayout(title_layout)
        
        # 内容输入
        content_layout = QVBoxLayout()
        content_layout.addWidget(QLabel("内容:"))
        self.content_edit = QTextEdit()
        self.content_edit.setMaximumHeight(80)
        content_layout.addWidget(self.content_edit)
        edit_layout.addLayout(content_layout)
        
        # 提醒时间设置
        reminder_layout = QHBoxLayout()
        self.reminder_checkbox = QCheckBox("设置提醒")
        reminder_layout.addWidget(self.reminder_checkbox)
        
        reminder_layout.addWidget(QLabel("提醒时间:"))
        self.datetime_edit = CustomDateTimeEdit()
        self.datetime_edit.setDateTime(datetime.now())
        self.datetime_edit.setEnabled(False)
        reminder_layout.addWidget(self.datetime_edit)
        
        # 连接复选框信号
        self.reminder_checkbox.toggled.connect(self.datetime_edit.setEnabled)
        
        edit_layout.addLayout(reminder_layout)
        
        layout.addLayout(edit_layout)
        
        # 按钮区域
        buttons_layout = QHBoxLayout()
        
        self.add_button = QPushButton("添加")
        self.add_button.clicked.connect(self.add_memo)
        buttons_layout.addWidget(self.add_button)
        
        self.update_button = QPushButton("更新")
        self.update_button.clicked.connect(self.update_memo)
        self.update_button.setEnabled(False)
        buttons_layout.addWidget(self.update_button)
        
        self.delete_button = QPushButton("删除")
        self.delete_button.clicked.connect(self.delete_memo)
        self.delete_button.setEnabled(False)
        buttons_layout.addWidget(self.delete_button)
        
        self.reset_reminder_button = QPushButton("重置提醒")
        self.reset_reminder_button.clicked.connect(self.reset_reminder)
        self.reset_reminder_button.setEnabled(False)
        self.reset_reminder_button.setToolTip("重置已提醒状态，允许再次提醒")
        buttons_layout.addWidget(self.reset_reminder_button)
        
        layout.addLayout(buttons_layout)
        
        # 确定取消按钮
        dialog_buttons = QHBoxLayout()
        self.ok_button = QPushButton("确定")
        self.ok_button.clicked.connect(self.accept)
        self.cancel_button = QPushButton("取消")
        self.cancel_button.clicked.connect(self.reject)
        dialog_buttons.addWidget(self.ok_button)
        dialog_buttons.addWidget(self.cancel_button)
        layout.addLayout(dialog_buttons)
        
        self.setLayout(layout)
        
        # 连接列表选择信号
        self.memos_list.itemSelectionChanged.connect(self.selection_changed)
        self.memos_list.itemDoubleClicked.connect(self.item_double_clicked)
    
    def update_memos_list(self):
        """更新备忘录列表显示"""
        self.memos_list.clear()
        for memo in self.memos:
            title = memo.get('title', '无标题')
            reminder_time = memo.get('reminder_time')
            reminder_shown = memo.get('reminder_shown', False)
            
            if reminder_time:
                if reminder_shown:
                    reminder_str = f" (提醒: {reminder_time} - 已提醒)"
                else:
                    reminder_str = f" (提醒: {reminder_time} - 待提醒)"
            else:
                reminder_str = ""
            self.memos_list.addItem(f"📝 {title}{reminder_str}")
    
    def selection_changed(self):
        """列表选择变化处理"""
        has_selection = len(self.memos_list.selectedItems()) > 0
        self.update_button.setEnabled(has_selection)
        self.delete_button.setEnabled(has_selection)
        
        # 检查是否有提醒时间且已提醒过
        if has_selection:
            index = self.memos_list.currentRow()
            memo = self.memos[index]
            has_reminder = bool(memo.get('reminder_time'))
            reminder_shown = memo.get('reminder_shown', False)
            self.reset_reminder_button.setEnabled(has_reminder and reminder_shown)
        else:
            self.reset_reminder_button.setEnabled(False)
        
        if has_selection:
            index = self.memos_list.currentRow()
            memo = self.memos[index]
            self.title_edit.setText(memo.get('title', ''))
            self.content_edit.setText(memo.get('content', ''))
            
            # 设置提醒时间
            reminder_time = memo.get('reminder_time')
            if reminder_time:
                try:
                    dt = datetime.fromisoformat(reminder_time)
                    self.datetime_edit.setDateTime(dt)
                    self.reminder_checkbox.setChecked(True)
                except:
                    self.reminder_checkbox.setChecked(False)
            else:
                self.reminder_checkbox.setChecked(False)
    
    def item_double_clicked(self, item):
        """双击列表项处理"""
        index = self.memos_list.row(item)
        memo = self.memos[index]
        self.title_edit.setText(memo.get('title', ''))
        self.content_edit.setText(memo.get('content', ''))
        
        # 设置提醒时间
        reminder_time = memo.get('reminder_time')
        if reminder_time:
            try:
                dt = datetime.fromisoformat(reminder_time)
                self.datetime_edit.setDateTime(dt)
                self.reminder_checkbox.setChecked(True)
            except:
                self.reminder_checkbox.setChecked(False)
        else:
            self.reminder_checkbox.setChecked(False)
    
    def add_memo(self):
        """添加新备忘录"""
        title = self.title_edit.text().strip()
        content = self.content_edit.toPlainText().strip()
        
        if not title:
            return
        
        memo = {
            'title': title,
            'content': content,
            'created_time': datetime.now().isoformat()
        }
        
        # 添加提醒时间
        if self.reminder_checkbox.isChecked():
            memo['reminder_time'] = self.datetime_edit.dateTime().isoformat()
        
        self.memos.append(memo)
        self.update_memos_list()
        
        # 清空输入框
        self.title_edit.clear()
        self.content_edit.clear()
        self.reminder_checkbox.setChecked(False)
    
    def update_memo(self):
        """更新选中的备忘录"""
        if not self.memos_list.selectedItems():
            return
        
        index = self.memos_list.currentRow()
        title = self.title_edit.text().strip()
        content = self.content_edit.toPlainText().strip()
        
        if not title:
            return
        
        memo = {
            'title': title,
            'content': content,
            'created_time': self.memos[index].get('created_time', datetime.now().isoformat())
        }
        
        # 添加提醒时间
        if self.reminder_checkbox.isChecked():
            memo['reminder_time'] = self.datetime_edit.dateTime().isoformat()
        
        self.memos[index] = memo
        self.update_memos_list()
    
    def delete_memo(self):
        """删除选中的备忘录"""
        if not self.memos_list.selectedItems():
            return
        
        index = self.memos_list.currentRow()
        del self.memos[index]
        self.update_memos_list()
        
        # 清空输入框
        self.title_edit.clear()
        self.content_edit.clear()
        self.reminder_checkbox.setChecked(False)

    def reset_reminder(self):
        """重置提醒状态"""
        if not self.memos_list.selectedItems():
            return
        
        index = self.memos_list.currentRow()
        memo = self.memos[index]
        
        # 重置提醒状态
        memo['reminder_shown'] = False
        memo['advance_shown'] = False
        
        self.update_memos_list()
        
        # 更新按钮状态
        self.selection_changed()
        
        # 保存到设置文件
        if hasattr(self.parent(), 'settings'):
            parent_settings = self.parent().settings
            # 更新父窗口设置中的备忘录
            parent_memos = parent_settings.get('memos', [])
            if index < len(parent_memos):
                parent_memos[index] = memo
                save_settings(parent_settings)

class ReminderDialog(QDialog):
    def __init__(self, memo, parent=None):
        super().__init__(parent)
        self.setWindowTitle("备忘录提醒")
        self.setFixedSize(400, 200)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        # 设置窗口样式
        self.setStyleSheet("""
            QDialog {
                background-color: #2c2c2c;
                color: white;
                border: 2px solid #5f9ea0;
                border-radius: 10px;
            }
            QLabel {
                color: white;
            }
            QPushButton {
                background-color: #3a3a3a;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #4a4a4a;
            }
            QTextEdit {
                background-color: #3a3a3a;
                color: white;
                border: 1px solid #555555;
                border-radius: 5px;
                padding: 5px;
            }
        """)
        
        layout = QVBoxLayout()
        
        # 标题
        title_label = QLabel(f"⏰ 备忘录提醒: {memo.get('title', '无标题')}")
        title_label.setFont(QFont("Caveat", 14, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #5f9ea0;")
        layout.addWidget(title_label)
        
        # 内容
        content_label = QLabel("内容:")
        layout.addWidget(content_label)
        
        content_edit = QTextEdit()
        content_edit.setPlainText(memo.get('content', ''))
        content_edit.setReadOnly(True)
        content_edit.setMaximumHeight(80)
        layout.addWidget(content_edit)
        
        # 按钮
        button_layout = QHBoxLayout()
        
        snooze_button = QPushButton("稍后提醒 (5分钟)")
        snooze_button.clicked.connect(lambda: self.snooze_reminder(5))
        button_layout.addWidget(snooze_button)
        
        dismiss_button = QPushButton("关闭")
        dismiss_button.clicked.connect(self.accept)
        button_layout.addWidget(dismiss_button)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
        # 存储备忘录信息
        self.memo = memo
    
    def snooze_reminder(self, minutes):
        """稍后提醒"""
        # 更新提醒时间
        new_time = datetime.now() + timedelta(minutes=minutes)
        self.memo['reminder_time'] = new_time.isoformat()
        self.accept()

class ReminderManager(QObject):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.reminder_timer = QTimer()
        self.reminder_timer.timeout.connect(self.check_reminders)
        self.reminder_timer.start(30000)  # 每30秒检查一次
        print("提醒管理器已初始化，每30秒检查一次提醒")
    
    def check_reminders(self):
        """检查备忘录提醒"""
        if not hasattr(self.parent, 'settings'):
            print("警告：父窗口没有settings属性")
            return
        
        # 重新加载settings以确保获取最新数据
        self.parent.settings = load_settings()
        settings = self.parent.settings
        memos = settings.get('memos', [])
        reminder_settings = settings.get('reminder_settings', {})
        advance_minutes = reminder_settings.get('advance_minutes', 5)
        
        current_time = datetime.now()
        advance_time = current_time + timedelta(minutes=advance_minutes)
        
        print(f"检查提醒 - 当前时间: {current_time.strftime('%H:%M:%S')}, 备忘录数量: {len(memos)}")
        
        settings_changed = False  # 标记设置是否有变化
        
        for i, memo in enumerate(memos):
            reminder_time = memo.get('reminder_time')
            if not reminder_time:
                continue
            
            try:
                reminder_dt = datetime.fromisoformat(reminder_time)
                print(f"备忘录 {i+1}: {memo.get('title', '无标题')} - 提醒时间: {reminder_dt.strftime('%H:%M:%S')}")
                print(f"时间比较: 当前={current_time}, 提醒={reminder_dt}, 提前={advance_time}")
                print(f"是否到了提醒时间: {current_time >= reminder_dt}")
                print(f"是否需要提前提醒: {advance_time >= reminder_dt and not memo.get('advance_shown')}")
                print(f"是否已经提醒过: {memo.get('reminder_shown', False)}")
                
                # 检查是否到了提醒时间且还没显示过提醒
                if current_time >= reminder_dt and not memo.get('reminder_shown', False):
                    print(f"触发正式提醒: {memo.get('title', '无标题')}")
                    self.show_reminder(memo)
                    # 标记为已提醒
                    memo['reminder_shown'] = True
                    settings_changed = True
                
                # 检查是否需要提前提醒（只有在还没到正式提醒时间时才显示）
                elif advance_time >= reminder_dt and not memo.get('advance_shown'):
                    print(f"触发提前提醒: {memo.get('title', '无标题')}")
                    self.show_advance_reminder(memo, advance_minutes)
                    memo['advance_shown'] = True
                    settings_changed = True
                    
            except Exception as e:
                print(f"处理提醒时间失败: {e}")
        
        # 如果有设置变化，保存到文件
        if settings_changed:
            save_settings(settings)
    
    def show_reminder(self, memo):
        """显示提醒对话框"""
        if not hasattr(self.parent, 'settings'):
            return
        
        settings = self.parent.settings
        reminder_settings = settings.get('reminder_settings', {})
        
        print(f"显示提醒对话框: {memo.get('title', '无标题')}")
        
        # 显示弹窗提醒
        if reminder_settings.get('enable_popup', True):
            dialog = ReminderDialog(memo, self.parent)
            dialog.exec()
        
        # 播放声音提醒
        if reminder_settings.get('enable_sound', True):
            QApplication.beep()
    
    def show_advance_reminder(self, memo, advance_minutes):
        """显示提前提醒"""
        if not hasattr(self.parent, 'settings'):
            return
        
        settings = self.parent.settings
        reminder_settings = settings.get('reminder_settings', {})
        
        print(f"显示提前提醒: {memo.get('title', '无标题')}")
        
        # 显示提前提醒弹窗
        if reminder_settings.get('enable_popup', True):
            advance_dialog = QDialog(self.parent)
            advance_dialog.setWindowTitle("")
            advance_dialog.setFixedSize(300, 150)
            advance_dialog.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
            
            advance_dialog.setStyleSheet("""
                QDialog {
                    background-color: #2c2c2c;
                    color: white;
                    border: 2px solid #ffa500;
                    border-radius: 10px;
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
            """)
            
            layout = QVBoxLayout()
            
            title_label = QLabel(f"⏰ {advance_minutes}分钟后有备忘录提醒")
            title_label.setFont(QFont("Caveat", 12, QFont.Weight.Bold))
            title_label.setStyleSheet("color: #ffa500;")
            layout.addWidget(title_label)
            
            content_label = QLabel(f"标题: {memo.get('title', '无标题')}")
            layout.addWidget(content_label)
            
            ok_button = QPushButton("知道了")
            ok_button.clicked.connect(advance_dialog.accept)
            layout.addWidget(ok_button)
            
            advance_dialog.setLayout(layout)
            advance_dialog.exec()
        
        # 播放声音提醒
        if reminder_settings.get('enable_sound', True):
            QApplication.beep()

class CustomDateTimeEdit(QWidget):
    """自定义日期时间选择器 - 简化版本"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        
    def init_ui(self):
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        
        # 时间输入框
        self.time_edit = QLineEdit()
        self.time_edit.setPlaceholderText("2025-06-12 14:30")
        self.time_edit.setFixedWidth(150)
        self.time_edit.setText(datetime.now().strftime("%Y-%m-%d %H:%M"))
        layout.addWidget(self.time_edit)
        
        # 快速时间按钮
        quick_layout = QHBoxLayout()
        quick_layout.setSpacing(2)
        
        # 5分钟后
        btn_5min = QPushButton("5分钟")
        btn_5min.setFixedSize(50, 25)
        btn_5min.clicked.connect(lambda: self.set_quick_time(5))
        quick_layout.addWidget(btn_5min)
        
        # 10分钟后
        btn_10min = QPushButton("10分钟")
        btn_10min.setFixedSize(50, 25)
        btn_10min.clicked.connect(lambda: self.set_quick_time(10))
        quick_layout.addWidget(btn_10min)
        
        # 30分钟后
        btn_30min = QPushButton("30分钟")
        btn_30min.setFixedSize(50, 25)
        btn_30min.clicked.connect(lambda: self.set_quick_time(30))
        quick_layout.addWidget(btn_30min)
        
        # 1小时后
        btn_1hour = QPushButton("1小时")
        btn_1hour.setFixedSize(50, 25)
        btn_1hour.clicked.connect(lambda: self.set_quick_time(60))
        quick_layout.addWidget(btn_1hour)
        
        layout.addLayout(quick_layout)
        self.setLayout(layout)
        
        # 设置样式
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
        """设置快速时间"""
        future_time = datetime.now() + timedelta(minutes=minutes)
        self.time_edit.setText(future_time.strftime("%Y-%m-%d %H:%M"))
    
    def setDateTime(self, dt):
        """设置日期时间"""
        self.time_edit.setText(dt.strftime("%Y-%m-%d %H:%M"))
    
    def dateTime(self):
        """获取日期时间"""
        try:
            time_str = self.time_edit.text().strip()
            if not time_str:
                return datetime.now()
            
            # 尝试解析时间字符串
            if len(time_str) == 16:  # "2025-06-12 14:30" 格式
                return datetime.strptime(time_str, "%Y-%m-%d %H:%M")
            elif len(time_str) == 19:  # "2025-06-12 14:30:00" 格式
                return datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
            else:
                # 如果格式不对，返回当前时间
                return datetime.now()
        except ValueError:
            # 如果解析失败，返回当前时间
            return datetime.now()
    
    def setEnabled(self, enabled):
        """设置启用状态"""
        super().setEnabled(enabled)
        self.time_edit.setEnabled(enabled)
        for i in range(self.layout().count()):
            item = self.layout().itemAt(i)
            if isinstance(item, QHBoxLayout):
                for j in range(item.count()):
                    child_item = item.itemAt(j)
                    if child_item.widget():
                        child_item.widget().setEnabled(enabled)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon("./icon.ico")) 
    
    # 设置全局工具提示样式 - 白底黑字
    app.setStyleSheet("""
        QToolTip {
            background-color: white;
            color: white;
            border: 1px solid #cccccc;
            border-radius: 4px;
            padding: 4px 8px;
            font-size: 12px;
        }
    """)
    
    widget = AcrylicWidget()
    widget.show()
    sys.exit(app.exec())