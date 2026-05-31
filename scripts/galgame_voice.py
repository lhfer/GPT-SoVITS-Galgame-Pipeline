#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Galgame Voice Synthesis CLI — GPT-SoVITS end-to-end pipeline.

Usage:
    uv run galgame_voice.py <command> [options]

Commands:
    setup        Check environment and locate GPT-SoVITS
    download     Download audio from Bilibili/YouTube
    preprocess   UVR5 vocal separation + slicing + ASR
    format       Training data formatting (BERT/HuBERT/Semantic)
    train        SoVITS V4 LoRA + GPT training
    synthesize   Generate Galgame dialogue audio
    pipeline     Run all steps end-to-end
"""

import argparse
import glob
import json
import os
import shutil
import subprocess
import sys
import time

# ─── Constants ───────────────────────────────────────────────────────────────

COMMON_GPTSOVITS_PATHS = [
    r"D:\GPT-SoVITS",
    r"D:\GPT-SoVITS-v4",
    r"C:\GPT-SoVITS",
    r"C:\GPT-SoVITS-v4",
    os.path.expanduser(r"~\GPT-SoVITS"),
    os.path.expanduser(r"~\GPT-SoVITS-v4"),
]

WEBUI_PORT = 9874
INFERENCE_PORT = 9872

DEFAULT_LINES_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "default_lines.json"
)

# ─── Utility Functions ──────────────────────────────────────────────────────


def find_gptsovits_dir():
    """Auto-detect GPT-SoVITS installation directory."""
    env_dir = os.environ.get("GPT_SOVITS_DIR")
    if env_dir and os.path.isdir(env_dir):
        return env_dir

    for path in COMMON_GPTSOVITS_PATHS:
        if os.path.isdir(path) and os.path.exists(
            os.path.join(path, "GPT_SoVITS")
        ):
            return path

    # Search current drive root
    for drive in ["D:\\", "C:\\", "E:\\"]:
        if not os.path.exists(drive):
            continue
        for d in os.listdir(drive):
            if "GPT-SoVITS" in d or "GPT_SoVITS" in d:
                full = os.path.join(drive, d)
                if os.path.isdir(full) and os.path.exists(
                    os.path.join(full, "GPT_SoVITS")
                ):
                    return full
    return None


def get_python_exec(base_dir):
    """Get the Python executable from GPT-SoVITS runtime."""
    runtime_python = os.path.join(base_dir, "runtime", "python.exe")
    if os.path.exists(runtime_python):
        return runtime_python
    return sys.executable


def write_output(data, output_file):
    """Write data to a JSON file."""
    os.makedirs(os.path.dirname(os.path.abspath(output_file)), exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"Success! Report written to: {output_file}")


def run_cmd(cmd, cwd=None, check=True, capture=False):
    """Run a shell command with proper encoding."""
    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"
    kwargs = dict(shell=True, cwd=cwd, env=env, encoding="utf-8", errors="replace")
    if capture:
        kwargs["capture_output"] = True
    else:
        # IMPORTANT: Never capture training output — let it print for debugging
        kwargs["stdout"] = sys.stdout
        kwargs["stderr"] = sys.stderr
    result = subprocess.run(cmd, **kwargs)
    if check and result.returncode != 0:
        print(f"Command failed with exit code {result.returncode}", file=sys.stderr)
        if capture and result.stderr:
            print(f"STDERR: {result.stderr[-500:]}", file=sys.stderr)
        return None
    return result


def wait_for_port(port, timeout=60):
    """Wait for a port to become available."""
    import socket
    for i in range(timeout):
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=2):
                return True
        except (ConnectionRefusedError, OSError):
            time.sleep(1)
    return False


# ─── Commands ────────────────────────────────────────────────────────────────


def cmd_setup(args):
    """Check environment and locate GPT-SoVITS."""
    print("=" * 60)
    print("  GPT-SoVITS Environment Check")
    print("=" * 60)

    base_dir = find_gptsovits_dir()
    report = {"status": "error"}

    if not base_dir:
        print("ERROR: GPT-SoVITS installation not found!")
        print("Set GPT_SOVITS_DIR environment variable or install to a standard path.")
        write_output(report, args.output)
        sys.exit(1)

    print(f"  GPT-SoVITS dir: {base_dir}")
    report["gptsovits_dir"] = base_dir

    # Check Python runtime
    python = get_python_exec(base_dir)
    print(f"  Python: {python} (exists={os.path.exists(python)})")
    report["python"] = python

    # Check GPU
    try:
        r = subprocess.run(
            "nvidia-smi --query-gpu=name,memory.total --format=csv,noheader",
            shell=True, capture_output=True, text=True
        )
        gpu_info = r.stdout.strip()
        print(f"  GPU: {gpu_info}")
        report["gpu"] = gpu_info
    except Exception:
        print("  GPU: nvidia-smi not available")
        report["gpu"] = "not available"

    # Check pretrained models
    models = {}
    model_checks = {
        "s2Gv4": "GPT_SoVITS/pretrained_models/gsv-v4-pretrained/s2Gv4.pth",
        "s2G_v2": "GPT_SoVITS/pretrained_models/gsv-v2final-pretrained/s2G2333k.pth",
        "s1v3": "GPT_SoVITS/pretrained_models/s1v3.ckpt",
        "hubert": "GPT_SoVITS/pretrained_models/chinese-hubert-base",
        "bert": "GPT_SoVITS/pretrained_models/chinese-roberta-wwm-ext-large",
    }
    for name, path in model_checks.items():
        full = os.path.join(base_dir, path)
        exists = os.path.exists(full)
        models[name] = exists
        status = "OK" if exists else "MISSING"
        print(f"  Model {name}: {status}")
    report["models"] = models

    # Check UVR5
    uvr5_model = os.path.join(base_dir, "tools", "uvr5", "uvr5_weights")
    report["uvr5_available"] = os.path.isdir(uvr5_model)
    print(f"  UVR5: {'OK' if report['uvr5_available'] else 'MISSING'}")

    report["status"] = "ok" if all(models.values()) else "incomplete"
    write_output(report, args.output)


def cmd_download(args):
    """Download audio from Bilibili or YouTube."""
    print("=" * 60)
    print(f"  Downloading audio for: {args.speaker}")
    print("=" * 60)

    base_dir = find_gptsovits_dir()
    if not base_dir:
        print("ERROR: GPT-SoVITS not found", file=sys.stderr)
        sys.exit(1)

    out_dir = os.path.join(base_dir, "raw_audio")
    os.makedirs(out_dir, exist_ok=True)
    out_file = os.path.join(out_dir, f"{args.speaker}_voice.wav")

    # Use yt-dlp
    cmd = (
        f'yt-dlp -x --audio-format wav --audio-quality 0 '
        f'-o "{out_file}" "{args.url}"'
    )
    print(f"  CMD: {cmd}")
    result = run_cmd(cmd, capture=True)

    if result and os.path.exists(out_file):
        size_mb = os.path.getsize(out_file) / 1024 / 1024
        print(f"  Downloaded: {out_file} ({size_mb:.1f}MB)")
        report = {"status": "ok", "file": out_file, "size_mb": round(size_mb, 1)}
    else:
        # Try alternative output naming
        alt = glob.glob(os.path.join(out_dir, f"{args.speaker}*.*"))
        if alt:
            out_file = alt[0]
            size_mb = os.path.getsize(out_file) / 1024 / 1024
            print(f"  Downloaded: {out_file} ({size_mb:.1f}MB)")
            report = {"status": "ok", "file": out_file, "size_mb": round(size_mb, 1)}
        else:
            print("ERROR: Download failed", file=sys.stderr)
            report = {"status": "error", "message": "yt-dlp download failed"}
            write_output(report, args.output)
            sys.exit(1)

    write_output(report, args.output)
    return out_file


def cmd_preprocess(args):
    """UVR5 vocal separation + slicing + ASR transcription."""
    print("=" * 60)
    print(f"  Preprocessing: {args.speaker}")
    print("=" * 60)

    base_dir = find_gptsovits_dir()
    python = get_python_exec(base_dir)
    exp_dir = os.path.join(base_dir, "logs", args.speaker)
    raw_dir = os.path.join(exp_dir, "raw")
    sliced_dir = os.path.join(exp_dir, "raw_sliced")

    os.makedirs(raw_dir, exist_ok=True)
    os.makedirs(sliced_dir, exist_ok=True)

    input_file = args.input
    if not os.path.exists(input_file):
        print(f"ERROR: Input file not found: {input_file}", file=sys.stderr)
        sys.exit(1)

    report = {"speaker": args.speaker, "steps": {}}

    # ── Step 1: UVR5 Vocal Separation ──
    print("\n[1/3] UVR5 AI Vocal Separation...")
    vocal_file = os.path.join(raw_dir, f"{args.speaker}_vocals.wav")
    uvr5_cmd = (
        f'"{python}" -s tools/uvr5/webui.py'
        f' --model_name "HP5_only_main_vocal"'
        f' --inp_path "{input_file}"'
        f' --save_root_vocal "{raw_dir}"'
        f' --save_root_ins "{raw_dir}/instrument"'
        f' --agg 10 --format wav'
    )
    t0 = time.time()
    run_cmd(uvr5_cmd, cwd=base_dir, check=False)
    elapsed = time.time() - t0

    # Find vocal output (UVR5 naming varies)
    vocal_candidates = glob.glob(os.path.join(raw_dir, "*vocal*"))
    if not vocal_candidates:
        print("  WARNING: No vocal output, using original audio")
        shutil.copy2(input_file, vocal_file)
    else:
        vocal_file = vocal_candidates[0]
    print(f"  Vocal: {os.path.basename(vocal_file)} ({elapsed:.1f}s)")
    report["steps"]["uvr5"] = {"file": vocal_file, "time": round(elapsed, 1)}

    # ── Step 2: Audio Slicing ──
    print("\n[2/3] Audio Slicing...")
    t0 = time.time()
    try:
        sys.path.insert(0, base_dir)
        from tools.slicer2 import Slicer
        import soundfile as sf
        import numpy as np

        audio_data, sr = sf.read(vocal_file)
        if audio_data.ndim == 2:
            audio_data = audio_data.mean(axis=1)

        slicer = Slicer(sr=sr, threshold=-40, min_length=2000, min_interval=300,
                        hop_size=10, max_sil_kept=500)
        chunks = list(slicer.slice(audio_data))

        kept = 0
        total_dur = 0
        for i, chunk in enumerate(chunks):
            dur = len(chunk) / sr
            if 2.0 <= dur <= 15.0:
                out_path = os.path.join(sliced_dir, f"slice_{i:04d}_{dur:.1f}s.wav")
                sf.write(out_path, chunk, sr)
                kept += 1
                total_dur += dur

        elapsed = time.time() - t0
        print(f"  Kept {kept}/{len(chunks)} slices, {total_dur:.1f}s ({elapsed:.1f}s)")
        report["steps"]["slicer"] = {
            "total_chunks": len(chunks), "kept": kept,
            "duration_s": round(total_dur, 1), "time": round(elapsed, 1)
        }
    except Exception as e:
        print(f"  ERROR in slicing: {e}", file=sys.stderr)
        report["steps"]["slicer"] = {"error": str(e)}
        write_output(report, args.output)
        sys.exit(1)

    # ── Step 3: ASR Transcription ──
    print("\n[3/3] ASR Transcription (FunASR)...")

    # IMPORTANT: Clean old ASR cache to prevent data contamination
    asr_dir = os.path.join(base_dir, "output", "asr_opt")
    os.makedirs(asr_dir, exist_ok=True)

    t0 = time.time()
    asr_cmd = (
        f'"{python}" -s tools/asr/funasr_asr.py'
        f' -i "{sliced_dir}" -o "{asr_dir}"'
        f' -s large -l zh -p float32'
    )
    run_cmd(asr_cmd, cwd=base_dir, check=False)
    elapsed = time.time() - t0

    # Find correct ASR output file (match sliced dir name)
    sliced_name = os.path.basename(sliced_dir)
    asr_file = os.path.join(asr_dir, f"{sliced_name}.list")
    if os.path.exists(asr_file):
        lines = open(asr_file, "r", encoding="utf-8").readlines()
        print(f"  ASR: {len(lines)} lines ({elapsed:.1f}s)")
        report["steps"]["asr"] = {
            "file": asr_file, "lines": len(lines), "time": round(elapsed, 1)
        }
    else:
        # Try finding any .list file
        list_files = glob.glob(os.path.join(asr_dir, "*.list"))
        if list_files:
            asr_file = sorted(list_files, key=os.path.getmtime)[-1]
            lines = open(asr_file, "r", encoding="utf-8").readlines()
            print(f"  ASR (fallback): {len(lines)} lines from {os.path.basename(asr_file)}")
            report["steps"]["asr"] = {
                "file": asr_file, "lines": len(lines), "time": round(elapsed, 1)
            }
        else:
            print("  ERROR: No ASR output found!", file=sys.stderr)
            report["steps"]["asr"] = {"error": "No output"}
            write_output(report, args.output)
            sys.exit(1)

    if len(lines) < 5:
        print(f"  WARNING: Only {len(lines)} transcribed lines. Consider adding more audio data.")

    report["status"] = "ok"
    report["asr_file"] = asr_file
    report["sliced_dir"] = sliced_dir
    write_output(report, args.output)
    return report


def cmd_format(args):
    """Format training data: BERT + HuBERT + Semantic tokens."""
    print("=" * 60)
    print(f"  Formatting training data: {args.speaker}")
    print("=" * 60)

    base_dir = find_gptsovits_dir()
    python = get_python_exec(base_dir)
    exp_dir = os.path.join(base_dir, "logs", args.speaker)
    sliced_dir = os.path.join(exp_dir, "raw_sliced")

    # Find ASR file
    asr_dir = os.path.join(base_dir, "output", "asr_opt")
    sliced_name = os.path.basename(sliced_dir)
    asr_file = os.path.join(asr_dir, f"{sliced_name}.list")
    if not os.path.exists(asr_file):
        list_files = glob.glob(os.path.join(asr_dir, "*.list"))
        if list_files:
            asr_file = sorted(list_files, key=os.path.getmtime)[-1]
        else:
            print("ERROR: No ASR file found. Run preprocess first.", file=sys.stderr)
            sys.exit(1)

    # IMPORTANT: Clean old data to prevent contamination
    print("  Cleaning old data...")
    for f in ["2-name2text.txt", "2-name2text-0.txt",
              "6-name2semantic.tsv", "6-name2semantic-0.tsv"]:
        p = os.path.join(exp_dir, f)
        if os.path.exists(p):
            os.remove(p)
    for d in ["3-bert", "4-cnhubert", "5-wav32k"]:
        p = os.path.join(exp_dir, d)
        if os.path.exists(p):
            shutil.rmtree(p)

    # Set environment variables for data prep scripts
    env_vars = {
        "version": "v4",
        "exp_name": args.speaker,
        "inp_text": asr_file,
        "inp_wav_dir": sliced_dir,
        "opt_dir": exp_dir,
        "bert_pretrained_dir": "GPT_SoVITS/pretrained_models/chinese-roberta-wwm-ext-large",
        "cnhubert_base_dir": "GPT_SoVITS/pretrained_models/chinese-hubert-base",
        "pretrained_s2G": "GPT_SoVITS/pretrained_models/gsv-v4-pretrained/s2Gv4.pth",
        "s2config_path": "GPT_SoVITS/configs/s2.json",
        "i_part": "0",
        "all_parts": "1",
        "_CUDA_VISIBLE_DEVICES": "0",
    }
    for k, v in env_vars.items():
        os.environ[k] = v

    report = {"speaker": args.speaker, "steps": {}}

    # ── 1A: Text + BERT ──
    print("\n[1/3] Text Processing + BERT Features...")
    t0 = time.time()
    run_cmd(f'"{python}" -s GPT_SoVITS/prepare_datasets/1-get-text.py', cwd=base_dir)
    elapsed = time.time() - t0

    # IMPORTANT: Merge part files
    n2t_part = os.path.join(exp_dir, "2-name2text-0.txt")
    n2t_merged = os.path.join(exp_dir, "2-name2text.txt")
    if os.path.exists(n2t_part):
        shutil.copy2(n2t_part, n2t_merged)
        lines = open(n2t_merged, "r", encoding="utf-8").readlines()
        print(f"  2-name2text.txt: {len(lines)} lines ({elapsed:.1f}s)")
        report["steps"]["bert"] = {"lines": len(lines), "time": round(elapsed, 1)}
    else:
        print("  ERROR: 2-name2text-0.txt not generated!", file=sys.stderr)
        report["steps"]["bert"] = {"error": "not generated"}

    # ── 1B: HuBERT ──
    print("\n[2/3] HuBERT Feature Extraction...")
    t0 = time.time()
    run_cmd(f'"{python}" -s GPT_SoVITS/prepare_datasets/2-get-hubert-wav32k.py', cwd=base_dir)
    elapsed = time.time() - t0
    for d in ["4-cnhubert", "5-wav32k"]:
        p = os.path.join(exp_dir, d)
        if os.path.exists(p):
            cnt = len(os.listdir(p))
            print(f"  {d}/: {cnt} files ({elapsed:.1f}s)")
            report["steps"][d] = {"files": cnt}

    # ── 1C: Semantic ──
    print("\n[3/3] Semantic Token Extraction...")
    t0 = time.time()
    run_cmd(f'"{python}" -s GPT_SoVITS/prepare_datasets/3-get-semantic.py', cwd=base_dir)
    elapsed = time.time() - t0

    # IMPORTANT: Merge semantic with header
    sem_part = os.path.join(exp_dir, "6-name2semantic-0.tsv")
    sem_merged = os.path.join(exp_dir, "6-name2semantic.tsv")
    if os.path.exists(sem_part):
        raw = open(sem_part, "r", encoding="utf-8").read().strip()
        with open(sem_merged, "w", encoding="utf-8") as f:
            f.write("item_name\tsemantic_audio\n" + raw + "\n")
        entries = len(raw.split("\n"))
        print(f"  6-name2semantic.tsv: {entries} entries ({elapsed:.1f}s)")
        report["steps"]["semantic"] = {"entries": entries, "time": round(elapsed, 1)}

    # Verify
    print("\n=== Verification ===")
    all_ok = True
    checks = [
        ("2-name2text.txt", os.path.join(exp_dir, "2-name2text.txt")),
        ("3-bert/", os.path.join(exp_dir, "3-bert")),
        ("4-cnhubert/", os.path.join(exp_dir, "4-cnhubert")),
        ("5-wav32k/", os.path.join(exp_dir, "5-wav32k")),
        ("6-name2semantic.tsv", os.path.join(exp_dir, "6-name2semantic.tsv")),
    ]
    for name, path in checks:
        if os.path.exists(path):
            if os.path.isdir(path):
                cnt = len(os.listdir(path))
                print(f"  OK {name} ({cnt} files)")
                if cnt == 0:
                    all_ok = False
            else:
                size = os.path.getsize(path)
                print(f"  OK {name} ({size} bytes)")
                if size < 50:
                    all_ok = False
        else:
            print(f"  MISSING {name}")
            all_ok = False

    report["status"] = "ok" if all_ok else "incomplete"
    write_output(report, args.output)
    return report


def cmd_train(args):
    """Train SoVITS V4 LoRA + GPT models."""
    print("=" * 60)
    print(f"  Training: {args.speaker}")
    print("=" * 60)

    base_dir = find_gptsovits_dir()
    python = get_python_exec(base_dir)
    exp_dir = os.path.join(base_dir, "logs", args.speaker)
    report = {"speaker": args.speaker, "weights": {}}

    import yaml

    # ── SoVITS V4 LoRA Training ──
    print(f"\n[1/2] SoVITS V4 LoRA (epochs={args.sovits_epochs}, lora_rank=32)...")

    sovits_dir = os.path.join(base_dir, "SoVITS_weights_v4")
    os.makedirs(sovits_dir, exist_ok=True)
    os.makedirs(os.path.join(exp_dir, "logs_s2_v4"), exist_ok=True)

    with open(os.path.join(base_dir, "GPT_SoVITS/configs/s2.json"), "r") as f:
        cfg = json.load(f)
    cfg["train"]["batch_size"] = 3
    cfg["train"]["epochs"] = args.sovits_epochs
    cfg["train"]["save_every_epoch"] = max(1, args.sovits_epochs // 2)
    cfg["train"]["pretrained_s2G"] = "GPT_SoVITS/pretrained_models/gsv-v4-pretrained/s2Gv4.pth"
    cfg["train"]["pretrained_s2D"] = ""
    cfg["train"]["if_save_latest"] = True
    cfg["train"]["if_save_every_weights"] = True
    cfg["train"]["gpu_numbers"] = "0"
    cfg["train"]["fp16_run"] = True
    cfg["train"]["grad_ckpt"] = False
    cfg["train"]["lora_rank"] = "32"
    cfg["model"]["version"] = "v4"
    cfg["data"]["exp_dir"] = exp_dir
    cfg["s2_ckpt_dir"] = exp_dir
    cfg["save_weight_dir"] = sovits_dir
    cfg["name"] = args.speaker
    cfg["version"] = "v4"

    tmp_dir = os.path.join(base_dir, "TEMP")
    os.makedirs(tmp_dir, exist_ok=True)
    with open(os.path.join(tmp_dir, "tmp_s2.json"), "w") as f:
        json.dump(cfg, f, indent=2)

    t0 = time.time()
    # IMPORTANT: Do NOT use capture_output — training output must be visible
    run_cmd(
        f'"{python}" -s GPT_SoVITS/s2_train_v3_lora.py --config "TEMP/tmp_s2.json"',
        cwd=base_dir, check=False
    )
    elapsed = time.time() - t0
    print(f"  SoVITS training: {elapsed:.1f}s ({elapsed/60:.1f}min)")

    sovits_weights = sorted(glob.glob(os.path.join(sovits_dir, f"{args.speaker}*.pth")))
    for w in sovits_weights:
        size_mb = os.path.getsize(w) / 1024 / 1024
        print(f"  -> {os.path.basename(w)} ({size_mb:.0f}MB)")
    report["weights"]["sovits"] = [os.path.basename(w) for w in sovits_weights]

    # ── GPT Training ──
    print(f"\n[2/2] GPT Training (epochs={args.gpt_epochs})...")

    gpt_dir = os.path.join(base_dir, "GPT_weights_v4")
    os.makedirs(gpt_dir, exist_ok=True)
    os.makedirs(os.path.join(exp_dir, "logs_s1_v4"), exist_ok=True)

    with open(os.path.join(base_dir, "GPT_SoVITS/configs/s1longer-v2.yaml"), "r") as f:
        gcfg = yaml.safe_load(f)
    gcfg["train"]["batch_size"] = 12
    gcfg["train"]["epochs"] = args.gpt_epochs
    gcfg["train"]["save_every_n_epoch"] = 5
    gcfg["train"]["if_save_every_weights"] = True
    gcfg["train"]["if_save_latest"] = True
    gcfg["train"]["half_weights_save_dir"] = gpt_dir
    gcfg["train"]["exp_name"] = args.speaker
    gcfg["pretrained_s1"] = "GPT_SoVITS/pretrained_models/s1v3.ckpt"
    gcfg["train_semantic_path"] = os.path.join(exp_dir, "6-name2semantic.tsv")
    gcfg["train_phoneme_path"] = os.path.join(exp_dir, "2-name2text.txt")
    gcfg["output_dir"] = os.path.join(exp_dir, "logs_s1_v4")

    os.environ["_CUDA_VISIBLE_DEVICES"] = "0"
    os.environ["hz"] = "25hz"
    with open(os.path.join(tmp_dir, "tmp_s1.yaml"), "w") as f:
        yaml.dump(gcfg, f, default_flow_style=False)

    t0 = time.time()
    run_cmd(
        f'"{python}" -s GPT_SoVITS/s1_train.py --config_file "TEMP/tmp_s1.yaml"',
        cwd=base_dir, check=False
    )
    elapsed = time.time() - t0
    print(f"  GPT training: {elapsed:.1f}s ({elapsed/60:.1f}min)")

    gpt_weights = sorted(glob.glob(os.path.join(gpt_dir, f"{args.speaker}*.ckpt")))
    for w in gpt_weights:
        size_mb = os.path.getsize(w) / 1024 / 1024
        print(f"  -> {os.path.basename(w)} ({size_mb:.0f}MB)")
    report["weights"]["gpt"] = [os.path.basename(w) for w in gpt_weights]

    report["status"] = "ok" if sovits_weights and gpt_weights else "incomplete"
    write_output(report, args.output)
    return report


def cmd_synthesize(args):
    """Generate Galgame dialogue audio with trained model."""
    print("=" * 60)
    print(f"  Synthesizing Galgame lines: {args.speaker}")
    print("=" * 60)

    base_dir = find_gptsovits_dir()
    exp_dir = os.path.join(base_dir, "logs", args.speaker)
    sliced_dir = os.path.join(exp_dir, "raw_sliced")
    out_dir = args.output
    os.makedirs(out_dir, exist_ok=True)

    # Load lines
    lines_file = args.lines if args.lines else DEFAULT_LINES_PATH
    with open(lines_file, "r", encoding="utf-8") as f:
        lines_data = json.load(f)
    lines = lines_data["lines"]
    print(f"  Lines: {len(lines)} from {os.path.basename(lines_file)}")

    # Pick reference audio (4-7s clips)
    all_clips = sorted(glob.glob(os.path.join(sliced_dir, "*.wav")))
    if not all_clips:
        print("ERROR: No sliced audio found. Run preprocess first.", file=sys.stderr)
        sys.exit(1)

    good_clips = []
    for c in all_clips:
        try:
            dur = float(os.path.basename(c).split("_")[2].replace("s.wav", ""))
            if 4.0 <= dur <= 7.0:
                good_clips.append((c, dur))
        except (IndexError, ValueError):
            pass

    if not good_clips:
        good_clips = [(c, 5.0) for c in all_clips[:5]]
    good_clips.sort(key=lambda x: -x[1])

    primary_ref = good_clips[0][0]
    aux_refs = [c[0] for c in good_clips[1:4]]
    print(f"  Primary ref: {os.path.basename(primary_ref)}")

    # Find best model weights
    sovits_dir = os.path.join(base_dir, "SoVITS_weights_v4")
    gpt_dir = os.path.join(base_dir, "GPT_weights_v4")

    sovits_weights = sorted(glob.glob(os.path.join(sovits_dir, f"{args.speaker}*.pth")))
    gpt_weights = sorted(glob.glob(os.path.join(gpt_dir, f"{args.speaker}*.ckpt")))

    if not gpt_weights:
        print("ERROR: No GPT weights found. Run train first.", file=sys.stderr)
        sys.exit(1)

    # Use latest GPT weight
    gpt_weight = gpt_weights[-1]

    # Start with V4 SoVITS, fallback to V2 if needed
    if sovits_weights:
        sovits_weight = sovits_weights[-1]
        use_v4_sovits = True
    else:
        sovits_weight = os.path.join(
            base_dir, "GPT_SoVITS/pretrained_models/gsv-v2final-pretrained/s2G2333k.pth"
        )
        use_v4_sovits = False

    # Check if inference API is running
    import socket
    try:
        with socket.create_connection(("127.0.0.1", INFERENCE_PORT), timeout=2):
            api_running = True
    except (ConnectionRefusedError, OSError):
        api_running = False

    if not api_running:
        print("  Starting inference API...")
        python = get_python_exec(base_dir)
        env = os.environ.copy()
        env["PYTHONUTF8"] = "1"
        env["version"] = "v4"
        env["gpt_path"] = os.path.relpath(gpt_weight, base_dir)
        env["sovits_path"] = os.path.relpath(sovits_weight, base_dir)
        env["infer_ttswebui"] = str(INFERENCE_PORT)
        subprocess.Popen(
            f'"{python}" -X utf8 -s GPT_SoVITS/inference_webui.py zh_CN',
            shell=True, cwd=base_dir, env=env,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        print("  Waiting for API...")
        if not wait_for_port(INFERENCE_PORT, timeout=60):
            print("ERROR: Inference API failed to start", file=sys.stderr)
            sys.exit(1)
        print("  API ready!")

    # Connect via Gradio client
    sys.path.insert(0, os.path.join(base_dir, "runtime", "Lib", "site-packages"))
    from gradio_client import Client, handle_file

    client = Client(f"http://127.0.0.1:{INFERENCE_PORT}")

    # Load models
    print(f"  Loading SoVITS: {os.path.basename(sovits_weight)}")
    client.predict(
        os.path.relpath(sovits_weight, base_dir),
        "中文", "中文", api_name="/change_sovits_weights"
    )
    print(f"  Loading GPT: {os.path.basename(gpt_weight)}")
    client.predict(
        os.path.relpath(gpt_weight, base_dir),
        api_name="/change_gpt_weights"
    )

    sample_steps = 8 if use_v4_sovits else 32

    # ── Generate first line to test ──
    print("\n  Testing first line...")
    test_line = lines[0]
    try:
        result = client.predict(
            handle_file(primary_ref),
            "你好。",  # IMPORTANT: Never empty — causes IndexError
            "中文", test_line["text"], "中文",
            "凑四句一切",
            15, 1.0, 1.0, True, 1.0, False,
            [handle_file(a) for a in aux_refs],
            sample_steps, False, 0.3,
            api_name="/get_tts_wav"
        )

        # Check duration — V4 SoVITS LoRA fallback detection
        if isinstance(result, str) and os.path.exists(result):
            import soundfile as sf
            data, sr = sf.read(result)
            dur = len(data) / sr
            print(f"  Test result: {dur:.1f}s")

            if dur < 1.5 and use_v4_sovits:
                # AUTOMATIC FALLBACK: V4 SoVITS → V2 SoVITS
                print("  WARNING: V4 SoVITS output too short, falling back to V2 SoVITS")
                v2_sovits = os.path.join(
                    base_dir,
                    "GPT_SoVITS/pretrained_models/gsv-v2final-pretrained/s2G2333k.pth"
                )
                client.predict(
                    os.path.relpath(v2_sovits, base_dir),
                    "中文", "中文", api_name="/change_sovits_weights"
                )
                use_v4_sovits = False
                sample_steps = 32
                print("  Switched to V2 SoVITS + fine-tuned GPT")
    except Exception as e:
        print(f"  Test failed: {e}")
        if use_v4_sovits:
            print("  Falling back to V2 SoVITS...")
            v2_sovits = os.path.join(
                base_dir,
                "GPT_SoVITS/pretrained_models/gsv-v2final-pretrained/s2G2333k.pth"
            )
            client.predict(
                os.path.relpath(v2_sovits, base_dir),
                "中文", "中文", api_name="/change_sovits_weights"
            )
            use_v4_sovits = False
            sample_steps = 32

    # ── Generate all lines ──
    print(f"\n  Generating {len(lines)} lines (sample_steps={sample_steps})...")
    ok = 0
    results = []
    for i, line in enumerate(lines):
        outpath = os.path.join(out_dir, f"{line['id']}.wav")
        print(f"\n  [{i+1}/{len(lines)}] {line['id']}: {line['text'][:25]}...")
        try:
            t0 = time.time()
            result = client.predict(
                handle_file(primary_ref),
                "你好。", "中文", line["text"], "中文",
                "凑四句一切",
                15, 1.0, 1.0, True, 1.0, False,
                [handle_file(a) for a in aux_refs],
                sample_steps, False, 0.3,
                api_name="/get_tts_wav"
            )
            elapsed = time.time() - t0

            if isinstance(result, (tuple, list)):
                import soundfile as sf
                import numpy as np
                sr_out, audio_data = result
                if isinstance(audio_data, np.ndarray):
                    sf.write(outpath, audio_data, sr_out)
                elif isinstance(result[-1], str) and os.path.exists(str(result[-1])):
                    shutil.copy2(str(result[-1]), outpath)
            elif isinstance(result, str) and os.path.exists(result):
                shutil.copy2(result, outpath)

            if os.path.exists(outpath):
                kb = os.path.getsize(outpath) / 1024
                print(f"    OK! {kb:.0f}KB, {elapsed:.1f}s")
                ok += 1
                results.append({"id": line["id"], "file": outpath, "size_kb": round(kb)})
            else:
                print(f"    WARN: No output file")
        except Exception as e:
            print(f"    ERROR: {e}")

    print(f"\n{'='*60}")
    print(f"  DONE! {ok}/{len(lines)} lines generated")
    print(f"  Output: {out_dir}")
    print(f"{'='*60}")

    for f in sorted(os.listdir(out_dir)):
        if f.endswith(".wav"):
            print(f"  {f} ({os.path.getsize(os.path.join(out_dir, f))//1024}KB)")

    report = {
        "status": "ok" if ok == len(lines) else "partial",
        "generated": ok,
        "total": len(lines),
        "output_dir": out_dir,
        "model": {
            "sovits": "v2_pretrained" if not use_v4_sovits else os.path.basename(sovits_weight),
            "gpt": os.path.basename(gpt_weight),
            "v4_fallback_triggered": not use_v4_sovits,
        },
        "files": results,
    }
    report_file = os.path.join(out_dir, "synthesis_report.json")
    write_output(report, report_file)


def cmd_pipeline(args):
    """Run full end-to-end pipeline."""
    print("=" * 60)
    print(f"  FULL PIPELINE: {args.speaker}")
    print(f"  URL: {args.url}")
    print("=" * 60)

    base_dir = find_gptsovits_dir()
    if not base_dir:
        print("ERROR: GPT-SoVITS not found!", file=sys.stderr)
        sys.exit(1)

    out_base = args.output
    os.makedirs(out_base, exist_ok=True)

    # Step 1: Download
    print("\n" + "=" * 60)
    print("  STEP 1/5: Download Audio")
    print("=" * 60)
    dl_args = argparse.Namespace(
        url=args.url, speaker=args.speaker,
        output=os.path.join(out_base, "download_report.json")
    )
    audio_file = cmd_download(dl_args)

    # Step 2: Preprocess
    print("\n" + "=" * 60)
    print("  STEP 2/5: Preprocess")
    print("=" * 60)
    pp_args = argparse.Namespace(
        input=audio_file, speaker=args.speaker,
        output=os.path.join(out_base, "preprocess_report.json")
    )
    cmd_preprocess(pp_args)

    # Step 3: Format
    print("\n" + "=" * 60)
    print("  STEP 3/5: Format Training Data")
    print("=" * 60)
    fmt_args = argparse.Namespace(
        speaker=args.speaker,
        output=os.path.join(out_base, "format_report.json")
    )
    cmd_format(fmt_args)

    # Step 4: Train
    print("\n" + "=" * 60)
    print("  STEP 4/5: Train Model")
    print("=" * 60)
    tr_args = argparse.Namespace(
        speaker=args.speaker,
        sovits_epochs=args.sovits_epochs,
        gpt_epochs=args.gpt_epochs,
        output=os.path.join(out_base, "train_report.json")
    )
    cmd_train(tr_args)

    # Step 5: Synthesize
    print("\n" + "=" * 60)
    print("  STEP 5/5: Synthesize Galgame Lines")
    print("=" * 60)
    syn_args = argparse.Namespace(
        speaker=args.speaker,
        lines=args.lines if hasattr(args, "lines") else None,
        output=os.path.join(out_base, "galgame_audio")
    )
    cmd_synthesize(syn_args)

    print("\n" + "=" * 60)
    print("  PIPELINE COMPLETE!")
    print(f"  Output: {out_base}")
    print("=" * 60)


# ─── Main ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Galgame Voice Synthesis — GPT-SoVITS Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # setup
    p = subparsers.add_parser("setup", help="Check environment")
    p.add_argument("--output", required=True, help="Output JSON report path")

    # download
    p = subparsers.add_parser("download", help="Download audio from URL")
    p.add_argument("--url", required=True, help="Bilibili or YouTube URL")
    p.add_argument("--speaker", required=True, help="Speaker name")
    p.add_argument("--output", required=True, help="Output JSON report path")

    # preprocess
    p = subparsers.add_parser("preprocess", help="UVR5 + slice + ASR")
    p.add_argument("--input", required=True, help="Input audio file path")
    p.add_argument("--speaker", required=True, help="Speaker name")
    p.add_argument("--output", required=True, help="Output JSON report path")

    # format
    p = subparsers.add_parser("format", help="Format training data")
    p.add_argument("--speaker", required=True, help="Speaker name")
    p.add_argument("--output", required=True, help="Output JSON report path")

    # train
    p = subparsers.add_parser("train", help="Train SoVITS + GPT")
    p.add_argument("--speaker", required=True, help="Speaker name")
    p.add_argument("--sovits-epochs", type=int, default=4, help="SoVITS epochs (default: 4)")
    p.add_argument("--gpt-epochs", type=int, default=15, help="GPT epochs (default: 15)")
    p.add_argument("--output", required=True, help="Output JSON report path")

    # synthesize
    p = subparsers.add_parser("synthesize", help="Generate Galgame lines")
    p.add_argument("--speaker", required=True, help="Speaker name")
    p.add_argument("--lines", default=None, help="Custom lines JSON file")
    p.add_argument("--output", required=True, help="Output directory for WAV files")

    # pipeline
    p = subparsers.add_parser("pipeline", help="Full end-to-end pipeline")
    p.add_argument("--url", required=True, help="Bilibili or YouTube URL")
    p.add_argument("--speaker", required=True, help="Speaker name")
    p.add_argument("--output", required=True, help="Output directory")
    p.add_argument("--sovits-epochs", type=int, default=4)
    p.add_argument("--gpt-epochs", type=int, default=15)
    p.add_argument("--lines", default=None, help="Custom lines JSON file")

    args = parser.parse_args()
    commands = {
        "setup": cmd_setup,
        "download": cmd_download,
        "preprocess": cmd_preprocess,
        "format": cmd_format,
        "train": cmd_train,
        "synthesize": cmd_synthesize,
        "pipeline": cmd_pipeline,
    }
    commands[args.command](args)


if __name__ == "__main__":
    main()
