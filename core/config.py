from dotenv import load_dotenv
import os

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GPT_MODEL = "gpt-4o"
TTS_MODEL = "tts-1"
OUTPUT_DIR = "output"
