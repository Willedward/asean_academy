"""Reversible image preparation. Evidence always comes from the original PDF."""

from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np


@dataclass
class PreparedImage:
    path: Path
    width: int
    height: int
    inverse: np.ndarray
    steps: dict

    def original_box(self, box) -> tuple[float, float, float, float]:
        x0, y0, x1, y1 = box
        corners = np.array([[x0, y0, 1], [x1, y0, 1], [x0, y1, 1], [x1, y1, 1]])
        mapped = corners @ self.inverse.T
        low, high = mapped.min(axis=0), mapped.max(axis=0)
        return (
            float(np.clip(low[0], 0, self.width)),
            float(np.clip(low[1], 0, self.height)),
            float(np.clip(high[0], 0, self.width)),
            float(np.clip(high[1], 0, self.height)),
        )


def prepare_image(source: Path, destination: Path, *, enabled: bool = True) -> PreparedImage:
    gray = cv2.imread(str(source), cv2.IMREAD_GRAYSCALE)
    if gray is None:
        raise ValueError("Cannot read rendered image")
    height, width = gray.shape
    identity = np.array([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]])
    if not enabled:
        return PreparedImage(source, width, height, identity, {"enabled": False})

    # Work on a copy. Only near-solid dark edge strips are removed; internal
    # rules/fraction bars/diagrams and ordinary page-edge text are preserved.
    clean = gray.copy()
    borders = []
    for axis, size in [(0, height), (1, width)]:
        profile = np.mean(clean < 70, axis=1 - axis)
        for reverse in [False, True]:
            indices = (
                range(size - 1, size - 1 - max(1, size // 100), -1)
                if reverse
                else range(max(1, size // 100))
            )
            for index in indices:
                if profile[index] < 0.75:
                    break
                if axis == 0:
                    clean[index, :] = 255
                else:
                    clean[:, index] = 255
                borders.append((axis, index))

    # Normalize uneven backgrounds without eroding small punctuation/exponents.
    background = cv2.GaussianBlur(clean, (0, 0), 15)
    clean = cv2.divide(clean, np.maximum(background, 1), scale=255)
    clean = cv2.bilateralFilter(clean, 5, 18, 18)
    edges = cv2.Canny(clean, 80, 180)
    segments = cv2.HoughLinesP(
        edges,
        1,
        np.pi / 1800,
        threshold=80,
        minLineLength=max(50, width // 12),
        maxLineGap=12,
    )
    angles = []
    if segments is not None:
        for x0, y0, x1, y1 in segments[:, 0]:
            angle = np.degrees(np.arctan2(y1 - y0, x1 - x0))
            if abs(angle) <= 5:
                angles.append(angle)
    angle = float(np.median(angles)) if len(angles) >= 5 else 0.0
    # Require agreement; a sloping graph or triangle isn't evidence of page skew.
    if angles and np.median(np.abs(np.array(angles) - angle)) > 0.6:
        angle = 0.0
    if abs(angle) < 0.15:
        angle = 0.0
    transform = cv2.getRotationMatrix2D((width / 2, height / 2), angle, 1.0)
    clean = cv2.warpAffine(clean, transform, (width, height), borderValue=255)
    destination.parent.mkdir(parents=True, exist_ok=True)
    if not cv2.imwrite(str(destination), clean):
        raise OSError("Cannot write prepared image")
    return PreparedImage(
        destination,
        width,
        height,
        cv2.invertAffineTransform(transform),
        {
            "enabled": True,
            "deskew_degrees": angle,
            "removed_border_lines": len(borders),
            "contrast": "background_normalization",
            "denoise": "bilateral",
        },
    )
