# RNN RUL workload templates

These workloads model `RNN_RUL` from UniCT:

- input window: `[B, 30, 25]`
- `window_size = 30`
- `input_size = 25`
- RNN hidden sizes: `64 -> 32 -> 16 -> 8 -> 4`
- FC head: `Linear(4, 40) -> ReLU -> Linear(40, 1)`

Each `nn.RNN` layer is decomposed into two affine transforms:

- `x2h`: input-to-hidden transform, `x_t @ W_ih`
- `h2h`: recurrent hidden-to-hidden transform, `h_{t-1} @ W_hh`

The transforms are represented as `1x1` `cnn-layer` workloads because MEDEA already uses this shape for dense/GEMM-like layers. ReLU, bias additions, hidden-state dependency, and optional sigmoid output activation are not explicitly modeled (**TODO?**)

Important: the sequence dimension is encoded as `Q=30`, which captures the arithmetic volume for all time steps. This is optimistic for latency because a true RNN has a sequential dependency along time for the recurrent `h2h` path.
The model instantiation sets:

```text
input_size = args.input_size = 25
window_size = 30
fc_hidden = 40
batch_size = 16
local_learning_rate = 0.001
```

`batch_size` and `local_learning_rate` are training settings, so these workloads use `N=1` for single-window inference analysis.

Suggested lookup for the compact 12-workload run:

```text
-l 0 1 2 3 4 5 6 7 8 9 10 11
```
