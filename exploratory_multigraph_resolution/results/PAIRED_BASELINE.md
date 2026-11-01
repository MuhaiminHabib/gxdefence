# Paired attack contrast against clean reruns

Exploratory follow-up after observing the resolution audit. Each comparison shares the same clean explanation; the baseline uses an independent clean rerun. For each similarity measure, excess disruption = clean-to-clean similarity minus clean-to-attacked similarity. Positive values mean the attack departs further from the clean explanation than an ordinary rerun does on average.

Seeds/trials are averaged within targets before 5,000 paired target bootstrap draws. These intervals omit graph-node dependence and training variation. Matched overlap is the original audit diagnostic, not semantic accuracy. The larger cohort overlaps the fresh-seed cohort and is not an independent replication. Fresh seeds were not used for attack selection; the full cohort uses selection seeds.

| Scope | Dataset | Method | Selection | Targets | Row excess, 95% interval | Matched excess, 95% interval | Change in contrast, 95% interval |
|---|---|---|---|---:|---|---|---|
| Fresh seed audit | amlsim | GNN-targeted GX adaptation | top10 | 50 | -0.0036 (-0.0108, 0.0036) | 0.0916 (0.0568, 0.1284) | 0.0952 (0.0632, 0.1292) |
| Fresh seed audit | amlsim | GNN-targeted GX adaptation | top25 | 50 | 0.0469 (0.0367, 0.0569) | 0.1250 (0.0978, 0.1530) | 0.0782 (0.0602, 0.0973) |
| Fresh seed audit | amlsim | Random flipping | top10 | 50 | -0.3376 (-0.4456, -0.2396) | -0.1996 (-0.2864, -0.1212) | 0.1380 (0.1056, 0.1712) |
| Fresh seed audit | amlsim | Random flipping | top25 | 50 | -0.2325 (-0.3086, -0.1602) | -0.0322 (-0.0561, -0.0094) | 0.2003 (0.1469, 0.2560) |
| Fresh seed audit | amlsim | Random search | top10 | 50 | 0.0008 (-0.0044, 0.0068) | 0.0892 (0.0580, 0.1220) | 0.0884 (0.0580, 0.1196) |
| Fresh seed audit | amlsim | Random search | top25 | 50 | 0.0496 (0.0392, 0.0606) | 0.1296 (0.1022, 0.1601) | 0.0800 (0.0612, 0.1007) |
| Fresh seed audit | hi_small | GNN-targeted GX adaptation | top10 | 50 | 0.0522 (0.0002, 0.1036) | 0.2450 (0.1746, 0.3174) | 0.1928 (0.1496, 0.2388) |
| Fresh seed audit | hi_small | GNN-targeted GX adaptation | top25 | 50 | 0.0510 (-0.0084, 0.1065) | 0.2307 (0.1551, 0.3042) | 0.1797 (0.1442, 0.2170) |
| Fresh seed audit | hi_small | Random flipping | top10 | 50 | -0.2260 (-0.3113, -0.1419) | -0.0748 (-0.1553, 0.0083) | 0.1512 (0.1060, 0.1984) |
| Fresh seed audit | hi_small | Random flipping | top25 | 50 | -0.1930 (-0.2663, -0.1201) | -0.0469 (-0.1097, 0.0171) | 0.1462 (0.1097, 0.1825) |
| Fresh seed audit | hi_small | Random search | top10 | 50 | 0.0934 (0.0393, 0.1493) | 0.2858 (0.2109, 0.3605) | 0.1924 (0.1472, 0.2356) |
| Fresh seed audit | hi_small | Random search | top25 | 50 | 0.0942 (0.0330, 0.1491) | 0.2807 (0.2078, 0.3505) | 0.1864 (0.1480, 0.2245) |
| Full three-trial GNN | amlsim | GNN-targeted GX adaptation | top10 | 166 | 0.0283 (0.0227, 0.0341) | 0.0904 (0.0713, 0.1100) | 0.0620 (0.0440, 0.0809) |
| Full three-trial GNN | amlsim | GNN-targeted GX adaptation | top25 | 166 | 0.0676 (0.0612, 0.0745) | 0.1514 (0.1367, 0.1673) | 0.0838 (0.0739, 0.0945) |
| Full three-trial GNN | amlsim | Random flipping | top10 | 166 | -0.3283 (-0.3645, -0.2922) | -0.2137 (-0.2460, -0.1811) | 0.1147 (0.0998, 0.1293) |
| Full three-trial GNN | amlsim | Random flipping | top25 | 166 | -0.2537 (-0.2794, -0.2293) | -0.0372 (-0.0467, -0.0282) | 0.2165 (0.1993, 0.2344) |
| Full three-trial GNN | amlsim | Random rewiring | top10 | 166 | -0.1580 (-0.1773, -0.1390) | -0.0757 (-0.0942, -0.0578) | 0.0823 (0.0665, 0.0988) |
| Full three-trial GNN | amlsim | Random rewiring | top25 | 166 | -0.1367 (-0.1499, -0.1236) | -0.0070 (-0.0130, -0.0002) | 0.1297 (0.1184, 0.1410) |
| Full three-trial GNN | amlsim | Random search | top10 | 166 | 0.0299 (0.0245, 0.0355) | 0.0974 (0.0787, 0.1161) | 0.0675 (0.0494, 0.0851) |
| Full three-trial GNN | amlsim | Random search | top25 | 166 | 0.0636 (0.0578, 0.0700) | 0.1427 (0.1276, 0.1589) | 0.0791 (0.0686, 0.0903) |
| Full three-trial GNN | hi_small | GNN-targeted GX adaptation | top10 | 795 | 0.1393 (0.1268, 0.1524) | 0.2923 (0.2749, 0.3110) | 0.1530 (0.1408, 0.1652) |
| Full three-trial GNN | hi_small | GNN-targeted GX adaptation | top25 | 795 | 0.1348 (0.1228, 0.1466) | 0.2547 (0.2362, 0.2738) | 0.1199 (0.1090, 0.1304) |
| Full three-trial GNN | hi_small | Random flipping | top10 | 795 | -0.1691 (-0.1864, -0.1518) | -0.0246 (-0.0408, -0.0082) | 0.1445 (0.1353, 0.1537) |
| Full three-trial GNN | hi_small | Random flipping | top25 | 795 | -0.1458 (-0.1591, -0.1327) | -0.0185 (-0.0312, -0.0055) | 0.1273 (0.1203, 0.1343) |
| Full three-trial GNN | hi_small | Random rewiring | top10 | 795 | -0.0608 (-0.0739, -0.0476) | 0.0465 (0.0333, 0.0602) | 0.1073 (0.0992, 0.1154) |
| Full three-trial GNN | hi_small | Random rewiring | top25 | 795 | -0.0567 (-0.0665, -0.0467) | 0.0461 (0.0352, 0.0573) | 0.1028 (0.0960, 0.1100) |
| Full three-trial GNN | hi_small | Random search | top10 | 795 | 0.1602 (0.1474, 0.1733) | 0.3461 (0.3278, 0.3640) | 0.1859 (0.1742, 0.1979) |
| Full three-trial GNN | hi_small | Random search | top25 | 795 | 0.1538 (0.1424, 0.1654) | 0.3071 (0.2888, 0.3257) | 0.1532 (0.1425, 0.1642) |