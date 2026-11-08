import os
import sys
import time
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import cv2
from PIL import Image, ImageTk
from core import IPBlurProcessor

class AutoIPBlurApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Auto IP Blur & Redaction Tool")
        self.root.geometry("760x620")
        self.root.minsize(650, 480)

        # Clean, modern color scheme
        self.bg_color = "#1e1e24"
        self.card_color = "#2b2b36"
        self.text_color = "#f0f0f5"
        self.accent_color = "#007acc"
        self.accent_hover = "#0098ff"
        self.success_color = "#28a745"

        self.root.configure(bg=self.bg_color)

        self.processor = None
        self.is_processing = False
        self.preview_window = None

        self._init_styles()
        self._build_ui()

    def _init_styles(self):
        self.style = ttk.Style()
        self.style.theme_use("clam")

        self.style.configure(".", background=self.bg_color, foreground=self.text_color, font=("Segoe UI", 10))
        self.style.configure("Card.TFrame", background=self.card_color, relief="flat")
        self.style.configure("TLabel", background=self.bg_color, foreground=self.text_color)
        self.style.configure("Card.TLabel", background=self.card_color, foreground=self.text_color)
        self.style.configure("CardHeader.TLabel", background=self.card_color, foreground="#ffffff", font=("Segoe UI", 11, "bold"))
        self.style.configure("TCombobox", fieldbackground="#3a3a48", background="#3a3a48", foreground="#ffffff")
        self.style.configure("TCheckbutton", background=self.card_color, foreground=self.text_color)
        self.style.configure("TRadiobutton", background=self.card_color, foreground=self.text_color)
        self.style.configure("Horizontal.TProgressbar", troughcolor="#3a3a48", background=self.accent_color)

    def _build_ui(self):
        # 1. Header (Pinned to Top)
        header_frame = tk.Frame(self.root, bg="#121217", pady=10, padx=20)
        header_frame.pack(side="top", fill="x")

        title_lbl = tk.Label(
            header_frame,
            text="Auto IP Blur & Redaction Tool",
            font=("Segoe UI", 15, "bold"),
            fg="#ffffff",
            bg="#121217"
        )
        title_lbl.pack(anchor="w")

        sub_lbl = tk.Label(
            header_frame,
            text="Automatically detect and blur IP addresses in screen recordings for Premiere Pro",
            font=("Segoe UI", 9),
            fg="#a0a0b0",
            bg="#121217"
        )
        sub_lbl.pack(anchor="w", pady=(1, 0))

        # 2. Bottom Action Bar (PINNED TO BOTTOM - ALWAYS VISIBLE)
        bottom_bar = tk.Frame(self.root, bg="#181820", padx=20, pady=12, highlightbackground="#32323e", highlightthickness=1)
        bottom_bar.pack(side="bottom", fill="x")

        self.progress_bar = ttk.Progressbar(bottom_bar, orient="horizontal", mode="determinate", style="Horizontal.TProgressbar")
        self.progress_bar.pack(fill="x", pady=(0, 6))

        self.status_lbl = tk.Label(bottom_bar, text="Ready. Select a video above to begin.", bg="#181820", fg="#c0c0d0", font=("Segoe UI", 9))
        self.status_lbl.pack(anchor="w", pady=(0, 8))

        btn_row = tk.Frame(bottom_bar, bg="#181820")
        btn_row.pack(fill="x")

        self.btn_start = tk.Button(
            btn_row,
            text="▶ Start Blurring Video",
            bg=self.accent_color,
            fg="#ffffff",
            font=("Segoe UI", 11, "bold"),
            activebackground=self.accent_hover,
            relief="flat",
            padx=22,
            pady=8,
            cursor="hand2",
            command=self.start_processing
        )
        self.btn_start.pack(side="left")

        self.btn_cancel = tk.Button(
            btn_row,
            text="Cancel",
            bg="#474758",
            fg="#ffffff",
            font=("Segoe UI", 10),
            activebackground="#5a5a6e",
            relief="flat",
            padx=16,
            pady=8,
            state="disabled",
            command=self.cancel_processing
        )
        self.btn_cancel.pack(side="left", padx=10)

        self.btn_open_folder = tk.Button(
            btn_row,
            text="Open Output Folder",
            bg="#2c6b3f",
            fg="#ffffff",
            font=("Segoe UI", 10),
            activebackground="#36864e",
            relief="flat",
            padx=16,
            pady=8,
            state="disabled",
            command=self.open_output_folder
        )
        self.btn_open_folder.pack(side="right")

        # 3. Middle Scrollable Area (Files & Settings)
        canvas_container = tk.Frame(self.root, bg=self.bg_color)
        canvas_container.pack(side="top", fill="both", expand=True)

        canvas = tk.Canvas(canvas_container, bg=self.bg_color, highlightthickness=0)
        scrollbar = ttk.Scrollbar(canvas_container, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=self.bg_color, padx=15, pady=10)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas_window = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")

        def _on_canvas_configure(event):
            canvas.itemconfig(canvas_window, width=event.width)

        canvas.bind("<Configure>", _on_canvas_configure)
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Optional Mouse Wheel scrolling
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)

        # --- Section A: File Selection Card ---
        files_frame = ttk.Frame(scrollable_frame, style="Card.TFrame", padding=12)
        files_frame.pack(fill="x", pady=(0, 10))

        ttk.Label(files_frame, text="1. Select Video Files", style="CardHeader.TLabel").grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 8))

        ttk.Label(files_frame, text="Input Video:", style="Card.TLabel").grid(row=1, column=0, sticky="w", pady=4)
        self.input_entry = tk.Entry(files_frame, bg="#3b3b4a", fg="#ffffff", insertbackground="#ffffff", font=("Segoe UI", 9), relief="flat")
        self.input_entry.grid(row=1, column=1, sticky="ew", padx=8, pady=4)
        btn_browse_in = tk.Button(files_frame, text="Browse...", bg="#474758", fg="#ffffff", activebackground="#5a5a6e", relief="flat", padx=12, command=self.browse_input)
        btn_browse_in.grid(row=1, column=2, pady=4)

        ttk.Label(files_frame, text="Output Video:", style="Card.TLabel").grid(row=2, column=0, sticky="w", pady=4)
        self.output_entry = tk.Entry(files_frame, bg="#3b3b4a", fg="#ffffff", insertbackground="#ffffff", font=("Segoe UI", 9), relief="flat")
        self.output_entry.grid(row=2, column=1, sticky="ew", padx=8, pady=4)
        btn_browse_out = tk.Button(files_frame, text="Browse...", bg="#474758", fg="#ffffff", activebackground="#5a5a6e", relief="flat", padx=12, command=self.browse_output)
        btn_browse_out.grid(row=2, column=2, pady=4)

        files_frame.columnconfigure(1, weight=1)

        # --- Section B: Blur Settings Card ---
        settings_frame = ttk.Frame(scrollable_frame, style="Card.TFrame", padding=12)
        settings_frame.pack(fill="x", pady=(0, 10))

        ttk.Label(settings_frame, text="2. Detection & Blur Settings", style="CardHeader.TLabel").grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 8))

        # Effect Style
        ttk.Label(settings_frame, text="Blur Style:", style="Card.TLabel").grid(row=1, column=0, sticky="w", pady=4)
        self.style_var = tk.StringVar(value="pixelate")
        style_box = ttk.Combobox(settings_frame, textvariable=self.style_var, values=["pixelate", "blur", "blackout"], state="readonly", width=14)
        style_box.grid(row=1, column=1, sticky="w", padx=8, pady=4)
        ttk.Label(settings_frame, text="(pixelate = mosaic / blur = smooth / blackout = solid bar)", style="Card.TLabel", font=("Segoe UI", 8), foreground="#9090a0").grid(row=1, column=2, sticky="w")

        # Strength Slider
        ttk.Label(settings_frame, text="Strength:", style="Card.TLabel").grid(row=2, column=0, sticky="w", pady=4)
        self.strength_scale = tk.Scale(settings_frame, from_=5, to=45, orient="horizontal", bg=self.card_color, fg="#ffffff", highlightthickness=0, troughcolor="#3b3b4a")
        self.strength_scale.set(15)
        self.strength_scale.grid(row=2, column=1, sticky="ew", padx=8, pady=4)

        # Target Mode
        ttk.Label(settings_frame, text="Target IP:", style="Card.TLabel").grid(row=3, column=0, sticky="nw", pady=4)
        self.target_mode_var = tk.StringVar(value="all")

        radio_frame = tk.Frame(settings_frame, bg=self.card_color)
        radio_frame.grid(row=3, column=1, columnspan=2, sticky="w", padx=8, pady=4)

        rb_all = ttk.Radiobutton(radio_frame, text="Detect ALL IPv4 Addresses automatically", variable=self.target_mode_var, value="all", command=self.toggle_target_input)
        rb_all.pack(anchor="w")

        rb_specific = ttk.Radiobutton(radio_frame, text="Only blur specific IP(s) or words:", variable=self.target_mode_var, value="specific", command=self.toggle_target_input)
        rb_specific.pack(anchor="w", pady=(4, 2))

        self.specific_entry = tk.Entry(radio_frame, bg="#3b3b4a", fg="#ffffff", insertbackground="#ffffff", font=("Segoe UI", 9), relief="flat", width=42, state="disabled")
        self.specific_entry.pack(anchor="w", padx=(20, 0))
        self.specific_hint = tk.Label(radio_frame, text="Separate multiple with commas (e.g. 192.168.1.50, 10.0.0.1)", font=("Segoe UI", 8), fg="#9090a0", bg=self.card_color)
        self.specific_hint.pack(anchor="w", padx=(20, 0))

        # Checkbox for IPv6
        self.ipv6_var = tk.BooleanVar(value=False)
        cb_ipv6 = ttk.Checkbutton(settings_frame, text="Also detect IPv6 addresses", variable=self.ipv6_var)
        cb_ipv6.grid(row=4, column=1, sticky="w", padx=8, pady=(4, 0))

        # Preview Button
        btn_preview = tk.Button(
            settings_frame,
            text="👁 Preview Blur on Current Video",
            bg="#3b3b4a",
            fg="#ffffff",
            activebackground="#4c4c5e",
            relief="flat",
            padx=12,
            pady=4,
            command=self.open_preview
        )
        btn_preview.grid(row=5, column=1, sticky="w", padx=8, pady=(8, 0))

        settings_frame.columnconfigure(1, weight=1)

    def toggle_target_input(self):
        if self.target_mode_var.get() == "specific":
            self.specific_entry.configure(state="normal")
        else:
            self.specific_entry.configure(state="disabled")

    def browse_input(self):
        path = filedialog.askopenfilename(
            title="Select Video File",
            filetypes=[("Video Files", "*.mp4 *.mov *.mkv *.avi *.wmv *.m4v"), ("All Files", "*.*")]
        )
        if path:
            self.input_entry.delete(0, tk.END)
            self.input_entry.insert(0, os.path.normpath(path))

            # Auto-fill output path
            base, ext = os.path.splitext(path)
            auto_out = f"{base}_blurred{ext}"
            self.output_entry.delete(0, tk.END)
            self.output_entry.insert(0, os.path.normpath(auto_out))
            self.status_lbl.configure(text=f"Selected: {os.path.basename(path)}")

    def browse_output(self):
        path = filedialog.asksaveasfilename(
            title="Save Blurred Video As",
            defaultextension=".mp4",
            filetypes=[("MP4 Video", "*.mp4"), ("All Files", "*.*")]
        )
        if path:
            self.output_entry.delete(0, tk.END)
            self.output_entry.insert(0, os.path.normpath(path))

    def open_output_folder(self):
        out_path = self.output_entry.get().strip()
        if out_path and os.path.exists(os.path.dirname(out_path)):
            os.startfile(os.path.dirname(out_path))

    def open_preview(self):
        in_path = self.input_entry.get().strip()
        if not in_path or not os.path.exists(in_path):
            messagebox.showwarning("No Video Selected", "Please select a valid input video first.")
            return

        cap = cv2.VideoCapture(in_path)
        if not cap.isOpened():
            messagebox.showerror("Error", "Could not open video for preview.")
            return

        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        target_frame = min(30, max(0, total_frames // 10))
        cap.set(cv2.CAP_PROP_POS_FRAMES, target_frame)
        ret, frame = cap.read()
        cap.release()

        if not ret:
            messagebox.showerror("Error", "Could not read preview frame.")
            return

        targets = None
        if self.target_mode_var.get() == "specific":
            targets = [t.strip() for t in self.specific_entry.get().split(",") if t.strip()]

        proc = IPBlurProcessor(
            style=self.style_var.get(),
            strength=int(self.strength_scale.get()),
            custom_targets=targets,
            include_ipv6=self.ipv6_var.get()
        )

        blurred_frame, count = proc.process_single_frame(frame)

        top = tk.Toplevel(self.root)
        top.title(f"Preview Frame #{target_frame} - IPs Detected: {count}")
        top.configure(bg=self.bg_color)

        h, w = blurred_frame.shape[:2]
        max_dim = 700
        scale = min(max_dim / w, max_dim / h, 1.0)
        disp_w, disp_h = int(w * scale), int(h * scale)
        rgb = cv2.cvtColor(cv2.resize(blurred_frame, (disp_w, disp_h)), cv2.COLOR_BGR2RGB)
        img_pil = Image.fromarray(rgb)
        img_tk = ImageTk.PhotoImage(img_pil)

        info_lbl = tk.Label(top, text=f"Detected & Blurred {count} IP regions on frame #{target_frame}", fg="#ffffff", bg=self.bg_color, font=("Segoe UI", 10, "bold"), pady=8)
        info_lbl.pack()

        lbl_img = tk.Label(top, image=img_tk, bg=self.bg_color)
        lbl_img.image = img_tk
        lbl_img.pack(padx=10, pady=10)

    def start_processing(self):
        in_path = self.input_entry.get().strip()
        out_path = self.output_entry.get().strip()

        if not in_path or not os.path.exists(in_path):
            messagebox.showerror("Error", "Please select a valid input video.")
            return

        if not out_path:
            messagebox.showerror("Error", "Please specify an output video file.")
            return

        targets = None
        if self.target_mode_var.get() == "specific":
            targets = [t.strip() for t in self.specific_entry.get().split(",") if t.strip()]
            if not targets:
                messagebox.showwarning("Warning", "Please enter at least one target IP or string, or choose 'Detect ALL IPv4'.")
                return

        self.processor = IPBlurProcessor(
            style=self.style_var.get(),
            strength=int(self.strength_scale.get()),
            custom_targets=targets,
            include_ipv6=self.ipv6_var.get()
        )

        self.is_processing = True
        self.btn_start.configure(state="disabled")
        self.btn_cancel.configure(state="normal")
        self.btn_open_folder.configure(state="disabled")
        self.progress_bar["value"] = 0
        self.status_lbl.configure(text="Starting video processing...", fg="#ffffff")

        thread = threading.Thread(target=self._run_process_thread, args=(in_path, out_path), daemon=True)
        thread.start()

    def _run_process_thread(self, in_path, out_path):
        start_time = time.time()

        def progress_cb(current, total, percent, detected_count):
            elapsed = time.time() - start_time
            fps = current / elapsed if elapsed > 0 else 0
            eta = (total - current) / fps if fps > 0 else 0
            self.root.after(0, self._update_ui_progress, current, total, percent, fps, eta, detected_count)

        try:
            success = self.processor.process_video(in_path, out_path, progress_callback=progress_cb)
            elapsed = time.time() - start_time
            self.root.after(0, self._process_finished, success, out_path, elapsed)
        except Exception as e:
            self.root.after(0, self._process_failed, str(e))

    def _update_ui_progress(self, current, total, percent, fps, eta, detected_count):
        self.progress_bar["value"] = percent
        self.status_lbl.configure(
            text=f"Frame {current}/{total} ({percent:.1f}%) | {fps:.1f} FPS | ETA: {eta:.0f}s | Detections: {detected_count}"
        )

    def _process_finished(self, success, out_path, elapsed):
        self.is_processing = False
        self.btn_start.configure(state="normal")
        self.btn_cancel.configure(state="disabled")

        if success:
            self.progress_bar["value"] = 100
            self.status_lbl.configure(text=f"✓ Complete in {elapsed:.1f}s! Saved to: {os.path.basename(out_path)}", fg="#4cd137")
            self.btn_open_folder.configure(state="normal")
            messagebox.showinfo("Success", f"Video has been redacted successfully!\n\nSaved to:\n{out_path}")
        else:
            self.status_lbl.configure(text="Processing was cancelled.", fg="#e74c3c")

    def _process_failed(self, error_msg):
        self.is_processing = False
        self.btn_start.configure(state="normal")
        self.btn_cancel.configure(state="disabled")
        self.status_lbl.configure(text=f"Error: {error_msg}", fg="#e74c3c")
        messagebox.showerror("Error during processing", error_msg)

    def cancel_processing(self):
        if self.processor and self.is_processing:
            self.processor.cancel()
            self.status_lbl.configure(text="Cancelling... cleaning up temporary files.", fg="#f39c12")

def main():
    root = tk.Tk()
    app = AutoIPBlurApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
