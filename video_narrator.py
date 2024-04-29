# coding: utf-8
import logging
import os
import base64
import time
import errno
from openai import OpenAI
from elevenlabs import generate, play, set_api_key


class ImageAnalyzer:
    def __init__(self, openai_api_key, elevenlabs_api_key, elevenlabs_voice_id, base_url=None, logger=None):
        self.latest_audio_path = None
        self.logger = logger if logger is not None else logging.getLogger(__name__)
        if base_url:
            self.client = OpenAI(api_key=openai_api_key, base_url=base_url)
        else:
            self.client = OpenAI(api_key=openai_api_key)

        # 使用ElevenLabs API密钥
        set_api_key(api_key=elevenlabs_api_key)
        self.elevenlabs_voice_id = elevenlabs_voice_id

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
            max_tokens=500,
        )
        return response.choices[0].message.content

    def _play_audio(self, text):
        audio = generate(text, voice=self.elevenlabs_voice_id)
        unique_id = base64.urlsafe_b64encode(os.urandom(30)).decode("utf-8").rstrip("=")
        dir_path = os.path.join("narration", unique_id)
        os.makedirs(dir_path, exist_ok=True)
        file_path = os.path.join(dir_path, "audio.wav")
        with open(file_path, "wb") as f:
            f.write(audio)
        self.latest_audio_path = file_path  # 更新最新的音频文件路径
        return file_path

    def get_latest_audio_path(self):
        return self.latest_audio_path

    def main(self):
        script = []
        frames_dir = os.path.join(os.getcwd(), "video_frames")
        frame_files = sorted(os.listdir(frames_dir))

        for frame_file in frame_files:
            frame_path = os.path.join(frames_dir, frame_file)
            if not frame_file.lower().endswith(('.png', '.jpg', '.jpeg')):
                continue
            base64_image = self.encode_image(frame_path)
            self.logger.info("👀 David is watching...")
            analysis = self.analyze_image(base64_image, script=script)
            self.logger.info("🎙️ David says:")
            self.logger.info(analysis)
            script = script + [{"role": "assistant", "content": analysis}]
            time.sleep(5)
