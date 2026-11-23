import os
import shutil
import subprocess
import threading
import time

import cv2 as cv


class Camera:
    """Base: keeps the latest frame avaiable on a updated mailbox
    via thread. Its subclasses determine how to obtain the frame."""

    def __init__(self, max_failures=3):
        self._max_failures = max_failures
        self._join_timeout = 2
        self._lock = threading.Lock()
        self._frame = None
        self._frame_id = 0
        self._stamp = 0.0
        self._running = False
        self._thread = None

    # ---- to be filled in the subclasses ----
    def _open(self):
        pass

    def _grab(self):
        """Devolve (ok, frame)."""
        raise NotImplementedError

    def _close(self):
        pass

    # ---- public interface (identical to all modes) ----
    def start(self):
        if self._thread is not None and self._thread.is_alive():
            return
        self._open()                      # may raise RuntimeError
        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _run(self):
        failures = 0
        while self._running:
            ok, frame = self._grab()
            if not ok:
                failures += 1
                if failures >= self._max_failures:
                    print(f"Camera: {failures} falhas seguidas, encerrando captura")
                    self._running = False
                    break
                time.sleep(0.2)
                continue
            failures = 0
            with self._lock:
                self._frame = frame
                self._frame_id += 1
                self._stamp = time.time()

    def read(self):
        with self._lock:
            return self._frame, self._frame_id, self._stamp

    def is_running(self):
        return self._running

    def stop(self):
        self._running = False
        if self._thread is not None:
            self._thread.join(timeout=self._join_timeout)
        self._close()


class OpenCvCamera(Camera):
    """Webcam, vídeo gravado ou URL, via cv.VideoCapture."""

    def __init__(self, source=0, loop=False, pace=False, **kwargs):
        super().__init__(**kwargs)
        self._source = source
        self._loop = loop
        self._pace = pace
        self._cap = None
        self._period = 1.0 / 30
        self._next_t = 0.0

    def _open(self):
        cap = cv.VideoCapture(self._source)
        if not cap.isOpened():
            raise RuntimeError(f"Não abri a fonte: {self._source!r}")
        self._cap = cap
        fps = cap.get(cv.CAP_PROP_FPS)
        self._period = 1.0 / fps if fps and fps > 0 else 1.0 / 30
        self._next_t = time.perf_counter()

    def _grab(self):
        ok, frame = self._cap.read()
        if not ok and self._loop:
            self._cap.set(cv.CAP_PROP_POS_FRAMES, 0)
            ok, frame = self._cap.read()
        if not ok:
            return False, None

        if self._pace:
            self._next_t += self._period
            delay = self._next_t - time.perf_counter()
            if delay > 0:
                time.sleep(delay)
            else:
                self._next_t = time.perf_counter()
        return True, frame

    def _close(self):
        if self._cap is not None:
            self._cap.release()
            self._cap = None


class RpicamCamera(Camera):
    """Câmera do Pi, uma foto por vez via 'rpicam-still'."""

    def __init__(self, width=1280, height=720, path="/dev/shm/photo.jpg",
                 capture_timeout=15, **kwargs):
        super().__init__(**kwargs)
        self._width = width
        self._height = height
        self._path = path
        self._timeout = capture_timeout
        self._join_timeout = capture_timeout + 2

    def _open(self):
        if shutil.which("rpicam-still") is None:
            raise RuntimeError("rpicam-still não encontrado (isto está rodando no Pi?)")

    def _grab(self):
        if os.path.exists(self._path):
            os.remove(self._path)

        cmd = ["rpicam-still", "--immediate", "--nopreview",
               "--width", str(self._width), "--height", str(self._height),
               "-o", self._path]
        try:
            result = subprocess.run(cmd, capture_output=True, timeout=self._timeout)
        except subprocess.TimeoutExpired:
            print(f"Camera: rpicam-still passou de {self._timeout}s")
            return False, None

        if result.returncode != 0:
            print("Camera: rpicam-still falhou:",
                  result.stderr.decode(errors="replace"))
            return False, None

        frame = cv.imread(self._path)
        if frame is None:
            print(f"Camera: não consegui ler {self._path}")
            return False, None
        return True, frame


def create_camera(mode, **kwargs):
    if mode == "opencv":
        return OpenCvCamera(**kwargs)
    if mode == "rpicam":
        return RpicamCamera(**kwargs)
    raise ValueError(f"Modo de câmera desconhecido: {mode!r}")