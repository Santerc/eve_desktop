from PyQt6.QtCore import QTimer, QObject
from datetime import datetime, timedelta
from ui.dialogs import ReminderDialog
from core.settings import load_settings, save_settings

class ReminderManager(QObject):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.reminder_timer = QTimer()
        self.reminder_timer.timeout.connect(self.check_reminders)
        self.reminder_timer.start(30000)
        print("提醒管理器已初始化，每30秒检查一次提醒")
    def check_reminders(self):
        if not hasattr(self.parent, 'settings'):
            print("警告：父窗口没有settings属性")
            return
        self.parent.settings = load_settings()
        settings = self.parent.settings
        memos = settings.get('memos', [])
        reminder_settings = settings.get('reminder_settings', {})
        advance_minutes = reminder_settings.get('advance_minutes', 5)
        current_time = datetime.now()
        advance_time = current_time + timedelta(minutes=advance_minutes)
        print(f"检查提醒 - 当前时间: {current_time.strftime('%H:%M:%S')}, 备忘录数量: {len(memos)}")
        settings_changed = False
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
                if current_time >= reminder_dt and not memo.get('reminder_shown', False):
                    print(f"触发正式提醒: {memo.get('title', '无标题')}")
                    self.show_reminder(memo)
                    memo['reminder_shown'] = True
                    settings_changed = True
                elif advance_time >= reminder_dt and not memo.get('advance_shown'):
                    print(f"触发提前提醒: {memo.get('title', '无标题')}")
                    self.show_advance_reminder(memo, advance_minutes)
                    memo['advance_shown'] = True
                    settings_changed = True
            except Exception as e:
                print(f"处理提醒时间失败: {e}")
        if settings_changed:
            save_settings(settings)
    def show_reminder(self, memo):
        if not hasattr(self.parent, 'settings'):
            return
        settings = self.parent.settings
        reminder_settings = settings.get('reminder_settings', {})
        print(f"显示提醒对话框: {memo.get('title', '无标题')}")
        if reminder_settings.get('enable_popup', True):
            dialog = ReminderDialog(memo, self.parent)
            dialog.exec()
        if reminder_settings.get('enable_sound', True):
            from PyQt6.QtWidgets import QApplication
            QApplication.beep()
    def show_advance_reminder(self, memo, advance_minutes):
        if not hasattr(self.parent, 'settings'):
            return
        settings = self.parent.settings
        reminder_settings = settings.get('reminder_settings', {})
        print(f"显示提前提醒: {memo.get('title', '无标题')}")
        if reminder_settings.get('enable_popup', True):
            from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton
            from PyQt6.QtGui import QFont
            from PyQt6.QtCore import Qt
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
        if reminder_settings.get('enable_sound', True):
            from PyQt6.QtWidgets import QApplication
            QApplication.beep() 