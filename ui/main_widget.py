import sys
import os
import subprocess
import psutil
import numpy as np
from datetime import datetime, timedelta
from PyQt6.QtCore import Qt, QTimer, QPoint, QEvent, QObject, QRect, QRectF, QSize, QPropertyAnimation, QEasingCurve, QPointF, QSequentialAnimationGroup
from PyQt6.QtGui import QFont, QColor, QPainter, QGuiApplication, QPainterPath, QIcon, QAction
from PyQt6.QtWidgets import QWidget, QLabel, QPushButton, QMenu, QVBoxLayout, QHBoxLayout, QTextEdit, QFrame, QDialog, QSystemTrayIcon, QComboBox, QListWidget, QLineEdit, QCheckBox, QColorDialog, QFileDialog, QSlider, QToolButton, QScrollArea, QDateTimeEdit, QSpinBox

from core.settings import load_settings, save_settings
from core.music import AudioVisualizer
from core.reminder import ReminderManager
from ui.dialogs import SettingsDialog, QuickToolsDialog, MemoDialog, ReminderDialog
from ui.custom_widgets import CustomLineEdit, MediaControlButton, MusicButton

import ctypes
user32 = ctypes.windll.user32
VK_MEDIA_PLAY_PAUSE = 0xB3
VK_MEDIA_NEXT_TRACK = 0xB0
VK_MEDIA_PREV_TRACK = 0xB1

AUDIO_AVAILABLE = True
try:
    import pyaudio
except ImportError:
    AUDIO_AVAILABLE = False

class EventFilter(QObject):
    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.WindowStateChange:
            if obj.windowState() & Qt.WindowState.WindowMinimized:
                obj.setWindowState(Qt.WindowState.WindowNoState)
                return True
        return super().eventFilter(obj, event)

class AcrylicWidget(QWidget):
    """主窗口类，负责主 UI 和主要逻辑。"""
    def __init__(self):
        super().__init__()
        self.is_playing = False
        self.setAcceptDrops(True)
        self.settings = load_settings()
        initial_pos = self.settings.get("initial_position", {"x": None, "y": None})
        if initial_pos["x"] is not None and initial_pos["y"] is not None:
            self.move(initial_pos["x"], initial_pos["y"])
        self.netease_music_path = self.settings["netease_music_path"]
        self.everything_path = self.settings["everything_path"]
        self.browser_path = self.settings["browser_path"]
        color_settings = self.settings["bg_color"]
        self.bg_color = QColor(
            color_settings["r"],
            color_settings["g"],
            color_settings["b"],
            color_settings["a"]
        )
        self.search_engines = {
            "everything": {"name": "Everything", "icon": "🔍", "action": self.search_everything},
            "bing": {"name": "Bing", "icon": "🌐", "action": self.search_bing},
            "chatgpt": {"name": "ChatGPT", "icon": "🤖", "action": self.search_chatgpt},
            "bilibili": {"name": "Bilibili", "icon": "📺", "action": self.search_bilibili},
        }
        self.current_search_engine = self.settings.get("default_search_engine", "everything")
        self.sidebar_expanded = False
        self.init_ui()
        self.init_tray_icon()
        self.event_filter = EventFilter()
        self.installEventFilter(self.event_filter)
        self.reminder_manager = ReminderManager(self)
        if AUDIO_AVAILABLE:
            self.audio_visualizer = AudioVisualizer(self)
            self.frequency_data = []
        else:
            self.audio_visualizer = None
            self.frequency_data = np.zeros(64)

    def init_ui(self):
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool | Qt.WindowType.MSWindowsFixedSizeDialogHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(340, 200)

        font_time = QFont("Caveat", 36, QFont.Weight.Bold)
        font_info = QFont("Caveat", 24)
        font_search = QFont("Caveat", 14)

        self.time_label = QLabel(self)
        self.time_label.setFont(font_time)
        self.time_label.setStyleSheet("color: rgba(0, 191, 255, 230);")
        self.time_label.move(20, 20)

        self.date_label = QLabel(self)
        self.date_label.setFont(font_info)
        self.date_label.setStyleSheet("color: rgba(180, 220, 255, 180);")
        self.date_label.move(20, 70)

        self.battery_label = QLabel(self)
        self.battery_label.setFont(font_info)
        self.battery_label.setStyleSheet("color: rgba(255, 160, 255, 200);")
        self.battery_label.move(20, 100)

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
        for key, engine in self.search_engines.items():
            action = QAction(f"{engine['icon']} {engine['name']}", self)
            action.setData(key)
            self.search_engine_menu.addAction(action)
        self.search_engine_menu.triggered.connect(self.change_search_engine_from_menu)
        self.search_icon_button.clicked.connect(self.show_search_engine_menu)

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
        self.search_input.setFixedSize(200, 28)
        self.search_input.move(60, 160)
        self.search_input.returnPressed.connect(self.perform_search)

        self.music_button = MusicButton(self)
        self.music_button.setFixedSize(30, 30)
        self.music_button.move(self.width() - 40, 20)
        self.music_button.clicked.connect(self.open_netease_music)

        self.prev_button = MediaControlButton("△", "上一曲", self)
        self.prev_button.move(self.width() - 40, 60)
        self.prev_button.clicked.connect(self.prev_track)

        self.play_pause_button = MediaControlButton("◼", "播放/暂停", self)
        self.play_pause_button.move(self.width() - 40, 90)
        self.play_pause_button.clicked.connect(self.play_pause_music)

        self.next_button = MediaControlButton("▽", "下一曲", self)
        self.next_button.move(self.width() - 40, 120)
        self.next_button.clicked.connect(self.next_track)

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

        self.extension_panel = QWidget(self)
        self.extension_panel.setStyleSheet("""
            background-color: rgba(30, 30, 40, 180);
            border-radius: 10px;
        """)
        self.extension_panel.setFixedWidth(self.width() - 20)
        self.extension_panel.setFixedHeight(300)
        self.extension_panel.move(10, self.height())

        extension_layout = QVBoxLayout(self.extension_panel)
        extension_layout.setContentsMargins(10, 10, 10, 10)
        extension_layout.setSpacing(10)

        tools_title = QLabel("常用工具", self.extension_panel)
        tools_title.setFont(QFont("Caveat", 14, QFont.Weight.Bold))
        tools_title.setStyleSheet("color: rgba(200, 220, 255, 220);")
        extension_layout.addWidget(tools_title)

        self.tools_container = QWidget(self.extension_panel)
        tools_layout = QHBoxLayout(self.tools_container)
        tools_layout.setContentsMargins(0, 0, 0, 0)
        tools_layout.setSpacing(10)
        self.quick_tools = self.settings.get("quick_tools", [])
        for tool in self.quick_tools:
            tool_button = self.create_tool_button(tool)
            tools_layout.addWidget(tool_button)
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
        tools_layout.addStretch()
        extension_layout.addWidget(self.tools_container)
        separator = QFrame(self.extension_panel)
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet("background-color: rgba(100, 100, 120, 100);")
        extension_layout.addWidget(separator)
        memo_layout = QHBoxLayout()
        memo_title = QLabel("备忘录", self.extension_panel)
        memo_title.setFont(QFont("Caveat", 14, QFont.Weight.Bold))
        memo_title.setStyleSheet("color: rgba(200, 220, 255, 220);")
        memo_layout.addWidget(memo_title)
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
        memo_layout.addStretch()
        extension_layout.addLayout(memo_layout)
        notes_title = QLabel("快速笔记", self.extension_panel)
        notes_title.setFont(QFont("Caveat", 14, QFont.Weight.Bold))
        notes_title.setStyleSheet("color: rgba(200, 220, 255, 220);")
        extension_layout.addWidget(notes_title)
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
        self.notes_edit.setText(self.settings.get("notes", ""))
        self.notes_edit.textChanged.connect(self.save_notes)
        extension_layout.addWidget(self.notes_edit)
        self.panel_animation = QPropertyAnimation(self.extension_panel, b"geometry")
        self.panel_animation.setDuration(300)
        self.panel_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.panel_expanded = False
        timer = QTimer(self)
        timer.timeout.connect(self.update_info)
        timer.start(1000)
        self.update_info()

    def init_tray_icon(self):
        self.tray_icon = QSystemTrayIcon(self)
        try:
            self.tray_icon.setIcon(QIcon("./icon.ico"))
        except:
            from PyQt6.QtWidgets import QStyle, QApplication
            self.tray_icon.setIcon(QApplication.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon))
        tray_menu = QMenu()
        show_action = QAction("显示", self)
        show_action.triggered.connect(self.show)
        hide_action = QAction("隐藏", self)
        hide_action.triggered.connect(self.hide)
        settings_action = QAction("设置", self)
        settings_action.triggered.connect(self.open_settings)
        exit_action = QAction("退出", self)
        exit_action.triggered.connect(self.close_app)
        tray_menu.addAction(show_action)
        tray_menu.addAction(hide_action)
        tray_menu.addSeparator()
        tray_menu.addAction(settings_action)
        tray_menu.addSeparator()
        tray_menu.addAction(exit_action)
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.setToolTip("eve desktop")
        self.tray_icon.activated.connect(self.tray_icon_activated)
        self.tray_icon.show()

    def tray_icon_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            if self.isVisible():
                self.hide()
            else:
                self.show()
                self.activateWindow()

    def closeEvent(self, event):
        if self.tray_icon.isVisible():
            self.hide()
            if hasattr(self, 'sidebar_expanded') and self.sidebar_expanded:
                self.sidebar.hide()
            event.ignore()
        else:
            event.accept()

    def close_app(self):
        if hasattr(self, 'audio_visualizer') and self.audio_visualizer:
            self.audio_visualizer.stop()
        if hasattr(self, 'sidebar'):
            self.sidebar.close()
        self.tray_icon.hide()
        from PyQt6.QtWidgets import QApplication
        QApplication.quit()

    def change_search_engine(self, index):
        engine_key = list(self.search_engines.keys())[index]
        self.current_search_engine = engine_key
        self.search_icon_button.setText(self.search_engines[engine_key]["icon"])
        self.search_icon_button.setToolTip(f"当前搜索引擎: {self.search_engines[engine_key]['name']}")
        self.search_input.setPlaceholderText(f"Search with {self.search_engines[engine_key]['name']}...")
        self.settings["default_search_engine"] = engine_key
        save_settings(self.settings)

    def show_search_engine_menu(self):
        pos = self.search_icon_button.mapToGlobal(QPoint(0, self.search_icon_button.height()))
        self.search_engine_menu.popup(pos)

    def change_search_engine_from_menu(self, action):
        engine_key = action.data()
        if engine_key in self.search_engines:
            self.current_search_engine = engine_key
            engine = self.search_engines[engine_key]
            self.search_icon_button.setText(engine["icon"])
            self.search_icon_button.setToolTip(f"当前搜索引擎: {engine['name']}")
            self.search_input.setPlaceholderText(f"Search with {engine['name']}...")
            self.settings["default_search_engine"] = engine_key
            save_settings(self.settings)

    def perform_search(self):
        search_action = self.search_engines[self.current_search_engine]["action"]
        search_action()

    def search_everything(self):
        query = self.search_input.text().strip()
        if query and os.path.exists(self.everything_path):
            try:
                subprocess.Popen([self.everything_path, "-search", query])
                self.search_input.clear()
            except Exception as e:
                print(f"启动Everything失败: {e}")

    def search_bing(self):
        query = self.search_input.text().strip()
        if query:
            url = f"https://www.bing.com/search?q={query}"
            self.open_browser(url)
            self.search_input.clear()

    def search_bilibili(self):
        query = self.search_input.text().strip()
        if query:
            url = f"https://search.bilibili.com/all?keyword={query}"
            self.open_browser(url)
            self.search_input.clear()

    def search_chatgpt(self):
        query = self.search_input.text().strip()
        if query:
            url = f"https://chat.openai.com/?q={query}"
            self.open_browser(url)
            self.search_input.clear()

    def open_browser(self, url):
        try:
            if os.path.exists(self.browser_path):
                subprocess.Popen([self.browser_path, url])
            else:
                import webbrowser
                webbrowser.open(url)
        except Exception as e:
            print(f"打开浏览器失败: {e}")

    def moveEvent(self, event):
        super().moveEvent(event)
        if hasattr(self, 'sidebar_expanded') and self.sidebar_expanded:
            sidebar_x = self.x() - self.sidebar.width() - 10
            sidebar_y = self.y() + 10
            self.sidebar.move(sidebar_x, sidebar_y)

    def toggle_extension_panel(self):
        if self.panel_expanded:
            self.collapse_panel()
        else:
            self.expand_panel()

    def expand_panel(self):
        new_height = self.height() + self.extension_panel.height() + 10
        self.setFixedSize(self.width(), new_height)
        start_rect = self.extension_panel.geometry()
        end_rect = QRect(10, self.height() - self.extension_panel.height() - 10, self.extension_panel.width(), self.extension_panel.height())
        self.panel_animation.setStartValue(start_rect)
        self.panel_animation.setEndValue(end_rect)
        self.panel_animation.start()
        self.expand_button.setText("▲")
        self.panel_expanded = True

    def collapse_panel(self):
        start_rect = self.extension_panel.geometry()
        end_rect = QRect(10, self.height(), self.extension_panel.width(), self.extension_panel.height())
        self.panel_animation.setStartValue(start_rect)
        self.panel_animation.setEndValue(end_rect)
        self.panel_animation.start()
        self.panel_animation.finished.connect(self.resize_after_collapse)
        self.expand_button.setText("▼")
        self.panel_expanded = False

    def resize_after_collapse(self):
        self.panel_animation.finished.disconnect(self.resize_after_collapse)
        self.setFixedSize(self.width(), 200)

    def create_tool_button(self, tool):
        button = QPushButton(self.tools_container)
        button.setToolTip(tool["name"])
        button.setFixedSize(40, 40)
        icon_path = tool.get("icon", "")
        if icon_path and (icon_path.endswith(('.ico', '.png', '.jpg', '.jpeg')) or os.path.exists(icon_path)):
            try:
                if os.path.exists(icon_path):
                    icon = QIcon(icon_path)
                    button.setIcon(icon)
                    button.setIconSize(QSize(24, 24))
                    button.setText("")
                else:
                    button.setText("🔧")
            except Exception as e:
                print(f"加载图标失败 {icon_path}: {e}")
                button.setText("🔧")
        else:
            button.setText(icon_path if icon_path else "🔧")
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
        button.setProperty("tool_path", tool["path"])
        button.clicked.connect(lambda: self.open_tool(tool["path"]))
        return button

    def open_tool(self, path):
        try:
            subprocess.Popen(path)
        except Exception as e:
            print(f"打开工具失败: {e}")

    def edit_quick_tools(self):
        dialog = QuickToolsDialog(self.quick_tools, self)
        if dialog.exec():
            self.quick_tools = dialog.tools
            self.settings["quick_tools"] = self.quick_tools
            save_settings(self.settings)
            for i in reversed(range(self.tools_container.layout().count())):
                item = self.tools_container.layout().itemAt(i)
                if item.widget():
                    item.widget().deleteLater()
            for tool in self.quick_tools:
                tool_button = self.create_tool_button(tool)
                self.tools_container.layout().addWidget(tool_button)
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
            self.tools_container.layout().addStretch()

    def save_notes(self):
        self.settings["notes"] = self.notes_edit.toPlainText()
        save_settings(self.settings)

    def manage_memos(self):
        memos = self.settings.get("memos", [])
        dialog = MemoDialog(memos, self)
        if dialog.exec():
            self.settings["memos"] = dialog.memos
            save_settings(self.settings)

    def contextMenuEvent(self, event):
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
        menu.exec(event.globalPos())

    def set_current_position_as_initial(self):
        current_pos = self.pos()
        self.settings["initial_position"] = {"x": current_pos.x(), "y": current_pos.y()}
        save_settings(self.settings)
        from PyQt6.QtWidgets import QApplication
        QApplication.beep()

    def open_settings(self):
        dialog = SettingsDialog(self)
        dialog.autostart_checkbox.setChecked(self.settings.get("autostart", False))
        dialog.color_button.setStyleSheet(f"background-color: {self.bg_color.name()}")
        current_alpha = self.bg_color.alpha()
        dialog.transparency_slider.setValue(current_alpha)
        dialog.transparency_value_label.setText(str(current_alpha))
        import os
        if os.path.exists(self.netease_music_path):
            dialog.music_path_button.setText(os.path.basename(self.netease_music_path))
        if os.path.exists(self.everything_path):
            dialog.everything_path_button.setText(os.path.basename(self.everything_path))
        if os.path.exists(self.browser_path):
            dialog.browser_path_button.setText(os.path.basename(self.browser_path))
        for i in range(dialog.search_engine_combo.count()):
            if dialog.search_engine_combo.itemText(i).lower() == self.search_engines[self.current_search_engine]["name"].lower():
                dialog.search_engine_combo.setCurrentIndex(i)
                break
        reminder_settings = self.settings.get("reminder_settings", {})
        dialog.advance_slider.setValue(reminder_settings.get("advance_minutes", 5))
        dialog.advance_value_label.setText(str(reminder_settings.get("advance_minutes", 5)))
        dialog.enable_sound_checkbox.setChecked(reminder_settings.get("enable_sound", True))
        dialog.enable_popup_checkbox.setChecked(reminder_settings.get("enable_popup", True))
        if dialog.exec():
            autostart = dialog.autostart_checkbox.isChecked()
            self.settings["autostart"] = autostart
            dialog.set_autostart(autostart)
            if hasattr(dialog, 'selected_color'):
                self.bg_color = dialog.selected_color
                self.settings["bg_color"] = {
                    "r": self.bg_color.red(),
                    "g": self.bg_color.green(),
                    "b": self.bg_color.blue(),
                    "a": self.bg_color.alpha()
                }
            if hasattr(dialog, 'music_path'):
                self.netease_music_path = dialog.music_path
                self.settings["netease_music_path"] = dialog.music_path
            if hasattr(dialog, 'everything_path'):
                self.everything_path = dialog.everything_path
                self.settings["everything_path"] = dialog.everything_path
            if hasattr(dialog, 'browser_path'):
                self.browser_path = dialog.browser_path
                self.settings["browser_path"] = dialog.browser_path
            selected_engine = dialog.search_engine_combo.currentText().lower()
            for key, engine in self.search_engines.items():
                if engine["name"].lower() == selected_engine:
                    self.current_search_engine = key
                    self.settings["default_search_engine"] = key
                    self.search_icon_button.setText(engine["icon"])
                    self.search_icon_button.setToolTip(f"当前搜索引擎: {engine['name']}")
                    self.search_input.setPlaceholderText(f"Search with {engine['name']}...")
                    break
            self.settings["reminder_settings"] = {
                "advance_minutes": dialog.advance_slider.value(),
                "enable_sound": dialog.enable_sound_checkbox.isChecked(),
                "enable_popup": dialog.enable_popup_checkbox.isChecked()
            }
            save_settings(self.settings)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(self.bg_color)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(self.rect(), 20, 20)
        self.draw_audio_waveform(painter)
        search_rect = QRectF(15, 155, 250, 35)
        search_color = QColor(30, 30, 30, 100)
        painter.setBrush(search_color)
        painter.drawRoundedRect(search_rect, 15, 15)
        music_rect = QRectF(260, 55, 35, 95)
        music_color = QColor(30, 30, 40, 80)
        painter.setBrush(music_color)
        painter.drawRoundedRect(music_rect, 12, 12)

    def draw_audio_waveform(self, painter):
        if not hasattr(self, 'settings') or not self.settings.get('audio_waveform', {}).get('enable_waveform', True):
            return
        waveform_settings = self.settings.get('audio_waveform', {})
        color_settings = waveform_settings.get('waveform_color', {'r': 0, 'g': 191, 'b': 255, 'a': 180})
        sensitivity = waveform_settings.get('waveform_sensitivity', 1.0)
        if self.audio_visualizer and self.audio_visualizer.is_running:
            self.frequency_data = self.audio_visualizer.get_frequency_data()
        if len(self.frequency_data) > 0:
            painter.setPen(Qt.PenStyle.NoPen)
            width = self.width()
            height = self.height()
            bar_height = 40
            bar_width = width / len(self.frequency_data)
            bar_y = height - bar_height - 10
            for i, freq in enumerate(self.frequency_data):
                adjusted_freq = freq * sensitivity
                bar_x = i * bar_width
                bar_w = bar_width * 0.8
                bar_h = adjusted_freq * bar_height
                alpha = int(color_settings['a'] * (0.3 + 0.7 * adjusted_freq))
                bar_color = QColor(
                    color_settings['r'],
                    color_settings['g'],
                    color_settings['b'],
                    alpha
                )
                painter.setBrush(bar_color)
                bar_rect = QRectF(bar_x + bar_width * 0.1, bar_y + bar_height - bar_h, bar_w, bar_h)
                painter.drawRoundedRect(bar_rect, 3, 3)

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

    def open_netease_music(self):
        try:
            subprocess.Popen(f'start "" "{self.netease_music_path}"', shell=True)
        except Exception as e:
            print(f"启动网易云音乐失败: {e}")
            try:
                subprocess.Popen('start "" "D:\\Program Files\\Netease\\CloudMusic\\cloudmusic.exe"', shell=True)
            except Exception as e2:
                print(f"备用路径启动网易云音乐失败: {e2}")

    def play_pause_music(self):
        user32.keybd_event(VK_MEDIA_PLAY_PAUSE, 0, 0, 0)
        user32.keybd_event(VK_MEDIA_PLAY_PAUSE, 0, 2, 0)

    def next_track(self):
        user32.keybd_event(VK_MEDIA_NEXT_TRACK, 0, 0, 0)
        user32.keybd_event(VK_MEDIA_NEXT_TRACK, 0, 2, 0)

    def prev_track(self):
        user32.keybd_event(VK_MEDIA_PREV_TRACK, 0, 0, 0)
        user32.keybd_event(VK_MEDIA_PREV_TRACK, 0, 2, 0)

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