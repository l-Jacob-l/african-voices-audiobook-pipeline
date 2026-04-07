import os
import time
import requests
import subprocess
from agents.base_agent import BaseAgent
from core.config import D_ID_API_KEY, GPT_MODEL, OUTPUT_DIR, FFMPEG_PATH

_D_ID_HEADERS = {
    "Authorization": f"Basic {D_ID_API_KEY}",
    "Content-Type": "application/json",
    "accept": "application/json",
}
_POLL_INTERVAL = 5
_MAX_WAIT = 600  # seconds

# D-ID text input limit per talk is ~1000 chars.
# We split the script and stitch multiple talks together.
_D_ID_CHUNK_SIZE = 900


class TalkingHeadAgent(BaseAgent):
    """
    1. DALL-E generates a photorealistic portrait of the author
    2. D-ID animates it with Abeo (Nigerian English male, Microsoft) reading the script
    3. Multiple D-ID clips are stitched together with ffmpeg
    4. SRT subtitles are burned in
    """

    def run(
        self,
        author: str,
        region: str,
        year: str,
        script: str,
        srt_path: str,
        output_name: str,
    ) -> str:
        print("  Generating author portrait...")
        image_url = self._generate_portrait(author, region, year)

        # Split script into chunks D-ID can handle
        chunks = self._split_chunks(script, _D_ID_CHUNK_SIZE)
        print(f"  Generating {len(chunks)} D-ID video clip(s)...")

        clip_paths = []
        for i, chunk in enumerate(chunks, 1):
            print(f"  Clip {i}/{len(chunks)}: {chunk[:60]}...")
            video_url = self._animate_chunk(image_url, chunk)
            clip_path = f"{output_name}_clip{i}.mp4"
            self._download(video_url, clip_path)
            clip_paths.append(clip_path)

        print("  Stitching clips...")
        stitched_path = f"{output_name}_stitched.mp4"
        self._stitch(clip_paths, stitched_path)
        for p in clip_paths:
            os.remove(p)

        print("  Burning in subtitles...")
        final_path = f"{output_name}.mp4"
        self._burn_subtitles(stitched_path, srt_path, final_path)
        os.remove(stitched_path)

        return final_path

    def _generate_portrait(self, author: str, region: str, year: str) -> str:
        prompt = (
            f"A photorealistic portrait photograph of {author}, a person from {region} "
            f"circa {year}. Traditional clothing of the region and era. "
            f"Dignified, looking directly at the camera. Natural warm lighting. "
            f"Close-up face and shoulders. Highly detailed skin texture. "
            f"No text, no watermark."
        )
        response = self.client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size="1024x1024",
            quality="hd",
            n=1,
        )
        return response.data[0].url

    def _split_chunks(self, text: str, max_chars: int) -> list[str]:
        import re
        sentences = re.split(r'(?<=[.!?…])\s+', text.strip())
        chunks, current = [], ""
        for sentence in sentences:
            if current and len(current) + len(sentence) + 1 > max_chars:
                chunks.append(current.strip())
                current = sentence
            else:
                current = (current + " " + sentence).strip() if current else sentence
        if current:
            chunks.append(current.strip())
        return chunks

    def _animate_chunk(self, image_url: str, text: str) -> str:
        payload = {
            "source_url": image_url,
            "script": {
                "type": "text",
                "input": text,
                "provider": {
                    "type": "microsoft",
                    "voice_id": "en-NG-AbeoNeural",
                },
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

    def _stitch(self, clip_paths: list[str], output_path: str) -> None:
        if len(clip_paths) == 1:
            import shutil
            shutil.copy(clip_paths[0], output_path)
            return

        # Write concat list
        list_path = output_path + "_list.txt"
        with open(list_path, "w") as f:
            for p in clip_paths:
                f.write(f"file '{os.path.abspath(p)}'\n")

        cmd = [
            FFMPEG_PATH, "-y",
            "-f", "concat", "-safe", "0",
            "-i", list_path,
            "-c", "copy",
            output_path,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        os.remove(list_path)
        if result.returncode != 0:
            raise RuntimeError(f"ffmpeg stitch failed:\n{result.stderr}")

    def _burn_subtitles(self, video_path: str, srt_path: str, output_path: str) -> None:
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
            raise RuntimeError(f"ffmpeg subtitle burn failed:\n{result.stderr}")
