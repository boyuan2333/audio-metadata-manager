from __future__ import annotations

from dataclasses import asdict, dataclass, field


@dataclass
class ErrorInfo:
    stage: str
    message: str
    error_type: str | None = None


@dataclass
class TechnicalMetadata:
    duration_sec: float | None = None
    sample_rate_hz: int | None = None
    channels: int | None = None


@dataclass
class FeatureMetadata:
    loudness_lufs: float | None = None
    tempo_bpm: float | None = None
    tempo_confidence: float | None = None
    tempo_quality: str | None = None
    spectral_centroid_hz: float | None = None
    rms: float | None = None


@dataclass
class FileResult:
    status: str
    file_name: str
    source_path: str
    file_format: str
    tempo_applicable: bool | None = None
    is_loop: bool | None = None
    duration_bucket: str | None = None
    brightness: str | None = None
    technical: TechnicalMetadata = field(default_factory=TechnicalMetadata)
    features: FeatureMetadata = field(default_factory=FeatureMetadata)
    errors: list[ErrorInfo] = field(default_factory=list)


@dataclass
class RunSummary:
    generated_at: str
    input_dir: str
    output_path: str
    recursive: bool
    total_files: int
    ok_count: int
    partial_count: int
    failed_count: int


@dataclass
class OutputPayload:
    run: RunSummary
    files: list[FileResult]

    def to_dict(self) -> dict:
        return asdict(self)
