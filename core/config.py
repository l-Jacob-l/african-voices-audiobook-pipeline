from dotenv import load_dotenv
import os

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
D_ID_API_KEY = os.getenv("D_ID_API_KEY")
GPT_MODEL = "gpt-4o"
TTS_MODEL = "tts-1"
TTS_AUDIO_MODEL = "gpt-4o-audio-preview"
OUTPUT_DIR = "output"
FFMPEG_PATH = os.getenv(
    "FFMPEG_PATH",
    r"C:\Users\Jacob-machine\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.1-full_build\bin\ffmpeg.exe"
)
