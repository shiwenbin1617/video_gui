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


class VideoProcessorUI:
    def __init__(self, root):
        self.root = root
        self.configure_ui()
        self.create_widgets()

    def configure_ui(self):
        self.root.title("视频处理工具")
        self.root.geometry("800x600")

    def create_widgets(self):
        # 使用PanedWindow作为主布局容器
        paned_window = ttk.PanedWindow(self.root, orient=tk.VERTICAL)
        paned_window.pack(fill=tk.BOTH, expand=True)

        # 上方的输入区域
        self.input_frame = ttk.Frame(paned_window)
        paned_window.add(self.input_frame, weight=1)

        # 下方的日志区域
        log_frame = ttk.Labelframe(paned_window, text="日志", padding="10")
        paned_window.add(log_frame, weight=1)

        log_text = scrolledtext.ScrolledText(log_frame, state='disabled', height=10)
        log_text.pack(fill=tk.BOTH, expand=True)

        text_handler = TextHandler(log_text)
        text_handler.setFormatter(formatter)
        logger.addHandler(text_handler)

        self.create_input_widgets()

    def create_input_widgets(self):
        labels = ["帧提取的时间间隔（秒）:", "视频文件路径:", "OpenAI API密钥:",'声音ID:',
                  "OpenAI API的基本URL（可选）:"]
        self.entries = {}
        for i, label in enumerate(labels):
            ttk.Label(self.input_frame, text=label).grid(row=i, column=0, padx=5, pady=5, sticky=tk.W)
            entry = ttk.Entry(self.input_frame)
            entry.grid(row=i, column=1, padx=5, pady=5, sticky=(tk.W, tk.E))
            self.input_frame.columnconfigure(1, weight=1)
            self.entries[label] = entry

        ttk.Button(self.input_frame, text="浏览...", command=self.browse_video).grid(row=1, column=2, padx=5, pady=5,
                                                                                     sticky=tk.W)
        ttk.Button(self.input_frame, text="开始处理", command=self.start_processing).grid(row=6, column=0, columnspan=3,
                                                                                          padx=5, pady=5)

        self.audio_path = tk.StringVar()  # 使用StringVar来动态更新标签内容
        audio_path_label = ttk.Label(self.input_frame, textvariable=self.audio_path)
        audio_path_label.grid(row=8, column=1, padx=5, pady=5, sticky=tk.W)

        play_audio_button = ttk.Button(self.input_frame, text="播放最新音频", command=self.play_latest_audio)
        play_audio_button.grid(row=7, column=0, columnspan=3, padx=5, pady=5, sticky=tk.W)

        open_folder_button = ttk.Button(self.input_frame, text="预览", command=self.open_audio_folder)
        open_folder_button.grid(row=7, column=2, padx=5, pady=5, sticky=tk.W)

    def start_processing(self):
        try:
            frame_interval = int(self.entries["帧提取的时间间隔（秒）:"].get())
            video_path = self.entries["视频文件路径:"].get()
            openai_api_key = self.entries["OpenAI API密钥:"].get()
            voice_id = self.entries["声音ID:"].get()
            base_url = self.entries["OpenAI API的基本URL（可选）:"].get() if self.entries[
                "OpenAI API的基本URL（可选）:"].get() else None

            logger.info("开始处理视频...")
            extract_frames(video_path=video_path, frame_interval=frame_interval)
            logger.info("视频帧提取完成")
            logger.info("开始处理帧图像...")
            self.analyzer = ImageAnalyzer(openai_api_key=openai_api_key,
                                          voice_id=voice_id,
                                          base_url=base_url,
                                          logger=logger)
            self.analyzer.main(voice=voice_id)
            self.audio_path.set(self.analyzer.get_latest_audio_path())  # 更新标签内容为最新的音频文件路径
            logger.info("帧图像处理完成")
        except Exception as e:
            logger.error(f"处理过程中发生错误: {e}")
            messagebox.showerror("错误", f"处理过程中发生错误: {e}")

    def play_latest_audio(self):
        # 检查self.analyzer是否已经被正确初始化
        if hasattr(self, 'analyzer') and self.analyzer.get_latest_audio_path():
            pygame.mixer.music.load(self.analyzer.get_latest_audio_path())
            pygame.mixer.music.play()
            self.audio_path.set(self.analyzer.get_latest_audio_path())  # 更新标签内容为最新的音频文件路径
        else:
            messagebox.showinfo("提示", "没有可播放的音频。")

    def open_audio_folder(self):
        # 检查self.analyzer是否已经被正确初始化
        if hasattr(self, 'analyzer') and self.analyzer.get_latest_audio_path():
            folder_path = os.path.dirname(self.analyzer.get_latest_audio_path())
            os.startfile(folder_path)  # 打开音频文件所在的文件夹
        else:
            messagebox.showinfo("提示", "没有可打开的文件夹。")

    def browse_video(self):
        filepath = filedialog.askopenfilename(
            title="选择视频文件",
            filetypes=[("MP4视频文件", "*.mp4"), ("AVI视频文件", "*.avi"), ("MOV视频文件", "*.mov"),
                       ("所有文件", "*.*")])
        if filepath:  # 确保用户选择了文件
            # 通过标签从self.entries字典中获取视频路径输入框，并对其进行操作
            video_path_entry = self.entries["视频文件路径:"]
            video_path_entry.delete(0, tk.END)
            video_path_entry.insert(0, filepath)


# 配置日志
logger = logging.getLogger()
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

root = ThemedTk(theme="aqua")
app = VideoProcessorUI(root)
root.mainloop()
