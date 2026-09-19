# Source Traceability

- Previous: [decision_pending.md](decision_pending.md)
- Next: [glossary.md](glossary.md)
- Overview: [../00_project_overview.md](../00_project_overview.md)
- Related Reference: [../README.md](../README.md)

## 1．原典と再構成方針

原典は「BDX型二足歩行ロボット開発 作業手順書 v0.3」である．原典中の`bdx_robot/`は`First_tekuteku/`へ読み替えた．内容を削除せず，重複を共通Referenceへ集約し，実行順序，確認方法，安全gate，成果物，完了条件を補った．

本書群で原典と異なる判断を行った箇所は次である．

- `00_proect_overview.md`という依頼内の誤記を，後段指定と整合する`00_project_overview.md`へ修正した．
- 原典の`SimulationRobot`表記は，class案と揃えるため本文では主に`MuJoCoRobot`とした．概念上は同じSimulation backendである．
- 原典の`q_knee`は，10軸orderingと揃えるため`q_knee_pitch`へ正規化した．
- 原典にあるcode treeは将来構成案として扱い，今回の範囲では`docs/`だけを作成した．
- 実験再現性，未決定事項，追跡性のため，指定外のReference文書を追加した．これは「提案」であり，software実装を追加したものではない．

## 2．v0.3節から文書への対応

| v0.3 section | 主な再構成先 | 備考 |
|---|---|---|
| 1．開発目的 | `00_project_overview.md` 1，2 | Reference Implementation方針を統合 |
| 2．最終的なシステム構成 | Overview 2，`software_architecture.md` | `RobotInterface` contractへ展開 |
| 3．初期hardware | `01_real_hardware.md` 4，`hardware_inventory.md` | 想定と現物確認を分離 |
| 4．初期robot構成 | `joint_definition.md` | 10 DoF orderingを正規化 |
| 5．開発Repository | `docs/README.md`，architecture | 今回はdocsのみ作成 |
| A-0〜A-6 | `01_real_hardware.md` Step 1〜7 | motorなし確認，read-first，小角度を維持 |
| A-7〜A-10 | Real Hardware Step 8〜10 | protocol，自作Driver，SI，zero / sign |
| A-11〜A-13 | Real Hardware Step 11，architecture | 2 bus，複数軸，Motor Interface |
| A-14〜A-15 | Real Hardware Step 12〜13 | XL330，IMU単体試験 |
| A-16〜A-18 | Real Hardware Step 14，architecture | RobotState / Command / RealRobot |
| A-19 | Real Hardware Step 15 | safety項目をfault testへ展開 |
| B-0〜B-3 | `02_simulation.md` Step 1〜3 | installation，Ground，Free Body |
| B-4〜B-7 | Simulation Step 4〜7 | 1 DoF，torque，PD，step response |
| B-8〜B-9 | Simulation Step 8〜9，architecture | SimulatedMotor，RobotInterface |
| B-10〜B-14 | Simulation Step 10〜13，joint reference | 片脚，座標，全軸確認，二足，HOME |
| B-15〜B-18 | Simulation Step 14〜16 | contact，Virtual IMU，共通Controller |
| C-1〜C-4 | `03_integration.md` Step 1〜8 | Hold Position，unit，ordering，log |
| C-5〜C-6 | Integration Step 9〜10 | 実機同定と段階model化 |
| D-1〜D-4 | `04_cad_integration.md` | 物性，visual，collision，不変条件 |
| E-1〜E-5 | `05_control.md` | Standing，Balance，Walking，RL，Sim-to-Real |
| F Stage 1〜10 | Overview 3 | 並行Stage表へ統合 |
| G 基盤完成の判定 | Overview 7，各Phase Completion | 検証可能な条件へ展開 |

## 3．依頼追加要件から文書への対応

| Requirement | Location |
|---|---|
| M1〜M14 | `00_project_overview.md` 5 |
| Phaseの目的・前提・作業・成果・完了・関係 | Overview 4，各Phase 1〜11 |
| Phase依存関係 | Overview 6 |
| 各Phaseの理由付きStep | `01`〜`05`の6章 |
| 各Stepの正常時・観測・記録 | `01`〜`05`の各Stepと7章 |
| 症状→原因→確認→対処 | `01`〜`05`の9章 |
| 文書間link | 全文書header |
| checklistとCompletion Criteriaの分離 | 全Phase末尾 |
| 実験記録 | `experiment_log_template.md` |
| 確定／案／仮定／Decision Pending | `README.md`，`decision_pending.md` |
| terminology / joint / coordinate / SI / state / command統一 | `glossary.md`と各Reference |
| Hardware安全9項目 | `01_real_hardware.md` Step 15 |
| CAD replaceability | Overview 2.2，`04_cad_integration.md` |

## 4．外部Referenceの扱い

次の外部資料は実施時の一次情報・比較対象として利用できる．この文書作成時点では，version依存の数値を外部確認なしに確定していない．

- MuJoCo公式documentation
- Seeed Studio公式documentation
- Feetech公式documentation
- ROBOTIS公式documentation
- Pollen Robotics Microduck / `microduck_rl`
- Open Duck Mini
- SO-101

公式資料はprotocol，pinout，電圧，register，API等の根拠とする．既存repositoryはarchitecture比較，troubleshoot，結果検証に使い，本実装の代替としてcopyしない．参照時にはURL，revision，参照日，採用・不採用理由を実験またはdecision recordへ残す．

## 5．不足・矛盾のreview結果

### 整理により解消した事項

- `SimulationRobot`と`MuJoCoRobot`は同じbackend概念として整理した．
- `q_knee`と`q_knee_pitch`は後者へ統一した．
- 原典のReal / Simulation別手順とStage 1〜10を，Overviewの交互開発表で接続した．
- RobotStateの実機診断fieldはoptional，基本fieldは共通として整理した．

### 未決定として保持した事項

motor関節割当て，link寸法，質量，battery，周期，limit，torque，IMU型式・frame，quaternion順序，CAD export，歩行・RL評価値である．一覧と決定条件は[decision_pending.md](decision_pending.md)に置いた．

### 提案として追加した事項

- Asset IDとServo IDを分離したinventory管理
- state validity，stale data，partial failureの明示
- fault injectionによる安全機能検証
- CAD nominalと実測値の併記
- RLの複数seed，baseline比較，randomization ablation

## Completion Criteria

原典と依頼追加要件の全項目が少なくとも1つの管理先へ対応し，名称変更・追加判断・未決定事項が黙って混入していないことを完了条件とする．
