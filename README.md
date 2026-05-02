# WES-Image-Preprocessor

A **bilingual (Chinese/English)** desktop tool for batch preprocessing image datasets for **Stable Diffusion LoRA training**.  
It converts, resizes, crops, and renames images with a focus on **safety**, **resumability**, and **ease of use**.

## ✨ Core Features

- 🖼 **Safe Format Conversion** – Converts all images to **WebP (85% quality)** while preserving untouched backups in the `originals` (or `原图`) folder.
- ✂️ **Customizable Crop Rules** – Set minimum/maximum resolution and alignment step; long images are downscaled, short ones are copied to a separate folder without modification.
- 🔄 **Resumable Processing** – Never re‑processes already handled files. Restart the tool anytime and it continues where it left off.
- 🔢 **Intelligent Renaming** – Auto‑number files by resolution (ascending/descending). Newly added images are numbered sequentially from the last existing number.
- 🧠 **Rule Memory** – Your cropping rules (min, max, step) are saved globally in `config.json` and automatically reused.
- 🗑 **Safe Deletion** – Original files are moved to the **Recycle Bin** rather than permanently deleted.
- 🌐 **Bilingual GUI** – Switch between Chinese and English instantly from the menu bar. The whole interface updates without restarting.
- 📂 **Batch Processing** – Process multiple subfolders at once with clear per‑folder progress.
- 📋 **Detailed Logs & Progress Bar** – See exactly what is happening in real time.

## 🚀 Quick Start

### For Windows Users (no Python required)
1. Download the latest `WES-Img-prep-for-lora.exe` from [Releases](https://github.com/WhaleEyes/WES-Img-prep-for-lora/releases).
2. Double‑click the `.exe` – the GUI opens immediately. No installation needed.

### For Python Users
```bash
git clone https://github.com/WhaleEyes/WES-Img-prep-for-lora.git
cd WES-Img-prep-for-lora
pip install -r requirements.txt
