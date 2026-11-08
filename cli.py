import argparse
import sys
import os
import time
from core import IPBlurProcessor

def main():
    parser = argparse.ArgumentParser(
        description="Auto Blur / Redact IP Addresses in Video Demos (For Adobe Premiere Pro & Montages)"
    )
    parser.add_argument("-i", "--input", required=True, help="Path to input video file")
    parser.add_argument("-o", "--output", default=None, help="Path to output video file (optional)")
    parser.add_argument(
        "--style",
        choices=["pixelate", "blur", "blackout"],
        default="pixelate",
        help="Redaction style (default: pixelate)"
    )
    parser.add_argument("--strength", type=int, default=15, help="Blur / Pixel block strength (default: 15)")
    parser.add_argument("--padding", type=int, default=6, help="Padding in pixels around detected box (default: 6)")
    parser.add_argument("--stride", type=int, default=2, help="Run OCR every N frames for speed (default: 2)")
    parser.add_argument("--persistence", type=int, default=6, help="Frames to keep blur alive to prevent flicker (default: 6)")
    parser.add_argument("--targets", nargs="*", default=None, help="Specific IP addresses or words to blur instead of all IPs")
    parser.add_argument("--ipv6", action="store_true", help="Also detect and blur IPv6 addresses")

    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"Error: Input file does not exist: {args.input}")
        sys.exit(1)

    if not args.output:
        base, ext = os.path.splitext(args.input)
        args.output = f"{base}_blurred{ext}"

    print("=" * 60)
    print("      AUTO IP BLUR / REDACTION TOOL (FOR PREMIERE PRO)")
    print("=" * 60)
    print(f"Input Video : {args.input}")
    print(f"Output Video: {args.output}")
    print(f"Style       : {args.style}")
    print(f"Strength    : {args.strength}")
    print(f"Target IPs  : {args.targets if args.targets else 'ALL IPv4 Addresses'}")
    print("-" * 60)

    start_time = time.time()
    last_print = 0

    def progress(current, total, percent, detected_count):
        nonlocal last_print
        now = time.time()
        if now - last_print > 0.5 or current == total:
            last_print = now
            elapsed = now - start_time
            fps = current / elapsed if elapsed > 0 else 0
            eta = (total - current) / fps if fps > 0 else 0
            bar_len = 30
            filled = int(bar_len * (current / total))
            bar = "█" * filled + "-" * (bar_len - filled)
            sys.stdout.write(
                f"\r[{bar}] {percent:5.1f}% | Frame {current}/{total} | {fps:.1f} fps | ETA: {eta:.0f}s | Detections: {detected_count}"
            )
            sys.stdout.flush()

    processor = IPBlurProcessor(
        style=args.style,
        strength=args.strength,
        padding=args.padding,
        ocr_stride=args.stride,
        box_persistence=args.persistence,
        custom_targets=args.targets,
        include_ipv6=args.ipv6
    )

    print("Processing video...")
    success = processor.process_video(args.input, args.output, progress_callback=progress)
    print("\n" + "-" * 60)

    if success:
        total_time = time.time() - start_time
        print(f"Done in {total_time:.1f} seconds!")
        print(f"Blurred video ready: {args.output}")
    else:
        print("Processing was cancelled or encountered an error.")

if __name__ == "__main__":
    main()

