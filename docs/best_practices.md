# GPT-SoVITS Galgame 语音克隆最佳实践

本文档总结了使用 GPT-SoVITS 进行 Galgame 声音克隆过程中积累的所有经验。

## 1. 端口配置

| 服务 | 端口 | 说明 |
|------|------|------|
| WebUI 训练界面 | **9874** | 用于可视化训练管理 |
| 推理 API | **9872** | Gradio API，用于 TTS 合成 |

两者是完全独立的服务，不能混淆。推理脚本应该连接 9872 端口。

## 2. ASR 缓存陷阱

`output/asr_opt/` 目录下会保留旧项目的 `.list` 文件。

**危险场景**: 如果之前训练过其他模型，旧的 `.list` 文件可能被错误读取。

**解决方案**:
- 按切片目录名精确匹配 ASR 输出文件（`{sliced_dir_name}.list`）
- 训练前清理旧的中间文件：
  - `2-name2text-*.txt`
  - `6-name2semantic-*.tsv`
  - `3-bert/`, `4-cnhubert/`, `5-wav32k/` 目录

## 3. V4 SoVITS LoRA 推理过短问题

**症状**: V4 LoRA 训练后的权重在推理时输出极短音频（~0.6s），而不是预期的 3-8s。

**原因**: V4 LoRA 与推理管线的兼容性问题，可能和训练数据量不足有关。

**解决方案**: 使用 V2 SoVITS 预训练模型 + 微调 GPT 组合
- SoVITS: `GPT_SoVITS/pretrained_models/gsv-v2final-pretrained/s2G2333k.pth`
- GPT: `GPT_weights_v4/{speaker}-e{epoch}.ckpt`

**自动检测**: 合成第一句台词后检查时长，如果 < 1.5s 自动回退 V2。

## 4. prompt_text 空字符串 Bug

`inference_webui.py` 第 727 行:
```python
if prompt_text[-1] not in splits:
```

空字符串会触发 `IndexError: string index out of range`。

**解决方案**: 始终传入非空的占位文本，如 `"你好。"`。

## 5. 训练参数推荐

### SoVITS V4 LoRA
| 参数 | 推荐值 | 说明 |
|------|--------|------|
| batch_size | 3 | RTX 4090 安全值 |
| epochs | 4-8 | 数据少用 4，多用 8 |
| lora_rank | 32 | 平衡质量与速度 |
| fp16_run | True | 节省显存 |
| save_every_epoch | 2 | 方便选择最优 |

### GPT (s1)
| 参数 | 推荐值 | 说明 |
|------|--------|------|
| batch_size | 12 | RTX 4090 安全值 |
| epochs | 15-20 | 15 足够 |
| save_every_n_epoch | 5 | 保存 3 个检查点 |
| pretrained_s1 | s1v3.ckpt | V3/V4 通用 |

## 6. 推理参数

| 参数 | V2 SoVITS | V4 SoVITS |
|------|-----------|----------|
| sample_steps | 32 | 8 |
| top_k | 15 | 15 |
| top_p | 1.0 | 1.0 |
| temperature | 1.0 | 1.0 |
| speed | 1.0 | 1.0 |
| ref_text_free | True | True |
| prompt_text | "你好。"(占位) | "你好。"(占位) |

## 7. 数据量与效果关系

| 数据量 | 效果 | 建议来源 |
|--------|------|----------|
| 1-3 min | 基本可用，音色有偏差 | 1 个短视频 |
| 3-10 min | 较好 | 1-2 个视频 |
| 10-30 min | 优秀，音色还原度高 | 多个视频 |
| 30-60 min | 专业级 | 采访/演讲 |

## 8. 音频预处理要点

- **UVR5 模型**: HP5_only_main_vocal 效果最好
- **切片参数**: 2-15 秒，threshold=-40dB
- **采样率**: 保持原始采样率，训练脚本会自动重采样到 32kHz
- **干净录音优先**: 没有 BGM、混响的录音质量最佳

## 9. subprocess 输出陷阱

使用 `subprocess.run(capture_output=True)` 会吞掉所有输出，导致错误难以排查。

**建议**: 训练脚本中让 stdout/stderr 直接打印，不要捕获：
```python
subprocess.run(cmd, shell=True)  # 不要加 capture_output=True
```

## 10. 训练数据格式化合并

数据格式化脚本（1-get-text.py 等）输出分片文件（如 `2-name2text-0.txt`），
但训练脚本需要合并后的文件（`2-name2text.txt`）。

**必须手动合并**:
```python
# 合并 name2text
shutil.copy('logs/exp/2-name2text-0.txt', 'logs/exp/2-name2text.txt')

# 合并 semantic（需要加 header）
with open('logs/exp/6-name2semantic.tsv', 'w') as f:
    f.write('item_name\tsemantic_audio\n')
    f.write(open('logs/exp/6-name2semantic-0.tsv').read())
```
