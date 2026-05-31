<p align="center">
  <img src="assets/banner.png" alt="GPT-SoVITS Galgame Pipeline Banner" width="100%"/>
</p>

<h1 align="center">🎙️ GPT-SoVITS Galgame Pipeline</h1>

<p align="center">
  <strong>一键从视频到 Galgame 语音 — 端到端 AI 声音克隆管线</strong><br/>
  <em>One-click Video-to-Galgame Voice — End-to-End AI Voice Cloning Pipeline</em>
</p>

<p align="center">
  <a href="#-快速开始--quick-start"><img src="https://img.shields.io/badge/Quick%20Start-点击开始-brightgreen?style=for-the-badge" alt="Quick Start"/></a>
  <a href="https://github.com/RVC-Boss/GPT-SoVITS"><img src="https://img.shields.io/badge/Based%20on-GPT--SoVITS%20v4-blue?style=for-the-badge" alt="GPT-SoVITS"/></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge" alt="MIT License"/></a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white" alt="Python"/>
  <img src="https://img.shields.io/badge/NVIDIA-RTX%203090%2F4090-76B900?logo=nvidia&logoColor=white" alt="NVIDIA GPU"/>
  <img src="https://img.shields.io/badge/Platform-Windows-0078D6?logo=windows&logoColor=white" alt="Windows"/>
  <img src="https://img.shields.io/badge/Audio-Bilibili%20%7C%20YouTube-FF0000?logo=youtube&logoColor=white" alt="Audio Source"/>
</p>

---

## 🌟 项目亮点 | Highlights

<table>
<tr>
<td width="50%">

### 🇨🇳 中文

**只需一个视频链接，就能让你喜欢的角色「开口说话」。**

本项目是一个**全自动 Galgame 语音合成管线**，基于 [GPT-SoVITS v4](https://github.com/RVC-Boss/GPT-SoVITS) 构建。从 Bilibili/YouTube 下载音频开始，经过 AI 人声分离、语音识别、模型训练，最终生成覆盖**日常、告白、战斗、温柔、傲娇、离别**等多种情感的 Galgame 台词语音。

✅ **一条命令跑完全流程** — 无需手动操作 WebUI  
✅ **自动 V4→V2 回退** — 数据量不足时智能切换模型  
✅ **内置 12 条经典台词** — 覆盖 8 种 Galgame 常见情感  
✅ **最少 1 分钟音频即可训练** — 一个短视频就能开始  

</td>
<td width="50%">

### 🇬🇧 English

**Turn any video into Galgame character voices with a single command.**

A fully automated **Galgame voice synthesis pipeline** built on [GPT-SoVITS v4](https://github.com/RVC-Boss/GPT-SoVITS). Downloads audio from Bilibili/YouTube, separates vocals with AI, transcribes speech, trains a speaker-specific model, and generates multi-emotion dialogue lines covering **daily life, confession, battle, tender, tsundere, farewell** and more.

✅ **One command, full pipeline** — No manual WebUI interaction  
✅ **Auto V4→V2 fallback** — Smart model switching for limited data  
✅ **12 built-in classic lines** — Covering 8 common Galgame emotions  
✅ **Train with as little as 1 min audio** — Start from a single video  

</td>
</tr>
</table>

---

## 🔧 管线架构 | Pipeline Architecture

<p align="center">
  <img src="assets/pipeline.png" alt="Pipeline Architecture" width="90%"/>
</p>

```
📥 Download        从 Bilibili/YouTube 下载音频
       ↓           Download audio from Bilibili/YouTube
🎵 UVR5            AI 人声分离 (HP5_only_main_vocal)
       ↓           AI vocal separation
🗣️ ASR             FunASR 语音识别 + 智能切片
       ↓           Speech recognition + smart slicing
📊 Format          BERT + HuBERT + Semantic Token 特征提取
       ↓           Feature extraction
🧠 Train           SoVITS V4 LoRA + GPT 模型训练
       ↓           Model training
🎭 Synthesize      多情感 Galgame 台词合成
                   Multi-emotion dialogue synthesis
```

---

## 📋 环境要求 | Requirements

| 组件 Component | 要求 Requirement |
|---|---|
| **GPU** | NVIDIA GPU ≥ 16GB VRAM（推荐 RTX 3090 / 4090） |
| **GPT-SoVITS** | [v4 版本](https://github.com/RVC-Boss/GPT-SoVITS)，需预先安装 |
| **Python** | 3.10+（GPT-SoVITS 自带 runtime 即可） |
| **yt-dlp** | 用于下载 Bilibili / YouTube 音频 |
| **OS** | Windows 10/11（推荐），Linux 也可适配 |

---

## 🚀 快速开始 | Quick Start

### 安装 | Installation

```bash
# 克隆本仓库 | Clone this repo
git clone https://github.com/panyero-mobile/GPT-SoVITS-Galgame-Pipeline.git
cd GPT-SoVITS-Galgame-Pipeline

# 确保已安装 uv (Python 包管理器)
# Ensure uv is installed
pip install uv
```

### 一键全流程 | One-Click Full Pipeline

```bash
uv run scripts/galgame_voice.py pipeline \
  --url "https://www.bilibili.com/video/BVxxxxxx" \
  --speaker "my_character" \
  --output ./output
```

**就这么简单！** 🎉 等待训练完成后，你的 Galgame 语音文件将出现在 `./output/galgame_audio/` 目录。

**That's it!** 🎉 After training completes, your Galgame voice files will be in `./output/galgame_audio/`.

### 分步执行 | Step by Step

<details>
<summary><b>点击展开分步说明 | Click to expand step-by-step</b></summary>

```bash
# 1️⃣ 环境检查 | Environment check
uv run scripts/galgame_voice.py setup --output ./setup_report.json

# 2️⃣ 下载音频 | Download audio
uv run scripts/galgame_voice.py download \
  --url "https://www.bilibili.com/video/BVxxxxxx" \
  --speaker "character_name" \
  --output ./download_report.json

# 3️⃣ 预处理 (UVR5 人声分离 + 切片 + ASR)
# Preprocess (UVR5 vocal separation + slicing + ASR)
uv run scripts/galgame_voice.py preprocess \
  --input ./raw_audio/audio.wav \
  --speaker "character_name" \
  --output ./preprocess_report.json

# 4️⃣ 格式化训练数据 | Format training data
uv run scripts/galgame_voice.py format \
  --speaker "character_name" \
  --output ./format_report.json

# 5️⃣ 训练模型 | Train model
uv run scripts/galgame_voice.py train \
  --speaker "character_name" \
  --sovits-epochs 4 \
  --gpt-epochs 15 \
  --output ./train_report.json

# 6️⃣ 合成 Galgame 台词 | Synthesize Galgame lines
uv run scripts/galgame_voice.py synthesize \
  --speaker "character_name" \
  --output ./galgame_output
```

</details>

---

## 🎭 内置台词 | Built-in Dialogue Lines

项目内置 **12 条经典 Galgame 台词**，覆盖 8 种常见情感场景：

The project includes **12 classic Galgame lines** covering 8 common emotional scenarios:

| 情感 Emotion | 示例 Example |
|---|---|
| 🌅 **日常** Daily | 「早上好啊，今天天气真不错呢。要不要一起去学校后面的咖啡厅坐坐？」 |
| 💕 **告白** Confession | 「那个……我有件事情想跟你说。其实……从很久以前开始，我就一直……喜欢你。」 |
| ⚔️ **战斗** Battle | 「就算前方是绝路，我也不会退缩！为了保护你，我愿意赌上一切！」 |
| 🌸 **温柔** Tender | 「别哭了。不管发生什么事情，我都会陪在你身边的。所以，不用害怕。」 |
| 😤 **傲娇** Tsundere | 「才、才不是因为担心你才来的！只是正好路过而已……别误会了！」 |
| 😂 **搞笑** Comedy | 「等等等等！那个不是我的！你听我解释！事情不是你想的那样啊！」 |
| 🍂 **离别** Farewell | 「如果有一天我不在了……你要好好照顾自己。答应我，要幸福地活下去。」 |
| 🌟 **重逢** Reunion | 「真的是你吗！太好了！我一直在找你，终于又见面了！」 |

> 💡 你也可以自定义台词！创建一个 JSON 文件，使用 `--lines your_lines.json` 参数即可。  
> 💡 You can also customize lines! Create a JSON file and use the `--lines your_lines.json` parameter.

---

## ⚙️ 训练参数推荐 | Recommended Training Parameters

### SoVITS V4 LoRA

| 参数 Parameter | 推荐值 Value | 说明 Note |
|---|---|---|
| `batch_size` | 3 | RTX 4090 安全值 / Safe for 4090 |
| `epochs` | 4-8 | 数据少用 4，多用 8 / 4 for limited data, 8 for more |
| `lora_rank` | 32 | 平衡质量与速度 / Balance quality and speed |
| `fp16_run` | True | 节省显存 / Save VRAM |

### GPT (s1)

| 参数 Parameter | 推荐值 Value | 说明 Note |
|---|---|---|
| `batch_size` | 12 | RTX 4090 安全值 / Safe for 4090 |
| `epochs` | 15-20 | 15 通常足够 / 15 is usually enough |
| `save_every_n_epoch` | 5 | 保存 3 个检查点 / Save 3 checkpoints |

### 数据量与效果 | Data Volume vs Quality

| 数据量 Data | 效果 Quality | 建议来源 Suggested Source |
|---|---|---|
| 1-3 min | ⭐⭐ 基本可用 | 1 个短视频 / 1 short video |
| 3-10 min | ⭐⭐⭐ 较好 | 1-2 个视频 / 1-2 videos |
| 10-30 min | ⭐⭐⭐⭐ 优秀 | 多个视频 / Multiple videos |
| 30-60 min | ⭐⭐⭐⭐⭐ 专业级 | 采访/演讲 / Interview/Speech |

---

## 🛡️ 智能容错 | Smart Error Handling

### 自动 V4→V2 回退 | Automatic V4→V2 Fallback

当训练数据量不足时，V4 SoVITS LoRA 可能产生极短音频（<1.5秒）。本管线会**自动检测并切换**到 V2 SoVITS 预训练模型 + 微调 GPT 的组合，确保输出质量。

When training data is limited, V4 SoVITS LoRA may produce very short audio (<1.5s). The pipeline **automatically detects and switches** to a V2 SoVITS pretrained + fine-tuned GPT combination to ensure output quality.

### 其他内置保护 | Other Built-in Protections

- 🧹 **ASR 缓存自动清理** — 防止旧数据污染新训练
- 🔧 **prompt_text 占位符** — 避免空字符串导致的 IndexError
- 📊 **分片文件自动合并** — 自动处理 `name2text` 和 `name2semantic` 合并
- 🖥️ **训练输出可视化** — 不捕获 stdout/stderr，便于实时调试

---

## 📁 项目结构 | Project Structure

```
GPT-SoVITS-Galgame-Pipeline/
├── 📄 README.md                    # 本文件
├── 📄 LICENSE                      # MIT License
├── 📂 scripts/
│   ├── 🐍 galgame_voice.py        # 主管线脚本 (981 行)
│   └── 📋 default_lines.json      # 内置 12 条 Galgame 台词
├── 📂 docs/
│   └── 📖 best_practices.md       # GPT-SoVITS 最佳实践
├── 📂 examples/
│   └── 📋 custom_lines_example.json  # 自定义台词示例
└── 📂 assets/
    ├── 🖼️ banner.png               # 项目横幅
    └── 🖼️ pipeline.png             # 管线架构图
```

---

## ❓ 常见问题 | FAQ

<details>
<summary><b>Q: 需要多少时间训练？| How long does training take?</b></summary>

在 RTX 4090 上，SoVITS 4 epochs + GPT 15 epochs 大约需要 **5-15 分钟**（取决于数据量）。

On RTX 4090, SoVITS 4 epochs + GPT 15 epochs takes approximately **5-15 minutes** (depending on data volume).
</details>

<details>
<summary><b>Q: 支持英文/日语吗？| Does it support English/Japanese?</b></summary>

当前默认配置为中文。GPT-SoVITS 本身支持多语言，修改 ASR 和推理的语言参数即可适配。

Currently configured for Chinese by default. GPT-SoVITS supports multiple languages — modify the ASR and inference language parameters to adapt.
</details>

<details>
<summary><b>Q: 可以用自己的音频文件吗？| Can I use my own audio files?</b></summary>

可以！跳过 `download` 步骤，直接从 `preprocess` 开始，用 `--input` 指定你的音频文件路径。

Yes! Skip the `download` step and start from `preprocess`, specifying your audio file path with `--input`.
</details>

<details>
<summary><b>Q: 为什么合成的音频很短？| Why is the synthesized audio very short?</b></summary>

这是 V4 SoVITS LoRA 在数据量不足时的已知问题。管线会自动回退到 V2 SoVITS。如果仍有问题，尝试增加训练数据量。

This is a known issue with V4 SoVITS LoRA when training data is limited. The pipeline automatically falls back to V2 SoVITS. If issues persist, try increasing training data volume.
</details>

---

## 🤝 贡献 | Contributing

欢迎贡献！请随时提交 Issue 或 Pull Request。

Contributions are welcome! Feel free to open Issues or Pull Requests.

- 🐛 **Bug Reports**: 提交 Issue 描述问题和复现步骤
- 💡 **Feature Requests**: 提交 Issue 描述你想要的功能
- 🔀 **Pull Requests**: Fork 后修改并提交 PR

---

## 📜 License

This project is licensed under the [MIT License](LICENSE).

---

## 🙏 致谢 | Acknowledgements

- [GPT-SoVITS](https://github.com/RVC-Boss/GPT-SoVITS) — 核心 TTS 引擎 / Core TTS Engine
- [UVR5](https://github.com/Anjok07/ultimatevocalremovergui) — AI 人声分离 / AI Vocal Separation
- [FunASR](https://github.com/modelscope/FunASR) — 语音识别 / Speech Recognition
- [yt-dlp](https://github.com/yt-dlp/yt-dlp) — 视频音频下载 / Video Audio Download

---

<p align="center">
  <b>⭐ 如果这个项目对你有帮助，请给个 Star！</b><br/>
  <b>⭐ If this project helps you, please give it a Star!</b>
</p>

<p align="center">
  Made with ❤️ for the Galgame community
</p>
