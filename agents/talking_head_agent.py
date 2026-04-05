import os
import time
import requests
import subprocess
from agents.base_agent import BaseAgent
from core.config import D_ID_API_KEY, GPT_MODEL, OUTPUT_DIR, FFMPEG_PATH

_D_ID_HEADERS = {
    "Authorization": f"Basic {D_ID_API_KEY}",
    "Content-Type": "application/json",
}
_POLL_INTERVAL = 5
_MAX_WAIT = 300  # seconds


class TalkingHeadAgent(BaseAgent):
    """
    Three steps:
    1. DALL-E generates a portrait of the author
    2. D-ID animates it lip-synced to the audio
    3. ffmpeg burns in the SRT subtitles
    """

    def run(
        self,
        author: str,
        region: str,
        year: str,
        audio_path: str,
        srt_path: str,
        output_name: str,
    ) -> str:
        print("  Generating author portrait...")
        image_url = self._generate_portrait(author, region, year)

        print("  Animating talking head via D-ID...")
        video_url = self._animate(image_url, audio_path)

        raw_video_path = f"{output_name}_raw.mp4"
        self._download(video_url, raw_video_path)

        print("  Burning in subtitles...")
        final_path = f"{output_name}.mp4"
        self._burn_subtitles(raw_video_path, srt_path, final_path)
        os.remove(raw_video_path)

        return final_path

    def _generate_portrait(self, author: str, region: str, year: str) -> str:
        prompt = (
            f"A realistic painted portrait of {author}, a person from {region} "
            f"circa {year}. Traditional clothing of the region and era. "
            f"Dignified, looking slightly toward the camera. Warm natural lighting. "
            f"No text. Museum quality oil painting style."
        )
        response = self.client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size="1024x1024",
            quality="standard",
            n=1,
        )
        return response.data[0].url

    def _animate(self, image_url: str, audio_path: str) -> str:
        # D-ID limit ~10MB — trim to first 30s into a clean temp file
        trimmed_path = os.path.join(os.path.dirname(audio_path), "did_upload_temp.mp3")
        trim_cmd = [
            FFMPEG_PATH, "-y", "-i", audio_path,
            "-t", "30", "-ac", "1", "-ar", "22050", trimmed_path
        ]
        result = subprocess.run(trim_cmd, capture_output=True)
        if result.returncode != 0 or not os.path.exists(trimmed_path):
            raise RuntimeError(f"ffmpeg trim failed: {result.stderr.decode()}")

        # Upload audio to D-ID
        with open(trimmed_path, "rb") as f:
            upload_resp = requests.post(
                "https://api.d-id.com/audios",
                headers={"Authorization": f"Basic {D_ID_API_KEY}"},
                files={"audio": ("narration.mp3", f, "audio/mpeg")},
            )
        os.remove(trimmed_path)
        if not upload_resp.ok:
            raise RuntimeError(f"D-ID upload failed {upload_resp.status_code}: {upload_resp.text}")
        audio_url = upload_resp.json()["url"]

        # Create talk
        payload = {
            "source_url": image_url,
            "script": {
                "type": "audio",
                "audio_url": audio_url,
            },
            "config": {"result_format": "mp4"},
        }
        create_resp = requests.post(
            "https://api.d-id.com/talks",
            headers=_D_ID_HEADERS,
            json=payload,
        )
        create_resp.raise_for_status()
        talk_id = create_resp.json()["id"]

        # Poll until done
        elapsed = 0
        while elapsed < _MAX_WAIT:
            time.sleep(_POLL_INTERVAL)
            elapsed += _POLL_INTERVAL
            status_resp = requests.get(
                f"https://api.d-id.com/talks/{talk_id}",
                headers=_D_ID_HEADERS,
            )
            status_resp.raise_for_status()
            data = status_resp.json()
            status = data.get("status")
            print(f"    D-ID status: {status} ({elapsed}s)")
            if status == "done":
                return data["result_url"]
            if status == "error":
                raise RuntimeError(f"D-ID error: {data}")

        raise TimeoutError("D-ID animation timed out")

    def _download(self, url: str, path: str) -> None:
        resp = requests.get(url, stream=True, timeout=60)
        resp.raise_for_status()
        with open(path, "wb") as f:
            for chunk in resp.iter_content(8192):
                f.write(chunk)

    def _burn_subtitles(self, video_path: str, srt_path: str, output_path: str) -> None:
        # Escape path separators for ffmpeg subtitles filter on Windows
        srt_escaped = srt_path.replace("\\", "/").replace(":", "\\:")
        cmd = [
            FFMPEG_PATH, "-y",
            "-i", video_path,
            "-vf", (
                f"subtitles='{srt_escaped}'"
                ":force_style='FontName=Arial,FontSize=18,"
                "PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,"
                "BackColour=&H80000000,Bold=1,Outline=2,Shadow=1,"
                "Alignment=2,MarginV=30'"
            ),
            "-c:a", "copy",
            output_path,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"ffmpeg failed:\n{result.stderr}")
