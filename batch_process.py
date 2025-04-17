import os
import subprocess
import argparse

def process_images(input_folder, output_folder, preset=None, upscale_factor=2, framerate=1, video_fps=30):
    """
    Processes all images in the input_folder using Fooocus for upscaling/variation,
    then merges them into a video.

    Args:
        input_folder (str): Directory containing input images.
        output_folder (str): Directory where processed frames and final video will be saved.
        preset (str): Optional Fooocus preset, e.g., "anime" or "realistic".
        upscale_factor (int): Upscaling multiplier (e.g., 2 means 2× upscaling).
        framerate (int): Number of seconds each frame holds in the video (default 1 sec per frame).
        video_fps (int): Frames‑per‑second of the final video.
    """
    # 1) Prepare output folder
    os.makedirs(output_folder, exist_ok=True)

    # 2) Gather all image files
    extensions = {'.png', '.jpg', '.jpeg', '.bmp', '.tif', '.tiff'}
    files = sorted([
        f for f in os.listdir(input_folder)
        if os.path.splitext(f)[1].lower() in extensions
    ])

    if not files:
        print(f"No images found in {input_folder}")
        return

    # 3) Process each image
    for idx, filename in enumerate(files, start=1):
        input_path = os.path.join(input_folder, filename)
        frame_name = f"frame_{idx:03d}.png"
        print(f"[{idx}/{len(files)}] Processing {filename} → {frame_name}")

        cmd = [
            sys.executable,    # ensures same Python interpreter
            "entry_with_update.py",
            "--share",         # headless mode; omit if you prefer --listen
            "--in-browser", "False",
            "--always-high-vram",
            "--upscale", str(upscale_factor),
            "--output-path", output_folder,
        ]
        if preset:
            cmd += ["--preset", preset]
        cmd += ["--image", input_path]

        subprocess.run(cmd, check=True)

        # Rename/move the single output image to our standardized frame name
        # (Fooocus will drop its own timestamped file into output_folder)
        # Find the newest PNG in output_folder:
        generated = sorted(
            [fn for fn in os.listdir(output_folder) if fn.lower().endswith(".png")],
            key=lambda fn: os.path.getmtime(os.path.join(output_folder, fn))
        )[-1]
        os.rename(
            os.path.join(output_folder, generated),
            os.path.join(output_folder, frame_name)
        )

    # 4) Stitch frames into video with ffmpeg
    video_path = os.path.join(output_folder, "output_video.mp4")
    ffmpeg_cmd = (
        f"ffmpeg -framerate {1/framerate:.6f} "
        f"-i {output_folder}/frame_%03d.png "
        f"-c:v libx264 -r {video_fps} -pix_fmt yuv420p {video_path}"
    )
    print("Merging frames into video…")
    os.system(ffmpeg_cmd)
    print(f"✅ Video saved to: {video_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Batch-process multiple images through Fooocus and compile them into a video."
    )
    parser.add_argument(
        "--input_folder", "-i", required=True,
        help="Path to folder of input images"
    )
    parser.add_argument(
        "--output_folder", "-o", required=True,
        help="Path to save processed frames and final video"
    )
    parser.add_argument(
        "--preset", "-p", default=None,
        help="Fooocus preset to use (anime, realistic, etc.)"
    )
    parser.add_argument(
        "--upscale_factor", "-u", type=int, default=2,
        help="Upscaling multiplier (e.g., 2 = 2×)"
    )
    parser.add_argument(
        "--framerate", "-f", type=int, default=1,
        help="Seconds each frame holds (default: 1s per image)"
    )
    parser.add_argument(
        "--video_fps", type=int, default=30,
        help="Frames-per-second of the output video"
    )
    args = parser.parse_args()

    # ensure we’re running from repo root
    import sys
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    process_images(
        args.input_folder,
        args.output_folder,
        preset=args.preset,
        upscale_factor=args.upscale_factor,
        framerate=args.framerate,
        video_fps=args.video_fps
    )
