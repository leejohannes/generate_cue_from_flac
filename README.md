# FLAC Silence Splitter (CUE Generator)

本工具用于对整轨 FLAC 文件进行静音检测，并自动生成 CUE 文件。  
适合遗失原始 `.cue` 时，通过音频中“空白区间”来恢复分轨。

---

## 📦 环境依赖

- Python 3.8+
- [pydub](https://github.com/jiaaro/pydub)
- [tqdm](https://github.com/tqdm/tqdm)
- [FFmpeg](https://ffmpeg.org/) （必须安装，否则 `pydub` 无法读取 FLAC）

安装依赖：
```bash
pip install pydub tqdm
```

安装 FFmpeg：
Ubuntu/Debian: `sudo apt install ffmpeg`
macOS (Homebrew): `brew install ffmpeg`
Windows: 从 [FFmpeg Builds](https://www.gyan.dev/ffmpeg/builds/) 下载并加入 PATH

## 🧩 设计思路

1. 遍历整轨 FLAC，逐步检测音量（默认步长 20ms）
2. 判断连续音量低于 -40 dBFS 且持续时间 ≥ 1000 ms 的区间为「静音」
3. 取静音区间的 中点 作为分轨点
4. 特殊处理：
   - 第一个分轨点固定为 0s
   - 如果最后一个静音点离音频末尾 ≤ 5 秒，则丢弃，避免生成空轨
   - 最后一轨延伸到文件结尾
5. 输出标准 .cue 文件

## ⚙️ 脚本参数
```
usage: generate_cue_from_flac_midpoint.py [-h] [--silence-thresh SILENCE_THRESH]
                                          [--min-silence-len MIN_SILENCE_LEN]
                                          [--step-ms STEP_MS]
                                          [--min-tail-gap MIN_TAIL_GAP]
                                          flac_path
```
`flac_path`
输入的 FLAC 文件路径

`--silence-thresh` (默认 `-40`)
静音判定的阈值（单位 dBFS）

`--min-silence-len` (默认 `1000`)
最小静音长度（单位 ms），低于阈值并持续该时间才算静音

`--step-ms` (默认 `20`)
分析步长（单位 ms），越小越精细，但分析速度越慢

`--min-tail-gap` (默认 `5`)
若最后一个静音点距离文件尾 ≤ 此值（秒），则忽略该分轨点

## ▶️ 使用示例

生成默认参数的 `.cue`：
```
python generate_cue_from_flac_midpoint.py "album.flac"
```

指定静音阈值 -45 dB、最小静音长度 1500 ms：
```
python generate_cue_from_flac_midpoint.py "album.flac" \
  --silence-thresh -45 \
  --min-silence-len 1500
```

更高精度分析（10ms 步长）并忽略距离结尾 3 秒内的分轨点：
```
python generate_cue_from_flac_midpoint.py "album.flac" \
  --step-ms 10 \
  --min-tail-gap 3
```

运行后将在同目录生成：
```
album_generated.cue
```
## 📚 输出示例

```
PERFORMER "Unknown Artist"
TITLE "album"
FILE "album.flac" WAVE
  TRACK 01 AUDIO
    TITLE "Track 01"
    PERFORMER "Unknown Artist"
    INDEX 01 00:00:00
  TRACK 02 AUDIO
    TITLE "Track 02"
    PERFORMER "Unknown Artist"
    INDEX 01 05:42:20
  TRACK 03 AUDIO
    TITLE "Track 03"
    PERFORMER "Unknown Artist"
    INDEX 01 12:15:40
```
