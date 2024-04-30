# coding: utf-8
import logging
import os
import base64
import shutil
import time
import errno
from openai import OpenAI


class ImageAnalyzer:
    def __init__(self, openai_api_key, voice_id, base_url=None, logger=None):
        self.latest_audio_path = None
        self.logger = logger if logger is not None else logging.getLogger(__name__)
        if base_url:
            self.client = OpenAI(api_key=openai_api_key, base_url=base_url)
        else:
            self.client = OpenAI(api_key=openai_api_key)

    def encode_image(self, image_path):
        while True:
            try:
                with open(image_path, "rb") as image_file:
                    return base64.b64encode(image_file.read()).decode("utf-8")
            except IOError as e:
                if e.errno != errno.EACCES:
                    raise
                time.sleep(0.1)

    def generate_new_line(self, base64_image):
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

    def analyze_image(self, base64_image, script):
        try:
            self.logger.info(f"正在发送的图像数据: {self.generate_new_line(base64_image)}")
            response = self.client.chat.completions.create(
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
                         + self.generate_new_line(base64_image),
                max_tokens=1200,
            )
            # 确保响应中包含预期的数据
            if response.choices and len(response.choices) > 0 and response.choices[0].message:
                return response.choices[0].message.content
            else:
                self.logger.error("响应缺少预期的数据。")
                self.logger.info(f"响应内容: {response}")
        except Exception as e:
            self.logger.error(f"分析图像时发生错误: {e}")
            self.logger.debug(f"错误详情:{response}")

    def _openai_play_audio(self, text, voice="alloy"):
        self.logger.info("🔊 Playing audio...")
        response = self.client.audio.speech.create(
            model="tts-1",
            voice=voice,
            input=text
        )
        speech_file_path = os.path.join("narration", "speech.mp3")
        response.stream_to_file(speech_file_path)
        self.latest_audio_path = speech_file_path
        self.logger.info("🎵 Audio saved to: %s", speech_file_path)

    def get_latest_audio_path(self):
        return self.latest_audio_path

    def main(self,voice="alloy"):
        script = []
        time.sleep(3)
        frames_dir = os.path.join(os.getcwd(), "video_frames")
        frame_files = [f for f in sorted(os.listdir(frames_dir)) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]

        self.logger.info(f"找到 {len(frame_files)} 个图像文件进行分析。")

        ai_message = ''
        for index, frame_file in enumerate(frame_files):
            frame_path = os.path.join(frames_dir, frame_file)
            base64_image = self.encode_image(frame_path)

            # 为了提高日志的可读性，我们可以在日志中添加文件索引和名称
            self.logger.info(f"👀 正在分析第 {index + 1}/{len(frame_files)} 个文件: {frame_file}...")
            analysis = self.analyze_image(base64_image, script=script)

            if analysis:  # 确保分析结果不为空
                self.logger.info("🎙️ 分析结果:")
                self.logger.info(analysis)
                script.append({"role": "assistant", "content": analysis})
                ai_message += analysis + " "  # 添加空格以分隔不同帧的分析结果
                time.sleep(5)  # 根据需要调整等待时间
            else:
                self.logger.info("没有获取到分析结果。")

        # 检查ai_message是否为空，避免尝试播放空消息
        if ai_message:
            self._openai_play_audio(text=ai_message,voice=voice)
        else:
            self.logger.info("没有生成任何音频消息。")
