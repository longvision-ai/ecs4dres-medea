# Chen CNN RUL workload templates

These workloads model `Chen_CNN_RUL` neural network:

- input window: `[B, 30, 25]`
- MEDEA tensor view: `[B, 1, 30, 25]` (treat the input as a single-channel image)
- `conv1..conv5`: `Conv2d(..., kernel_size=(10, 1), stride=1)`
- `conv6`: `Conv2d(..., kernel_size=(3, 1), stride=1)`
- `conv_channels`: `[16, 16, 16, 16, 16, 16]`
- time-axis same padding is applied in PyTorch before each convolution, so all convolution workloads keep `P=30`, `Q=25`
- `AdaptiveAvgPool2d((1, 1))` is not modeled directly by MEDEA (**TODO?**)
- `fc1`: `Linear(16, 350)`, represented as a `1x1` `cnn-layer`
- `fc2`: `Linear(350, 120)`, represented as a `1x1` `cnn-layer`
- `fc3`: `Linear(120, 1)`, represented as a `1x1` `cnn-layer`

The model instantiation sets:

```text
conv_channels = [16, 16, 16, 16, 16, 16]
batch_size = 16
local_learning_rate = 0.01
window_size = 30
```

`batch_size` and `local_learning_rate` are training settings, so they do not change the single-inference MEDEA workloads. Convolution layers use `cnn-layer`; dense layers are encoded as `1x1` `cnn-layer` workloads. 

Tanh, dropout, adaptive pooling, and the optional sigmoid output activation are not represented here (**TODO?**)

Suggested lookup for a full nine-layer run:

```text
-l 0 1 2 3 4 5 6 7 8
```
