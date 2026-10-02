"""HSI-YOLO lightweight modules and shape self-checks."""

import torch
import torch.nn as nn


class ConvBNAct(nn.Module):
    def __init__(self, c1, c2, k=1, s=1, p=None, g=1):
        super().__init__()
        p = k // 2 if p is None else p
        self.block = nn.Sequential(
            nn.Conv2d(c1, c2, k, s, p, groups=g, bias=False),
            nn.BatchNorm2d(c2),
            nn.SiLU(inplace=True),
        )

    def forward(self, x):
        return self.block(x)


class GSConv(nn.Module):
    """Standard and depthwise convolution branches followed by channel shuffle."""

    def __init__(self, c1, c2, k=1, s=1):
        super().__init__()
        assert c2 % 2 == 0, "GSConv output channels must be even"
        half = c2 // 2
        self.cv = ConvBNAct(c1, half, k, s)
        self.dw = ConvBNAct(half, half, 5, 1, g=half)

    def forward(self, x):
        first = self.cv(x)
        y = torch.cat((first, self.dw(first)), 1)
        batch, channels, height, width = y.shape
        return y.reshape(batch, 2, channels // 2, height, width).transpose(1, 2).reshape(batch, channels, height, width)


class GSBottleneck(nn.Module):
    def __init__(self, c1, c2):
        super().__init__()
        assert c1 == c2, "residual connection requires matching channels"
        self.cv1 = GSConv(c1, c2)
        self.cv2 = GSConv(c2, c2, 3)

    def forward(self, x):
        return x + self.cv2(self.cv1(x))


class VoVGSCSP2(nn.Module):
    def __init__(self, c1, c2, n=1, *args):
        super().__init__()
        if c2 < 2:
            self.tiny = ConvBNAct(c1, c2, 1)
            self.a = self.b = self.blocks = self.out = None
            return
        self.tiny = None
        hidden = c2 // 2
        self.a = ConvBNAct(c1, hidden, 1)
        self.b = ConvBNAct(c1, hidden, 1)
        self.blocks = nn.Sequential(*[GSBottleneck(hidden, hidden) for _ in range(n)])
        self.out = ConvBNAct(hidden * 2, c2, 1)

    def forward(self, x):
        if self.tiny is not None:
            return self.tiny(x)
        return self.out(torch.cat((self.blocks(self.a(x)), self.b(x)), 1))


class VoVGSCSP2CR(VoVGSCSP2):
    """VoVGSCSP2 with lightweight channel recalibration."""

    def __init__(self, c1, c2, n=1, *args):
        super().__init__(c1, c2, n, *args)
        mid = max(c2 // 8, 4)
        self.cr = nn.Sequential(
            nn.AdaptiveAvgPool2d(1),
            nn.Conv2d(c2, mid, 1),
            nn.SiLU(inplace=True),
            nn.Conv2d(mid, c2, 1),
            nn.Sigmoid(),
        )

    def forward(self, x):
        y = super().forward(x)
        return y * self.cr(y)


class DSHGBlock(nn.Module):
    """Multi-branch feature block retained for controlled architecture experiments."""

    def __init__(self, c1, c2):
        super().__init__()
        assert c2 % 5 == 0, "output channels must be divisible by five"
        branch = c2 // 5
        self.branches = nn.ModuleList(
            [ConvBNAct(c1, branch, kernel, 1, g=c1 if c1 == branch else 1) for kernel in (3, 5, 7, 9, 11)]
        )
        self.fuse = ConvBNAct(c2, c2, 1)
        self.ese = nn.Sequential(nn.AdaptiveAvgPool2d(1), nn.Conv2d(c2, c2, 1), nn.Sigmoid())

    def forward(self, x):
        y = self.fuse(torch.cat([branch(x) for branch in self.branches], 1))
        return y * self.ese(y)


if __name__ == "__main__":
    for size in (640, 320):
        x = torch.randn(2, 32, size, size)
        modules = [
            ("GSConv", GSConv(32, 64), 64),
            ("GSBottleneck", GSBottleneck(32, 32), 32),
            ("VoVGSCSP2", VoVGSCSP2(32, 64), 64),
            ("DSHGBlock", DSHGBlock(32, 40), 40),
        ]
        for name, module, channels in modules:
            y = module(x)
            assert y.shape[1] == channels and y.shape[2:] == x.shape[2:]
            print(size, name, tuple(y.shape))
