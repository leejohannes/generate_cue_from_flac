import argparse
import os
from pydub import AudioSegment
from tqdm import tqdm

def sec_to_mmssff(seconds: float) -> str:
    """Convert seconds to mm:ss:ff (CD frames, 1 sec = 75 frames)."""
    total_frames = int(round(seconds * 75))
    minutes = total_frames // (60 * 75)
    seconds_part = (total_frames // 75) % 60
    frames = total_frames % 75
    return f"{minutes:02d}:{seconds_part:02d}:{frames:02d}"

def detect_silence_midpoints(audio, silence_thresh=-60, min_silence_len=1000, step_ms=20):
    """检测静音并取中点"""
    total_ms = len(audio)
    silent_ranges = []
    current_silence = None

    for i in tqdm(range(0, total_ms, step_ms), desc="🔍 Analyzing audio"):
        seg = audio[i:i+step_ms]
        dB = seg.dBFS if seg.rms > 0 else -100.0

        if dB < silence_thresh:
            if current_silence is None:
                current_silence = [i, i + step_ms]
            else:
                current_silence[1] = i + step_ms
        else:
            if current_silence and (current_silence[1] - current_silence[0]) >= min_silence_len:
                midpoint = (current_silence[0] + current_silence[1]) / 2000.0
                silent_ranges.append(midpoint)
            current_silence = None

    # 结尾静音补偿
    if current_silence and (current_silence[1] - current_silence[0]) >= min_silence_len:
        midpoint = (current_silence[0] + current_silence[1]) / 2000.0
        silent_ranges.append(midpoint)

    return silent_ranges

def generate_cue(flac_path, silence_thresh=-60, min_silence_len=1000, step_ms=20, min_tail_gap=5):
    print(f"🎵 Loading {flac_path} ...")
    audio = AudioSegment.from_file(flac_path, format="flac")
    total_length = len(audio) / 1000.0  # 秒

    print(f"➡️  Detecting silences: below {silence_thresh} dB, ≥{min_silence_len} ms, step {step_ms} ms")
    splits = detect_silence_midpoints(audio, silence_thresh, min_silence_len, step_ms)

    # 过滤掉离结尾太近的分轨点
    valid_splits = [s for s in splits if (total_length - s) > min_tail_gap]

    # 构造轨道起点列表
    track_starts = [0.0] + valid_splits
    track_starts = sorted(list(set(track_starts)))

    # 最后一首延伸到文件结束
    track_starts.append(total_length)

    print(f"\n✅ Detected {len(track_starts)-1} tracks.")
    cue_lines = [
        'PERFORMER "Unknown Artist"',
        f'TITLE "{os.path.splitext(os.path.basename(flac_path))[0]}"',
        f'FILE "{os.path.basename(flac_path)}" WAVE'
    ]

    for i, start_time in enumerate(track_starts[:-1], 1):
        cue_lines.append(f'  TRACK {i:02d} AUDIO')
        cue_lines.append(f'    TITLE "Track {i:02d}"')
        cue_lines.append(f'    PERFORMER "Unknown Artist"')
        cue_lines.append(f'    INDEX 01 {sec_to_mmssff(start_time)}')

    output_path = os.path.splitext(flac_path)[0] + "_generated.cue"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(cue_lines))

    print(f"\n🎯 CUE file generated: {output_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate CUE from FLAC by detecting silence midpoints (with progress).")
    parser.add_argument("flac_path", help="Path to the FLAC file.")
    parser.add_argument("--silence-thresh", type=float, default=-60,
                        help="Silence threshold in dBFS (default -60).")
    parser.add_argument("--min-silence-len", type=int, default=1000,
                        help="Minimum silence length in ms (default 1000).")
    parser.add_argument("--step-ms", type=int, default=20,
                        help="Step size in ms for analysis (default 20).")
    parser.add_argument("--min-tail-gap", type=int, default=5,
                        help="Ignore last split if it is within N seconds of the file end (default 5).")
    args = parser.parse_args()

    generate_cue(args.flac_path, args.silence_thresh, args.min_silence_len, args.step_ms, args.min_tail_gap)
