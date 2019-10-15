import torch
import torch.nn as nn


class DIAL1d(nn.Module):
    def __init__(self, num_features):
        super(DIAL1d, self).__init__()
        self.bn_S = nn.BatchNorm1d(num_features, affine=False)
        self.bn_T = nn.BatchNorm1d(num_features, affine=False)
        self.gamma = nn.Parameter(torch.Tensor(1, num_features, 1))
        self.beta = nn.Parameter(torch.Tensor(1, num_features, 1))
        self.reset_parameters()

    def forward(self, x, is_source=True):
        if is_source:
            x = self.bn_S(x)
        else:
            x = self.bn_T(x)
        return self.gamma * x + self.beta

    def reset_parameters(self):
        nn.init.uniform_(self.gamma)
        nn.init.zeros_(self.beta)


class DIAL(nn.Module):
    def __init__(self, num_features):
        super(DIAL, self).__init__()
        self.bn_S = nn.BatchNorm1d(num_features, affine=False)
        self.bn_T = nn.BatchNorm1d(num_features, affine=False)
        self.gamma = nn.Parameter(torch.Tensor(1, num_features))
        self.beta = nn.Parameter(torch.Tensor(1, num_features))
        self.reset_parameters()

    def forward(self, x, is_source=True):
        if is_source:
            x = self.bn_S(x)
        else:
            x = self.bn_T(x)
        return self.gamma * x + self.beta

    def reset_parameters(self):
        nn.init.uniform_(self.gamma)
        nn.init.zeros_(self.beta)


class BaselineModel(nn.Module):
    def __init__(self, dial_last=False, num_classes=5):
        super(BaselineModel, self).__init__()

        self.conv1 = nn.Conv1d(2048, 4096, 1)
        self.conv2 = nn.Conv1d(4096, 8192, 1)
        self.pool1 = nn.AvgPool1d(5)
        self.fc = nn.Linear(8192, num_classes)
        self.bn1 = DIAL1d(4096)
        self.bn2 = DIAL1d(8192)

        if dial_last:
            self.bn3 = DIAL(num_classes)
        else:
            self.bn3 = None

    def forward(self, input, is_source=True):
        out = input.permute(0, 2, 1)

        out = torch.relu(self.bn1(self.conv1(out), is_source))
        out = torch.relu(self.bn2(self.conv2(out), is_source))
        out = self.pool1(out)

        out = out.view((out.shape[0], -1))

        out = self.fc(out)

        if self.bn3 is not None:
            out = self.bn3(out, True)

        return out