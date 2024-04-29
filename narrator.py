# coding: utf-8
import os
from openai import OpenAI
import base64
import json
import time
import simpleaudio as sa
import errno
from elevenlabs import generate, play, set_api_key, voices

# 初始化OpenAI客户端
client = OpenAI()

# 使用环境变量中的ElevenLabs API密钥
set_api_key(os.environ.get("ELEVENLABS_API_KEY"))


# 定义一个函数，用于将图片文件编码为base64字符串
def encode_image(image_path):
    while True:
        try:
            with open(image_path, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode("utf-8")
        except IOError as e:
            if e.errno != errno.EACCES:
                # 如果不是"文件正在使用中"的错误，重新抛出异常
                raise
            # 如果文件正在写入，稍等一会儿再重试
            time.sleep(0.1)


# 定义一个函数，用于播放通过文本生成的音频
def play_audio(text):
    # 使用ElevenLabs生成音频
    audio = generate(text, voice=os.environ.get("ELEVENLABS_VOICE_ID"))

    # 生成一个唯一的文件名
    unique_id = base64.urlsafe_b64encode(os.urandom(30)).decode("utf-8").rstrip("=")
    dir_path = os.path.join("narration", unique_id)
    os.makedirs(dir_path, exist_ok=True)
    file_path = os.path.join(dir_path, "audio.wav")

    # 保存音频文件
    with open(file_path, "wb") as f:
        f.write(audio)

    # 播放音频
    play(audio)


# 定义一个函数，用于生成新的对话行
def generate_new_line(base64_image):
    return [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "Describe this image"},
                {
                    "type": "image_url",
                    "image_url": f"data:image/jpeg;base64,{base64_image}",
                },
            ],
        },
    ]


# 定义一个函数，用于分析图片并生成描述
def analyze_image(base64_image, script):
    response = client.chat.completions.create(
        model="gpt-4-vision-preview",
        messages=[
                     {
                         "role": "system",
                         "content": """
                You are Sir David Attenborough. Narrate the picture of the human as if it is a nature documentary.
                Make it snarky and funny. Don't repeat yourself. Make it short. If I do anything remotely interesting, make a big deal about it!
                """,
                     },
                 ]
                 + script
                 + generate_new_line(base64_image),
        max_tokens=500,
    )
    response_text = response.choices[0].message.content
    return response_text


# 主函数，循环执行图像分析和音频播放
def main():
    script = []

    while True:
        # 图片路径
        image_path = os.path.join(os.getcwd(), "./frames/frame.jpg")

        # 获取图片的base64编码
        base64_image = encode_image(image_path)

        # 分析图像
        print("👀 David is watching...")
        analysis = analyze_image(base64_image, script=script)

        print("🎙️ David says:")
        print(analysis)

        # 播放分析结果的音频
        play_audio(analysis)

        # 更新对话脚本
        script = script + [{"role": "assistant", "content": analysis}]

        # 等待5秒钟
        time.sleep(5)


# 如果是直接运行这个脚本，则执行main函数
if __name__ == "__main__":
    main()
