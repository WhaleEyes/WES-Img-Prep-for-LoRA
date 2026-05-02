# WES图片预处理工具

一款**中英双语**的桌面图像预处理工具，专为 **Stable Diffusion LoRA 训练**设计。  
在**安全备份**、**可中断续传**的前提下，实现格式转换、缩放、裁切与智能重命名。

[![English](https://img.shields.io/badge/README-English-blue)](README_EN.md)

## ✨ 核心功能

- 🖼 **安全格式转换** – 所有图片转为 **WebP (85%质量)**，同时在 `原图`（或 `originals`）文件夹保留完整备份。
- ✂️ **灵活裁切规则** – 自定义最小/最大分辨率和尺寸步进，超长图自动缩，过小的图拷贝到单独文件夹，不修改。
- 🔄 **断点续传** – 中断后重新运行绝不会重复处理已完成文件，真正“即停即续”。
- 🔢 **智能重命名** – 按分辨率大小排序后自动编号；再次添加新图片时，编号自动续接。
- 🧠 **规则记忆** – 裁切规则全局保存，下次启动自动加载，无需重复设置。
- 🗑 **安全删除** – 原始文件移入**系统回收站**，而非直接永久删除。
- 🌐 **双语界面实时切换** – 菜单栏切换中/英文，界面即时更新，无需重启程序。
- 📂 **批量处理** – 一次性处理多个子文件夹，每个文件夹进度清晰反馈。
- 📋 **详细日志与进度条** – 实时展示每一步操作和整体进度。

## 📸 界面截图
![GUI Screenshot](screenshots/gui_zh.png)
![GUI Screenshot](screenshots/gui.png)

## 🚀 快速开始

### Windows 用户（无需 Python 环境）
1. Download the latest `exe` from [Releases](https://github.com/WhaleEyes/WES-Img-prep-for-lora/releases).
2. 双击运行，即出现图形界面，无需安装。

### Python 用户
```bash
git clone https://github.com/WhaleEyes/WES-Img-prep-for-lora.git
cd WES-Img-prep-for-lora
pip install -r requirements.txt
```

#### 启动 GUI

```bash
python gui.py
```

#### 命令行（中文版）

```bash
python run_zh.py /path/to/images --rename --sort asc
```

#### 命令行（英文版）

```bash
python run_en.py /path/to/images --rename --sort desc --min 640 --max 1536 --step 64
```

## 📖 使用方法

### GUI 操作

1. 选择 **单个文件夹** 或 **批量处理** 模式。
2. 在输入框中直接修改裁切规则（最小分辨率、最大分辨率、尺寸步进），点击 **保存当前规则**。
3. 勾选 **自动重命名** 并选择排序方式（按分辨率从小到大 / 从大到小）。
4. 浏览选择文件夹（批量模式下需选择父目录并扫描子文件夹）。
5. 点击 **开始处理**，进度条和日志会实时展示状态。
6. 过程中可随时取消。

### 命令行参数

```
python run_zh.py <文件夹路径> [选项]

选项：
  --rename           启用自动重命名（按分辨率排序）
  --sort {asc,desc}  排序方式：asc(从小到大) 或 desc(从大到小)，默认 asc
  --min <整数>       最小边长（默认 512）
  --max <整数>       最大边长（默认 2048）
  --step <整数>      尺寸步进（默认 64）
```

## 📁 输出目录结构

处理完成后，目标文件夹内结构如下：

```
你的文件夹/
├── originals/ (或 原图/)    # 所有 WebP 备份文件（未做任何修改）
├── lt512/                   # 短边不足最小值的图片副本（不裁切，保持原样）
├── 512x512/                 # 处理后的图片按最终尺寸归类存放
├── 1024x1536/
├── .process_rules           # 该文件夹保存的裁切规则
└── config.json              # 全局规则与语言配置（已加入 .gitignore）
```

## 🔧 依赖环境

- Python 3.8+
- [Pillow](https://python-pillow.org/)
- [send2trash](https://pypi.org/project/Send2Trash/)

安装依赖:

```bash
pip install -r requirements.txt
```

## 🤝 参与贡献

欢迎提交PR。
