# core.py
import sys
import json
from pathlib import Path
import shutil
from PIL import Image
import send2trash
from typing import Callable, Optional, Dict, Tuple, List
import threading

IMAGE_SUFFIXES = {'.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff', '.webp'}

LANG = "zh"

TEXTS = {
    "title": {"zh": "WES图片预处理工具", "en": "WES Image Preprocessing Tool"},
    "origin_folder": {"zh": "原图", "en": "originals"},
    "input_prompt": {"zh": "请输入包含图片的文件夹路径: ", "en": "Please enter the path to the folder containing images: "},
    "error_no_dir": {"zh": "错误：路径不存在或不是文件夹。", "en": "Error: Path does not exist or is not a folder."},
    "renaming_question": {"zh": "是否进行重命名（按分辨率排序并自动编号）？输入1重命名，输入2跳过: ", "en": "Rename files (sort by resolution, auto-number)? Enter 1 to rename, 2 to skip: "},
    "renaming_choice_invalid": {"zh": "输入无效，请输入1或2。", "en": "Invalid input, please enter 1 or 2."},
    "renaming_skipped": {"zh": "跳过重命名，保留原始文件名。", "en": "Skipping rename, keeping original file names."},
    "renaming_info": {"zh": "原图已有最大编号：{max_num}，新增 {num_new} 张，将编号 {start_num} 至 {total_after}（{digits}位数）", "en": "Existing max number in origin: {max_num}, {num_new} new files, numbering from {start_num} to {total_after} ({digits} digits)"},
    "renaming_file": {"zh": "重命名: {old} -> {new}", "en": "Rename: {old} -> {new}"},
    "step1_title": {"zh": "第一步：转换原始图片为 WebP 格式...", "en": "Step 1: Converting original images to WebP format..."},
    "step1_skip": {"zh": "第一步：没有原始图片需要转换。", "en": "Step 1: No original images to convert."},
    "step1_converted": {"zh": "已转换并删除原始文件: {name}", "en": "Converted and deleted original file: {name}"},
    "step1_fail": {"zh": "转换失败: {name} ({error})，原始文件保留", "en": "Conversion failed: {name} ({error}), original file kept."},
    "step1_done": {"zh": "转换完成，{count} 张图片已存入“原图”文件夹。", "en": "Conversion done, {count} images saved to 'originals' folder."},
    "step2_title": {"zh": "第二步：处理“原图”中的图片，共 {total} 张...", "en": "Step 2: Processing images in 'originals' (total {total} files)..."},
    "step2_empty": {"zh": "“原图”文件夹为空，没有需要处理的图片，脚本退出。", "en": "'originals' folder is empty, no images to process, exiting."},
    "processing_file": {"zh": "({idx}/{total}) 处理: {name}", "en": "({idx}/{total}) Processing: {name}"},
    "orig_size": {"zh": "原始尺寸: {w}x{h}", "en": "Original size: {w}x{h}"},
    "skip_unreadable": {"zh": "跳过无法识别的图片: {name} ({error})", "en": "Skipping unreadable image: {name} ({error})"},
    "small_min_side": {"zh": "最小边<{min}，复制至: {folder}/{name}", "en": "Min side < {min}, copied to: {folder}/{name}"},
    "scaled": {"zh": "缩放至: {w}x{h}", "en": "Scaled to: {w}x{h}"},
    "no_scale": {"zh": "无需缩放", "en": "No scaling needed"},
    "scaled_still_small": {"zh": "缩放后最小边<{min}，保存缩略图至: {folder}/{name}", "en": "After scaling, min side < {min}, saved thumbnail to: {folder}/{name}"},
    "no_crop": {"zh": "无需裁切，最终尺寸: {w}x{h}", "en": "No crop needed, final size: {w}x{h}"},
    "center_crop": {"zh": "居中裁切至: {w}x{h}", "en": "Center cropped to: {w}x{h}"},
    "saved": {"zh": "保存至: {folder}/{name}", "en": "Saved to: {folder}/{name}"},
    "target_exists": {"zh": "目标文件已存在，跳过保存: {folder}/{name}", "en": "Target file exists, skipped: {folder}/{name}"},
    "save_fail": {"zh": "保存失败: {error}", "en": "Save failed: {error}"},
    "stats_title": {"zh": "处理完成！统计如下：", "en": "Processing complete! Statistics:"},
    "stats_skipped": {"zh": "跳过（目标已存在）: {count} 张", "en": "Skipped (already exists): {count} files"},
    "stats_small": {"zh": "移入 {folder}: {count} 张", "en": "Moved to {folder}: {count} files"},
    "stats_errors": {"zh": "处理错误: {count} 张", "en": "Errors: {count} files"},
    "stats_size_folders": {"zh": "各尺寸文件夹新增图片数量：", "en": "Images added per size folder:"},
    "stats_none": {"zh": "(无新图片)", "en": "(No new images)"},
    "origin_preserved": {"zh": "“原图”文件夹完整保留，未做任何修改。", "en": "'originals' folder is fully preserved, no modifications made."},
    "cancelled": {"zh": "处理被取消。", "en": "Processing cancelled."},
    "rule_saved": {"zh": "裁切规则已保存，下次运行将自动沿用。", "en": "Crop rule saved, will be reused next time."},
    "rule_detected": {"zh": "检测到保存的规则：min={min}, max={max}, step={step}，将自动沿用。", "en": "Saved rule detected: min={min}, max={max}, step={step}, will be used automatically."},
    "rule_corrupted": {"zh": "规则文件损坏，将使用默认规则并重新询问。", "en": "Rule file corrupted, using default rule and re-asking."},
    "rule_default_prompt": {"zh": "当前默认裁切规则：min={min}, max={max}, reso steps={step}\n按 Enter 继续使用默认规则，或输入新规则（格式：min max step）后按 Enter 更新: ", "en": "Default crop rule: min={min}, max={max}, reso steps={step}\nPress Enter to use default, or enter new rule (format: min max step) then press Enter: "},
    "rule_updated": {"zh": "规则已更新为：min={min}, max={max}, step={step}", "en": "Rule updated to: min={min}, max={max}, step={step}"},
    "rule_invalid_format": {"zh": "输入格式错误，必须为三个整数，将使用默认规则。", "en": "Invalid format, must be three integers. Using default rule."},
    "rule_invalid_min_max": {"zh": "错误：min 不能大于 max，将使用默认规则。", "en": "Error: min cannot be larger than max. Using default rule."},
    "rule_invalid_step": {"zh": "错误：step 必须为正整数，将使用默认规则。", "en": "Error: step must be a positive integer. Using default rule."},
    "rule_use_default": {"zh": "使用默认规则。", "en": "Using default rule."},
    "checking_new_files": {"zh": "检测到新的图片文件，可进行重命名以便后续管理。", "en": "New image files detected. You can rename them for better management."},
    "no_new_raw_files": {"zh": "没有发现新的原始图片，跳过重命名。", "en": "No new raw images found, skipping rename."},
    # GUI 相关（此处省略，与原始相同，已保留）
    "mode_selection": {"zh": "处理模式", "en": "Processing Mode"},
    "single_folder": {"zh": "单个文件夹", "en": "Single Folder"},
    "batch_folder": {"zh": "批量处理（直接子文件夹）", "en": "Batch (Direct Subfolders)"},
    "current_rule": {"zh": "当前裁切规则", "en": "Current Crop Rule"},
    "edit_rule": {"zh": "修改规则", "en": "Edit Rule"},
    "single_path_label": {"zh": "图片文件夹路径:", "en": "Image folder path:"},
    "browse": {"zh": "浏览", "en": "Browse"},
    "rename_option": {"zh": "对新增图片自动重命名（按分辨率排序）", "en": "Auto-rename new images (by resolution)"},
    "batch_parent_label": {"zh": "父目录路径（含多个子文件夹）:", "en": "Parent directory (contains subfolders):"},
    "scan_subdirs": {"zh": "扫描子文件夹", "en": "Scan Subfolders"},
    "batch_list_label": {"zh": "待处理的子文件夹（勾选=处理）", "en": "Subfolders to process (checked = process)"},
    "select_all": {"zh": "全选", "en": "Select All"},
    "invert_selection": {"zh": "反选", "en": "Invert Selection"},
    "clear_selection": {"zh": "清除选中", "en": "Clear Selection"},
    "log_label": {"zh": "处理日志", "en": "Processing Log"},
    "start_process": {"zh": "开始处理", "en": "Start Processing"},
    "cancel": {"zh": "取消", "en": "Cancel"},
    "warning": {"zh": "警告", "en": "Warning"},
    "error": {"zh": "错误", "en": "Error"},
    "info": {"zh": "信息", "en": "Information"},
    "invalid_parent_dir": {"zh": "请先选择一个有效的父目录。", "en": "Please select a valid parent directory first."},
    "no_subdirs": {"zh": "该目录下没有子文件夹。", "en": "No subfolders found in this directory."},
    "task_running": {"zh": "已有处理任务正在进行。", "en": "A processing task is already running."},
    "invalid_single_folder": {"zh": "请选择有效的图片文件夹。", "en": "Please select a valid image folder."},
    "no_selection": {"zh": "请至少勾选一个子文件夹。", "en": "Please check at least one subfolder."},
    "batch_cancelled": {"zh": "批量处理已取消。", "en": "Batch processing cancelled."},
    "batch_start": {"zh": "开始处理文件夹", "en": "Start processing folder"},
    "batch_error": {"zh": "处理失败", "en": "failed"},
    "batch_done": {"zh": "处理完成", "en": "done"},
    "task_completed": {"zh": "当前任务处理完成！", "en": "Current task completed!"},
    "edit_rule_dialog_title": {"zh": "修改裁切规则", "en": "Modify Crop Rule"},
    "min_resolution": {"zh": "最小分辨率", "en": "Min Resolution"},
    "max_resolution": {"zh": "最大分辨率", "en": "Max Resolution"},
    "step_size": {"zh": "尺寸步进", "en": "Step Size"},
    "save_rule": {"zh": "保存当前规则", "en": "Save Rule"},
    "rule_saved_ok": {"zh": "规则已保存。", "en": "Rule saved."},
    "auto_rename": {"zh": "自动重命名", "en": "Auto Rename"},
    "sort_order_label": {"zh": "排序方式", "en": "Sort Order"},
    "sort_asc": {"zh": "按分辨率从小到大", "en": "By Resolution Ascending"},
    "sort_desc": {"zh": "按分辨率从大到小", "en": "By Resolution Descending"},
    "min_max_error": {"zh": "最小分辨率不能大于最大分辨率。", "en": "Min resolution cannot be greater than max resolution."},
    "step_error": {"zh": "尺寸步进必须为正整数。", "en": "Step size must be a positive integer."},
    "invalid_integer": {"zh": "请输入有效整数。", "en": "Please enter valid integers."},
}

def t(key: str, **kwargs) -> str:
    """获取当前语言的文本，支持格式化参数"""
    text_dict = TEXTS.get(key, {})
    msg = text_dict.get(LANG, text_dict.get("en", key))
    return msg.format(**kwargs) if kwargs else msg

def get_max_number_from_origin(origin_folder: Path) -> int:
    """获取原图文件夹中最大编号（仅.webp数字文件名）"""
    if not origin_folder.exists():
        return 0
    max_num = 0
    for f in origin_folder.iterdir():
        if f.is_file() and f.suffix.lower() == '.webp' and f.stem.isdigit():
            try:
                max_num = max(max_num, int(f.stem))
            except ValueError:
                continue
    return max_num

def get_image_dimensions(path: Path) -> Optional[Tuple[int, int]]:
    """安全获取图片尺寸，失败返回 None"""
    try:
        with Image.open(path) as img:
            return img.size
    except Exception:
        return None

def get_image_area_cached(dimensions_cache: Dict[Path, Optional[Tuple[int, int]]], path: Path) -> int:
    """利用缓存获取图片面积"""
    dims = dimensions_cache.get(path)
    if dims is None:
        dims = get_image_dimensions(path)
        dimensions_cache[path] = dims
    if dims:
        return dims[0] * dims[1]
    return 0

def collect_raw_files(input_path: Path, origin_folder: Path) -> List[Path]:
    """收集需要处理的原始图片（不在原图文件夹内）"""
    return [f for f in input_path.iterdir()
            if f.is_file() and f.suffix.lower() in IMAGE_SUFFIXES and f.parent != origin_folder]

def rename_files(
    input_path: Path,
    origin_folder: Path,
    sort_order: str,
    log: Callable,
    cancel_event: Optional[threading.Event] = None,
    dimensions_cache: Optional[Dict[Path, Optional[Tuple[int, int]]]] = None
) -> None:
    """重命名原始文件（按面积排序后编号）"""
    raw_files = collect_raw_files(input_path, origin_folder)
    if not raw_files:
        log(t("no_new_raw_files"))
        return

    log(t("checking_new_files"))
    max_num = get_max_number_from_origin(origin_folder)
    num_new = len(raw_files)
    total_after = max_num + num_new
    digits = max(2, len(str(total_after)))
    start_num = max_num + 1
    log(t("renaming_info", max_num=max_num, num_new=num_new, start_num=start_num,
          total_after=total_after, digits=digits))

    # 使用缓存排序
    if dimensions_cache is None:
        dimensions_cache = {}
    reverse = (sort_order == 'desc')
    sorted_files = sorted(raw_files, key=lambda f: get_image_area_cached(dimensions_cache, f), reverse=reverse)

    for idx, file_path in enumerate(sorted_files, start=start_num):
        if cancel_event and cancel_event.is_set():
            log(t("cancelled"))
            return
        suffix = file_path.suffix.lower()
        new_name = f"{idx:0{digits}d}{suffix}"
        new_path = file_path.with_name(new_name)
        try:
            file_path.rename(new_path)
            log(t("renaming_file", old=file_path.name, new=new_name))
        except Exception as e:
            log(t("skip_unreadable", name=file_path.name, error=e))

def convert_to_webp(
    input_path: Path,
    origin_folder: Path,
    log: Callable,
    progress_range: Tuple[float, float],
    cancel_event: Optional[threading.Event] = None
) -> int:
    """将原始图片转换为 WebP 并存入原图文件夹，返回成功转换数量"""
    raw_files = collect_raw_files(input_path, origin_folder)
    if not raw_files:
        log(t("step1_skip"))
        return 0

    log(t("step1_title"))
    origin_folder.mkdir(exist_ok=True)
    converted_count = 0
    total = len(raw_files)
    start_pct, end_pct = progress_range

    for i, file_path in enumerate(raw_files):
        if cancel_event and cancel_event.is_set():
            log(t("cancelled"))
            return converted_count
        pct = start_pct + (i / max(total, 1)) * (end_pct - start_pct)
        try:
            with Image.open(file_path) as img:
                img.load()
        except Exception as e:
            log(t("skip_unreadable", name=file_path.name, error=e))
            continue

        new_name = file_path.stem + ".webp"
        dest_path = origin_folder / new_name
        try:
            with Image.open(file_path) as img:
                img.save(dest_path, format="WEBP", quality=85, method=6)
            send2trash.send2trash(str(file_path))
            log(t("step1_converted", name=file_path.name), pct)
            converted_count += 1
        except Exception as e:
            log(t("step1_fail", name=file_path.name, error=e), pct)

    log(t("step1_done", count=converted_count))
    return converted_count

def process_resize_crop(
    origin_folder: Path,
    input_path: Path,
    min_size: int,
    max_size: int,
    step: int,
    log: Callable,
    progress_range: Tuple[float, float],
    cancel_event: Optional[threading.Event] = None
) -> None:
    """第二步：对原图文件夹中的图片进行尺寸处理并分发"""
    if not origin_folder.exists() or not any(origin_folder.iterdir()):
        log(t("step2_empty"))
        return

    files = [f for f in origin_folder.iterdir()
             if f.is_file() and f.suffix.lower() in IMAGE_SUFFIXES]
    total_files = len(files)
    if total_files == 0:
        log(t("step2_empty"))
        return

    small_folder_name = f"lt{min_size}"
    small_folder = input_path / small_folder_name
    small_folder.mkdir(exist_ok=True)

    folder_count: Dict[str, int] = {}
    small_count = 0
    skipped = 0
    errors = 0

    start_pct, end_pct = progress_range
    log(t("step2_title", total=total_files))

    for idx, file_path in enumerate(files, start=1):
        if cancel_event and cancel_event.is_set():
            log(t("cancelled"))
            return
        pct = start_pct + (idx / total_files) * (end_pct - start_pct)
        log(t("processing_file", idx=idx, total=total_files, name=file_path.name), pct)

        try:
            img = Image.open(file_path)
            img.load()
        except Exception as e:
            log(t("skip_unreadable", name=file_path.name, error=e), pct)
            skipped += 1
            continue

        orig_w, orig_h = img.size
        log(t("orig_size", w=orig_w, h=orig_h))

        # 情况1：原始最小边 < min_size
        if min(orig_w, orig_h) < min_size:
            dest = small_folder / file_path.name
            if dest.exists():
                log(t("target_exists", folder=small_folder_name, name=file_path.name))
                skipped += 1
            else:
                try:
                    shutil.copy2(file_path, dest)
                    log(t("small_min_side", min=min_size, folder=small_folder_name, name=file_path.name))
                    small_count += 1
                except Exception as e:
                    log(t("save_fail", error=e))
                    errors += 1
            img.close()
            continue

        # 缩放处理
        scaled_w, scaled_h = orig_w, orig_h
        if max(orig_w, orig_h) > max_size:
            img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
            scaled_w, scaled_h = img.size
            log(t("scaled", w=scaled_w, h=scaled_h))
        else:
            log(t("no_scale"))

        # 情况2：缩放后最小边 < min_size
        if min(scaled_w, scaled_h) < min_size:
            dest = small_folder / file_path.name
            if dest.exists():
                log(t("target_exists", folder=small_folder_name, name=file_path.name))
                skipped += 1
            else:
                try:
                    img.save(dest, format="WEBP", quality=85, method=6)
                    log(t("scaled_still_small", min=min_size, folder=small_folder_name, name=file_path.name))
                    small_count += 1
                except Exception as e:
                    log(t("save_fail", error=e))
                    errors += 1
            img.close()
            continue

        # 正常裁切
        target_w = (scaled_w // step) * step
        target_h = (scaled_h // step) * step
        while target_w < min_size:
            target_w += step
        while target_h < min_size:
            target_h += step

        try:
            if target_w == scaled_w and target_h == scaled_h:
                final_img = img
                log(t("no_crop", w=target_w, h=target_h))
            else:
                left = (scaled_w - target_w) // 2
                top = (scaled_h - target_h) // 2
                final_img = img.crop((left, top, left + target_w, top + target_h))
                log(t("center_crop", w=target_w, h=target_h))

            size_folder_name = f"{target_w}x{target_h}"
            size_folder = input_path / size_folder_name
            size_folder.mkdir(exist_ok=True)
            output_path = size_folder / file_path.name

            if output_path.exists():
                log(t("target_exists", folder=size_folder_name, name=file_path.name))
                skipped += 1
            else:
                final_img.save(output_path, format="WEBP", quality=85, method=6)
                log(t("saved", folder=size_folder_name, name=file_path.name))
                folder_count[size_folder_name] = folder_count.get(size_folder_name, 0) + 1
        except Exception as e:
            log(t("save_fail", error=e))
            errors += 1
        finally:
            if final_img != img:
                final_img.close()
            img.close()

    # 最终统计
    log("=" * 50)
    log(t("stats_title"))
    log(t("stats_skipped", count=skipped))
    log(t("stats_small", folder=small_folder_name, count=small_count))
    log(t("stats_errors", count=errors))
    log(t("stats_size_folders"))
    if folder_count:
        for folder, count in sorted(folder_count.items()):
            log(f"  {folder}: {count} 张" if LANG == "zh" else f"  {folder}: {count} images")
    else:
        log(t("stats_none"))
    log(t("origin_preserved"))
    log("=" * 50)

def get_origin_folder(input_path: Path) -> Path:
    """
    获取原始图片备份文件夹路径。
    优先使用英文名 'originals'；若中文名 '原图' 已存在，则使用中文名；
    否则根据当前语言创建新文件夹。
    """
    en_name = input_path / "originals"
    zh_name = input_path / "原图"

    if en_name.exists():
        return en_name
    if zh_name.exists():
        return zh_name

    if LANG == "zh":
        zh_name.mkdir(exist_ok=True)
        return zh_name
    else:
        en_name.mkdir(exist_ok=True)
        return en_name

def process_images(
    input_folder: str,
    min_size: int = 512,
    max_size: int = 2048,
    step: int = 64,
    rename: bool = False,
    sort_order: str = 'asc',
    progress_callback: Optional[Callable[[str, Optional[float]], None]] = None,
    cancel_event: Optional[threading.Event] = None
) -> None:
    """
    主处理流程
    progress_callback: 接收两个参数 (message, percent)
    cancel_event: 提供取消机制，设置后各阶段将尽快终止
    """
    def log(msg: str, pct: Optional[float] = None):
        if progress_callback:
            progress_callback(msg, pct)

    input_path = Path(input_folder)
    if not input_path.is_dir():
        log(t("error_no_dir"))
        return

    origin_folder = get_origin_folder(input_path)

    # ---------- 重命名 ----------
    if rename:
        rename_files(input_path, origin_folder, sort_order, log, cancel_event)
    else:
        # 检查是否有新文件
        if collect_raw_files(input_path, origin_folder):
            log(t("checking_new_files"))
        else:
            log(t("renaming_skipped"))

    # ---------- 第一步：转换 ----------
    # 进度分配：第一步 0~0.3，第二步 0.3~1.0
    convert_to_webp(input_path, origin_folder, log, (0.0, 0.3), cancel_event)

    # ---------- 第二步：尺寸处理 ----------
    process_resize_crop(origin_folder, input_path, min_size, max_size, step, log, (0.3, 1.0), cancel_event)

def main(argv=None):
    import argparse
    parser = argparse.ArgumentParser(description=t("title"))
    parser.add_argument("folder", help="Path to the image folder")
    parser.add_argument("--min", type=int, default=None, help=f"Minimum resolution (default: 512)")
    parser.add_argument("--max", type=int, default=None, help=f"Maximum resolution (default: 2048)")
    parser.add_argument("--step", type=int, default=None, help=f"Resolution step (default: 64)")
    parser.add_argument("--rename", action="store_true", help="Enable auto-renaming")
    parser.add_argument("--sort", choices=["asc", "desc"], default="asc",
                        help="Sort order for renaming: asc (smallest first) or desc (largest first)")

    if argv is None:
        args = parser.parse_args()
    else:
        args = parser.parse_args(argv)

    folder = args.folder
    input_path = Path(folder)
    rules_file = input_path / ".process_rules"

    min_val = args.min
    max_val = args.max
    step_val = args.step

    if None in (min_val, max_val, step_val) and rules_file.exists():
        try:
            with open(rules_file, "r", encoding="utf-8") as f:
                saved = json.load(f)
            if min_val is None:
                min_val = saved.get("min", 512)
            if max_val is None:
                max_val = saved.get("max", 2048)
            if step_val is None:
                step_val = saved.get("step", 64)
        except Exception:
            pass

    if min_val is None:
        min_val = 512
    if max_val is None:
        max_val = 2048
    if step_val is None:
        step_val = 64

    process_images(
        folder,
        min_size=min_val,
        max_size=max_val,
        step=step_val,
        rename=args.rename,
        sort_order=args.sort
    )

if __name__ == "__main__":
    main()