# 导入所需的库
import cv2
import time
from PIL import Image
import numpy as np
import os

# 设置保存帧的文件夹名称
folder = "frames"

# 创建帧文件夹（如果不存在的话）
frames_dir = os.path.join(os.getcwd(), folder)
os.makedirs(frames_dir, exist_ok=True)

# 初始化摄像头
cap = cv2.VideoCapture(0)

# 检查摄像头是否正确打开
if not cap.isOpened():
    raise IOError("无法打开摄像头")

# 等待摄像头初始化并调整光线水平
time.sleep(2)

# 使用一个无限循环来不断地从摄像头读取帧
while True:
    ret, frame = cap.read()
    if ret:
        # 将捕获的帧转换成PIL图像格式
        pil_img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))

        # 调整图像大小
        max_size = 250
        ratio = max_size / max(pil_img.size)
        new_size = tuple([int(x*ratio) for x in pil_img.size])
        resized_img = pil_img.resize(new_size, Image.LANCZOS)

        # 将PIL图像转换回OpenCV图像格式
        frame = cv2.cvtColor(np.array(resized_img), cv2.COLOR_RGB2BGR)

        # 将帧作为图像文件保存
        print("📸 正在保存帧。！")
        path = f"{folder}/frame.jpg"
        cv2.imwrite(path, frame)
    else:
        print("捕获图像失败")

    # 等待2秒
    time.sleep(2)

# 释放摄像头并关闭所有窗口
cap.release()
cv2.destroyAllWindows()
