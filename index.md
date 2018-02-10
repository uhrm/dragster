
## Dragster

* Description of [game physics](physics.md).

## Races

* [Demo](plots/race_demo.svg) &emsp; A demo race in 6.04
* Analysis of global frame counter

  The following table lists eight races with same user input, but different
  race start frame.

  | Offset | Start (Frame) | Time   | Plots                            |
  |--------|---------------|--------|----------------------------------|
  | 0      | 160           | 6.07   | [Link](plots/race_demo_ofs0.svg) |
  | 2      | 162           | 6.04   | [Link](plots/race_demo_ofs2.svg) |
  | 4      | 164           | busted | [Link](plots/race_demo_ofs4.svg) |
  | 6      | 166           | 6.04   | [Link](plots/race_demo_ofs6.svg) |
  | 8      | 168           | 6.01   | [Link](plots/race_demo_ofs8.svg) |
  | 10     | 170           | 5.97   | [Link](plots/race_demo_ofsA.svg) |
  | 12     | 172           | busted | [Link](plots/race_demo_ofsC.svg) |
  | 14     | 174           | 6.07   | [Link](plots/race_demo_ofsE.svg) |

* Optimal races
  
  The following table lists the best possible distance achievable in 5.57,
  depending on the game start offset.
  
  | Offset | Start (Frame) | Distance | Plots                                |
  |--------|---------------|----------|--------------------------------------|
  | 0      | 160           | 24913    | [Link](plots/race_dprog168_ofs0.svg) |
  | 2      | 162           | 24846    | [Link](plots/race_dprog168_ofs2.svg) |
  | 4      | 164           | 24861    | [Link](plots/race_dprog168_ofs4.svg) |
  | 6      | 166           | 24878    | [Link](plots/race_dprog168_ofs6.svg) |
  | 8      | 168           | 24799*   | [Link](plots/race_dprog168_ofs8.svg) |
  | 10     | 170           | 24808*   | [Link](plots/race_dprog168_ofsA.svg) |
  | 12     | 172           | 24923    | [Link](plots/race_dprog168_ofsC.svg) |
  | 14     | 174           | 24930    | [Link](plots/race_dprog168_ofsE.svg) |

  Note that since the finish distance is 24832, the games marked with (*) are
  not beatable in 5.57. Also, to beat the game in 5.54, one would need to
  achieve 25085 (=24832+253) in 5.57 which is not possible.
  