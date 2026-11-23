import threading
import time

import cv2 as cv
from flask import Flask, Response, jsonify

_PAGE = """<!doctype html>
<html><body style="background:#111;color:#0f0;font-family:monospace">
<img src="/video" style="max-width:100%">
<pre id="s"></pre>  
<script>
setInterval(async () => {
  const r = await fetch('/status');
  document.getElementById('s').textContent = JSON.stringify(await r.json(), null, 1);
}, 500);
</script>
</body></html>"""


class MjpegStreamer:
    def __init__(self, host="0.0.0.0", port=8080, stream_fps=10,
                 jpeg_quality=70, max_width=640):
        self.host = host
        self.port = port
        self.stream_fps = stream_fps
        self.jpeg_quality = jpeg_quality
        self.max_width = max_width

        self._lock = threading.Lock()
        self._jpeg = None
        self._jpeg_id = 0
        self._status = {}
        self._last_pub = 0.0

        self._app = Flask(__name__)
        self._app.add_url_rule("/", "index", lambda: _PAGE)
        self._app.add_url_rule("/video", "video", self._video)
        self._app.add_url_rule("/status", "status", self._status_route)

    def publish(self, frame, status=None):
        now = time.perf_counter()
        if now - self._last_pub < 1.0 / self.stream_fps:
            return
        self._last_pub = now

        h, w = frame.shape[:2]
        if w > self.max_width:
            frame = cv.resize(frame, (self.max_width, int(h * self.max_width / w)))

        ok, buf = cv.imencode(".jpg", frame,
                              [cv.IMWRITE_JPEG_QUALITY, self.jpeg_quality])
        if not ok:
            return
        with self._lock:
            self._jpeg = buf.tobytes()
            self._jpeg_id += 1
            if status is not None:
                self._status = status

    def _video(self):
        return Response(self._frames(),
                        mimetype="multipart/x-mixed-replace; boundary=frame")

    def _frames(self):
        last_id = -1
        while True:
            with self._lock:
                jpeg, jid = self._jpeg, self._jpeg_id
            if jpeg is not None and jid != last_id:
                last_id = jid
                yield (b"--frame\r\nContent-Type: image/jpeg\r\n\r\n"
                       + jpeg + b"\r\n")
            time.sleep(0.01)

    def _status_route(self):
        with self._lock:
            return jsonify(self._status)

    def start(self):
        threading.Thread(
            target=lambda: self._app.run(host=self.host, port=self.port,
                                         threaded=True),
            daemon=True,
        ).start()