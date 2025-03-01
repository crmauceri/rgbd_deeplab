import math
import torch
import torch.nn as nn
import torch.nn.functional as F
from deeplab3.modeling.sync_batchnorm.batchnorm import SynchronizedBatchNorm2d

class Decoder(nn.Module):
    def __init__(self, cfg, BatchNorm):
        super(Decoder, self).__init__()

        if cfg.MODEL.BACKBONE in ['resnet', 'drn', 'depthaware_resnet', 'depthaware_vgg16']:
            low_level_inplanes = 256
        elif cfg.MODEL.BACKBONE == 'xception':
            low_level_inplanes = 128
        elif cfg.MODEL.BACKBONE == 'mobilenet':
            low_level_inplanes = 24
        else:
            raise NotImplementedError

        if cfg.MODEL.DECODER_DOUBLE:
            low_level_inplanes *= 2

        if cfg.MODEL.DECODER_DOUBLE and not cfg.MODEL.ASPP_DOUBLE:
            last_conv_dim = 560
        else:
            last_conv_dim = 304

        self.conv1 = nn.Conv2d(low_level_inplanes, 48, 1, bias=False)
        self.bn1 = BatchNorm(48)
        self.relu = nn.ReLU()
        self.last_conv = nn.Sequential(nn.Conv2d(last_conv_dim, 256, kernel_size=3, stride=1, padding=1, bias=False),
                                       BatchNorm(256),
                                       nn.ReLU(),
                                       nn.Dropout(0.5),
                                       nn.Conv2d(256, 256, kernel_size=3, stride=1, padding=1, bias=False),
                                       BatchNorm(256),
                                       nn.ReLU(),
                                       nn.Dropout(0.1),
                                       nn.Conv2d(256, cfg.DATASET.N_CLASSES, kernel_size=1, stride=1))
        self._init_weight()


    def forward(self, x, low_level_feat):
        low_level_feat = self.conv1(low_level_feat)
        low_level_feat = self.bn1(low_level_feat)
        low_level_feat = self.relu(low_level_feat)

        x = F.interpolate(x, size=low_level_feat.size()[2:], mode='bilinear', align_corners=True)
        x = torch.cat((x, low_level_feat), dim=1)
        x = self.last_conv(x)

        return x

    def _init_weight(self):
        for m in self.modules():
            if isinstance(m, nn.Conv2d):
                torch.nn.init.kaiming_normal_(m.weight)
            elif isinstance(m, SynchronizedBatchNorm2d):
                m.weight.data.fill_(1)
                m.bias.data.zero_()
            elif isinstance(m, nn.BatchNorm2d):
                m.weight.data.fill_(1)
                m.bias.data.zero_()

def build_decoder(cfg, BatchNorm):
    return Decoder(cfg, BatchNorm)