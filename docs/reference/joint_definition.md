# Joint Definition

- Previous: [hardware_inventory.md](hardware_inventory.md)
- Next: [coordinate_system.md](coordinate_system.md)
- Overview: [../00_project_overview.md](../00_project_overview.md)
- Related Reference: [software_architecture.md](software_architecture.md)，[decision_pending.md](decision_pending.md)

## 1．適用範囲

本書はSimulation，Real Hardware，Controller，config，loggerで共通に使うjoint nameとorderingを定義する．axis，zero，sign，rangeの数値は，CADと実機校正を経て更新する．名前とorderingの変更は広範な影響を持つため，decision recordなしに変更しない．

## 2．初期10 DoF ordering

片脚は次の5 DoFとする．

$$
\mathbf q_{leg}=
[q_{hip\_yaw},q_{hip\_roll},q_{hip\_pitch},q_{knee\_pitch},q_{ankle\_pitch}]^T
$$

全身の初期orderingは次である．

| Index | Joint name | Group | Axis / positive physical meaning | Range | Hardware assignment |
|---:|---|---|---|---|---|
| 0 | `left_hip_yaw` | left leg | Decision Pending | Decision Pending | Decision Pending |
| 1 | `left_hip_roll` | left leg | Decision Pending | Decision Pending | Decision Pending |
| 2 | `left_hip_pitch` | left leg | Decision Pending | Decision Pending | Decision Pending |
| 3 | `left_knee_pitch` | left leg | Decision Pending | Decision Pending | Decision Pending |
| 4 | `left_ankle_pitch` | left leg | Decision Pending | Decision Pending | Decision Pending |
| 5 | `right_hip_yaw` | right leg | Decision Pending | Decision Pending | Decision Pending |
| 6 | `right_hip_roll` | right leg | Decision Pending | Decision Pending | Decision Pending |
| 7 | `right_hip_pitch` | right leg | Decision Pending | Decision Pending | Decision Pending |
| 8 | `right_knee_pitch` | right leg | Decision Pending | Decision Pending | Decision Pending |
| 9 | `right_ankle_pitch` | right leg | Decision Pending | Decision Pending | Decision Pending |

原典の初期表記`q_knee`は，system-wideの一貫性を保つため`q_knee_pitch`へ正規化した．これは自由度の意味を変えるものではない．

## 3．zeroとsign

共通joint angleは，conceptとして次で定義する．

$$
q_j=s_j\,f_j(raw_j-raw_{0,j}),\qquad s_j\in\{-1,+1\}
$$

- $raw_{0,j}$：共通$q_j=0$に対応するServo値である．
- $s_j$：Servo増加方向を共通正方向へ写像する符号である．
- $f_j$：model固有のraw-to-rad変換である．

mechanical zero，servo zero，HOME姿勢は異なる概念である．HOMEをzeroの代用にしない．

## 4．axis決定手順

1. [coordinate_system.md](coordinate_system.md)のrobot frameを基準にする．
2. CAD上のjoint axisをrobot frameへ変換する．
3. $q>0$の小角度姿勢を図または物理的な言葉で定義する．
4. MJCFで同じ正方向を確認する．
5. 実機を現在位置近傍で小角度駆動し，`direction`設定を校正する．
6. name，axis vector，positive meaning，zero evidenceを本表へ記録する．

左右mirrorでaxis vectorの成分が異なる場合がある．「左右とも同じ数値axis」を先に仮定せず，物理的な正方向を共通定義とする．

## 5．HOME姿勢

$$
\mathbf q_{home}=[q_0,\ldots,q_9]^T
$$

HOME値は未決定である．決定時には，unitをradとし，joint ordering，CAD revision，実機zero calibration，self-collision，ground contact，安全marginを記録する．起動直後にHOMEへ瞬間移動させず，現在位置からrate-limited trajectoryで移る．

## 6．将来の14 DoF拡張

将来的に頭部4 DoFを追加し，合計14 DoFとする．頭部jointの具体名，axis，ordering，XL330-M077 / M288の割当ては未決定である．既存10 indexを保持し，頭部をindex 10〜13へ追加する案を優先するが，正式決定ではない．

## 7．変更時の確認

- [ ] Simulation，RealRobot，Controller，loggerのname listが一致する
- [ ] 1-hot commandで対象jointだけが動く
- [ ] 正方向が図・CAD・Simulation・実機で一致する
- [ ] raw-to-radとrad-to-rawが許容誤差内でround-tripする
- [ ] rangeがmechanical，CAD，softwareの3種に分けて記録される
- [ ] HOMEがcurrent positionから安全に到達可能である

## Completion Criteria

全10軸のname，index，axis，zero，positive meaning，range，hardware assignmentがevidence付きで埋まり，全層の自動比較と1軸ずつの物理確認が通った時点でjoint定義を確定する．
