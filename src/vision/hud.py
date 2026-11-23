import cv2 as cv

BLUE = (255, 0, 0)
GREEN = (0, 255, 0)
RED = (0, 0, 255)
WHITE = (255, 255, 255)
FONT = cv.FONT_HERSHEY_SIMPLEX


def draw_hud(frame, detection, fps):
    """ Draws HUD in the actual frame object.
        Always pass a copy to the function to not loose original frame """
    h, w = frame.shape[:2]
    cx, cy = w // 2, h // 2

    # Aim in the center
    cv.line(frame, (cx - 15, cy), (cx + 15, cy), WHITE, 1)
    cv.line(frame, (cx, cy - 15), (cx, cy + 15), WHITE, 1)

    # Resolution and FPS 
    cv.putText(frame, f"{w}x{h}  {fps:.1f} FPS", (10, 25), FONT, 1, GREEN, 2)

    # If no target is identified, then exits and do not try to draw circle and line
    if detection is None:
        cv.putText(frame, "SEM ALVO", (10, 55), FONT, 1, RED, 2)
        return

    cv.putText(frame, "ALVO IDENTIFICADO", (10, 55), FONT, 1, GREEN, 2)
    
    # cv.circle e cv.putText need integers. We convert float data here
    x, y = int(detection.center[0]), int(detection.center[1])
    r = int(detection.radius)

    cv.circle(frame, (x, y), r, GREEN, 2)          # balloon contour
    cv.circle(frame, (x, y), 5, BLUE, -1)          # center
    cv.line(frame, (cx, cy), (x, y), BLUE, 1)      # error line
    cv.putText(frame, f"x={x} y={y} r={r}",
               (x - 40, max(y - r - 10, 15)), FONT, 0.5, GREEN, 2)