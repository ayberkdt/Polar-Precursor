# Pilot gate report (2001-2005, CHAMP)

Configuration `pilot` (digest `c97064b20414`), ladder ['B0', 'B1', 'B2', 'D', 'B3', 'B3k', 'B3t', 'M'], G = 30 storms, 20525 samples.

## Primary result

M vs B3: relative RMSE reduction +4.28% [+2.17%, +7.85%] (95% cluster bootstrap, 10000 resamples, seed 20270207, G = 30); storms improved 83%, bootstrap p 0.0001; permutation (one-sided, 1000 resamples, seed 20270207): observed +4.28%, null mean -0.21% (SD 0.02%), p = 0.0010

Storm-to-storm SD of d_s = MSE_B3 − MSE_M: 0.00204 (input to the minimum-effect decision, plan 07 item 9).

## Ladder, lead times pooled

| model | n | mean_residual | sd_residual | rmse | correlation | skill_vs_persistence | skill_vs_reference |
| --- | --- | --- | --- | --- | --- | --- | --- |
| B0 | 20525.0000 | 0.0793 | 0.2948 | 0.3053 |  | -4.1528 | -4.1252 |
| B1 | 20507.0000 | 0.0016 | 0.1345 | 0.1345 | 0.8953 | 0.0000 | 0.0053 |
| B2 | 20525.0000 | -0.0016 | 0.1493 | 0.1493 | 0.8622 | -0.2331 | -0.2265 |
| D | 20525.0000 | -0.0092 | 0.2640 | 0.2642 | 0.5322 | -2.8596 | -2.8390 |
| B3 | 20525.0000 | -0.0024 | 0.1348 | 0.1348 | 0.8893 | -0.0054 | 0.0000 |
| B3k | 20525.0000 | -0.0005 | 0.1457 | 0.1457 | 0.8699 | -0.1738 | -0.1675 |
| B3t | 20525.0000 | -0.0022 | 0.1305 | 0.1305 | 0.8966 | 0.0578 | 0.0629 |
| M | 20525.0000 | -0.0030 | 0.1272 | 0.1273 | 0.9020 | 0.1042 | 0.1090 |

## Secondary comparisons (cluster bootstrap, one-sided p)

| reference | candidate | label | subset | n_storms | relative_rmse_reduction | ci_low | ci_high | mean_loss_difference | fraction_storms_improved | p_one_sided |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| B3 | M | H1 primary: polar passes added | all | 30 | 0.0428 | 0.0217 | 0.0785 | 0.0014 | 0.8333 | 0.0001 |
| D | B3 | H4: own history added to drivers | all | 30 | 0.4786 | 0.4022 | 0.5313 | 0.0435 | 0.9667 | 0.0001 |
| B3t | M | control: polar vs mid-latitude freshness | all | 30 | 0.0220 | 0.0079 | 0.0470 | 0.0007 | 0.7000 | 0.0002 |
| B3k | M | control: polar vs oracle drivers | all | 30 | 0.1320 | 0.0159 | 0.1905 | 0.0049 | 0.6667 | 0.0014 |
| B1 | B2 | ladder: autoregression over persistence | all | 30 | -0.0955 | -0.1952 | 0.0009 | -0.0034 | 0.3333 | 0.9720 |
| B2 | B3 | ladder: drivers over own history | all | 30 | 0.1092 | 0.0618 | 0.1811 | 0.0042 | 0.9000 | 0.0001 |

## Primary comparison per lead-time bin (Holm-adjusted)

| reference | candidate | lead_bin | n_storms | relative_rmse_reduction | ci_low | ci_high | mean_loss_difference | fraction_storms_improved | p_raw | p_holm | significant_holm |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| B3 | M | 105-150 | 30 | 0.0532 | 0.0376 | 0.0833 | 0.0018 | 0.8333 | 0.0001 | 0.0005 | True |
| B3 | M | 150-195 | 30 | 0.0515 | 0.0189 | 0.1026 | 0.0014 | 0.8333 | 0.0001 | 0.0005 | True |
| B3 | M | 195-240 | 30 | 0.0525 | 0.0312 | 0.0900 | 0.0020 | 0.9000 | 0.0001 | 0.0005 | True |
| B3 | M | 240-270 | 30 | 0.0368 | 0.0105 | 0.0752 | 0.0013 | 0.7667 | 0.0008 | 0.0016 | True |
| B3 | M | 60-105 | 30 | 0.0116 | -0.0154 | 0.0456 | 0.0003 | 0.4667 | 0.2192 | 0.2192 | False |

H2 (gain highest in the 105-195 min bins): yes (descriptive).

## d_s by storm class

| intensity | n_storms | mean_d | sd_d | median_d | fraction_improved |
| --- | --- | --- | --- | --- | --- |
| moderate | 12 | 0.0016 | 0.0027 | 0.0009 | 0.8333 |
| severe | 2 | 0.0009 | 0.0001 | 0.0009 | 1.0000 |
| strong | 6 | 0.0023 | 0.0021 | 0.0026 | 0.8333 |
| weak | 10 | 0.0006 | 0.0009 | 0.0004 | 0.8000 |

## Peak errors of M per storm

amplitude error mean -0.0903 (SD 0.1386); timing error median +93 min, IQR +91..+230 min.

## Power (2.8 × SD / √G with the measured SD)

| n_storms | detectable_sd | detectable_loss_difference |
| --- | --- | --- |
| 30.0000 | 0.5115 | 0.0010 |
| 100.0000 | 0.2802 | 0.0006 |
| 127.0000 | 0.2486 | 0.0005 |
| 150.0000 | 0.2287 | 0.0005 |
| 200.0000 | 0.1981 | 0.0004 |

## Buffer check

no violations
