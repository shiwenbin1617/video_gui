# coding: utf-8
import os
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
from tkinter import ttk
import logging

import pygame
from ttkthemes import ThemedTk

from video_narrator import ImageAnalyzer
from videos import extract_frames

pygame.mixer.init()


class TextHandler(logging.Handler):
    def __init__(self, text_widget):
        super().__init__()
        self.text_widget = text_widget

    def emit(self, record):
        msg = self.format(record)
        self.text_widget.configure(state='normal')
        self.text_widget.insert(tk.END, msg + '\n')
        self.text_widget.configure(state='disabled')
        self.text_widget.yview(tk.END)


def start_processing():
    global analyzer  # 声明analyzer为全局变量
    global audio_path
    try:
        frame_interval = int(frame_interval_entry.get())
        video_path = video_path_entry.get()
        openai_api_key = openai_api_key_entry.get()
        elevenlabs_api_key = elevenlabs_api_key_entry.get()
        elevenlabs_voice_id = elevenlabs_voice_id_entry.get()
        base_url = base_url_entry.get() if base_url_entry.get() else None

        logger.info("开始处理视频...")
        extract_frames(video_path=video_path, frame_interval=frame_interval)
        logger.info("视频帧提取完成")
        logger.info("开始处理帧图像...")
        analyzer = ImageAnalyzer(openai_api_key=openai_api_key,
                                 elevenlabs_api_key=elevenlabs_api_key,
                                 elevenlabs_voice_id=elevenlabs_voice_id,
                                 base_url=base_url,
                                 logger=logger)
        analyzer.main()
        audio_path.set(analyzer.get_latest_audio_path())  # 更新标签内容为最新的音频文件路径
        logger.info("帧图像处理完成")
    except Exception as e:
        logger.error(f"处理过程中发生错误: {e}")
        messagebox.showerror("错误", f"处理过程中发生错误: {e}")


def play_latest_audio():
    if 'analyzer' in globals() and analyzer.get_latest_audio_path():
        pygame.mixer.music.load(analyzer.get_latest_audio_path())
        pygame.mixer.music.play()
        audio_path.set(analyzer.get_latest_audio_path())  # 更新标签内容为最新的音频文件路径
    else:
        messagebox.showinfo("提示", "没有可播放的音频。")


def open_audio_folder():
    if 'analyzer' in globals() and analyzer.get_latest_audio_path():
        folder_path = os.path.dirname(analyzer.get_latest_audio_path())
        os.startfile(folder_path)  # 打开音频文件所在的文件夹
    else:
        messagebox.showinfo("提示", "没有可打开的文件夹。")


def browse_video():
    filepath = filedialog.askopenfilename(
        title="选择视频文件",
        filetypes=[("MP4视频文件", "*.mp4"), ("AVI视频文件", "*.avi"), ("MOV视频文件", "*.mov"), ("所有文件", "*.*")])
    video_path_entry.delete(0, tk.END)
    video_path_entry.insert(0, filepath)


# 配置日志
logger = logging.getLogger()
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

root = ThemedTk(theme="aqua")  # 使用ThemedTk代替Tk，并选择一个主题
root.title("视频处理工具")
root.geometry("800x600")

# 使用PanedWindow作为主布局容器
paned_window = ttk.PanedWindow(root, orient=tk.VERTICAL)
paned_window.pack(fill=tk.BOTH, expand=True)

# 上方的输入区域
input_frame = ttk.Frame(paned_window)
paned_window.add(input_frame, weight=1)

# 下方的日志区域
log_frame = ttk.Labelframe(paned_window, text="日志", padding="10")
paned_window.add(log_frame, weight=1)

log_text = scrolledtext.ScrolledText(log_frame, state='disabled', height=10)
log_text.pack(fill=tk.BOTH, expand=True)

text_handler = TextHandler(log_text)
text_handler.setFormatter(formatter)
logger.addHandler(text_handler)

# 输入区域的布局
entries = {}
labels = ["帧提取的时间间隔（秒）:", "视频文件路径:", "OpenAI API密钥:", "ElevenLabs API密钥:", "ElevenLabs 声音ID:",
          "OpenAI API的基本URL（可选）:"]
for i, label in enumerate(labels):
    ttk.Label(input_frame, text=label).grid(row=i, column=0, padx=5, pady=5, sticky=tk.W)
    entry = ttk.Entry(input_frame)
    entry.grid(row=i, column=1, padx=5, pady=5, sticky=(tk.W, tk.E))
    input_frame.columnconfigure(1, weight=1)
    entries[label] = entry

frame_interval_entry, video_path_entry, openai_api_key_entry, elevenlabs_api_key_entry, elevenlabs_voice_id_entry, base_url_entry = entries.values()

ttk.Button(input_frame, text="浏览...", command=browse_video).grid(row=1, column=2, padx=5, pady=5, sticky=tk.W)
ttk.Button(input_frame, text="开始处理", command=start_processing).grid(row=6, column=0, columnspan=3, padx=5, pady=5)

audio_path = tk.StringVar()  # 使用StringVar来动态更新标签内容
audio_path_label = ttk.Label(input_frame, textvariable=audio_path)
audio_path_label.grid(row=8, column=1, padx=5, pady=5, sticky=tk.W)

play_audio_button = ttk.Button(input_frame, text="播放最新音频", command=play_latest_audio)
play_audio_button.grid(row=7, column=0, columnspan=3, padx=5, pady=5, sticky=tk.W)

open_folder_button = ttk.Button(input_frame, text="预览", command=open_audio_folder)
open_folder_button.grid(row=7, column=2, padx=5, pady=5, sticky=tk.W)

root.mainloop()
