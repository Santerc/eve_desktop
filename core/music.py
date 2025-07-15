import numpy as np
from PyQt6.QtCore import QTimer

try:
    import pyaudio
    AUDIO_AVAILABLE = True
except ImportError:
    AUDIO_AVAILABLE = False

class AudioVisualizer:
    def __init__(self, parent=None):
        self.parent = parent
        self.audio = None
        self.stream = None
        self.is_running = False
        self.audio_data = []
        self.frequency_data = []
        self.max_frequencies = 64
        self.CHUNK = 1024
        self.FORMAT = pyaudio.paFloat32 if AUDIO_AVAILABLE else None
        self.CHANNELS = 2
        self.RATE = 44100
        self.visual_timer = QTimer()
        self.visual_timer.timeout.connect(self.update_visualization)
        self.visual_timer.start(33)
        if AUDIO_AVAILABLE:
            self.init_audio()

    def init_audio(self):
        try:
            self.audio = pyaudio.PyAudio()
            info = self.audio.get_host_api_info_by_index(0)
            numdevices = info.get('deviceCount')
            input_devices = []
            for i in range(numdevices):
                device_info = self.audio.get_device_info_by_host_api_device_index(0, i)
                if device_info.get('maxInputChannels') > 0:
                    device_name = device_info.get('name')
                    input_devices.append((i, device_name))
            stereo_mix_keywords = [
                'stereo mix', '立体声混音', 'what u hear', 'loopback'
            ]
            selected_device = None
            for device_id, device_name in input_devices:
                device_lower = device_name.lower()
                if any(keyword in device_lower for keyword in stereo_mix_keywords):
                    selected_device = device_id
                    break
            if selected_device is None:
                print("未找到立体声混音设备！")
                self.is_running = False
                return
            self.stream = self.audio.open(
                format=self.FORMAT,
                channels=self.CHANNELS,
                rate=self.RATE,
                input=True,
                input_device_index=selected_device,
                frames_per_buffer=self.CHUNK,
                stream_callback=self.audio_callback
            )
            self.stream.start_stream()
            self.is_running = True
            print("音频捕获已启动，使用立体声混音设备，30FPS可视化更新")
        except Exception as e:
            print(f"音频捕获初始化失败: {e}")
            self.is_running = False

    def audio_callback(self, in_data, frame_count, time_info, status):
        if self.is_running:
            try:
                audio_array = np.frombuffer(in_data, dtype=np.float32)
                if len(audio_array) > 0:
                    self.update_frequency_data(audio_array)
                return (in_data, pyaudio.paContinue)
            except Exception as e:
                print(f"音频处理错误: {e}")
                return (in_data, pyaudio.paContinue)
        else:
            return (None, pyaudio.paComplete)

    def update_frequency_data(self, audio_data):
        try:
            window = np.hanning(len(audio_data))
            windowed_data = audio_data * window
            fft_data = np.fft.fft(windowed_data)
            fft_magnitude = np.abs(fft_data[:len(fft_data)//2])
            fft_magnitude = np.log10(fft_magnitude + 1)
            if len(fft_magnitude) > self.max_frequencies:
                indices = np.linspace(0, len(fft_magnitude)-1, self.max_frequencies)
                self.frequency_data = np.interp(indices, np.arange(len(fft_magnitude)), fft_magnitude)
            else:
                self.frequency_data = np.zeros(self.max_frequencies)
                self.frequency_data[:len(fft_magnitude)] = fft_magnitude
            if np.max(self.frequency_data) > 0:
                self.frequency_data = self.frequency_data / np.max(self.frequency_data)
        except Exception as e:
            print(f"频域分析错误: {e}")
            self.frequency_data = np.zeros(self.max_frequencies)

    def update_visualization(self):
        if self.parent and hasattr(self.parent, 'update'):
            self.parent.update()

    def get_frequency_data(self):
        return self.frequency_data.copy()

    def stop(self):
        self.is_running = False
        if self.visual_timer:
            self.visual_timer.stop()
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        if self.audio:
            self.audio.terminate()
        print("音频捕获已停止")

def play_pause_music():
    pass

def next_track():
    pass

def prev_track():
    pass 