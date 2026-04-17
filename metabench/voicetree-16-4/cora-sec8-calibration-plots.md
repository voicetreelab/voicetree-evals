---
color: cyan
isContextNode: false
agent_name: Eli
---
# §8 — six M1/M2 calibration plots (embedded)

Six ASCII reliability diagrams: M1 + M2 per model (Sonnet/Gemini/GPT). Embedded verbatim from metacog_analysis.md §8.

# §8 — Calibration plots (M1 and M2)

Binned reliability diagrams per model. `.` = bin's mean forecast p̄; `o` = bin's observed frequency ȳ. Horizontal displacement = bin reliability residual. Vertical spread of ȳ = resolution.

```text
M1 calibration — claude-sonnet-4.6
Brier=0.186  reliability=0.051  resolution=0.101  uncertainty=0.236  n=34
bin            n     p̄      ȳ   |0.0-------0.25-------0.5-------0.75-------1.0|
[[0.0,0.1)      0      —      —   |                                        |
[0.1,0.2)      0      —      —   |                                        |
[0.2,0.3)      0      —      —   |                                        |
[0.3,0.4)      0      —      —   |                                        |
[0.4,0.5)      1   0.45   0.00   |o                 .                     |
[0.5,0.6)      7   0.51   0.29   |           o        .                   |
[0.6,0.7)      7   0.63   0.29   |           o             .              |
[0.7,0.8)     15   0.75   0.87   |                             .    o     |
[0.8,0.9)      4   0.81   1.00   |                                .      o|
[0.9,1.0)      0      —      —   |                                        |
```

```text
M1 calibration — gemini-flash-latest
Brier=0.207  reliability=0.132  resolution=0.022  uncertainty=0.099  n=45
bin            n     p̄      ȳ   |0.0-------0.25-------0.5-------0.75-------1.0|
[0.0,0.1)      0      —      —   |                                        |
[0.1,0.2)      1   0.10   1.00   |    .                                  o|
[0.2,0.3)      2   0.20   1.00   |        .                              o|
[0.3,0.4)      2   0.32   0.50   |             .      o                   |
[0.4,0.5)      5   0.40   1.00   |                .                      o|
[0.5,0.6)     13   0.50   0.85   |                    .            o      |
[0.6,0.7)      2   0.60   0.50   |                    o  .                |
[0.7,0.8)      4   0.71   1.00   |                            .          o|
[0.8,0.9)      4   0.81   0.75   |                             o  .       |
[0.9,1.0)     12   0.92   1.00   |                                    .  o|
```

```text
M1 calibration — gpt-5.4-mini
Brier=0.275  reliability=0.176  resolution=0.121  uncertainty=0.220  n=49
bin            n     p̄      ȳ   |0.0-------0.25-------0.5-------0.75-------1.0|
[0.2,0.3)      9   0.22   0.00   |o        .                              |
[0.3,0.4)     15   0.35   0.80   |              .                o        |
[0.4,0.5)     17   0.42   0.88   |                .                 o     |
[0.7,0.8)      5   0.76   1.00   |                             .         o|
[0.9,1.0)      3   0.96   0.33   |             o                       .  |
```

```text
M2 calibration — claude-sonnet-4.6
Brier=0.097  reliability=0.013  resolution=0.120  uncertainty=0.204  n=360
bin            n     p̄      ȳ   |0.0-------0.25-------0.5-------0.75-------1.0|
[0.0,0.1)     86   0.05   0.00   |o .                                     |
[0.1,0.2)     74   0.12   0.04   |  o  .                                  |
[0.2,0.3)     48   0.21   0.10   |    o   .                               |
[0.3,0.4)     20   0.33   0.05   |  o          .                          |
[0.4,0.5)     17   0.43   0.41   |                o.                      |
[0.5,0.6)     18   0.52   0.56   |                    . o                 |
[0.6,0.7)      8   0.63   0.50   |                    o    .              |
[0.7,0.8)     18   0.73   0.83   |                            .   o       |
[0.8,0.9)     21   0.83   0.57   |                      o         .       |
[0.9,1.0)     50   0.98   0.92   |                                    o . |
```

```text
M2 calibration — gemini-flash-latest
Brier=0.322  reliability=0.117  resolution=0.028  uncertainty=0.237  n=375
bin            n     p̄      ȳ   |0.0-------0.25-------0.5-------0.75-------1.0|
[0.0,0.1)     19   0.02   0.00   |o.                                      |
[0.1,0.2)     30   0.10   0.17   |    . o                                 |
[0.2,0.3)     22   0.20   0.27   |        .  o                            |
[0.3,0.4)     31   0.30   0.26   |          o .                           |
[0.4,0.5)     11   0.40   0.36   |              o .                       |
[0.5,0.6)     24   0.50   0.29   |           o        .                   |
[0.6,0.7)     23   0.60   0.30   |            o          .                |
[0.7,0.8)     12   0.70   0.50   |                    o      .            |
[0.8,0.9)     32   0.80   0.25   |          o                    .        |
[0.9,1.0)    171   0.96   0.54   |                     o                . |
```

```text
M2 calibration — gpt-5.4-mini
Brier=0.172  reliability=0.118  resolution=0.002  uncertainty=0.055  n=447
bin            n     p̄      ȳ   |0.0-------0.25-------0.5-------0.75-------1.0|
[0.0,0.1)    193   0.04   0.04   | o.                                     |
[0.1,0.2)     43   0.15   0.12   |     o.                                 |
[0.2,0.3)     71   0.23   0.04   |  o      .                              |
[0.3,0.4)     24   0.35   0.04   |  o           .                         |
[0.4,0.5)     10   0.42   0.00   |o               .                       |
[0.5,0.6)     30   0.52   0.00   |o                   .                   |
[0.6,0.7)     21   0.62   0.19   |       o                .               |
[0.7,0.8)     15   0.70   0.13   |     o                     .            |
[0.8,0.9)      2   0.82   0.00   |o                               .       |
[0.9,1.0)     38   0.97   0.11   |    o                                 . |
```

Empty-bin rows omitted from GPT's M1 plot here for space — full rendering with all 10 bins is in `kaggle_submission/results/metacog_analysis.md` lines 193–293.

artifact [cora-metacog-writereport-extension-done]]

[[/Users/bobbobby/repos/voicetree-evals/metabench/voicetree-16-4/cora-metacog-writereport-extension-done.md]]