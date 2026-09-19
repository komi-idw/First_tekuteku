# Decision Pending Register

- Previous: [experiment_log_template.md](experiment_log_template.md)
- Next: [source_traceability.md](source_traceability.md)
- Overview: [../00_project_overview.md](../00_project_overview.md)
- Related Reference: [hardware_inventory.md](hardware_inventory.md)，[joint_definition.md](joint_definition.md)，[coordinate_system.md](coordinate_system.md)

## 1．運用規則

未決定事項を推測で確定しない．各decisionには，必要になる時点，決定に必要なevidence，候補，安全影響，決定記録を付ける．決定後も行を削除せず，状態と根拠を更新する．

| ID | Topic | Current status | Needed by | Evidence / decision rule |
|---|---|---|---|---|
| DP-001 | STS3215の型式・減速比内訳 | 想定のみ | 最初の通電前 | 全12個の実機label確認 |
| DP-002 | motor個体の脚関節割当て | 未決定 | 5軸実機組立前 | torque / speed要求，減速比，配線，個体試験 |
| DP-003 | 2枚のSeeed bus割当て | 左右分離案 | 5軸拡張前 | 配線，bandwidth，障害分離，cycle計測 |
| DP-004 | STS3215 baud rateとregister仕様 | 未確認 | 単体通信前 | model一致を確認した公式資料とSDK実測 |
| DP-005 | 10軸用電源・battery | 未決定 | 10軸通電前 | peak / continuous current，voltage drop，重量，安全 |
| DP-006 | communication rate | 未決定 | 共通loop設計前 | 1→2→5→10軸latency / error測定 |
| DP-007 | control period | 未決定 | Hold Position設計前 | plant bandwidth，communication，jitter，CPU負荷 |
| DP-008 | communication timeout / watchdog閾値 | 未決定 | 実機closed-loop前 | cycle分布，停止risk，safe action時間 |
| DP-009 | joint axis / positive direction | conventionのみ | 片脚model検証前 | CADまたは機構案，MJCF，実機小角度確認 |
| DP-010 | mechanical / software joint limits | 未決定 | 複数軸動作前 | CAD干渉，実機stop，cable，安全margin |
| DP-011 | velocity / command rate limits | 未決定 | 小角度以外の試験前 | actuator応答，機構risk，電源，制御要求 |
| DP-012 | motor torque limits | 未決定 | load試験前 | model仕様，実測，機構許容，熱 |
| DP-013 | mechanical zero / HOME姿勢 | 未決定 | 組立・HOME保持前 | assembly，CAD，校正治具，contact |
| DP-014 | final link dimensions | CAD待ち | CAD統合 | CAD revisionと実測 |
| DP-015 | final mass / CoM / inertia | CAD・実測待ち | Standing前 | material付きCADとassembled measurement |
| DP-016 | IMU exact modelとmounting transform | 未確認 | IMU統合前 | 現物，firmware，取付CAD，6面試験 |
| DP-017 | quaternion order / orientation direction | 未決定 | `RobotState`実装前 | 使用library，Real / Sim既知姿勢test |
| DP-018 | accelの重力扱い | 未決定 | Real / Sim IMU比較前 | sensor API定義と静止・自由落下相当test |
| DP-019 | `base`と`torso` frame関係 | 未決定 | CAD / IMU統合前 | CAD構造とstate estimation要求 |
| DP-020 | missing / validity表現 | 未決定 | `RobotState`実装前 | logger，type system，partial failure要求 |
| DP-021 | XL330の頭部4軸割当て | 構想のみ | 頭部設計前 | DoF設計，load，speed，range |
| DP-022 | CAD mesh形式・export規約 | 未決定 | CAD export前 | tool互換性，scale，metadata，performance |
| DP-023 | Walking合格基準 | 未決定 | Walking実験前 | 機体能力，試験場所，risk，反復性 |
| DP-024 | RL framework / observation / action | 未決定 | RL開始前 | baseline，実機sensor / actuator，reproducibility |
| DP-025 | Domain Randomization範囲 | 未決定 | RL robustness学習前 | CAD差，同定分布，sensor / latency測定 |
| DP-026 | microcontroller導入条件 | 当面導入しない | PC制御が要求未達時 | cycle，jitter，safety，I/O要求 |
| DP-027 | fault時のsafe action | 状態別に未決定 | 複数軸自立前 | 支持状態，転倒risk，hardware挙動 |

## 2．Decision record template

### DP-XXX：題名

- Status：Proposed / Decided / Superseded
- Decision date：
- Decision：
- Applies from commit / configuration：
- Alternatives considered：
- Evidence：
- Safety impact：
- Affected documents / tests：
- Revisit condition：

## 3．review timing

- 各Phase開始前に，そのPhaseの`Needed by`を確認する．
- 実験終了時に，新規decisionと解消候補を記録する．
- 数値limitを決める場合，source，実測分布，margin，単位を残す．
- 「とりあえず」の仮値はconfigに置く前に仮定と期限を付ける．

## Completion Criteria

未決定であること自体は不備ではない．下流作業に必要なdecisionが，必要時点までにevidenceと安全影響を伴って決まり，未決定のまま暗黙に実装されていないことを完了条件とする．
