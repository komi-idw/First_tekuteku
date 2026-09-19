# Experiment Log Template

- Previous: [software_architecture.md](software_architecture.md)
- Next: [decision_pending.md](decision_pending.md)
- Overview: [../00_project_overview.md](../00_project_overview.md)
- Related Reference: [hardware_inventory.md](hardware_inventory.md)，[source_traceability.md](source_traceability.md)

以下を1実験または1試験seriesごとに複製して使用する．「成功した」だけでなく，再現条件，raw data，失敗，次Actionを残す．Hardware試験では安全確認と停止理由を必須とする．

---

## Experiment ID：`YYYYMMDD-short-name-runNN`

### 1．目的・仮説

- 目的：
- 検証する仮説：
- 対応Milestone / Phase：
- 事前に定めた成功条件：
- 停止・中止条件：

### 2．実施情報

| Field | Value |
|---|---|
| Date / time / timezone | |
| Operator / reviewer | |
| Git commit | |
| Working tree state | clean / changed（差分への参照） |
| OS | |
| Python / MuJoCo / package version | |
| Log schema version | |
| Config file / hash | |

### 3．Hardware configuration

- 使用Asset ID：
- Servo model / ID / reduction：
- Driver Board / COM port / firmware：
- Bus構成：
- 電源，設定電圧，定格：
- IMU model / mounting / firmware：
- link，horn，負荷，支持治具：
- wiring / photographへのlink：
- 室温，battery状態等：

Simulationのみの場合は「該当なし」とし，model fileとparameterへ置き換える．

### 4．Simulation configuration

- MJCF / mesh revision：
- timestep / solver：
- initial state：
- contact parameter：
- actuator model：
- random seed：
- randomization sample：

実機のみの場合は「該当なし」とする．

### 5．Control and communication settings

- joint ordering：
- Controller / gain：
- target trajectory：
- command rate / communication rate：
- joint / velocity / torque / rate limit：
- timeout / watchdog：
- baud rate / protocol setting：
- sensor filter / calibration：

### 6．安全pre-check

- [ ] 対象と危険範囲を確認した
- [ ] 現在位置をreadしてからtargetを作る
- [ ] joint，velocity，command rate limitが有効である
- [ ] communication timeoutとwatchdogが有効である
- [ ] software torque disableを確認した
- [ ] 物理的なemergency stop / 電源遮断へ即時アクセスできる
- [ ] 最初のtrialは小角度，低速，低負荷または支持ありである

### 7．Procedure

1. 
2. 
3. 

### 8．Observed result

- 正常時に期待した観測：
- 実際の観測：
- 取得data / plot / videoへのlink：
- metricと値：
- warning / error / safety intervention：

### 9．結果判定

- Success / Partial / Fail / Aborted：
- 事前成功条件との比較：
- 不確かさ・data欠損：
- 結論が適用できる範囲：

### 10．問題と次Action

| Problem / finding | Evidence | Suspected cause | Next action | Owner | Due / gate |
|---|---|---|---|---|---|
| | | | | | |

### 11．Decision更新

- 解消したDecision Pending：
- 新たに追加するDecision Pending：
- 更新したReference：

---

## 記録品質の完了条件

commit，hardware / simulation構成，version，設定，条件，結果，問題，次Actionが揃い，第三者が同じ試験を再実行できることを完了条件とする．
