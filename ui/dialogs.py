from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit, QListWidget, QTextEdit, QCheckBox, QColorDialog, QFileDialog, QSlider, QComboBox, QFrame
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QRect, QTimer
from PyQt6.QtGui import QFont
from datetime import datetime, timedelta
from ui.custom_widgets import CustomDateTimeEdit

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("设置")
        self.setFixedSize(400, 400)
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
        self.autostart_checkbox = QCheckBox("开机自动启动")
        layout.addWidget(self.autostart_checkbox)
        color_layout = QHBoxLayout()
        color_layout.addWidget(QLabel("背景颜色:"))
        self.color_button = QPushButton("选择颜色")
        self.color_button.clicked.connect(self.choose_color)
        color_layout.addWidget(self.color_button)
        layout.addLayout(color_layout)
        transparency_layout = QHBoxLayout()
        transparency_layout.addWidget(QLabel("透明度:"))
        self.transparency_slider = QSlider(Qt.Orientation.Horizontal)
        self.transparency_slider.setMinimum(0)
        self.transparency_slider.setMaximum(255)
        self.transparency_slider.setValue(120)
        self.transparency_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.transparency_slider.setTickInterval(25)
        self.transparency_value_label = QLabel("120")
        transparency_layout.addWidget(self.transparency_slider)
        transparency_layout.addWidget(self.transparency_value_label)
        layout.addLayout(transparency_layout)
        self.transparency_slider.valueChanged.connect(self.update_transparency_value)
        path_layout = QHBoxLayout()
        path_layout.addWidget(QLabel("网易云音乐路径:"))
        self.music_path_button = QPushButton("选择路径")
        self.music_path_button.clicked.connect(self.choose_music_path)
        path_layout.addWidget(self.music_path_button)
        layout.addLayout(path_layout)
        everything_layout = QHBoxLayout()
        everything_layout.addWidget(QLabel("Everything路径:"))
        self.everything_path_button = QPushButton("选择路径")
        self.everything_path_button.clicked.connect(self.choose_everything_path)
        everything_layout.addWidget(self.everything_path_button)
        layout.addLayout(everything_layout)
        browser_layout = QHBoxLayout()
        browser_layout.addWidget(QLabel("浏览器路径:"))
        self.browser_path_button = QPushButton("选择路径")
        self.browser_path_button.clicked.connect(self.choose_browser_path)
        browser_layout.addWidget(self.browser_path_button)
        layout.addLayout(browser_layout)
        search_engine_layout = QHBoxLayout()
        search_engine_layout.addWidget(QLabel("默认搜索引擎:"))
        self.search_engine_combo = QComboBox()
        self.search_engine_combo.addItems(["Everything", "Bing", "ChatGPT", "Bilibili"])
        search_engine_layout.addWidget(self.search_engine_combo)
        layout.addLayout(search_engine_layout)
        reminder_title = QLabel("提醒设置")
        reminder_title.setFont(QFont("Caveat", 12, QFont.Weight.Bold))
        reminder_title.setStyleSheet("color: #5f9ea0; margin-top: 10px;")
        layout.addWidget(reminder_title)
        advance_layout = QHBoxLayout()
        advance_layout.addWidget(QLabel("提前提醒时间(分钟):"))
        self.advance_slider = QSlider(Qt.Orientation.Horizontal)
        self.advance_slider.setMinimum(1)
        self.advance_slider.setMaximum(60)
        self.advance_slider.setValue(5)
        self.advance_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.advance_slider.setTickInterval(5)
        self.advance_value_label = QLabel("5")
        advance_layout.addWidget(self.advance_slider)
        advance_layout.addWidget(self.advance_value_label)
        layout.addLayout(advance_layout)
        self.advance_slider.valueChanged.connect(self.update_advance_value)
        self.enable_sound_checkbox = QCheckBox("启用声音提醒")
        self.enable_sound_checkbox.setChecked(True)
        layout.addWidget(self.enable_sound_checkbox)
        self.enable_popup_checkbox = QCheckBox("启用弹窗提醒")
        self.enable_popup_checkbox.setChecked(True)
        layout.addWidget(self.enable_popup_checkbox)
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
        self.transparency_value_label.setText(str(value))
        if hasattr(self, 'selected_color'):
            self.selected_color.setAlpha(value)
            self.color_button.setStyleSheet(f"background-color: {self.selected_color.name()}")
    def choose_color(self):
        color_dialog = QColorDialog(self)
        color_dialog.setWindowTitle("选择背景颜色")
        if color_dialog.exec() == QDialog.DialogCode.Accepted:
            color = color_dialog.currentColor()
            if color.isValid():
                self.selected_color = color
                self.selected_color.setAlpha(self.transparency_slider.value())
                self.color_button.setStyleSheet(f"background-color: {self.selected_color.name()}")
    def set_autostart(self, enable):
        import winreg
        import sys
        import os
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
        self.advance_value_label.setText(str(value))
        if hasattr(self, 'advance_slider'):
            self.settings["reminder_settings"]["advance_minutes"] = value
            # save_settings(self.settings) 

class QuickToolsDialog(QDialog):
    def __init__(self, tools, parent=None):
        super().__init__(parent)
        self.setWindowTitle("编辑常用工具")
        self.setFixedSize(500, 400)
        self.tools = tools.copy()
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
        self.tools_list = QListWidget()
        self.update_tools_list()
        layout.addWidget(self.tools_list)
        edit_layout = QHBoxLayout()
        name_layout = QVBoxLayout()
        name_layout.addWidget(QLabel("名称:"))
        self.name_edit = QLineEdit()
        name_layout.addWidget(self.name_edit)
        edit_layout.addLayout(name_layout)
        icon_layout = QVBoxLayout()
        icon_layout.addWidget(QLabel("图标:"))
        icon_input_layout = QHBoxLayout()
        self.icon_edit = QLineEdit()
        self.icon_edit.setPlaceholderText("输入emoji或选择图标文件")
        icon_input_layout.addWidget(self.icon_edit)
        self.browse_icon_button = QPushButton("选择图标...")
        self.browse_icon_button.clicked.connect(self.browse_icon)
        icon_input_layout.addWidget(self.browse_icon_button)
        icon_layout.addLayout(icon_input_layout)
        edit_layout.addLayout(icon_layout)
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
        buttons_layout = QHBoxLayout()
        self.add_button = QPushButton("添加")
        self.add_button.clicked.connect(self.add_tool)
        buttons_layout.addWidget(self.add_button)
        self.update_button = QPushButton("更新")
        self.update_button.clicked.connect(self.update_tool)
        self.update_button.setEnabled(False)
        buttons_layout.addWidget(self.update_button)
        self.delete_button = QPushButton("删除")
        self.delete_button.clicked.connect(self.delete_tool)
        self.delete_button.setEnabled(False)
        buttons_layout.addWidget(self.delete_button)
        self.up_button = QPushButton("上移")
        self.up_button.clicked.connect(self.move_tool_up)
        self.up_button.setEnabled(False)
        buttons_layout.addWidget(self.up_button)
        self.down_button = QPushButton("下移")
        self.down_button.clicked.connect(self.move_tool_down)
        self.down_button.setEnabled(False)
        buttons_layout.addWidget(self.down_button)
        layout.addLayout(buttons_layout)
        dialog_buttons = QHBoxLayout()
        self.ok_button = QPushButton("确定")
        self.ok_button.clicked.connect(self.accept)
        self.cancel_button = QPushButton("取消")
        self.cancel_button.clicked.connect(self.reject)
        dialog_buttons.addWidget(self.ok_button)
        dialog_buttons.addWidget(self.cancel_button)
        layout.addLayout(dialog_buttons)
        self.setLayout(layout)
        self.tools_list.itemSelectionChanged.connect(self.selection_changed)
        self.tools_list.itemDoubleClicked.connect(self.item_double_clicked)
    def update_tools_list(self):
        self.tools_list.clear()
        for tool in self.tools:
            self.tools_list.addItem(f"{tool['icon']} {tool['name']} - {tool['path']}")
    def selection_changed(self):
        has_selection = len(self.tools_list.selectedItems()) > 0
        self.update_button.setEnabled(has_selection)
        self.delete_button.setEnabled(has_selection)
        self.up_button.setEnabled(has_selection and self.tools_list.currentRow() > 0)
        self.down_button.setEnabled(has_selection and self.tools_list.currentRow() < self.tools_list.count() - 1)
        if has_selection:
            index = self.tools_list.currentRow()
            tool = self.tools[index]
            self.name_edit.setText(tool["name"])
            self.icon_edit.setText(tool["icon"])
            self.path_edit.setText(tool["path"])
    def item_double_clicked(self, item):
        index = self.tools_list.row(item)
        tool = self.tools[index]
        self.name_edit.setText(tool["name"])
        self.icon_edit.setText(tool["icon"])
        self.path_edit.setText(tool["path"])
    def browse_icon(self):
        path, _ = QFileDialog.getOpenFileName(self, "选择图标文件", "", "图标文件 (*.ico *.png *.jpg *.jpeg)")
        if path:
            self.icon_edit.setText(path)
    def browse_path(self):
        path, _ = QFileDialog.getOpenFileName(self, "选择程序", "", "可执行文件 (*.exe)")
        if path:
            self.path_edit.setText(path)
    def add_tool(self):
        name = self.name_edit.text().strip()
        icon = self.icon_edit.text().strip()
        path = self.path_edit.text().strip()
        if not name or not path:
            return
        if not icon:
            icon = "🔧"
        self.tools.append({"name": name, "icon": icon, "path": path})
        self.update_tools_list()
        self.name_edit.clear()
        self.icon_edit.clear()
        self.path_edit.clear()
    def update_tool(self):
        if not self.tools_list.selectedItems():
            return
        index = self.tools_list.currentRow()
        name = self.name_edit.text().strip()
        icon = self.icon_edit.text().strip()
        path = self.path_edit.text().strip()
        if not name or not path:
            return
        if not icon:
            icon = "🔧"
        self.tools[index] = {"name": name, "icon": icon, "path": path}
        self.update_tools_list()
    def delete_tool(self):
        if not self.tools_list.selectedItems():
            return
        index = self.tools_list.currentRow()
        del self.tools[index]
        self.update_tools_list()
        self.name_edit.clear()
        self.icon_edit.clear()
        self.path_edit.clear()
    def move_tool_up(self):
        if not self.tools_list.selectedItems():
            return
        index = self.tools_list.currentRow()
        if index <= 0:
            return
        self.tools[index], self.tools[index-1] = self.tools[index-1], self.tools[index]
        self.update_tools_list()
        self.tools_list.setCurrentRow(index-1)
    def move_tool_down(self):
        if not self.tools_list.selectedItems():
            return
        index = self.tools_list.currentRow()
        if index >= len(self.tools) - 1:
            return
        self.tools[index], self.tools[index+1] = self.tools[index+1], self.tools[index]
        self.update_tools_list()
        self.tools_list.setCurrentRow(index+1) 

class MemoDialog(QDialog):
    def __init__(self, memos, parent=None):
        super().__init__(parent)
        self.setWindowTitle("备忘录管理")
        self.setFixedSize(600, 500)
        self.memos = memos.copy()
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
        tip_label = QLabel("💡 提示：勾选'设置提醒'后可以设置提醒时间，应用会在指定时间前提醒您")
        tip_label.setStyleSheet("color: #5f9ea0; font-size: 10px; padding: 5px;")
        tip_label.setWordWrap(True)
        layout.addWidget(tip_label)
        self.memos_list = QListWidget()
        self.update_memos_list()
        layout.addWidget(self.memos_list)
        edit_layout = QVBoxLayout()
        title_layout = QHBoxLayout()
        title_layout.addWidget(QLabel("标题:"))
        self.title_edit = QLineEdit()
        title_layout.addWidget(self.title_edit)
        edit_layout.addLayout(title_layout)
        content_layout = QVBoxLayout()
        content_layout.addWidget(QLabel("内容:"))
        self.content_edit = QTextEdit()
        self.content_edit.setMaximumHeight(80)
        content_layout.addWidget(self.content_edit)
        edit_layout.addLayout(content_layout)
        reminder_layout = QHBoxLayout()
        self.reminder_checkbox = QCheckBox("设置提醒")
        reminder_layout.addWidget(self.reminder_checkbox)
        reminder_layout.addWidget(QLabel("提醒时间:"))
        self.datetime_edit = CustomDateTimeEdit()
        self.datetime_edit.setDateTime(datetime.now())
        self.datetime_edit.setEnabled(False)
        reminder_layout.addWidget(self.datetime_edit)
        self.reminder_checkbox.toggled.connect(self.datetime_edit.setEnabled)
        edit_layout.addLayout(reminder_layout)
        layout.addLayout(edit_layout)
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
        dialog_buttons = QHBoxLayout()
        self.ok_button = QPushButton("确定")
        self.ok_button.clicked.connect(self.accept)
        self.cancel_button = QPushButton("取消")
        self.cancel_button.clicked.connect(self.reject)
        dialog_buttons.addWidget(self.ok_button)
        dialog_buttons.addWidget(self.cancel_button)
        layout.addLayout(dialog_buttons)
        self.setLayout(layout)
        self.memos_list.itemSelectionChanged.connect(self.selection_changed)
        self.memos_list.itemDoubleClicked.connect(self.item_double_clicked)
    def update_memos_list(self):
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
        has_selection = len(self.memos_list.selectedItems()) > 0
        self.update_button.setEnabled(has_selection)
        self.delete_button.setEnabled(has_selection)
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
        index = self.memos_list.row(item)
        memo = self.memos[index]
        self.title_edit.setText(memo.get('title', ''))
        self.content_edit.setText(memo.get('content', ''))
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
        title = self.title_edit.text().strip()
        content = self.content_edit.toPlainText().strip()
        if not title:
            return
        memo = {
            'title': title,
            'content': content,
            'created_time': datetime.now().isoformat()
        }
        if self.reminder_checkbox.isChecked():
            memo['reminder_time'] = self.datetime_edit.dateTime().isoformat()
        self.memos.append(memo)
        self.update_memos_list()
        self.title_edit.clear()
        self.content_edit.clear()
        self.reminder_checkbox.setChecked(False)
    def update_memo(self):
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
        if self.reminder_checkbox.isChecked():
            memo['reminder_time'] = self.datetime_edit.dateTime().isoformat()
        self.memos[index] = memo
        self.update_memos_list()
    def delete_memo(self):
        if not self.memos_list.selectedItems():
            return
        index = self.memos_list.currentRow()
        del self.memos[index]
        self.update_memos_list()
        self.title_edit.clear()
        self.content_edit.clear()
        self.reminder_checkbox.setChecked(False)
    def reset_reminder(self):
        if not self.memos_list.selectedItems():
            return
        index = self.memos_list.currentRow()
        memo = self.memos[index]
        memo['reminder_shown'] = False
        memo['advance_shown'] = False
        self.update_memos_list()
        self.selection_changed()
        if hasattr(self.parent(), 'settings'):
            parent_settings = self.parent().settings
            parent_memos = parent_settings.get('memos', [])
            if index < len(parent_memos):
                parent_memos[index] = memo
                from core.settings import save_settings
                save_settings(parent_settings) 

class ReminderDialog(QDialog):
    def __init__(self, memo, parent=None):
        super().__init__(parent)
        self.setWindowTitle("备忘录提醒")
        self.setFixedSize(400, 200)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
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
        title_label = QLabel(f"⏰ 备忘录提醒: {memo.get('title', '无标题')}")
        title_label.setFont(QFont("Caveat", 14, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #5f9ea0;")
        layout.addWidget(title_label)
        content_label = QLabel("内容:")
        layout.addWidget(content_label)
        content_edit = QTextEdit()
        content_edit.setPlainText(memo.get('content', ''))
        content_edit.setReadOnly(True)
        content_edit.setMaximumHeight(80)
        layout.addWidget(content_edit)
        button_layout = QHBoxLayout()
        snooze_button = QPushButton("稍后提醒 (5分钟)")
        snooze_button.clicked.connect(lambda: self.snooze_reminder(5))
        button_layout.addWidget(snooze_button)
        dismiss_button = QPushButton("关闭")
        dismiss_button.clicked.connect(self.accept)
        button_layout.addWidget(dismiss_button)
        layout.addLayout(button_layout)
        self.setLayout(layout)
        self.memo = memo
    def snooze_reminder(self, minutes):
        new_time = datetime.now() + timedelta(minutes=minutes)
        self.memo['reminder_time'] = new_time.isoformat()
        self.accept() 