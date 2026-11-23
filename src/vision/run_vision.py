import time
from pathlib import Path

from camera import  create_camera
from balloon_detector import BalloonDetector
from hud import draw_hud
from streaming import MjpegStreamer

VIDEO_PATH = Path(__file__).resolve().parent / "teste.mp4"

# No computador, com vídeo
CAMERA_MODE = "opencv"
CAMERA_ARGS = {"source": str(VIDEO_PATH), "loop": True, "pace": True}

# No drone:
# CAMERA_MODE = "rpicam"
# CAMERA_ARGS = {"width": 1280, "height": 720}

HOST = "0.0.0.0"      # no WSL, garante que o Windows consiga acessar
PORT = 8080


def build_status(detection, fps, capture_stamp, total_dropped):
    status = {
        "fps": round(fps, 1),
        "latency_ms": round((time.time() - capture_stamp) * 1000),
        "dropped_frames": total_dropped,
        "detected": detection is not None,
    }
    if detection is not None:
        status["center"] = [round(detection.center[0], 1),
                            round(detection.center[1], 1)]
        status["radius"] = round(detection.radius, 1)
    return status


def main():
    if not VIDEO_PATH.exists():
        raise SystemExit(f"Vídeo não encontrado: {VIDEO_PATH}")

    cam = create_camera(CAMERA_MODE, **CAMERA_ARGS)
    detector = BalloonDetector()
    streamer = MjpegStreamer(host=HOST, port=PORT)

    cam.start()
    streamer.start()
    print(f"Fonte: {VIDEO_PATH}")
    print(f"HUD em http://localhost:{PORT}  (Ctrl+C para sair)")

    last_id = 0
    total_dropped = 0
    fps = 0.0
    last_t = time.perf_counter()

    try:
        while cam.is_running():
            frame, fid, stamp = cam.read()
            if frame is None or fid == last_id:
                time.sleep(0.002)
                continue

            if last_id != 0:
                total_dropped += fid - last_id - 1
            last_id = fid

            now = time.perf_counter()
            inst = 1.0 / (now - last_t)
            last_t = now
            fps = inst if fps == 0 else 0.9 * fps + 0.1 * inst

            detection = detector.detect(frame)

            view = frame.copy()
            draw_hud(view, detection, fps)

            streamer.publish(view, build_status(detection, fps, stamp, total_dropped))
    except KeyboardInterrupt:
        pass
    finally:
        cam.stop()


if __name__ == "__main__":
    main()