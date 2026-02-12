# RTVG

![RTVG Demo](demo.gif)

## Race Telemetry Video Generator

RTVG (Race Telemetry Video Generator) is a Python tool that converts telemetry CSV files exported from **Racebox.pro** (and similar telemetry loggers) into a **video overlay with driving stats**.

It renders telemetry visuals frame-by-frame using Python, then uses **FFmpeg** to assemble the frames into a video.

RaceRender didn't work right for me, so I made my own. 

---

## Features

* CSV telemetry import
* Track path rendering
* Speed overlay
* G force meter
* Video encoding via FFmpeg
* Lightweight Python pipeline

---

## Planned features

* Drag racing mode, including 60ft, 0-60, 1/8mi, 1/4mi, 1/2mi, 60-130
* maybe a gui
* fancier looking
* you tell me


## Example Usage

```bash
python racebox_overlay.py data.csv
```

Transparent output video will be generated after frame rendering completes. Currently, it always exports as ```race_overlay.mov```

Put that video in a video editor and sync it up with your gopro footage.

---

## Requirements

### System Dependencies

You must have **FFmpeg** installed and available in your PATH.

Install FFmpeg:

Ubuntu / Pop!_OS:

```bash
sudo apt install ffmpeg
```

Mac (brew):

```bash
brew install ffmpeg
```

Windows:
Install from:
https://ffmpeg.org/download.html

---

### Python Dependencies

RTVG uses:

* numpy
* Pillow (PIL)

Install with:

```bash
pip install -r requirements.txt
```

---

## Installation

Clone the repository:

```bash
git clone https://github.com/BFCE/RTVG/rtvg.git
cd rtvg
```

Install dependencies:

```bash
pip install -r requirements.txt
```

---

## Notes

* CSV format should match Racebox export structure, if you have an incompatible format make a ticket and I might add support
* I have a 25hz datalogger so the video is 25fps. Change the fps variable at the top if you need it to be slower (or just do it in your video editor)
* Currently it outputs 4:3 video to match my GoPro Hero 6
* FFmpeg must be installed system-wide

---

## License

no license ez do whatever you want 
