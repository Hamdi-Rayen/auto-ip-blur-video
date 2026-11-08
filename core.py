import os
import re
import cv2
import numpy as np
import subprocess
import imageio_ffmpeg
from rapidocr_onnxruntime import RapidOCR

# Standard IPv4 Regex (supports optional port or subnet mask)
IPV4_REGEX = re.compile(
    r'\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)(?::\d{1,5})?(?:/\d{1,2})?\b'
)

# Optional IPv6 Regex
IPV6_REGEX = re.compile(
    r'\b(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}\b|\b(?:[0-9a-fA-F]{1,4}:){1,7}:'
    r'|\b:(?::[0-9a-fA-F]{1,4}){1,7}\b'
)

class IPBlurProcessor:
    def __init__(
        self,
        style="pixelate",          # "pixelate", "blur", "blackout"
        strength=15,               # pixel block size or gaussian blur radius
        padding=6,                 # extra pixel padding around detected box
        ocr_stride=2,              # run OCR every N frames for speed
        box_persistence=6,         # keep blur alive for N frames to prevent flickering
        custom_targets=None,       # list of specific strings/IPs to blur (None = blur all IPs)
        include_ipv6=False
    ):
        self.style = style
        self.strength = max(3, strength)
        self.padding = padding
        self.ocr_stride = max(1, ocr_stride)
        self.box_persistence = max(1, box_persistence)
        self.custom_targets = [t.strip() for t in custom_targets if t.strip()] if custom_targets else []
        self.include_ipv6 = include_ipv6
        self.ocr = RapidOCR()
        self.is_cancelled = False

    def cancel(self):
        self.is_cancelled = True

    def find_target_regions(self, frame):
        """
        Runs OCR on a frame and returns list of [x1, y1, x2, y2] bounding boxes
        where target IP addresses or custom keywords are found.
        """
        h_frame, w_frame = frame.shape[:2]
        regions = []

        try:
            results, _ = self.ocr(frame)
        except Exception:
            return regions

        if not results:
            return regions

        for box, text, score in results:
            if not text:
                continue

            matches = []
            if self.custom_targets:
                for target in self.custom_targets:
                    for m in re.finditer(re.escape(target), text, re.IGNORECASE):
                        matches.append((m.start(), m.end()))
            else:
                for m in IPV4_REGEX.finditer(text):
                    matches.append((m.start(), m.end()))
                if self.include_ipv6:
                    for m in IPV6_REGEX.finditer(text):
                        matches.append((m.start(), m.end()))

            if not matches:
                continue

            # Convert box polygon to bounding coordinates
            pts = np.array(box, dtype=np.int32)
            bx1 = max(0, int(np.min(pts[:, 0])))
            by1 = max(0, int(np.min(pts[:, 1])))
            bx2 = min(w_frame, int(np.max(pts[:, 0])))
            by2 = min(h_frame, int(np.max(pts[:, 1])))

            box_w = bx2 - bx1
            total_len = max(1, len(text))

            # Sub-slice horizontal coordinates for exact match if text has multiple words
            for start_idx, end_idx in matches:
                if len(matches) == 1 and start_idx == 0 and end_idx == total_len:
                    x1, x2 = bx1, bx2
                else:
                    x1 = int(bx1 + (start_idx / total_len) * box_w)
                    x2 = int(bx1 + (end_idx / total_len) * box_w)

                y1, y2 = by1, by2

                # Apply padding
                x1 = max(0, x1 - self.padding)
                y1 = max(0, y1 - self.padding)
                x2 = min(w_frame, x2 + self.padding)
                y2 = min(h_frame, y2 + self.padding)

                if x2 > x1 and y2 > y1:
                    regions.append([x1, y1, x2, y2])

        return regions

    def apply_effect(self, frame, regions):
        """
        Applies blur / pixelation / blackout to specified regions in the frame.
        """
        for (x1, y1, x2, y2) in regions:
            roi = frame[y1:y2, x1:x2]
            rh, rw = roi.shape[:2]
            if rh <= 0 or rw <= 0:
                continue

            if self.style == "pixelate":
                # Mosaic / Pixelation effect
                block_size = max(4, self.strength)
                small_w = max(1, rw // block_size)
                small_h = max(1, rh // block_size)
                small = cv2.resize(roi, (small_w, small_h), interpolation=cv2.INTER_LINEAR)
                pixelated = cv2.resize(small, (rw, rh), interpolation=cv2.INTER_NEAREST)
                frame[y1:y2, x1:x2] = pixelated

            elif self.style == "blur":
                # Gaussian Blur
                k = self.strength if self.strength % 2 == 1 else self.strength + 1
                k = max(3, k)
                blurred = cv2.GaussianBlur(roi, (k, k), 0)
                frame[y1:y2, x1:x2] = blurred

            elif self.style == "blackout":
                # Solid dark rectangle
                frame[y1:y2, x1:x2] = (25, 25, 25)

        return frame

    def process_single_frame(self, frame):
        """
        Convenience method for previews.
        """
        regions = self.find_target_regions(frame)
        return self.apply_effect(frame.copy(), regions), len(regions)

    def process_video(self, input_path, output_path, progress_callback=None):
        """
        Reads input video, redacts detected IPs, and writes output video with original audio preserved.
        """
        self.is_cancelled = False

        if not os.path.exists(input_path):
            raise FileNotFoundError(f"Input video not found: {input_path}")

        cap = cv2.VideoCapture(input_path)
        if not cap.isOpened():
            raise RuntimeError(f"Could not open video file: {input_path}")

        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        # Temporary video output file for video-only stream
        base_dir = os.path.dirname(os.path.abspath(output_path))
        temp_video = os.path.join(base_dir, f"_temp_video_{os.getpid()}.mp4")

        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        writer = cv2.VideoWriter(temp_video, fourcc, fps, (width, height))

        # Memory for persisting boxes across frames (prevents flickering)
        # Format: list of [x1, y1, x2, y2, remaining_life]
        active_tracked_boxes = []

        frame_idx = 0
        total_ips_detected = 0

        try:
            while cap.isOpened():
                if self.is_cancelled:
                    break

                ret, frame = cap.read()
                if not ret:
                    break

                # Decrement lifetime of active tracked boxes
                new_tracked = []
                for box in active_tracked_boxes:
                    box[4] -= 1
                    if box[4] > 0:
                        new_tracked.append(box)
                active_tracked_boxes = new_tracked

                # Run OCR check on stride
                if frame_idx % self.ocr_stride == 0:
                    found_regions = self.find_target_regions(frame)
                    if found_regions:
                        total_ips_detected += len(found_regions)
                        # Add / refresh boxes with persistence life
                        for r in found_regions:
                            active_tracked_boxes.append([r[0], r[1], r[2], r[3], self.box_persistence])

                # Deduplicate overlapping regions to draw
                draw_regions = [[b[0], b[1], b[2], b[3]] for b in active_tracked_boxes]

                # Apply blur/redaction
                if draw_regions:
                    frame = self.apply_effect(frame, draw_regions)

                writer.write(frame)
                frame_idx += 1

                if progress_callback and total_frames > 0:
                    percent = (frame_idx / total_frames) * 100.0
                    progress_callback(frame_idx, total_frames, percent, total_ips_detected)

        finally:
            cap.release()
            writer.release()

        if self.is_cancelled:
            if os.path.exists(temp_video):
                os.remove(temp_video)
            return False

        # Mux original audio into final output using bundled ffmpeg
        ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
        cmd = [
            ffmpeg_exe,
            "-y",
            "-i", temp_video,
            "-i", input_path,
            "-c:v", "copy",
            "-c:a", "aac",
            "-map", "0:v:0",
            "-map", "1:a:0?",
            "-shortest",
            output_path
        ]

        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # Cleanup temp file
        if os.path.exists(temp_video):
            os.remove(temp_video)

        if result.returncode != 0 and not os.path.exists(output_path):
            # If muxing failed, keep temp video as output
            os.rename(temp_video, output_path)

        return True

