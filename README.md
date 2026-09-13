# 🎬 Android Bootanimation Converter

[![Python Version](https://img.shields.io/badge/python-3.7%2B-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Android-brightgreen.svg)](https://www.android.com/)

**Android Bootanimation Converter** is a powerful Python-based Command-Line Interface (CLI) tool designed to convert standard video files into custom Android boot animation archives (`bootanimation.zip`). It also features direct packaging into flashable **Magisk**, **KernelSU**, and **APatch** modules for seamless installation on rooted devices.

---

## ✨ Key Features

- 🔄 **Two Flexible Animation Modes:**
  - **Looping Mode:** Converts a single video file into an infinitely looping boot animation.
  - **3-Stage Mode:** Advanced multi-video sequence consisting of **Opening** (plays once) $\rightarrow$ **Looping** (repeats indefinitely during boot) $\rightarrow$ **Closing** (plays once upon Android OS ready state).
- 📦 **Uncompressed Store (`ZIP_STORED`):** Automatically enforces a $0\%$ compression ratio inside the generated `.zip` archive, adhering strictly to Android surfaceflinger/bootanimation binary requirements.
- ⚡ **Magisk / KernelSU / APatch Module Builder:** Option to generate a ready-to-flash module containing the boot animation placed inside the `/system/media/` directory structure.
- 📐 **Resolution & FPS Customization:** Support for dynamic frame resampling and custom resolution adjustments (e.g., $1080 \times 2400$).
- 📜 **Automated `desc.txt` Generation:** Formats configuration rules with strict UNIX line endings (`\n`).

---

## 🛠️ Prerequisites

Ensure your system meets the following requirements before running the tool:

- **Python 3.7+**
- **OpenCV (`opencv-python`)**

---

## 🚀 Installation

1. **Clone this repository:**
   ```bash
   git clone https://github.com/your-username/bootanimation-converter.git
   cd bootanimation-converter
   ```

2. **Install required dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

---

## 💡 Usage Examples

### 1. Single Video Loop Mode
Convert a single video file into a standard continuous loop animation:

```bash
python main.py --mode loop --video input.mp4 --res 1080x2400 --fps 30 -o bootanimation.zip
```

### 2. 3-Stage Animation Mode
Combine three separate videos for opening, looping, and closing sequences:

```bash
python main.py --mode 3stage \
  --opening intro.mp4 \
  --loop-video loop.mp4 \
  --closing outro.mp4 \
  --res 1080x2400 \
  -o bootanimation.zip
```

### 3. Generate Flashable Magisk / KernelSU Module
Add the `--magisk` flag to generate a ready-to-flash ZIP module:

```bash
python main.py --mode loop --video input.mp4 --res 1080x2400 --magisk -o BootanimModule.zip
```

---

## 📖 CLI Arguments Reference

| Argument | Description | Required? |
| :--- | :--- | :---: |
| `--mode` | Animation mode: `loop` or `3stage` | **Yes** |
| `--video` | Input video path (Required for `loop` mode) | *Conditional* |
| `--opening` | Intro video path (Required for `3stage` mode) | *Conditional* |
| `--loop-video` | Looping video path (Required for `3stage` mode) | *Conditional* |
| `--closing` | Outro video path (Required for `3stage` mode) | *Conditional* |
| `-o`, `--output` | Output filename (default: `bootanimation.zip`) | No |
| `--res` | Target resolution formatted as `WIDTHxHEIGHT` (e.g., `1080x2400`) | No |
| `--fps` | Target frame rate (defaults to source video FPS if omitted) | No |
| `--magisk` | Output as a flashable Magisk/KernelSU module | No |

---

## 📁 Output Structure

### Standard Bootanimation File (`bootanimation.zip`)
```text
bootanimation.zip
├── desc.txt
├── part0/      # Frame sequence for opening or single loop
├── part1/      # Frame sequence for looping (3-stage mode)
└── part2/      # Frame sequence for closing (3-stage mode)
```

### Flashable Module Structure (`BootanimModule.zip`)
```text
BootanimModule.zip
├── module.prop
└── system/
    └── media/
        └── bootanimation.zip
```

---

## 🔬 Technical Specifications & Android Constraints

Android's native `bootanimation` binary requires specific formatting rules:

1. **Uncompressed ZIP Archive:** Android cannot render compressed image frames during early boot stages. The archive must use **`ZIP_STORED`** (compression level $0\%$).
2. **UNIX Line Endings (`\n`):** The `desc.txt` configuration file requires POSIX/UNIX line feeds. Windows-style CRLF (`\r\n`) will cause parsing failures.
3. **Part Types (`c` vs `p`):**
   - `c` (Complete): Ensures all frames in the directory play completely before switching to the next part. Used for `opening` (`part0`) and `closing` (`part2`).
   - `p` (Part): Loops continuously. A count value of `0` denotes infinite looping until system initialization completes.

### Sample `desc.txt` Layout
```text
1080 2400 30
c 1 0 part0
p 0 0 part1
c 1 0 part2
```

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).