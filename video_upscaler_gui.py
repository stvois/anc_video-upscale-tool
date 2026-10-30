# -*- coding: utf-8 -*-
from __future__ import annotations

import os
import queue
import subprocess
import threading
from pathlib import Path
from tkinter import (
    BOTH,
    END,
    LEFT,
    RIGHT,
    X,
    BooleanVar,
    Button,
    Checkbutton,
    DoubleVar,
    Entry,
    Frame,
    Label,
    LabelFrame,
    OptionMenu,
    StringVar,
    Tk,
    ttk,
)
from tkinter import filedialog, messagebox, scrolledtext

from video_upscaler_core import (
    APP_DIR,
    PipelineCancelled,
    PipelineError,
    RESOURCE_DIR,
    UpscaleSettings,
    VideoUpscalePipeline,
    engine_status,
    format_duration,
    probe_video,
)


SCALES = {"2배": 2, "4배": 4}
CONTENT_MODES = {"실사 / 범용": "real", "애니메이션 / 일러스트": "anime"}
DENOISE_MODES = {"사용 안 함": "none", "약하게": "low", "보통": "medium", "강하게": "high"}
BACKENDS = {"AI (Real-ESRGAN)": "ai", "일반 고품질 (Lanczos)": "lanczos"}
OUTPUT_FORMATS = {
    "MP4 H.264 (호환성 우선)": ("h264", ".mp4"),
    "MP4 H.265 (용량 절약)": ("h265", ".mp4"),
    "MKV H.265 (모든 트랙 보존)": ("h265", ".mkv"),
}
QUALITY_MODES = {"고화질 / 큰 용량": "high", "균형": "balanced", "작은 용량": "small"}


class VideoUpscalerApp:
    def __init__(self, root: Tk) -> None:
        self.root = root
        self.root.title("AI 영상 업스케일러")
        self.root.geometry("940x760")
        self.root.minsize(820, 690)

        self.input_path = StringVar()
        self.output_path = StringVar()
        self.scale = StringVar(value="2배")
        self.content_mode = StringVar(value="실사 / 범용")
        self.denoise = StringVar(value="약하게")
        self.backend = StringVar(value="AI (Real-ESRGAN)")
        self.output_format = StringVar(value="MP4 H.265 (용량 절약)")
        self.quality = StringVar(value="균형")
        self.interpolation = BooleanVar(value=False)
        self.hardware_encode = BooleanVar(value=True)
        self.keep_cache = BooleanVar(value=True)
        self.status_text = StringVar(value="준비")
        self.progress_value = DoubleVar(value=0.0)
        self.engine_text = StringVar()
        self.video_info_text = StringVar(value="영상을 선택하면 해상도와 예상 출력 정보를 표시합니다.")

        self.events: queue.Queue[tuple[str, object]] = queue.Queue()
        self.worker: threading.Thread | None = None
        self.pipeline: VideoUpscalePipeline | None = None
        self.cancel_event = threading.Event()
        self.install_process: subprocess.Popen[str] | None = None

        self._build_ui()
        self.scale.trace_add("write", self._refresh_output_hint)
        self.output_format.trace_add("write", self._on_output_format_change)
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self.root.after(100, self._drain_events)
        self._refresh_engine_status()

    def _build_ui(self) -> None:
        outer = Frame(self.root, padx=14, pady=12)
        outer.pack(fill=BOTH, expand=True)

        title_row = Frame(outer)
        title_row.pack(fill=X)
        Label(title_row, text="AI 영상 업스케일러", font=("Malgun Gothic", 17, "bold")).pack(side=LEFT)
        Button(title_row, text="AI 엔진 설치", command=self._install_engines, width=14).pack(side=RIGHT)
        Label(outer, textvariable=self.engine_text, anchor="w", fg="#555555").pack(fill=X, pady=(2, 10))

        files = LabelFrame(outer, text="파일", padx=10, pady=8)
        files.pack(fill=X)
        self._file_row(files, "입력 영상", self.input_path, self._choose_input)
        self._file_row(files, "출력 영상", self.output_path, self._choose_output)
        Label(files, textvariable=self.video_info_text, anchor="w", justify=LEFT, fg="#2f5d80").pack(fill=X, pady=(3, 0))

        options = LabelFrame(outer, text="화질 설정", padx=10, pady=8)
        options.pack(fill=X, pady=(10, 0))
        row1 = Frame(options)
        row1.pack(fill=X, pady=3)
        self._option(row1, "확대", self.scale, list(SCALES))
        self._option(row1, "영상 종류", self.content_mode, list(CONTENT_MODES))
        self._option(row1, "노이즈 제거", self.denoise, list(DENOISE_MODES))
        row2 = Frame(options)
        row2.pack(fill=X, pady=3)
        self._option(row2, "처리 방식", self.backend, list(BACKENDS))
        self._option(row2, "출력 형식", self.output_format, list(OUTPUT_FORMATS), menu_width=25)
        self._option(row2, "압축 품질", self.quality, list(QUALITY_MODES))

        checks = Frame(options)
        checks.pack(fill=X, pady=(6, 2))
        Checkbutton(checks, text="RIFE 프레임 보간 (FPS 2배)", variable=self.interpolation).pack(side=LEFT, padx=(0, 18))
        Checkbutton(checks, text="NVIDIA 하드웨어 인코딩", variable=self.hardware_encode).pack(side=LEFT, padx=(0, 18))
        Checkbutton(checks, text="이어하기 캐시 보존", variable=self.keep_cache).pack(side=LEFT)

        progress_box = LabelFrame(outer, text="진행 상태", padx=10, pady=8)
        progress_box.pack(fill=X, pady=(10, 0))
        Label(progress_box, textvariable=self.status_text, anchor="w").pack(fill=X)
        ttk.Progressbar(progress_box, variable=self.progress_value, maximum=100).pack(fill=X, pady=(6, 2))

        action_row = Frame(outer)
        action_row.pack(fill=X, pady=(10, 8))
        self.open_output_button = Button(action_row, text="출력 폴더 열기", command=self._open_output_folder, width=15)
        self.open_output_button.pack(side=LEFT)
        self.stop_button = Button(action_row, text="중지", command=self._stop, width=12, state="disabled")
        self.stop_button.pack(side=RIGHT, padx=(8, 0))
        self.run_button = Button(action_row, text="업스케일 시작", command=self._start, width=17, height=2)
        self.run_button.pack(side=RIGHT)

        self.log = scrolledtext.ScrolledText(outer, height=13, wrap="word", font=("Consolas", 9))
        self.log.pack(fill=BOTH, expand=True)
        self._append_log("입력 영상을 선택한 뒤 설정을 확인하고 '업스케일 시작'을 누르세요.\n")
        self._append_log("MKV 출력은 원본 오디오·자막 트랙을 가장 안전하게 보존합니다.\n")

    def _file_row(self, parent: Frame, text: str, variable: StringVar, command) -> None:
        row = Frame(parent)
        row.pack(fill=X, pady=3)
        Label(row, text=text, width=11, anchor="w").pack(side=LEFT)
        Entry(row, textvariable=variable).pack(side=LEFT, fill=X, expand=True)
        Button(row, text="찾아보기", command=command, width=10).pack(side=RIGHT, padx=(8, 0))

    def _option(self, parent: Frame, label: str, variable: StringVar, values: list[str], menu_width: int = 19) -> None:
        block = Frame(parent)
        block.pack(side=LEFT, fill=X, expand=True, padx=(0, 8))
        Label(block, text=label, width=10, anchor="w").pack(side=LEFT)
        menu = OptionMenu(block, variable, *values)
        menu.config(width=menu_width, anchor="w")
        menu.pack(side=LEFT, fill=X, expand=True)

    def _append_log(self, text: str) -> None:
        self.log.insert(END, text.rstrip() + "\n")
        self.log.see(END)

    def _refresh_engine_status(self) -> None:
        status = engine_status()
        ffmpeg = "준비" if status["ffmpeg"] else "없음"
        ai = "준비" if status["realesrgan"] else "미설치"
        rife = "준비" if status["rife"] else "미설치"
        gpu = status["gpu"] or "NVIDIA GPU 미감지"
        nvenc = "준비" if status["nvenc"] == "ready" else "드라이버 업데이트 필요 / CPU 대체"
        self.engine_text.set(
            f"FFmpeg: {ffmpeg}  |  Real-ESRGAN: {ai}  |  RIFE: {rife}  |  GPU: {gpu}  |  NVENC: {nvenc}"
        )

    def _choose_input(self) -> None:
        path = filedialog.askopenfilename(
            title="업스케일할 영상 선택",
            filetypes=[("영상 파일", "*.mp4 *.mov *.mkv *.avi *.webm *.m4v *.ts *.mts"), ("모든 파일", "*.*")],
        )
        if not path:
            return
        self.input_path.set(path)
        self._set_default_output()
        self.video_info_text.set("영상 정보를 분석하는 중...")

        def probe_worker() -> None:
            try:
                info = probe_video(path)
                self.events.put(("probe", info))
            except Exception as exc:  # UI boundary
                self.events.put(("probe_error", str(exc)))

        threading.Thread(target=probe_worker, daemon=True).start()

    def _output_suffix(self) -> str:
        return OUTPUT_FORMATS[self.output_format.get()][1]

    def _set_default_output(self) -> None:
        if not self.input_path.get():
            return
        source = Path(self.input_path.get())
        self.output_path.set(str(source.with_name(f"{source.stem}_upscaled_{SCALES[self.scale.get()]}x{self._output_suffix()}")))

    def _refresh_output_hint(self, *_args) -> None:
        if self.input_path.get() and (not self.output_path.get() or "_upscaled_" in Path(self.output_path.get()).stem):
            self._set_default_output()

    def _on_output_format_change(self, *_args) -> None:
        self._refresh_output_hint()

    def _choose_output(self) -> None:
        initial = self.output_path.get()
        suffix = self._output_suffix()
        path = filedialog.asksaveasfilename(
            title="출력 영상 저장",
            defaultextension=suffix,
            initialdir=str(Path(initial).parent) if initial else "",
            initialfile=Path(initial).name if initial else f"upscaled{suffix}",
            filetypes=[("MKV 영상", "*.mkv")] if suffix == ".mkv" else [("MP4 영상", "*.mp4")],
        )
        if path:
            self.output_path.set(path)

    def _settings(self) -> UpscaleSettings:
        codec, _suffix = OUTPUT_FORMATS[self.output_format.get()]
        return UpscaleSettings(
            input_path=self.input_path.get().strip(),
            output_path=self.output_path.get().strip(),
            scale=SCALES[self.scale.get()],
            content_mode=CONTENT_MODES[self.content_mode.get()],
            denoise=DENOISE_MODES[self.denoise.get()],
            backend=BACKENDS[self.backend.get()],
            interpolation=self.interpolation.get(),
            codec=codec,
            quality=QUALITY_MODES[self.quality.get()],
            hardware_encode=self.hardware_encode.get(),
            keep_cache=self.keep_cache.get(),
        )

    def _start(self) -> None:
        if self.worker and self.worker.is_alive():
            return
        if not self.input_path.get() or not Path(self.input_path.get()).is_file():
            messagebox.showerror("입력 영상 없음", "올바른 입력 영상을 선택해 주세요.")
            return
        if not self.output_path.get():
            messagebox.showerror("출력 경로 없음", "출력 영상 경로를 선택해 주세요.")
            return
        self.cancel_event.clear()
        self.progress_value.set(0)
        self.run_button.config(state="disabled")
        self.stop_button.config(state="normal")
        self.status_text.set("작업 준비 중")
        settings = self._settings()

        def emit_log(message: str) -> None:
            self.events.put(("log", message))

        def emit_progress(value: float, message: str) -> None:
            self.events.put(("progress", (value, message)))

        def worker() -> None:
            try:
                self.pipeline = VideoUpscalePipeline(settings, emit_log, emit_progress, self.cancel_event)
                result = self.pipeline.run()
                self.events.put(("complete", str(result)))
            except PipelineCancelled as exc:
                self.events.put(("cancelled", str(exc)))
            except (PipelineError, OSError, ValueError) as exc:
                self.events.put(("error", str(exc)))
            except Exception as exc:  # UI boundary
                self.events.put(("error", f"예상하지 못한 오류: {exc}"))
            finally:
                self.pipeline = None

        self.worker = threading.Thread(target=worker, daemon=True)
        self.worker.start()

    def _stop(self) -> None:
        if not (self.worker and self.worker.is_alive()):
            return
        self.status_text.set("안전하게 중지하는 중...")
        self.cancel_event.set()
        if self.pipeline:
            self.pipeline.cancel()

    def _set_idle(self) -> None:
        self.run_button.config(state="normal")
        self.stop_button.config(state="disabled")

    def _install_engines(self) -> None:
        if self.install_process and self.install_process.poll() is None:
            messagebox.showinfo("설치 진행 중", "AI 엔진을 설치하고 있습니다.")
            return
        script = RESOURCE_DIR / "setup_video_ai_engines.ps1"
        if not script.exists():
            messagebox.showerror("설치 파일 없음", str(script))
            return
        if not messagebox.askyesno(
            "AI 엔진 설치",
            "공식 GitHub 릴리스에서 Real-ESRGAN과 RIFE를 내려받습니다.\n약 수백 MB의 저장 공간이 필요할 수 있습니다. 계속할까요?",
        ):
            return
        self._append_log("AI 엔진 설치를 시작합니다...")
        self.status_text.set("AI 엔진 다운로드 및 설치 중")

        def install_worker() -> None:
            try:
                self.install_process = subprocess.Popen(
                    ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(script)],
                    cwd=str(APP_DIR),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    creationflags=subprocess.CREATE_NO_WINDOW,
                )
                assert self.install_process.stdout is not None
                for line in self.install_process.stdout:
                    if line.strip():
                        self.events.put(("log", line.strip()))
                code = self.install_process.wait()
                self.events.put(("install_complete", code))
            except Exception as exc:
                self.events.put(("error", f"엔진 설치 실패: {exc}"))

        threading.Thread(target=install_worker, daemon=True).start()

    def _open_output_folder(self) -> None:
        target = Path(self.output_path.get()).parent if self.output_path.get() else APP_DIR
        target.mkdir(parents=True, exist_ok=True)
        os.startfile(str(target))

    def _drain_events(self) -> None:
        while True:
            try:
                event, payload = self.events.get_nowait()
            except queue.Empty:
                break
            if event == "log":
                self._append_log(str(payload))
            elif event == "progress":
                value, message = payload  # type: ignore[misc]
                self.progress_value.set(float(value) * 100)
                self.status_text.set(f"{message} ({float(value) * 100:.1f}%)")
            elif event == "probe":
                info = payload
                scale = SCALES[self.scale.get()]
                self.video_info_text.set(
                    f"{info.width}x{info.height} → {info.width * scale}x{info.height * scale}  |  "
                    f"{info.fps:.3f}fps  |  {format_duration(info.duration)}  |  약 {info.frame_count:,}프레임"
                )
            elif event == "probe_error":
                self.video_info_text.set(f"영상 분석 실패: {payload}")
            elif event == "complete":
                self.progress_value.set(100)
                self.status_text.set("완료")
                self._append_log(f"최종 파일: {payload}")
                self._set_idle()
                messagebox.showinfo("업스케일 완료", f"영상 처리가 완료되었습니다.\n\n{payload}")
            elif event == "cancelled":
                self.status_text.set("중지됨 — 다음 실행에서 이어할 수 있습니다")
                self._append_log(str(payload))
                self._set_idle()
            elif event == "error":
                self.status_text.set("오류")
                self._append_log(str(payload))
                self._set_idle()
                messagebox.showerror("작업 오류", str(payload))
            elif event == "install_complete":
                self._refresh_engine_status()
                if int(payload) == 0:
                    self.status_text.set("AI 엔진 설치 완료")
                    self._append_log("AI 엔진 설치가 완료되었습니다.")
                    messagebox.showinfo("설치 완료", "Real-ESRGAN과 RIFE 설치가 완료되었습니다.")
                else:
                    self.status_text.set("AI 엔진 설치 실패")
                    messagebox.showerror("설치 실패", "로그를 확인해 주세요.")
        self.root.after(100, self._drain_events)

    def _on_close(self) -> None:
        if self.worker and self.worker.is_alive():
            if not messagebox.askyesno("작업 중", "현재 작업을 중지하고 종료할까요? 완료 프레임은 캐시에 남습니다."):
                return
            self._stop()
        self.root.destroy()


def main() -> None:
    root = Tk()
    try:
        ttk.Style().theme_use("vista")
    except Exception:
        pass
    VideoUpscalerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
