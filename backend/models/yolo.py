"""Compatibility layer for legacy YOLOv7 checkpoints.

The SCB weights stored in this repository were serialized from a YOLOv7
environment. This module provides the symbols referenced by the checkpoint so
`torch.load()` can reconstruct the model.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Dict, Iterable, List, Optional, Tuple

import numpy as np
import torch
from PIL import Image
from torch import nn
from torchvision.ops import nms

from .common import Concat, Conv, MP, RepConv, SPPCSPC


class Detect(nn.Module):
    """Minimal YOLOv7-style detect head compatible with serialized checkpoints."""

    def __init__(self, nc: int = 80, anchors: Any = (), ch: Tuple[int, ...] = (), inplace: bool = True):
        super().__init__()
        self.nc = nc
        self.no = nc + 5
        self.nl = len(anchors) if hasattr(anchors, "__len__") else 3
        self.na = len(anchors[0]) // 2 if anchors and hasattr(anchors[0], "__len__") else 3
        self.grid = [torch.empty(0) for _ in range(self.nl)]
        self.anchor_grid = [torch.empty(0) for _ in range(self.nl)]
        self.register_buffer("anchors", torch.tensor(anchors).float().view(self.nl, -1, 2) if anchors else torch.zeros(self.nl, self.na, 2))
        self.m = nn.ModuleList([nn.Conv2d(c, self.no * self.na, 1) for c in (ch or [1] * self.nl)])
        self.inplace = inplace
        self.stride = torch.ones(self.nl)

    def _make_grid(self, nx: int, ny: int, i: int):
        yv, xv = torch.meshgrid(torch.arange(ny), torch.arange(nx), indexing="ij")
        self.grid[i] = torch.stack((xv, yv), 2).view(1, 1, ny, nx, 2).float()
        self.anchor_grid[i] = self.anchors[i].clone().view(1, -1, 1, 1, 2)

    def forward(self, x):
        inplace = getattr(self, "inplace", True)
        if not hasattr(self, "grid") or len(self.grid) != self.nl:
            self.grid = [torch.empty(0) for _ in range(self.nl)]
        if not hasattr(self, "anchor_grid") or len(self.anchor_grid) != self.nl:
            self.anchor_grid = [torch.empty(0) for _ in range(self.nl)]

        outputs = []
        for i in range(self.nl):
            xi = self.m[i](x[i])
            bs, _, ny, nx = xi.shape
            xi = xi.view(bs, self.na, self.no, ny, nx).permute(0, 1, 3, 4, 2).contiguous()
            if not self.training:
                if self.grid[i].shape[2:4] != xi.shape[2:4]:
                    self._make_grid(nx, ny, i)
                y = xi.sigmoid()
                if inplace:
                    y[..., 0:2] = (y[..., 0:2] * 2.0 - 0.5 + self.grid[i]) * self.stride[i]
                    y[..., 2:4] = (y[..., 2:4] * 2.0) ** 2 * self.anchor_grid[i]
                outputs.append(y.view(bs, -1, self.no))
            else:
                outputs.append(xi)
        return torch.cat(outputs, 1) if not self.training else outputs


class Model(nn.Module):
    """Minimal YOLOv7 Model wrapper.

    The actual architecture is restored from the serialized checkpoint state.
    This class only needs to exist so pickle can import `models.yolo.Model`.
    """

    def __init__(self, *args, **kwargs):
        super().__init__()

    def forward(self, x, *args, **kwargs):
        if not hasattr(self, "model"):
            return x

        # YOLOv7 checkpoints store a graph of layers with `.f` routing metadata.
        # When that metadata exists, walk the graph explicitly so skip connections
        # and concatenations behave the same way as in the original repository.
        if isinstance(self.model, nn.Sequential):
            outputs = []
            layers = list(self.model)
            for index, module in enumerate(layers):
                from_index = getattr(module, "f", -1)
                if isinstance(from_index, int):
                    layer_input = x if from_index == -1 else outputs[from_index]
                else:
                    layer_input = [x if j == -1 else outputs[j] for j in from_index]

                x = module(layer_input)
                outputs.append(x)
            return x

        return self.model(x)


@dataclass
class LegacyBox:
    conf: torch.Tensor
    cls: torch.Tensor
    xyxy: torch.Tensor


class LegacyResult:
    def __init__(self, boxes: List[LegacyBox]):
        self.boxes = boxes


def _letterbox(image: np.ndarray, new_shape: int = 640, color=(114, 114, 114)) -> Tuple[np.ndarray, float, Tuple[float, float]]:
    shape = image.shape[:2]  # h, w
    ratio = min(new_shape / shape[0], new_shape / shape[1])
    new_unpad = (int(round(shape[1] * ratio)), int(round(shape[0] * ratio)))

    dw = new_shape - new_unpad[0]
    dh = new_shape - new_unpad[1]
    dw /= 2
    dh /= 2

    if shape[::-1] != new_unpad:
        image = np.array(Image.fromarray(image).resize(new_unpad, Image.BILINEAR))

    top, bottom = int(round(dh - 0.1)), int(round(dh + 0.1))
    left, right = int(round(dw - 0.1)), int(round(dw + 0.1))
    image = np.pad(image, ((top, bottom), (left, right), (0, 0)), mode="constant", constant_values=color[0])
    return image, ratio, (dw, dh)


def _xywh_to_xyxy(boxes: torch.Tensor) -> torch.Tensor:
    xyxy = boxes.clone()
    xyxy[:, 0] = boxes[:, 0] - boxes[:, 2] / 2
    xyxy[:, 1] = boxes[:, 1] - boxes[:, 3] / 2
    xyxy[:, 2] = boxes[:, 0] + boxes[:, 2] / 2
    xyxy[:, 3] = boxes[:, 1] + boxes[:, 3] / 2
    return xyxy


def _scale_boxes(boxes: torch.Tensor, ratio: float, pad: Tuple[float, float], orig_shape: Tuple[int, int]) -> torch.Tensor:
    boxes = boxes.clone()
    boxes[:, [0, 2]] -= pad[0]
    boxes[:, [1, 3]] -= pad[1]
    boxes[:, :4] /= ratio
    boxes[:, 0].clamp_(0, orig_shape[1])
    boxes[:, 1].clamp_(0, orig_shape[0])
    boxes[:, 2].clamp_(0, orig_shape[1])
    boxes[:, 3].clamp_(0, orig_shape[0])
    return boxes


def load_legacy_yolov7_detector(weights_path: Path, names: Optional[List[str]] = None, device: str = "cpu"):
    """Load a YOLOv7 checkpoint and wrap it in an Ultralytics-like callable."""
    checkpoint = torch.load(str(weights_path), map_location=device)
    model = checkpoint["model"] if isinstance(checkpoint, dict) and "model" in checkpoint else checkpoint
    if hasattr(model, "float"):
        model = model.float()
    if hasattr(model, "eval"):
        model.eval()

    return LegacyYOLODetector(model=model, names=names or [])


class LegacyYOLODetector:
    def __init__(self, model: nn.Module, names: List[str]):
        self.model = model
        self.names = names
        self.device = next(model.parameters()).device if any(True for _ in model.parameters()) else torch.device("cpu")

    def _forward(self, image_array: np.ndarray, conf: float = 0.5):
        original_h, original_w = image_array.shape[:2]
        resized, ratio, pad = _letterbox(image_array, 640)
        tensor = torch.from_numpy(resized).to(self.device).permute(2, 0, 1).float() / 255.0
        tensor = tensor.unsqueeze(0)

        with torch.no_grad():
            prediction = self.model(tensor)

        if isinstance(prediction, (tuple, list)):
            prediction = prediction[0]

        if prediction.ndim == 3:
            prediction = prediction[0]

        if prediction.ndim != 2 or prediction.shape[1] < 6:
            return []

        boxes_xywh = prediction[:, :4]
        objectness = prediction[:, 4]
        class_scores = prediction[:, 5:]
        if class_scores.numel() == 0:
            class_scores = torch.ones((prediction.shape[0], 1), device=prediction.device)

        scores, class_ids = (objectness.unsqueeze(1) * class_scores).max(dim=1)
        keep = scores >= conf
        if not keep.any():
            return []

        boxes_xyxy = _xywh_to_xyxy(boxes_xywh[keep])
        boxes_xyxy = _scale_boxes(boxes_xyxy, ratio, pad, (original_h, original_w))
        scores = scores[keep]
        class_ids = class_ids[keep]

        nms_keep = nms(boxes_xyxy, scores, 0.45)
        boxes_xyxy = boxes_xyxy[nms_keep]
        scores = scores[nms_keep]
        class_ids = class_ids[nms_keep]

        detections = []
        for i in range(boxes_xyxy.shape[0]):
            detections.append(
                LegacyBox(
                    conf=scores[i : i + 1].detach().cpu(),
                    cls=class_ids[i : i + 1].detach().cpu(),
                    xyxy=boxes_xyxy[i : i + 1].detach().cpu(),
                )
            )
        return detections

    def __call__(self, image_array: np.ndarray, conf: float = 0.5, verbose: bool = False):
        return [LegacyResult(self._forward(image_array, conf=conf))]
