import io
from agents.base_agent import BaseAgent


def _seconds_to_srt_time(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int(round((seconds % 1) * 1000))
    return f"{h:02}:{m:02}:{s:02},{ms:03}"


class TranscriptSyncAgent(BaseAgent):
    """Transcribes audio with Whisper to produce a timestamped SRT subtitle file."""

    def run(self, audio_path: str, srt_path: str) -> str:
        with open(audio_path, "rb") as f:
            audio_bytes = f.read()

        response = self.client.audio.transcriptions.create(
            model="whisper-1",
            file=("audio.mp3", io.BytesIO(audio_bytes), "audio/mpeg"),
            response_format="verbose_json",
            timestamp_granularities=["word"],
        )

        words = response.words or []
        srt_lines = []
        index = 1
        chunk_words = []
        chunk_start = None

        for word in words:
            if chunk_start is None:
                chunk_start = word.start
            chunk_words.append(word.word)

            # New subtitle block every ~8 words or at sentence boundaries
            ends_sentence = word.word.rstrip().endswith((".", "!", "?", "..."))
            if len(chunk_words) >= 8 or ends_sentence:
                chunk_end = word.end
                text = " ".join(chunk_words).strip()
                srt_lines.append(f"{index}")
                srt_lines.append(f"{_seconds_to_srt_time(chunk_start)} --> {_seconds_to_srt_time(chunk_end)}")
                srt_lines.append(text)
                srt_lines.append("")
                index += 1
                chunk_words = []
                chunk_start = None

        # Flush remaining words
        if chunk_words and chunk_start is not None:
            chunk_end = words[-1].end
            text = " ".join(chunk_words).strip()
            srt_lines.append(f"{index}")
            srt_lines.append(f"{_seconds_to_srt_time(chunk_start)} --> {_seconds_to_srt_time(chunk_end)}")
            srt_lines.append(text)
            srt_lines.append("")

        srt_content = "\n".join(srt_lines)
        with open(srt_path, "w", encoding="utf-8") as f:
            f.write(srt_content)

        return srt_path
