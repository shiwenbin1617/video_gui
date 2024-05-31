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
        data = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "Describe this image"},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{base64_image}"
                    }
                },
            ],
        },
        ]
        self.logger.info("🤖 AI is analyzing the image...")
        # self.logger.info(data)
        return data

    def analyze_image(self, base64_image, script):
        try:
            # self.logger.info(f"正在发送的图像数据: {self.generate_new_line(base64_image)}")
            response = self.client.chat.completions.create(
                model="gpt-4o",
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


    def _openai_play_audio_with_chunking(self, text, voice="alloy"):
        self.logger.info("🔊 Playing audio...")
        narration_dir = os.path.join(os.getcwd(), "narration")
        if not os.path.exists(narration_dir):
            os.makedirs(narration_dir)
            
        # 将文本分成多个小块，每个不超过 4096 个字符
        chunks = [text[i:i+4096] for i in range(0, len(text), 4096)]
        
        # 用于存储生成的音频文件路径
        self.latest_audio_path = []
        
        # 检查 voice 参数是否有效
        valid_voices = ['nova', 'shimmer', 'echo', 'onyx', 'fable', 'alloy']
        if voice not in valid_voices:
            self.logger.error(f"无效的语音选择: {voice}. 将使用默认值 'alloy'.")
            voice = 'alloy'
        
        for chunk in chunks:
            self.logger.info(f"正在生成第 {len(self.latest_audio_path) + 1} 个音频文件片段...")
            try:
                response = self.client.audio.speech.create(
                    model="tts-1",
                    voice=voice,
                    input=chunk,
                )
            except Exception as e:
                self.logger.error(f"生成音频文件片段时发生错误: {e}")
                continue
            
            # 生成新的音频文件路径
            speech_file_index = len(self.latest_audio_path) + 1
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            speech_file_path = os.path.join(narration_dir, f"speech_{speech_file_index}_{timestamp}.mp3")
            
            # 检查文件是否已经存在
            if not os.path.exists(speech_file_path):
                self.logger.info(f"正在保存第 {speech_file_index} 个音频文件片段到 {speech_file_path}...")
                try:
                    with open(speech_file_path, "wb") as f:
                        f.write(response.content)
                except Exception as e:
                    self.logger.error(f"保存音频文件片段 {speech_file_path} 时发生错误: {e}")
                    continue
                self.latest_audio_path.append(speech_file_path)
                self.logger.info("🎵 Audio saved to: %s", speech_file_path)
            else:
                self.logger.info(f"文件 {speech_file_path} 已存在, 跳过生成.")
                self.latest_audio_path.append(speech_file_path)
            
        self.logger.info("🎯 All audio files generated.")
        
        # 如果只有一个音频文件，就直接返回该文件路径
        if len(self.latest_audio_path) == 1:
            self.logger.info(f"🎉 Final audio file saved to: {self.latest_audio_path[0]}")
            return self.latest_audio_path[0]
        
        # 合并所有音频文件
        final_audio_path = os.path.join(narration_dir, f"final_narration_{timestamp}.mp3")
        self.logger.info(f"正在合并 {len(self.latest_audio_path)} 个音频文件到 {final_audio_path}...")
        self._merge_audio_files(self.latest_audio_path, final_audio_path)
        
        self.logger.info(f"🎉 Final audio file saved to: {final_audio_path}")
        return final_audio_path









    def _merge_audio_files(self, input_files, output_file):
        """将多个音频文件合并为一个文件"""
        import subprocess

        # 创建一个包含所有音频文件路径的文本文件
        concat_file = os.path.join("narration", "concat.txt")
        try:
            with open(concat_file, "w") as f:
                for file_path in input_files:
                    f.write(f"file '{file_path}'\n")
        except Exception as e:
            self.logger.error(f"创建 concat.txt 文件时发生错误: {e}")
            return

        # 使用 ffmpeg 命令合并音频文件
        try:
            subprocess.run(["ffmpeg", "-f", "concat", "-safe", "0", "-i", concat_file, "-c", "copy", output_file], check=True)
        except subprocess.CalledProcessError as e:
            self.logger.error(f"合并音频文件时发生错误: {e}")
            return

        # 删除临时文件
        self._delete_files([concat_file] + input_files, max_retries=3, retry_delay=0.5)


    def _delete_files(self, file_paths, max_retries=3, retry_delay=0.5):
        """尝试删除文件,如果失败则重试"""
        for file_path in file_paths:
            num_retries = 0
            while num_retries < max_retries:
                try:
                    os.remove(file_path)
                    break
                except OSError as e:
                    self.logger.error(f"删除文件 {file_path} 时发生错误: {e}")
                    num_retries += 1
                    if num_retries < max_retries:
                        self.logger.info(f"正在重试删除文件 {file_path}...")
                        time.sleep(retry_delay)
                    else:
                        self.logger.info(f"已成功删除文件 {file_path}")




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
            self._openai_play_audio_with_chunking(text=ai_message,voice=voice)
        else:
            self.logger.info("没有生成任何音频消息。")
