import argparse
import os
import shutil
import tempfile
import zipfile
import cv2


def extract_frames(video_path, output_dir, target_fps=None, target_size=None):
  """Mengekstrak frame dari video ke direktori tujuan sebagai file PNG."""
  os.makedirs(output_dir, exist_ok=True)
  cap = cv2.VideoCapture(video_path)

  if not cap.isOpened():
    raise ValueError(f"Gagal membuka file video: {video_path}")

  orig_fps = cap.get(cv2.CAP_PROP_FPS)
  fps = target_fps if target_fps else int(orig_fps)

  orig_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
  orig_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
  width, height = target_size if target_size else (orig_w, orig_h)

  saved_count = 0
  frame_idx = 0
  step = orig_fps / fps if (target_fps and target_fps < orig_fps) else 1.0
  next_target_frame = 0.0

  while True:
    ret, frame = cap.read()
    if not ret:
      break

    if frame_idx >= int(next_target_frame):
      if target_size:
        frame = cv2.resize(
            frame, (width, height), interpolation=cv2.INTER_AREA
        )

      filename = os.path.join(output_dir, f"{saved_count:05d}.png")
      cv2.imwrite(filename, frame)
      saved_count += 1
      next_target_frame += step

    frame_idx += 1

  cap.release()
  print(
      f"  [+] {saved_count} frame diekstrak dari {os.path.basename(video_path)}"
  )
  return width, height, fps


def generate_desc_txt(filepath, width, height, fps, parts):
  """Membuat desc.txt standar Android dengan UNIX line endings."""
  lines = [f"{width} {height} {fps}"]
  for ptype, count, pause, folder_name in parts:
    lines.append(f"{ptype} {count} {pause} {folder_name}")

  content = "\n".join(lines) + "\n"
  with open(filepath, "w", newline="\n") as f:
    f.write(content)


def build_bootanimation_zip(source_dir, output_zip_path):
  """Wajib menggunakan ZIP_STORED (tanpa kompresi) agar Android dapat membaca animasi."""
  with zipfile.ZipFile(output_zip_path, "w", zipfile.ZIP_STORED) as zipf:
    for root, _, files in os.walk(source_dir):
      for file in sorted(files):
        file_path = os.path.join(root, file)
        arcname = os.path.relpath(file_path, source_dir)
        zipf.write(file_path, arcname)


def build_magisk_module(bootanim_zip_path, output_module_path, mod_id, name):
  """Membungkus bootanimation.zip menjadi modul Magisk / KernelSU."""
  with tempfile.TemporaryDirectory() as temp_dir:
    prop_content = f"""id={mod_id}
name={name}
version=v1.0
versionCode=1
author=BootanimationConverter
description=Custom bootanimation module generated via Bootanimation Converter.
"""
    with open(os.path.join(temp_dir, "module.prop"), "w", newline="\n") as f:
      f.write(prop_content)

    system_media_dir = os.path.join(temp_dir, "system", "media")
    os.makedirs(system_media_dir, exist_ok=True)
    shutil.copy(
        bootanim_zip_path, os.path.join(system_media_dir, "bootanimation.zip")
    )

    with zipfile.ZipFile(
        output_module_path, "w", zipfile.ZIP_DEFLATED
    ) as mod_zip:
      for root, _, files in os.walk(temp_dir):
        for file in files:
          file_path = os.path.join(root, file)
          arcname = os.path.relpath(file_path, temp_dir)
          mod_zip.write(file_path, arcname)


def main():
  parser = argparse.ArgumentParser(
      description="Android Bootanimation Converter CLI"
  )
  parser.add_argument(
      "--mode",
      choices=["loop", "3stage"],
      required=True,
      help="Mode bootanimation: 'loop' (single video) atau '3stage' (opening,"
      " loop, closing)",
  )

  # Input video
  parser.add_argument(
      "--video",
      help="Path video tunggal untuk mode 'loop'",
  )
  parser.add_argument(
      "--opening",
      help="Path video opening/intro untuk mode '3stage'",
  )
  parser.add_argument(
      "--loop-video",
      help="Path video looping untuk mode '3stage'",
  )
  parser.add_argument(
      "--closing",
      help="Path video closing/outro untuk mode '3stage'",
  )

  # Konfigurasi Output
  parser.add_argument(
      "-o",
      "--output",
      default="bootanimation.zip",
      help="Nama file zip output (default: bootanimation.zip)",
  )
  parser.add_argument(
      "--magisk",
      action="store_true",
      help="Bungkus output langsung menjadi Modul Magisk/KernelSU (.zip)",
  )
  parser.add_argument(
      "--fps",
      type=int,
      help="Target FPS bootanimation (jika tidak diisi, mengikuti FPS video)",
  )
  parser.add_argument(
      "--res",
      type=str,
      help="Resolusi target contoh: '1080x2400' (jika tidak diisi, mengikuti"
      " video asli)",
  )

  args = parser.parse_args()

  target_size = None
  if args.res:
    try:
      w, h = map(int, args.res.lower().split("x"))
      target_size = (w, h)
    except ValueError:
      print("[-] Format --res salah. Gunakan format LEBARxTINGGI (misal:"
            " 1080x2400)")
      return

  with tempfile.TemporaryDirectory() as work_dir:
    parts_config = []
    width, height, fps = 1080, 1920, 30

    if args.mode == "loop":
      if not args.video:
        print("[-] Mode 'loop' membutuhkan parameter --video <path_video>")
        return

      part0_dir = os.path.join(work_dir, "part0")
      width, height, fps = extract_frames(
          args.video, part0_dir, target_fps=args.fps, target_size=target_size
      )
      # 'p' = part loop, '0' = loop infinite, '0' = pause 0 frame
      parts_config.append(("p", 0, 0, "part0"))

    elif args.mode == "3stage":
      if not (args.opening and args.loop_video and args.closing):
        print(
            "[-] Mode '3stage' membutuhkan 3 file video: --opening,"
            " --loop-video, dan --closing"
        )
        return

      # 1. Opening (Diputar 1x penuh)
      part0_dir = os.path.join(work_dir, "part0")
      w0, h0, fps0 = extract_frames(
          args.opening, part0_dir, target_fps=args.fps, target_size=target_size
      )
      parts_config.append(("c", 1, 0, "part0"))

      # 2. Looping (Diputar terus menerus selama booting)
      part1_dir = os.path.join(work_dir, "part1")
      w1, h1, _ = extract_frames(
          args.loop_video,
          part1_dir,
          target_fps=args.fps,
          target_size=target_size,
      )
      parts_config.append(("p", 0, 0, "part1"))

      # 3. Closing (Diputar 1x saat booting selesai)
      part2_dir = os.path.join(work_dir, "part2")
      w2, h2, _ = extract_frames(
          args.closing, part2_dir, target_fps=args.fps, target_size=target_size
      )
      parts_config.append(("c", 1, 0, "part2"))

      width, height, fps = w0, h0, fps0

    # Buat desc.txt
    desc_path = os.path.join(work_dir, "desc.txt")
    generate_desc_txt(desc_path, width, height, fps, parts_config)

    # Buat bootanimation.zip temporary atau final
    temp_bootanim_zip = (
        os.path.join(work_dir, "bootanimation_raw.zip")
        if args.magisk
        else args.output
    )

    print("[+] Membuat bootanimation.zip (Uncompressed STORED)...")
    build_bootanimation_zip(work_dir, temp_bootanim_zip)

    # Jika user memilih output Modul Magisk/KernelSU
    if args.magisk:
      mod_output = (
          args.output
          if args.output.endswith(".zip")
          else f"{args.output}_magisk.zip"
      )
      print(f"[+] Membungkus ke modul Magisk/KernelSU: {mod_output}")
      build_magisk_module(
          temp_bootanim_zip,
          mod_output,
          mod_id="custom_bootanim",
          name="Custom Bootanimation Module",
      )

  print("[✔] Selesai!")


if __name__ == "__main__":
  main()
