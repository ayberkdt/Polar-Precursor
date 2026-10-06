# Pilot gate report (2001-2005, CHAMP)

Configuration `pilot` (digest `338f28727289`), ladder ['B0', 'B1', 'B2', 'D', 'B3', 'B3k', 'B3t', 'B3t2', 'M'], G = 30 storms, 20525 samples.

## Primary result

M vs B3: relative RMSE reduction +5.99% [+3.27%, +9.85%] (95% cluster bootstrap, 10000 resamples, seed 20270207, G = 30); storms improved 90%, bootstrap p 0.0001; permutation (one-sided, 1000 resamples, seed 20270207): observed +5.99%, null mean -0.25% (SD 0.02%), p = 0.0010

Storm-to-storm SD of d_s = MSE_B3 − MSE_M: 0.00192 (input to the minimum-effect decision, plan 07 item 9).

## Ladder, lead times pooled

| model | n | mean_residual | sd_residual | rmse | correlation | skill_vs_persistence | skill_vs_reference |
| --- | --- | --- | --- | --- | --- | --- | --- |
| B0 | 20525.0000 | 0.0793 | 0.2948 | 0.3053 |  | -4.1528 | -6.4524 |
| B1 | 20507.0000 | 0.0016 | 0.1345 | 0.1345 | 0.8953 | 0.0000 | -0.4463 |
| B2 | 20525.0000 | -0.0015 | 0.1288 | 0.1288 | 0.8994 | 0.0820 | -0.3276 |
| D | 20525.0000 | -0.0092 | 0.2640 | 0.2642 | 0.5322 | -2.8596 | -4.5822 |
| B3 | 20525.0000 | -0.0020 | 0.1118 | 0.1118 | 0.9253 | 0.3086 | 0.0000 |
| B3k | 20525.0000 | -0.0008 | 0.1242 | 0.1242 | 0.9074 | 0.1475 | -0.2329 |
| B3t | 20525.0000 | -0.0020 | 0.1065 | 0.1065 | 0.9325 | 0.3730 | 0.0932 |
| B3t2 | 20525.0000 | -0.0018 | 0.1083 | 0.1083 | 0.9302 | 0.3518 | 0.0626 |
| M | 20525.0000 | -0.0033 | 0.1026 | 0.1027 | 0.9375 | 0.4170 | 0.1569 |

## Secondary comparisons (cluster bootstrap, one-sided p)

| reference | candidate | label | subset | n_storms | relative_rmse_reduction | ci_low | ci_high | mean_loss_difference | fraction_storms_improved | p_one_sided |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| B3 | M | H1 primary: polar passes added | all | 30 | 0.0599 | 0.0327 | 0.0985 | 0.0013 | 0.9000 | 0.0001 |
| D | B3 | H4: own history added to drivers | all | 30 | 0.5593 | 0.4669 | 0.6014 | 0.0482 | 0.9667 | 0.0001 |
| B3t | M | control: polar vs mid-latitude freshness (before the pass) | all | 30 | 0.0290 | 0.0083 | 0.0576 | 0.0006 | 0.7333 | 0.0010 |
| B3t2 | M | control: polar vs mid-latitude freshness (after the pass) | all | 30 | 0.0355 | 0.0060 | 0.0733 | 0.0008 | 0.8000 | 0.0062 |
| B3k | M | control: polar vs oracle drivers | all | 30 | 0.1723 | 0.0158 | 0.2586 | 0.0047 | 0.6667 | 0.0027 |
| B1 | B2 | ladder: autoregression over persistence | all | 30 | 0.0382 | 0.0196 | 0.0578 | 0.0013 | 0.7333 | 0.0001 |
| B2 | B3 | ladder: drivers over own history | all | 30 | 0.1425 | 0.0831 | 0.2120 | 0.0042 | 0.9000 | 0.0001 |

## Primary comparison per lead-time bin (Holm-adjusted)

| reference | candidate | lead_bin | n_storms | relative_rmse_reduction | ci_low | ci_high | mean_loss_difference | fraction_storms_improved | p_raw | p_holm | significant_holm |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| B3 | M | 105-150 | 30 | 0.0867 | 0.0646 | 0.1150 | 0.0018 | 0.8667 | 0.0001 | 0.0005 | True |
| B3 | M | 150-195 | 30 | 0.0675 | 0.0245 | 0.1251 | 0.0014 | 0.9000 | 0.0002 | 0.0006 | True |
| B3 | M | 195-240 | 30 | 0.0765 | 0.0517 | 0.1113 | 0.0021 | 0.9333 | 0.0001 | 0.0005 | True |
| B3 | M | 240-270 | 30 | 0.0407 | 0.0085 | 0.0822 | 0.0012 | 0.8000 | 0.0034 | 0.0068 | True |
| B3 | M | 60-105 | 30 | 0.0181 | -0.0219 | 0.0669 | 0.0003 | 0.5333 | 0.2102 | 0.2102 | False |

H2 (gain highest in the 105-195 min bins): yes (descriptive).

## d_s by storm class

| intensity | n_storms | mean_d | sd_d | median_d | fraction_improved |
| --- | --- | --- | --- | --- | --- |
| extreme | 2 | 0.0050 | 0.0059 | 0.0050 | 1.0000 |
| moderate | 10 | 0.0008 | 0.0006 | 0.0008 | 0.9000 |
| severe | 4 | 0.0020 | 0.0012 | 0.0016 | 1.0000 |
| strong | 8 | 0.0017 | 0.0017 | 0.0013 | 0.8750 |
| weak | 6 | 0.0000 | 0.0004 | 0.0001 | 0.8333 |

## Peak errors of M per storm

amplitude error mean -0.0221 (SD 0.0884); timing error median +182 min, IQR +91..+275 min.

## Power (2.8 × SD / √G with the measured SD)

| n_storms | detectable_sd | detectable_loss_difference |
| --- | --- | --- |
| 30.0000 | 0.5115 | 0.0010 |
| 100.0000 | 0.2802 | 0.0005 |
| 127.0000 | 0.2486 | 0.0005 |
| 150.0000 | 0.2287 | 0.0004 |
| 200.0000 | 0.1981 | 0.0004 |

## Buffer check

no violations
