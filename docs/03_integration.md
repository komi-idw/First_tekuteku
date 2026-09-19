# Phase 3：Real / Simulation統合

- Previous: [02_simulation.md](02_simulation.md)
- Next: [04_cad_integration.md](04_cad_integration.md)
- Overview: [00_project_overview.md](00_project_overview.md)
- Related Reference: [software_architecture.md](reference/software_architecture.md)，[joint_definition.md](reference/joint_definition.md)，[coordinate_system.md](reference/coordinate_system.md)，[experiment_log_template.md](reference/experiment_log_template.md)

## 1．目的

本Phaseの目的は，同じControllerを`MuJoCoRobot`と`RealRobot`へ接続し，両者を同じ単位，関節順序，時刻意味，ログ形式で観測できるようにすることである．最初の統合目標はWalkingではなく，Hold Position Controllerである．さらに，STS3215の応答を測定し，ideal PD modelへ非理想性を一つずつ追加する．

## 2．このPhaseが全体のどこに位置するか

[Phase 1](01_real_hardware.md)から実機Driver，校正，安全制約を受け取り，[Phase 2](02_simulation.md)からideal model，`SimulatedMotor`，Virtual IMUを受け取る．本Phaseでsoftware contractと比較方法を固定する．その成果は，[Phase 4](04_cad_integration.md)でgeometryや物性を交換するときの不変条件となり，[Phase 5](05_control.md)ではControllerの接続点となる．

## 3．前提知識

- **interface contract**：method名だけでなく，入力・出力，unit，shape，順序，時刻，error時の意味まで含む合意である．
- **RobotState**：観測時点のjointとIMU等をまとめた状態表現である．commanded stateではない．
- **RobotCommand**：Controllerがrobotへ要求する指令である．初期は`q_target[]`のみを有効とする．
- **timestamp**：dataが表す時刻である．PC受信時刻，device測定時刻，simulation時刻を区別する．
- **latency**：指令送信から作用・観測までの遅れである．jitterはその変動である．
- **step response**：入力を段階的に変えたときの時間応答である．rise，overshoot，settling，delay等を得る．
- **system identification**：入出力計測からmodel parameterや応答特性を推定する作業である．
- **saturation**：torqueやvelocity等が上限で制限される非線形性である．

## 4．使用するハードウェア・ソフトウェア

- Phase 1で検証済みのSTS3215単体構成および段階的な複数軸構成
- Phase 2で検証済みのMuJoCo model
- 共通config，logger，plot環境
- `MotorInterface`，`RobotInterface`，`RobotState`，`RobotCommand`の仕様
- emergency stopと物理的な電源遮断手段

本Phaseの文書作成時点では実装は開始しない．実施時には各成果物のGit commitとversionを固定する．

## 5．システム構成

```text
                      HoldPositionController
                               │
                        RobotCommand [SI]
                               │
                        RobotInterface
                         /           \
                        /             \
               MuJoCoRobot          RealRobot
                  │                    │
        SimulatedMotor[]       STS3215 / XL330 / IMU
                  │                    │
                  └──── RobotState ────┘
                               │
                        Common Logger
```

Controllerはbackend型を条件分岐しない．backend固有の接続・raw conversion・transport errorは各backendが共通statusへ変換する．安全判定は，driver内の局所limitとrobot層の全体監視を重ねる．

## 6．作業手順

### Step 1：共通data contractを確定する

`RobotState`の必須fieldを`time`，`q[]`，`dq[]`，`gyro[3]`，`accel[3]`，`orientation[4]`とする．実機診断用にtemperature，voltage，current/load，communication status等を追加可能とする．`RobotCommand`は`q_target[]`から始め，`dq_target[]`，`torque_target[]`，`torque_limit[]`は将来拡張とする．

**確認方法**：各fieldについてtype，shape，unit，frame，ordering，validity，missing value，timestamp関係を表にする．配列長はactive joint countと一致させる．`None`を使う場合のserialize規則も定める．

### Step 2：joint orderingを全層で固定する

初期10 DoFはleft 5軸，right 5軸の順とし，[joint_definition.md](reference/joint_definition.md)を正とする．config，MuJoCo，RealRobot，Controller，loggerでindexを独自に再定義しない．

**確認方法**：各層からname listを出力し，同一性を機械的に比較する．1軸ずつ小さな識別commandを送り，観測indexと物理関節が一致することを確認する．

### Step 3：unitと座標変換の境界を固定する

Servo raw値，degree，device固有axis，quaternion順序をbackend境界で共通conventionへ変換する．Controllerはrad，rad/s，m/s²，N m，s等の共通SI表現のみを見る．

**確認方法**：既知角度，既知速度，静止重力，単軸回転をReal / Simで比較する．round-trip変換誤差を記録し，共通層にraw名やdevice固有unitがないことをreviewする．

### Step 4：時刻とupdate責務を決める

Simulation time，device測定時刻，PC monotonic受信時刻を区別する．Controllerへ渡す`time`が何を意味するかを決め，状態のageとcommandのageを監視できるようにする．control rateとcommunication rateは同一とは限らない．

**確認方法**：一定期間のsample interval，latency，jitter，dropを記録する．wall clock変更の影響を受けないmonotonicな時間差を用いる．thresholdの数値は実測後に決める．

### Step 5：共通loggerを定義する

RealとSimulationで同じ列名を使用する．最低限，`time`，`q_0...q_9`，`dq_0...dq_9`，`qcmd_0...qcmd_9`，gyro 3軸，accel 3軸，orientation 4成分，backend，validity，error statusを記録する．診断telemetryは追加列とする．

**確認方法**：両backendのlogを同じreaderで読み，joint name metadataと配列列が一致することを確認する．設定値とhardware構成への参照をlog headerまたはmanifestへ持たせる．

### Step 6：1 DoFでbackendを切り替える

Hold Position Controllerを変更せず，1 DoFの`MuJoCoRobot`と単体`RealRobot`へ接続する．実機では現在位置を初期targetとし，Simulationでも同じstartup sequenceを使う．

**確認方法**：backend選択以外のController codeとconfig意味が同じであることを確認する．commandとstateを重ねてplotし，符号・unit・時間軸の一致を見る．実機は小角度・低速・無負荷で行う．

### Step 7：安全状態とerrorを共通化する

通信timeout，stale state，limit violation，over-temperature，low voltage，invalid sensor，emergency stopを共通statusへ写像する．ただし，backend固有の詳細error codeも診断用に保持する．

**確認方法**：抜線，command停止，範囲外command，NaN，古いtimestampを注入し，Controllerが通常stateと誤認しないことを確認する．実機のfault試験は危険を最小化した単体構成から行う．

### Step 8：5軸，10軸へ統合を拡張する

1 DoF contractが成立した後，片脚5軸，二足10軸へ増やす．配列を増やすだけでなく，busごとの更新時刻差，partial failure，全体safe actionを扱う．

**確認方法**：1軸ずつ識別commandを送り，全index mappingを検証する．cycleごとのstate age，bus差，error率を記録する．全軸同時stepは電源と安全性を評価するまで行わない．

### Step 9：STS3215単体の応答を同定する

安全確認済み範囲で，position stepとsine入力を使う．例としてstepは$0^\circ\rightarrow10^\circ$，sineは

$$
q_d(t)=A\sin(2\pi ft)
$$

とするが，zeroや可動域を考慮して現在位置周辺へoffsetする．振幅$A$，周波数$f$，速度，負荷，電源条件は試験前に定める．

**確認方法**：response delay，rise time，settling time，maximum velocity，overshoot，steady-state error，反転時のhysteresisを算出する．温度・電圧・負荷を併記し，1回の結果で全個体を代表させない．

### Step 10：Simulation actuatorを段階的に現実化する

ideal PDへ，次の順で要素を一つずつ追加する．

```text
Ideal PD
   ↓
Torque saturation
   ↓
Velocity saturation
   ↓
Delay
   ↓
Friction
   ↓
Backlash
```

各追加前後で同じ入力を使い，fitの改善と副作用を比較する．parameterを物理値として同定できない場合は，effective modelであることを明記する．

**確認方法**：Real / Simのtime seriesと定義済みerror metricを比較する．一つの試験だけに過学習せず，stepと複数sine条件でvalidationする．

### Step 11：10 DoF共通Controllerを確認する

最初はHOME保持だけを行う．Simulationでlimit，initial offset，contactを確認した後，実機では支持治具または無負荷条件から開始する．WalkingやRL policyをこのgateより先に接続しない．

**確認方法**：同じ`q_target`系列に対し，Real / Simの$q,\dot q$，error，latency，safety statusを比較する．差を「model gap」として記録し，説明できない差を残したまま次へ進まない．

## 7．確認方法と受入metric

- schema検査：field，shape，dtype，unit，frame，orderingが一致する．
- mapping検査：1軸commandに対し，意図した1軸が同符号で応答する．
- timing検査：sample interval，state age，command age，drop，jitterが記録される．
- logging検査：同じ解析scriptでReal / Sim logを読める．
- safety検査：invalid・stale・timeout時に通常commandが継続されない．
- identification検査：train条件以外の入力でも改善を確認する．

数値thresholdは現時点では未決定である．実測distributionと制御要求を得た後，[decision_pending.md](reference/decision_pending.md)で決定する．

## 8．完了条件

- `RobotState`，`RobotCommand`，`MotorInterface`，`RobotInterface`のdata contractが文書化されている．
- Real / Simでjoint ordering，unit，frame，timestamp意味が一致する．
- 同じloggerと解析手順で両backendを比較できる．
- Hold Position Controllerを変更せず，1 DoFから10 DoFまでbackendを切り替えられる．
- partial failure，timeout，invalid commandを検出し，定義済みsafe actionへ移る．
- STS3215同定dataとparameterがあり，actuator modelへ一要素ずつ反映されている．
- modelの改善を未使用条件でvalidationしている．

## 9．トラブルシュート

### RealとSimで逆方向へ動く

**症状** → 同じ正commandで動作方向が異なる．  
**考えられる原因** → mechanical zero，direction，MJCF axis，mapping indexの不一致．  
**確認方法** → 1軸だけを小角度で動かし，raw→joint→Controllerの各境界を追跡する．  
**対処** → 共通joint conventionを保持し，backend境界の校正・axisを修正する．

### 配列長は合うが関節が入れ替わる

**症状** → commandした関節と別の関節が動く．  
**考えられる原因** → ID list，MuJoCo joint index，logger列の独自順序．  
**確認方法** → name listの機械比較と1-hot commandを行う．  
**対処** → name-to-index mappingを一元化し，位置依存の重複設定を削除する．

### 比較plotの時間がずれる

**症状** → 波形形状は似るが遅れ評価が一定しない．  
**考えられる原因** → PC受信時刻とsimulation時刻の混同，buffer，異なる開始条件．  
**確認方法** → command生成，送信，device sample，受信のtimestampを区別する．  
**対処** → 明示した基準時刻で再sampleし，latency自体を消さずparameterとして扱う．

### actuator modelが一条件だけ合う

**症状** → stepには合うがsineや負荷条件で外れる．  
**考えられる原因** → parameter過学習，欠落したsaturation・delay，温度・電圧依存．  
**確認方法** → 未使用の振幅，周波数，方向，個体でvalidationする．  
**対処** → 要素を一つずつ追加し，適用範囲と不確かさを記録する．

## 10．成果物

- 共通interface仕様とschema test
- joint / unit / frame mapping table
- 共通log schemaと解析plot
- Hold Position ControllerのReal / Sim比較log
- timing，latency，jitter，error率の測定
- STS3215 step / sine応答data
- actuator parameterとvalidation結果
- safety fault injection記録

## 11．次のPhaseへ渡す情報

[Phase 4](04_cad_integration.md)へ，不変とするjoint name，ordering，Interface，baseline regression，model parameterを渡す．[Phase 5](05_control.md)へ，共通Controller接続，状態の信頼性，安全status，actuator limit，Real / Sim gapを渡す．

## 実行チェックリスト

- [ ] Step 1：共通data contractを確定した
- [ ] Step 2：joint orderingを全層で照合した
- [ ] Step 3：unitとframe変換を境界へ閉じ込めた
- [ ] Step 4：時刻とupdate責務を定義した
- [ ] Step 5：共通loggerを検証した
- [ ] Step 6：1 DoFでbackendを切り替えた
- [ ] Step 7：errorと安全状態を共通化した
- [ ] Step 8：5軸，10軸へ段階拡張した
- [ ] Step 9：STS3215応答を同定した
- [ ] Step 10：actuator modelを段階的に更新した
- [ ] Step 11：10 DoF HOME保持を両backendで確認した

## Phase Completion Criteria

第8章の全条件について，共通schemaによるReal / Simの比較証拠とfault時の安全遷移記録が存在し，同じController codeがbackend固有分岐なしで機能した時点で，本Phaseを完了とする．
