# Phase 5：姿勢制御，歩行，強化学習，Sim-to-Real

- Previous: [04_cad_integration.md](04_cad_integration.md)
- Next: なし
- Overview: [00_project_overview.md](00_project_overview.md)
- Related Reference: [software_architecture.md](reference/software_architecture.md)，[joint_definition.md](reference/joint_definition.md)，[coordinate_system.md](reference/coordinate_system.md)，[experiment_log_template.md](reference/experiment_log_template.md)，[decision_pending.md](reference/decision_pending.md)

## 1．目的

本Phaseでは，共通Interfaceと検証済みmodelの上に，HOME保持，Standing，Balance Control，Walking，Reinforcement Learning（RL），Domain Randomization，Sim-to-Realを順に構築する．最初からRLへ進まず，単純なPD制御と古典制御でSimulationと実機の状態・方向・限界・安全機能が正しいことを確認する．

## 2．このPhaseが全体のどこに位置するか

本Phaseは基盤構築後の応用段階である．[Phase 3](03_integration.md)から共通`RobotInterface`，actuator model，安全statusを受け取り，[Phase 4](04_cad_integration.md)からkinematics，mass，CoM，inertia，contact，joint rangeを受け取る．各段階の失敗を前段へfeedbackし，model・校正・安全制約を改善する．

```text
Motor communication
        ↓
Simulation and Common Interface
        ↓
Ideal Biped → CAD Integration → Actuator Identification
        ↓
Standing → Balance → Walking
        ↓
Reinforcement Learning → Domain Randomization → Sim-to-Real
```

## 3．前提知識

- **forward kinematics**：joint angleからlink・footの位置姿勢を求める計算である．
- **inverse kinematics（IK）**：望むfoot等の位置姿勢からjoint angleを求める計算である．
- **CoM**：robot全体の重心であり，支持領域との関係が静的安定性に影響する．
- **support polygon**：接地点が作る支持領域である．足裏接触状態により変化する．
- **LIPM**：重心運動を単純化したLinear Inverted Pendulum Modelである．
- **ZMP**：床反力momentが水平面内で釣り合う指標である．適用仮定とsensor有無に注意する．
- **MPC**：予測modelを使い有限時間先の制約付き最適化を繰り返す制御である．
- **RL**：報酬に基づいてpolicyを学習する方法である．PPOはpolicy optimization手法の一つである．
- **Domain Randomization**：mass，friction，delay等を学習中に変動させ，model誤差へのrobustnessを高める方法である．
- **Sim-to-Real**：Simulationで作ったControllerまたはpolicyを実機へ移す過程である．

## 4．使用するハードウェア・ソフトウェア

- 検証済み10 DoF RealRobotとMuJoCoRobot
- 実・仮想IMU
- joint limit，velocity limit，command rate limit，timeout，watchdog，emergency stop
- CAD-based modelとidentified actuator model
- 共通logger，plot，評価script
- 実機支持治具，落下・転倒を抑える試験環境
- RLを行う場合の学習frameworkと計算資源

RL framework，policy network，control period，battery，foot sensorの有無等は未決定である．必要になった時点で要求と根拠を定める．

## 5．システム構成

```text
Reference / velocity command
             │
             ↓
 Controller or learned Policy
             │ RobotCommand
             ↓
       Safety Supervisor
             │ validated command
             ↓
       RobotInterface
        /          \
MuJoCoRobot       RealRobot
        \          /
          RobotState
             │
      Estimation + Logger
```

Safety Supervisorはpolicyの外側に置き，RLが直接hardware limitやtimeout処理を置き換えない構成とする．

## 6．作業手順

### Step 1：評価指標と安全gateを先に定義する

各段階を始める前に，成功，停止，失敗，rollbackの条件を定める．Standingでは原典の目標である30 s以上を最低条件とする．Walking，RL，Sim-to-Realの具体的な距離，速度，転倒率等は現時点でDecision Pendingであり，実験前に確定する．

**確認方法**：metric，測定方法，試験回数，初期条件，許容範囲，安全停止条件を実験計画へ書く．結果を見てから合格基準を下げない．

### Step 2：HOME保持をbaseline化する

既に統合試験で用いたHold Position Controllerを，制御開発のbaselineとして固定する．異なる初期姿勢，外乱なし，軽微な外乱で$q$ error，velocity，actuator effort，IMU姿勢を測る．

**確認方法**：Simulationと支持された実機で同じcommand系列を用い，定常error，振動，温度，voltage，timeoutを記録する．このbaselineを下回る変更は理由なしに採用しない．

### Step 3：Standing姿勢とtrajectoryを作る

静的に実現可能なstanding poseをkinematicsとjoint rangeから設計し，HOMEからrate-limited trajectoryで移行する．いきなり自由立脚せず，Simulation，支持治具あり実機，安全な自立試験の順で進む．

**確認方法**：self-collision，foot contact，CoM projection，joint margin，actuator effortを確認する．30 sの保持を複数trialで記録し，成功率と停止理由を残す．

### Step 4：IMU feedbackと姿勢推定を確認する

gyro，accel，orientationを使い，torso roll / pitch等の推定を行う．最初から高度なfilterを導入せず，静止，既知傾斜，低速運動でsensor conventionとbiasを確認する．

**確認方法**：既知姿勢に対するerror，静止drift，delay，dropをReal / Simで比較する．quaternion正規化と不連続な符号反転の扱いを確認する．

### Step 5：Balance Controlを追加する

standing baselineへ小さな姿勢feedbackを追加する．目的はIMU feedback，CoM，足裏接触の関係を理解することである．制御対象，feedback量，output jointを限定し，一度に多くのgainを調整しない．

**確認方法**：既知の小外乱または初期傾斜からの回復を測り，最大姿勢偏差，回復時間，joint / torque marginを記録する．外乱試験の実機方法は安全評価後に定める．

### Step 6：手動joint trajectoryでweight shiftを行う

歩行前に，両脚支持から左右へのweight shiftをslow trajectoryで作る．片脚を浮かせる前に，contactとCoM移動のmodelが正しいかを見る．

**確認方法**：foot slip，torso姿勢，接触状態，joint marginを確認する．実機に足裏force sensorがない場合，接触推定の限界を明記する．

### Step 7：IKによる足先trajectoryを作る

足先位置姿勢をparameter化し，IKでjoint trajectoryへ変換する．最初は低い足上げ，小さいstep，低速とする．joint trajectoryの連続性とvelocity limitを優先する．

**確認方法**：forward kinematicsで足先trajectoryを再計算し，tracking error，joint limit，特異姿勢，self-collisionを確認する．Simulationで転倒・slip・contact timingを記録する．

### Step 8：初期Walkingを評価する

手動trajectoryとIKを用いて，定義済み歩数または距離を歩く．必要に応じてLIPM，ZMP，MPCを検討するが，名称を導入すること自体を目的としない．sensor構成と要求に合う方法を選ぶ．

**確認方法**：成功率，移動距離，速度，姿勢偏差，foot slip，energy proxy，停止理由を複数trialで記録する．Simulation成功だけで実機へ即時移さない．

### Step 9：RL課題を定義する

古典baselineとSimulationが安定した後に，observation，action，reward，termination，reset，command distribution，evaluation protocolを定義する．actionは直接torque，joint target，residual等の候補から，hardware安全性と学習目的に基づき選ぶ．

**確認方法**：各observationが実機で取得可能か，latencyとnoiseが再現されるか，reward項が望ましくないshortcutを生まないかをreviewする．baseline Controllerとの比較metricを固定する．

### Step 10：PPO等で学習し，再現性を確認する

algorithm候補としてPPOを検討する．複数seed，固定evaluation set，学習curve，checkpoint，configを保存する．単一seedの成功動画だけで完成としない．

**確認方法**：未学習のinitial conditionとcommandで評価し，平均，分散，failure modeを報告する．deterministicな古典baselineと比較する．

### Step 11：Domain Randomizationを段階導入する

mass，CoM，inertia，friction，motor strength，delay，sensor bias / noise，voltage相当等を一つのgroupずつrandomizeする．範囲はCAD差，実測同定，sensor試験から決め，根拠のない広範囲randomizationでmodel不備を隠さない．

**確認方法**：randomizationなし，単一要素，複数要素のablationを行い，nominal性能とrobustnessのtrade-offを記録する．sampleされたparameterをepisode logへ残す．

### Step 12：Sim-to-Realの段階的gateを通す

policyまたはControllerを，Simulation validation，software-in-the-loop，実機通信のみ，支持治具あり低gain・低速度，短時間自立の順で進める．commandはSafety Supervisorでlimitし，停止条件を独立に監視する．

**確認方法**：各gateでReal / Simのobservation分布，action，latency，tracking，姿勢，faultを比較する．gate失敗時はmodel，state estimation，actuator，policyのどこにgapがあるかを分類し，前段へ戻す．

## 7．確認方法と評価項目

| 段階 | 最低限の評価 |
|---|---|
| HOME保持 | joint error，振動，temperature，timeout |
| Standing | 30 s，成功率，torso姿勢，joint margin，停止理由 |
| Balance | 外乱量，最大偏差，回復時間，slip |
| Walking | 歩数・距離・速度，成功率，姿勢偏差，接触，energy proxy |
| RL | 複数seed，return，task metric，failure rate，baseline比較 |
| Sim-to-Real | observation / action gap，tracking，latency，安全介入回数 |

実験のtrial数，許容値，歩行目標はDecision Pendingである．選定時にはmechanical riskと統計的な再現性を両立させる．

## 8．完了条件

- HOME保持baselineがReal / Simで再現可能である．
- Standingを30 s以上，事前定義した複数trial条件で達成する．
- IMU feedbackとBalance Controlの改善を定量的に示す．
- Walkingを事前定義した距離・歩数・成功率で達成し，failure modeを記録する．
- RLは古典baselineと同じmetricで比較され，複数seedと未学習条件で評価される．
- Domain Randomization範囲に実測または設計上の根拠がある．
- Sim-to-Realは段階gateを通り，Safety Supervisorを迂回しない．
- 実機結果から得たgapがmodelまたは設計へfeedbackされている．

## 9．トラブルシュート

### StandingがSimulationだけで成功する

**症状** → Simulationでは30 s立つが実機では振動・転倒する．  
**考えられる原因** → zero，sign，delay，friction，CoM，contact，actuator limit，IMU biasの差．  
**確認方法** → HOME保持と単軸responseへ戻り，state・command・姿勢を同条件で比較する．  
**対処** → gapを一要因ずつmodelへ反映し，gainだけで隠さない．

### 姿勢feedbackで振動が増える

**症状** → IMU feedback追加後に高周波振動する．  
**考えられる原因** → sign，latency，noise，過大gain，rate mismatch．  
**確認方法** → sensorとcommandのtimestamp，phase，filter有無をplotする．  
**対処** → signを確認し，gainを下げ，遅れとfilterをmodel化する．

### IK trajectoryが限界へ張り付く

**症状** → 一部jointがrange端，高速度，特異姿勢になる．  
**考えられる原因** → 到達不能な足先目標，不適切な姿勢拘束，link寸法誤り．  
**確認方法** → forward kinematics，Jacobian conditioning，joint marginを確認する．  
**対処** → trajectoryを縮小し，constraintとnominal poseを見直す．

### RL rewardは高いが歩行品質が低い

**症状** → returnは上昇するが，滑る，激しい，実機不能な運動になる．  
**考えられる原因** → reward loophole，観測不足，action limit不足，contact model依存．  
**確認方法** → reward内訳，動画，task metric，action・contact分布を確認する．  
**対処** → task metricとterminationを先に修正し，実機制約をenvironmentへ反映する．

### Sim-to-Real直後に大commandが出る

**症状** → 初回policy updateで現在姿勢から大きく離れる．  
**考えられる原因** → observation normalization，joint ordering，zero，policy state，startup sequence．  
**確認方法** → torque disabledまたは通信のみのdry runでobservationとactionを記録する．  
**対処** → action clamp，rate limit，現在姿勢blend-inを使い，mapping修正後に前gateから再開する．

## 10．成果物

- 各段階の評価計画と安全gate
- HOME / Standing / Balance / Walking Controller仕様
- trajectory，IK parameter，評価log，plot
- RL environment仕様，config，checkpoint，複数seed結果
- Domain Randomization parameterと根拠，ablation
- Sim-to-Real gate記録とgap分析
- failure catalogと前段への修正decision

## 11．次のPhaseへ渡す情報

本Phaseが計画上の最終段階である．成果は次のiterationへ戻し，hardware設計，CAD物性，actuator同定，sensor構成，安全limit，Controller要求を更新する．新たなDoF，頭部4軸，battery，自律計算機を追加する場合も，共通contractと段階gateを維持する．

## 実行チェックリスト

- [ ] Step 1：評価指標と安全gateを事前定義した
- [ ] Step 2：HOME保持baselineを固定した
- [ ] Step 3：Standing姿勢と移行trajectoryを検証した
- [ ] Step 4：IMU feedbackと姿勢推定を検証した
- [ ] Step 5：Balance Controlを定量評価した
- [ ] Step 6：weight shiftを確認した
- [ ] Step 7：IK足先trajectoryを検証した
- [ ] Step 8：初期Walkingを複数trialで評価した
- [ ] Step 9：RL課題と実機可能な観測・行動を定義した
- [ ] Step 10：複数seedでRLを評価した
- [ ] Step 11：Domain Randomizationをablationした
- [ ] Step 12：Sim-to-Realの全gateを通過した

## Phase Completion Criteria

第8章の各条件を，事前定義したmetric，複数trial，再現可能なconfig，安全記録によって満たし，Sim-to-Real結果と残存gapが説明可能になった時点で，本Phaseを完了とする．
