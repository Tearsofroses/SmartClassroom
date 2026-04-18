"""Compatibility layer for legacy YOLOv7 checkpoints.

The SCB weights in this repository were serialized from a YOLOv7 training
environment. Their pickles reference `models.common` classes, so we provide
minimal implementations here to make `torch.load()` able to reconstruct the
checkpoint and run inference.
"""

from __future__ import annotations

from typing import List

import torch
from torch import nn


def autopad(kernel_size: int, padding: int | None = None) -> int:
    return kernel_size // 2 if padding is None else padding


class Conv(nn.Module):
    def __init__(self, c1=1, c2=1, k=1, s=1, p=None, g=1, act=True):
        super().__init__()
        self.conv = nn.Conv2d(c1, c2, k, s, autopad(k, p), groups=g, bias=False)
        self.bn = nn.BatchNorm2d(c2)
        self.act = nn.SiLU() if act else nn.Identity()

    def forward(self, x):
        return self.act(self.bn(self.conv(x)))


class Concat(nn.Module):
    def __init__(self, dimension=1):
        super().__init__()
        # Keep both names because some YOLOv7 checkpoints serialize this attr as `d`.
        self.dimension = dimension
        self.d = dimension

    def forward(self, tensors: List[torch.Tensor]):
        dim = getattr(self, "dimension", getattr(self, "d", 1))
        return torch.cat(tensors, dim)


class MP(nn.Module):
    def __init__(self, k=2):
        super().__init__()
        self.m = nn.MaxPool2d(kernel_size=k, stride=k)

    def forward(self, x):
        return self.m(x)


class RepConv(nn.Module):
    def __init__(self, c1=1, c2=1, k=3, s=1, p=None, g=1, act=True):
        super().__init__()
        self.conv = Conv(c1, c2, k, s, p, g, act)
        self.act = nn.SiLU() if act else nn.Identity()

    def forward(self, x):
        # Simple path for checkpoints initialized from this shim.
        if hasattr(self, "conv"):
            return self.conv(x)

        # YOLOv7 deploy path after rep-parameterization.
        if hasattr(self, "rbr_reparam"):
            return self.act(self.rbr_reparam(x))

        # YOLOv7 training/inference path with branch summation.
        dense_out = self.rbr_dense(x) if hasattr(self, "rbr_dense") else 0
        one_out = self.rbr_1x1(x) if hasattr(self, "rbr_1x1") else 0
        if hasattr(self, "rbr_identity") and self.rbr_identity is not None:
            id_out = self.rbr_identity(x)
        else:
            id_out = 0
        return self.act(dense_out + one_out + id_out)


class SPPCSPC(nn.Module):
    def __init__(self, c1=1, c2=1, k=(5, 9, 13)):
        super().__init__()
        # Match YOLOv7 SPPCSPC channel math used in serialized checkpoints.
        c_ = max(c2, 1)
        self.cv1 = Conv(c1, c_, 1, 1)
        self.cv2 = Conv(c1, c_, 1, 1)
        self.cv3 = Conv(c_, c_, 3, 1)
        self.cv4 = Conv(c_, c_, 1, 1)
        self.cv5 = Conv(c_ * 4, c_, 1, 1)
        self.cv6 = Conv(c_, c_, 3, 1)
        self.cv7 = Conv(c_ * 2, c2, 1, 1)
        self.m = nn.ModuleList([nn.MaxPool2d(kernel_size=kernel, stride=1, padding=kernel // 2) for kernel in k])

    def forward(self, x):
        x1 = self.cv4(self.cv3(self.cv1(x)))
        y1 = self.cv6(self.cv5(torch.cat([x1, *[pool(x1) for pool in self.m]], dim=1)))
        y2 = self.cv2(x)
        return self.cv7(torch.cat((y1, y2), dim=1))
