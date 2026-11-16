import threading
import time
import cv2 as cv


class Camera:
    def __init__(self, source, loop=False, pace=False):
        self._cap = cv.VideoCapture(source)
        if not self._cap.isOpened():
            raise RuntimeError(f"Não abri a fonte: {source!r}")
        self._loop = loop
        self._pace = pace
        fps = self._cap.get(cv.CAP_PROP_FPS)
        self._period = 1.0 / fps if fps and fps > 0 else 1.0 / 30
        self._lock = threading.Lock()
        self._frame = None
        self._frame_id = 0
        self._stamp = 0.0
        self._running = False

    def start(self):
        self._running = True
        threading.Thread(target=self._run, daemon=True).start()

    def _run(self):
        next_t = time.perf_counter()
        just_rewound = False
        while self._running:
            res, frame = self._cap.read()
            if not res:
                if self._loop and not just_rewound:
                    self._cap.set(cv.CAP_PROP_POS_FRAMES, 0)
                    just_rewound = True
                    continue
                self._running = False
                break
            just_rewound = False
            if self._pace:
                next_t += self._period
                delay = next_t - time.perf_counter()
                if delay > 0:
                    time.sleep(delay)
                else:
                    next_t = time.perf_counter()
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
        self._cap.release()