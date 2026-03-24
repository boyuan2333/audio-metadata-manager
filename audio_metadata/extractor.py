from __future__ import annotations

import importlib
import wave
from pathlib import Path
from typing import Any

from audio_metadata.models import ErrorInfo, FeatureMetadata, FileResult, TechnicalMetadata


TEMPO_MIN_DURATION_SEC = 3.0
TEMPO_MIN_BPM = 40.0
TEMPO_MAX_BPM = 220.0
TEMPO_MIN_CONFIDENCE = 0.08
TEMPO_MIN_PEAK_RATIO = 0.30
TEMPO_INFO_ERROR_TYPES = {'TempoEstimationNotApplicable'}


def extract_file_metadata(path: Path) -> FileResult:
    file_format = path.suffix.lower().lstrip('.')
    result = FileResult(
        status='failed',
        file_name=path.name,
        source_path=str(path.resolve()),
        file_format=file_format,
    )

    technical_errors: list[ErrorInfo] = []
    feature_errors: list[ErrorInfo] = []

    try:
        result.technical = extract_technical_metadata(path)
    except Exception as exc:
        technical_errors.append(build_error('technical_metadata', exc))

    if not technical_errors:
        result.features, feature_errors, result.tempo_applicable = extract_audio_features(path)

    result.duration_bucket = _classify_duration_bucket(result.technical.duration_sec)
    result.brightness = _classify_brightness(result.features.spectral_centroid_hz)
    result.is_loop = _classify_is_loop(path, result)

    result.errors.extend(technical_errors)
    result.errors.extend(feature_errors)

    if technical_errors:
        result.status = 'failed'
    elif _has_non_tempo_blocking_errors(feature_errors):
        result.status = 'partial'
    else:
        result.status = 'ok'

    return result


def extract_technical_metadata(path: Path) -> TechnicalMetadata:
    mutagen_module = _optional_import('mutagen')
    if mutagen_module is not None:
        return _extract_with_mutagen(path, mutagen_module)

    if path.suffix.lower() == '.wav':
        return _extract_wav_with_stdlib(path)

    raise RuntimeError(
        'mutagen is required to read technical metadata for this format. '
        'Install dependencies from requirements.txt.'
    )


def extract_audio_features(path: Path) -> tuple[FeatureMetadata, list[ErrorInfo], bool]:
    features = FeatureMetadata()
    errors: list[ErrorInfo] = []
    tempo_applicable = True

    try:
        numpy_module, scipy_signal_module, soundfile_module, pyloudnorm_module = _load_feature_dependencies()
        mono_signal, sample_rate = _decode_audio(path, numpy_module, soundfile_module)
    except Exception as exc:
        return features, [build_error('audio_decode', exc)], False

    if mono_signal.size == 0:
        return features, [ErrorInfo(stage='audio_decode', message='Decoded audio is empty.')], False

    features.rms = _compute_rms(mono_signal, numpy_module, errors)
    features.spectral_centroid_hz = _compute_spectral_centroid(mono_signal, sample_rate, numpy_module, errors)
    features.loudness_lufs = _compute_loudness(mono_signal, sample_rate, numpy_module, pyloudnorm_module, errors)
    (
        features.tempo_bpm,
        features.tempo_confidence,
        features.tempo_quality,
        tempo_applicable,
        tempo_note,
    ) = _compute_tempo(mono_signal, sample_rate, numpy_module, scipy_signal_module)
    if tempo_note is not None:
        errors.append(tempo_note)

    return features, errors, tempo_applicable


def _extract_with_mutagen(path: Path, mutagen_module: Any) -> TechnicalMetadata:
    audio = mutagen_module.File(path)
    if audio is None or not hasattr(audio, 'info') or audio.info is None:
        raise ValueError('Unable to parse audio metadata.')

    info = audio.info
    duration = getattr(info, 'length', None)
    sample_rate = getattr(info, 'sample_rate', None)
    channels = getattr(info, 'channels', None)

    if duration is None and path.suffix.lower() == '.wav':
        return _extract_wav_with_stdlib(path)

    return TechnicalMetadata(
        duration_sec=_round_or_none(duration, 6),
        sample_rate_hz=_int_or_none(sample_rate),
        channels=_int_or_none(channels),
    )


def _extract_wav_with_stdlib(path: Path) -> TechnicalMetadata:
    with wave.open(str(path), 'rb') as wav_file:
        frame_count = wav_file.getnframes()
        frame_rate = wav_file.getframerate()
        channels = wav_file.getnchannels()

    duration = frame_count / frame_rate if frame_rate else None
    return TechnicalMetadata(
        duration_sec=_round_or_none(duration, 6),
        sample_rate_hz=_int_or_none(frame_rate),
        channels=_int_or_none(channels),
    )


def _load_feature_dependencies() -> tuple[Any, Any, Any, Any]:
    missing: list[str] = []

    numpy_module = _optional_import('numpy')
    if numpy_module is None:
        missing.append('numpy')

    scipy_signal_module = _optional_import('scipy.signal')
    if scipy_signal_module is None:
        missing.append('scipy')

    soundfile_module = _optional_import('soundfile')
    if soundfile_module is None:
        missing.append('soundfile')

    pyloudnorm_module = _optional_import('pyloudnorm')
    if pyloudnorm_module is None:
        missing.append('pyloudnorm')

    if missing:
        missing_list = ', '.join(missing)
        raise RuntimeError(
            f'Missing optional audio feature dependencies: {missing_list}. '
            'Install requirements.txt for feature extraction.'
        )

    return numpy_module, scipy_signal_module, soundfile_module, pyloudnorm_module


def _decode_audio(path: Path, numpy_module: Any, soundfile_module: Any) -> tuple[Any, int]:
    signal, sample_rate = soundfile_module.read(str(path), always_2d=False)
    signal = numpy_module.asarray(signal, dtype='float64')

    if signal.ndim > 1:
        mono_signal = numpy_module.mean(signal, axis=1)
    else:
        mono_signal = signal

    return mono_signal, int(sample_rate)


def _compute_rms(mono_signal: Any, numpy_module: Any, errors: list[ErrorInfo]) -> float | None:
    try:
        rms = numpy_module.sqrt(numpy_module.mean(numpy_module.square(mono_signal)))
        return _round_or_none(float(rms), 6)
    except Exception as exc:
        errors.append(build_error('rms', exc))
        return None


def _compute_spectral_centroid(
    mono_signal: Any,
    sample_rate: int,
    numpy_module: Any,
    errors: list[ErrorInfo],
) -> float | None:
    try:
        spectrum = numpy_module.abs(numpy_module.fft.rfft(mono_signal))
        if spectrum.size == 0:
            return None
        total_energy = float(numpy_module.sum(spectrum))
        if total_energy <= 1e-12:
            return None
        frequencies = numpy_module.fft.rfftfreq(mono_signal.size, d=1.0 / sample_rate)
        centroid = float(numpy_module.sum(frequencies * spectrum) / total_energy)
        return _round_or_none(centroid, 3)
    except Exception as exc:
        errors.append(build_error('spectral_centroid', exc))
        return None


def _compute_loudness(
    mono_signal: Any,
    sample_rate: int,
    numpy_module: Any,
    pyloudnorm_module: Any,
    errors: list[ErrorInfo],
) -> float | None:
    try:
        meter = pyloudnorm_module.Meter(sample_rate)
        loudness = meter.integrated_loudness(numpy_module.asarray(mono_signal, dtype='float64'))
        return _round_or_none(float(loudness), 3)
    except Exception as exc:
        errors.append(build_error('loudness', exc))
        return None


def _compute_tempo(
    mono_signal: Any,
    sample_rate: int,
    numpy_module: Any,
    scipy_signal_module: Any,
) -> tuple[float | None, float | None, str | None, bool, ErrorInfo | None]:
    duration_sec = mono_signal.size / sample_rate
    if duration_sec < TEMPO_MIN_DURATION_SEC:
        return None, None, 'not_applicable', False, ErrorInfo(
            stage='tempo_bpm',
            message=(
                'tempo_bpm left null: audio too short for stable estimation '
                f'({duration_sec:.2f}s < {TEMPO_MIN_DURATION_SEC:.1f}s).'
            ),
            error_type='TempoEstimationNotApplicable',
        )

    frame_length = 2048
    hop_length = 512
    _, _, stft = scipy_signal_module.stft(
        mono_signal,
        fs=sample_rate,
        window='hann',
        nperseg=frame_length,
        noverlap=frame_length - hop_length,
        padded=False,
        boundary=None,
    )

    magnitude = numpy_module.abs(stft)
    if magnitude.shape[1] < 4:
        return None, None, 'not_applicable', False, ErrorInfo(
            stage='tempo_bpm',
            message='tempo_bpm left null: not enough analysis frames for onset tracking.',
            error_type='TempoEstimationNotApplicable',
        )

    spectral_flux = numpy_module.maximum(0.0, numpy_module.diff(magnitude, axis=1))
    onset_env = spectral_flux.mean(axis=0)
    onset_env = scipy_signal_module.medfilt(onset_env, kernel_size=5)
    onset_env = numpy_module.maximum(onset_env - onset_env.mean(), 0.0)

    peak_energy = float(numpy_module.max(onset_env)) if onset_env.size else 0.0
    if peak_energy <= 1e-9:
        return None, None, 'not_applicable', False, ErrorInfo(
            stage='tempo_bpm',
            message='tempo_bpm left null: onset energy is too weak for a stable beat estimate.',
            error_type='TempoEstimationNotApplicable',
        )

    frame_rate = sample_rate / hop_length
    min_lag = int(frame_rate * 60.0 / TEMPO_MAX_BPM)
    max_lag = int(frame_rate * 60.0 / TEMPO_MIN_BPM)

    autocorr = numpy_module.correlate(onset_env, onset_env, mode='full')[len(onset_env) - 1 :]
    if max_lag >= autocorr.size:
        max_lag = autocorr.size - 1
    if min_lag >= max_lag:
        return None, None, 'not_applicable', False, ErrorInfo(
            stage='tempo_bpm',
            message='tempo_bpm left null: onset envelope is too short for BPM lag search.',
            error_type='TempoEstimationNotApplicable',
        )

    tempo_region = autocorr[min_lag : max_lag + 1]
    peak_index = int(numpy_module.argmax(tempo_region))
    peak_value = float(tempo_region[peak_index])
    zero_lag = float(autocorr[0]) if autocorr.size else 0.0
    if zero_lag <= 1e-9:
        return None, None, 'not_applicable', False, ErrorInfo(
            stage='tempo_bpm',
            message='tempo_bpm left null: autocorrelation energy is too low.',
            error_type='TempoEstimationNotApplicable',
        )

    confidence = peak_value / zero_lag
    raw_bpm = 60.0 * frame_rate / (peak_index + min_lag)
    if raw_bpm < TEMPO_MIN_BPM or raw_bpm > TEMPO_MAX_BPM:
        return None, _round_or_none(confidence, 3), 'not_applicable', False, ErrorInfo(
            stage='tempo_bpm',
            message=(
                'tempo_bpm left null: estimated tempo '
                f'{raw_bpm:.3f} BPM is outside the supported range.'
            ),
            error_type='TempoEstimationNotApplicable',
        )

    if confidence < TEMPO_MIN_CONFIDENCE:
        return None, _round_or_none(confidence, 3), 'not_applicable', False, ErrorInfo(
            stage='tempo_bpm',
            message=f'tempo_bpm left null: periodic beat confidence is too low ({confidence:.3f}).',
            error_type='TempoEstimationNotApplicable',
        )

    peak_threshold = peak_energy * 0.35
    min_peak_distance = max(1, int(min_lag * 0.8))
    onset_peaks, _ = scipy_signal_module.find_peaks(
        onset_env,
        height=peak_threshold,
        distance=min_peak_distance,
    )
    expected_beats = duration_sec * raw_bpm / 60.0
    peak_ratio = (len(onset_peaks) / expected_beats) if expected_beats > 0 else 0.0
    if peak_ratio < TEMPO_MIN_PEAK_RATIO:
        return None, _round_or_none(confidence, 3), 'not_applicable', False, ErrorInfo(
            stage='tempo_bpm',
            message=(
                'tempo_bpm left null: detected onsets are not periodic enough '
                f'for a stable beat estimate (peak_ratio={peak_ratio:.3f}).'
            ),
            error_type='TempoEstimationNotApplicable',
        )

    bpm = _normalize_tempo(raw_bpm, confidence)
    tempo_confidence = _round_or_none(confidence, 3)
    tempo_quality = _classify_tempo_quality(confidence)
    return _round_or_none(bpm, 3), tempo_confidence, tempo_quality, True, None


def _normalize_tempo(raw_bpm: float, confidence: float) -> float:
    bpm = raw_bpm
    if bpm < 70.0 and confidence >= 0.5:
        bpm *= 2.0
    elif bpm > 160.0 and confidence >= 0.3:
        bpm /= 2.0
    return bpm


def _classify_tempo_quality(confidence: float) -> str:
    if confidence >= 0.6:
        return 'high'
    if confidence >= 0.3:
        return 'medium'
    return 'low'


def _classify_duration_bucket(duration_sec: float | None) -> str | None:
    if duration_sec is None:
        return None
    if duration_sec < 1.0:
        return 'micro'
    if duration_sec < 10.0:
        return 'short'
    if duration_sec < 60.0:
        return 'medium'
    return 'long'


def _classify_brightness(spectral_centroid_hz: float | None) -> str | None:
    if spectral_centroid_hz is None:
        return None
    if spectral_centroid_hz < 1500.0:
        return 'dark'
    if spectral_centroid_hz < 3500.0:
        return 'balanced'
    if spectral_centroid_hz < 6000.0:
        return 'bright'
    return 'very_bright'


def _classify_is_loop(path: Path, result: FileResult) -> bool | None:
    file_name = path.stem.casefold().replace('_', ' ').replace('-', ' ')
    positive_tokens = ('loop',)
    negative_tokens = ('oneshot', 'one shot', 'sweep', 'blip', 'impact', 'hit', 'stab')

    if any(token in file_name for token in positive_tokens):
        return True
    if any(token in file_name for token in negative_tokens):
        return False

    duration_sec = result.technical.duration_sec
    tempo_bpm = result.features.tempo_bpm
    if duration_sec is None:
        return None
    if duration_sec > 32.0:
        return False
    if tempo_bpm is None or result.tempo_applicable is False:
        return False

    beat_count = duration_sec * tempo_bpm / 60.0
    for candidate in (4.0, 8.0, 16.0, 32.0, 64.0):
        tolerance = max(0.35, candidate * 0.08)
        if abs(beat_count - candidate) <= tolerance:
            return True
    return False


def _has_non_tempo_blocking_errors(errors: list[ErrorInfo]) -> bool:
    return any(error.error_type not in TEMPO_INFO_ERROR_TYPES for error in errors)


def _optional_import(module_name: str) -> Any | None:
    try:
        return importlib.import_module(module_name)
    except Exception:
        return None


def build_error(stage: str, exc: Exception) -> ErrorInfo:
    return ErrorInfo(
        stage=stage,
        message=str(exc) or exc.__class__.__name__,
        error_type=exc.__class__.__name__,
    )


def _round_or_none(value: float | None, digits: int) -> float | None:
    if value is None:
        return None
    return round(float(value), digits)


def _int_or_none(value: Any) -> int | None:
    if value is None:
        return None
    return int(value)
