# coding: utf-8
from video_narrator import ImageAnalyzer
from videos import extract_frames

if __name__ == "__main__":
    try:
        frame_interval = input("请输入帧提取的时间间隔（秒）: ")
        _video_path = input("请输入视频文件的路径: ")
        extract_frames(video_path=_video_path,frame_interval=frame_interval)
    except Exception as e:
        print(f"提取帧过程中发生错误: {e}")
        raise e
    # 请根据实际情况替换API密钥和声音ID
    openai_api_key = input("请输入OpenAI的API密钥: ")
    elevenlabs_api_key = input("请输入ElevenLabs的API密钥: ")
    elevenlabs_voice_id = input("请输入ElevenLabs的声音ID: ")
    base_url = input("请输入OpenAI API的基本URL（按Enter键跳过）: ")

    analyzer = ImageAnalyzer(openai_api_key, elevenlabs_api_key, elevenlabs_voice_id)
    analyzer.main()
