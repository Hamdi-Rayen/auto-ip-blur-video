<div align="center">

# 🛡️ Auto IP Blur & Video Redaction Tool

**An automated AI-powered video privacy tool that detects, tracks, and blurs sensitive IP addresses (IPv4 & IPv6) and custom secret tokens in screen recordings and video demos.**

Designed specifically for **content creators, educators, software engineers, and video editors** using **Adobe Premiere Pro, DaVinci Resolve, or Final Cut Pro**.

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey.svg)]()
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

</div>

---

## 📌 The Problem
When recording coding tutorials, devops demos, terminal sessions, or tech walkthroughs, private IP addresses (`192.168.x.x`, public server IPs, cloud cluster endpoints) often appear on screen. 

Manually keyframing blur masks across hours of video in Adobe Premiere Pro or DaVinci Resolve is **slow, tedious, and prone to human error**.

## 💡 The Solution
**Auto IP Blur** scans video frames using fast, lightweight ONNX-accelerated OCR, detects IP patterns via regular expressions, and automatically applies smooth blur, pixelation (mosaic), or solid censorship bars. It features **anti-flicker box tracking** and **lossless audio pass-through**, producing ready-to-publish or ready-to-edit video files with zero manual masking.

---

## ✨ Features

- 🧠 **Automatic AI OCR Detection**: Uses `RapidOCR` (ONNX Runtime) to locate text across light/dark backgrounds, terminal windows, code editors, and browsers.
- 🎯 **Smart Regex Filtering**: Matches IPv4 (with optional ports and CIDR notations like `192.168.1.100:8080` or `10.0.0.0/24`) and optional IPv6 addresses.
- 🔒 **Custom Target Filtering**: Option to redact *only* your specific IP addresses, server domains, or sensitive secrets (e.g. `10.0.2.15, api.internal.local`) without blurring other numbers on screen.
- 🎨 **3 Redaction Styles**:
  - `pixelate`: Classic mosaic censorship (ideal for tech demos).
  - `blur`: Smooth Gaussian blur with configurable strength.
  - `blackout`: Clean solid security bar.
- ⏱️ **Anti-Flicker Box Persistence**: Automatically maintains censorship boxes across momentary frame drops or OCR fluctuations, preventing annoying visual flicker.
- 🔊 **Zero-Loss Audio Pass-Through**: Video is remuxed with the original audio track (AAC / pass-through) using embedded FFmpeg so voiceovers, sound effects, and microphone tracks remain perfectly synced.
- 🖥️ **Modern Desktop GUI**: Clean, responsive interface with a docked action bar, live progress percentage, FPS, ETA counter, and an interactive frame preview window.
- ⚡ **Powerful CLI**: Fully automatable via terminal for headless servers or automated batch rendering pipelines.

---

## 🚀 Quick Start (Windows)

If you are on Windows and just want to run the application:

1. Clone or download this repository.
2. Double-click:
   ```bat
   Run_IP_Blur_Tool.bat
   ```
3. The graphical interface will open. Select your video and click **▶ Start Blurring Video**!

---

## 📦 Installation & Setup

### Prerequisites
- Python 3.8 or higher installed ([Download Python](https://www.python.org/downloads/))
- Git (optional)

### 1. Clone the Repository
```bash
git clone https://github.com/Hamdi-Rayen/auto-ip-blur-video.git
cd auto-ip-blur-video
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

> **Note:** FFmpeg is automatically provided through `imageio-ffmpeg` — no manual FFmpeg system installation or PATH configuration is required!

---

## 🖥️ Graphical Interface (GUI) Guide

Launch the GUI by running:
```bash
python gui.py
```

<div align="center">
  <img src="https://via.placeholder.com/760x420/1e1e24/ffffff?text=Auto+IP+Blur+Tool+Interface" alt="App Preview" width="650"/>
</div>

### Controls & Options:
1. **Input Video**: Click **Browse...** to pick any video file (`.mp4`, `.mov`, `.mkv`, `.avi`, `.wmv`).
2. **Output Video**: Automatically names your file `yourvideo_blurred.mp4` (or customize the destination).
3. **Blur Style**:
   - `pixelate`: Pixel block mosaic effect (default, recommended).
   - `blur`: Gaussian blur.
   - `blackout`: Solid dark rectangle.
4. **Strength**: Adjust the slider (5 to 45) to increase or decrease the intensity of the blur/mosaic.
5. **Target Mode**:
   - **Detect ALL IPv4 Addresses automatically**: Scans and censors every IP found.
   - **Only blur specific IP(s) or words**: Enter comma-separated IPs or strings to redact only targeted sensitive info.
6. **👁 Preview Blur on Current Video**: Renders a sample frame showing exactly how the blur looks before you commit to processing the full file.
7. **▶ Start Blurring Video**: Starts the rendering thread with real-time frame progress, FPS, and ETA calculations.

---

## 🎬 How to Use with Adobe Premiere Pro 2026 (or DaVinci Resolve)

You don't need to rebuild your timeline or re-edit your montage!

### Workflow A: The "Replace Footage" Method (If already edited on Timeline)
If you have already sliced, timed, and edited your video inside Premiere Pro:
1. Run **Auto IP Blur** on the original raw video file on your disk.
2. In **Adobe Premiere Pro**, open your **Project Panel**.
3. Right-click your original video clip and select **Replace Footage...**
4. Choose the newly generated `_blurred.mp4` file.
5. **Premiere Pro automatically replaces the video across your entire timeline!** Every cut, transition, speed ramp, and audio sync remains 100% intact with the IP address blurred out.

### Workflow B: Pre-Processing (Recommended for New Projects)
1. Run **Auto IP Blur** on your raw screen recording directly after recording (e.g. from OBS, ShadowPlay, or Camtasia).
2. Import the clean `_blurred.mp4` into Premiere Pro and edit normally.

---

## 💻 Command Line (CLI) Usage

For power users, scripts, or batch folders:

```bash
# Basic usage (censors all IPv4 addresses with default mosaic)
python cli.py -i demo.mp4 -o demo_clean.mp4

# Smooth Gaussian Blur with custom strength
python cli.py -i demo.mp4 --style blur --strength 25

# Redact specific IP addresses only
python cli.py -i demo.mp4 --targets 192.168.1.50 10.0.0.1

# Include IPv6 detection
python cli.py -i demo.mp4 --ipv6

# High performance mode (OCR every 4 frames with longer persistence)
python cli.py -i demo.mp4 --stride 4 --persistence 8
```

### CLI Arguments Reference

| Argument | Description | Default |
| :--- | :--- | :--- |
| `-i`, `--input` | **(Required)** Path to input video file | — |
| `-o`, `--output` | Destination path for output video | `<input>_blurred.mp4` |
| `--style` | Redaction effect: `pixelate`, `blur`, `blackout` | `pixelate` |
| `--strength` | Block size or blur radius | `15` |
| `--padding` | Pixel padding around detected text box | `6` |
| `--stride` | Run OCR every N frames (higher = faster processing) | `2` |
| `--persistence` | Number of frames to persist blur to eliminate flicker | `6` |
| `--targets` | List of specific strings/IPs to redact | `None` (All IPs) |
| `--ipv6` | Enable detection and redaction of IPv6 addresses | `False` |

---

## 🛠️ How It Works Under the Hood

```
[ Video Input ]
       │
       ▼
[ OpenCV Video Capture ] ──────────────► [ Audio Extraction (FFmpeg) ]
       │                                              │
       ├─► (Every N frames) ──► [ RapidOCR Engine ]   │
       │                               │              │
       │                        [ Regex Match ]       │
       │                               │              │
       ▼                               ▼              │
[ Frame Buffer ] ◄──── [ Temporal Box Persistence ]   │
       │                                              │
       ▼                                              │
[ Apply Mosaic / Blur Effect ]                        │
       │                                              │
       ▼                                              │
[ Rendered Video Stream ] ◄───────────────────────────┘
       │
       ▼
[ Final Synchronized Output .mp4 ]
```

1. **Frame Ingestion**: Video frames are decoded via OpenCV.
2. **Text & IP Identification**: Every *N* frames, `RapidOCR` scans the image buffer and returns localized polygons. RegEx engines parse IP tokens (`\b\d{1,3}(?:\.\d{1,3}){3}\b`).
3. **Bounding Box Normalization**: Bounding polygons are mapped to horizontal sub-slices with configurable margin padding.
4. **Temporal Box Persistence**: Detected bounding coordinates are assigned a decay counter, ensuring that brief dips in OCR confidence don't cause the blur to flicker.
5. **Lossless Remuxing**: The redacted video stream is muxed with the original audio using FFmpeg without re-encoding audio channels.

---

## ❓ Frequently Asked Questions (FAQ)

<details>
<summary><b>Does this tool send my video to any cloud or external API?</b></summary>
<b>No.</b> Everything runs 100% locally on your machine. The OCR model runs via ONNX locally, ensuring complete privacy for your sensitive data.
</details>

<details>
<summary><b>Will my video lose quality or framerate?</b></summary>
The output matches the original video's resolution, aspect ratio, framerate, and audio track. Only the exact rectangular pixels over the sensitive text are altered.
</details>

<details>
<summary><b>Can I redact words other than IP addresses?</b></summary>
Yes! In the GUI, select <i>"Only blur specific IP(s) or words"</i> and type any sensitive keyword (e.g. passwords, secret API keys, emails, or server hostnames).
</details>

<details>
<summary><b>Does it work with 4K or 60 FPS videos?</b></summary>
Yes. For high-resolution or high-framerate screen recordings, you can increase `--stride` to `3` or `4` to speed up processing while keeping tracking smooth.
</details>

---

## 🤝 Contributing

Contributions, bug reports, and feature suggestions are very welcome!
1. Fork the Project.
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`).
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`).
4. Push to the Branch (`git push origin feature/AmazingFeature`).
5. Open a Pull Request.

---

## 📄 License

Distributed under the **MIT License**. See [`LICENSE`](LICENSE) for more information.
