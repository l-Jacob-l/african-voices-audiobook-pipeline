from pydantic import BaseModel, field_validator
from typing import List


class VoiceConfig(BaseModel):
    voice: str
    tone: str
    speed: float
    accent: str
    instructions: str = ""  # delivery instructions for gpt-4o-audio-preview


class PipelineResult(BaseModel):
    script: str
    voice_config: VoiceConfig
    audio_path: str


class SourceRecord(BaseModel):
    title: str
    author: str
    year: str
    region: str
    source: str
    pdf_link: str
    access: str  # "CONFIRMED" | "UNCERTAIN"

    @field_validator("year", mode="before")
    @classmethod
    def coerce_year(cls, v):
        return str(v)


class HistoryPipelineResult(BaseModel):
    sources: List[SourceRecord]
    validated_sources: List[SourceRecord]
    extracted_text: str
    script: str
    voice_config: VoiceConfig
    audio_path: str


class AudiobookResult(BaseModel):
    intro: str
    script: str
    audio_path: str
    srt_path: str
    video_path: str
