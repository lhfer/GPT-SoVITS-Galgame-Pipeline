# Changelog

## [1.0.0] - 2026-06-01

### 首次发布

- 完整的端到端管线：从视频 URL 到多情感 Galgame 语音
- 支持 Bilibili / YouTube 音频下载（via yt-dlp）
- UVR5 AI 人声分离（HP5_only_main_vocal）
- FunASR 语音识别 + 智能切片（2-15 秒）
- BERT / HuBERT / Semantic Token 特征提取
- SoVITS V4 LoRA + GPT 模型训练
- 多情感台词合成（内置 12 条台词，覆盖 8 种情感）
- 自动 V4→V2 SoVITS 回退机制
- ASR 缓存自动清理，防止数据污染
- `pipeline` 一键命令，支持分步执行
