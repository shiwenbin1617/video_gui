# coding: utf-8
import shutil

import cv2
import os
from PIL import Image
import numpy as np
import logging

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


@staticmethod
def clear_directory(directory):
    """
    清空指定的目录，如果目录中有文件或其他目录，则将它们全部删除。
    """
    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print(f'删除 {file_path} 时发生错误。原因: {e}')
def extract_frames(video_path, folder="video_frames", frame_interval=2):
    """
    从视频中提取帧并保存为图像文件。

    参数:
    - video_path: 视频文件的路径。
    - folder: 存储帧图像的文件夹名称，默认为"video_frames"。
    - frame_interval: 提取帧的时间间隔（秒），默认为2秒。
    """
    try:
        # 创建帧文件夹（如果不存在的话）
        frames_dir = os.path.join(os.getcwd(), folder)
        os.makedirs(frames_dir, exist_ok=True)
        if not os.path.exists(frames_dir):
            os.makedirs(frames_dir)
        else:
            # 如果目录已存在，清空该目录
            clear_directory(frames_dir)
        logging.info(f"帧图像将被保存在: {frames_dir}")

        # 读取视频文件
        cap = cv2.VideoCapture(video_path)

        # 检查视频是否正确打开
        if not cap.isOpened():
            raise IOError("无法打开视频文件")

        fps = cap.get(cv2.CAP_PROP_FPS)  # 获取视频的帧率
        interval_frames = int(fps * frame_interval)  # 计算间隔的帧数

        frame_count = 0  # 用于计数和决定是否保存帧

        while True:
            ret, frame = cap.read()
            if not ret:
                break  # 如果没有帧了，跳出循环

            if frame_count % interval_frames == 0:
                # 将捕获的帧转换成PIL图像格式
                pil_img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))

                # 调整图像大小
                max_size = 250
                ratio = max_size / max(pil_img.size)
                new_size = tuple([int(x * ratio) for x in pil_img.size])
                resized_img = pil_img.resize(new_size, Image.LANCZOS)

                # 将PIL图像转换回OpenCV图像格式
                frame = cv2.cvtColor(np.array(resized_img), cv2.COLOR_RGB2BGR)

                # 将帧作为图像文件保存
                path = f"{frames_dir}/frame_{frame_count}.jpg"
                cv2.imwrite(path, frame)
                logging.info(f"📸 正在保存帧 {frame_count}.")

            frame_count += 1

        logging.info("帧提取完成。")

    except Exception as e:
        logging.error(f"提取帧过程中发生错误: {e}")
    finally:
        # 释放视频文件并关闭所有窗口
        cap.release()
        cv2.destroyAllWindows()


if __name__ == '__main__':
    video_path = '/Users/shiwenbin/Downloads/66_1713949854.mp4'
    extract_frames(video_path)
