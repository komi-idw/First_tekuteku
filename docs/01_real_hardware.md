# Phase 1：Real Hardware基盤

- Previous: [00_project_overview.md](00_project_overview.md)
- Next: [02_simulation.md](02_simulation.md)
- Overview: [00_project_overview.md](00_project_overview.md)
- Related Reference: [hardware_inventory.md](reference/hardware_inventory.md)，[joint_definition.md](reference/joint_definition.md)，[coordinate_system.md](reference/coordinate_system.md)，[experiment_log_template.md](reference/experiment_log_template.md)，[decision_pending.md](reference/decision_pending.md)

## 1．目的

本Phaseの最初の目標は，Windows PCから1個のSTS3215を安全に読み書きし，通信の各層を説明できる状態にすることである．その後，モータ数を

$$
1\rightarrow2\rightarrow5\rightarrow10
$$

と増やし，XL330およびIMUを独立に確認して`RealRobot`へ統合する．公式SDKは正常動作の基準として使うが，最終的にblack boxのまま依存することを目的としない．

## 2．このPhaseが全体のどこに位置するか

本Phaseは，実世界との境界条件を確立する．[Phase 2](02_simulation.md)と交互に進め，単体モータと1 DoF model，複数モータと多関節modelを対応させる．本Phaseから[Phase 3](03_integration.md)へ，次の情報を渡す．

- 実在するmotorの型式，ID，bus，関節割当て
- raw値からSI単位への変換
- mechanical zero，servo zero，positive direction
- 読出し可能なtelemetryと欠損値の扱い
- 実測した通信周期，timeout，応答特性
- 安全limitおよびfail-safeの検証結果

## 3．前提知識

- **UART**：非同期serial通信方式であり，baud rate，data bit，parity，stop bit等の設定一致が必要である．
- **TTL half-duplex**：送信と受信が同じ信号線を共有し，同時には行わない通信方式である．送受信方向の切替と応答待ちが重要になる．
- **Servo ID**：同一bus上のmotorを区別するaddressである．重複すると衝突や誤動作の原因になる．
- **baud rate**：1秒当たりのsymbol数を表す通信設定である．PC，Driver Board，Servoで一致させる．
- **register**：ID，位置，温度等を格納するServo内部のaddress付き領域である．addressとdata幅は公式資料で確認する．
- **packet**：header，ID，length，instruction，address，data，checksum等から成る通信単位である．実際の構造は対象機器の公式仕様を正とする．
- **encoder**：軸位置を数値化するsensorである．raw値をradへ変換し，zeroと符号を適用する．
- **IMU**：加速度計とgyroscope等を組み合わせた慣性sensorである．frame，unit，bias，timestampを明示する必要がある．
- **quaternion**：3次元姿勢を4成分で表す表現である．成分順序と「どのframeからどのframeへの回転か」を固定しなければならない．

## 4．使用するハードウェア・ソフトウェア

### 確定事項

| 区分 | 対象 | 数量・仕様 | 初期用途 |
|---|---|---|---|
| PC | Windows PC | 1 | 直接制御，logging |
| Servo | STS3215 | 12個 | 主に脚部 |
| Driver | Seeed Bus Servo Driver Board for XIAO v1.0 | 2枚 | STS3215 TTL bus |
| 電源 | SO-101付属AC adapter | 5 V，4 A | 初期単体試験 |
| Servo | XL330-M077 | 2個 | 将来の頭部等 |
| Servo | XL330-M288 | 2個 | 将来の頭部等 |
| Controller | ROBOTIS OpenRB系board | 所有 | XL330系候補 |
| IMU | M5Stack ATOM ESP32-PICO系，MPU系IMU | 1系統 | USB接続sensor node |
| MCU | NUCLEO-F303K8 | 所有 | 当面使用しない |

STS3215の想定内訳はC001 1:345 ×7，C044 1:191 ×2，C046 1:147 ×3である．これは現物ラベル確認前の情報であり，最終的には実機確認を優先する．softwareはPython，仮想環境，`pyserial`，Git，Feetech公式SDKを使用候補とする．versionは試験時に記録する．

## 5．システム構成

初期のSTS3215単体構成は次のとおりである．電力経路とdata経路を混同しない．接続の極性，許容電圧，board側の給電方法は通電前に公式資料と現物表示で照合する．

```text
Data:   Windows PC ──USB──> Seeed Driver ──TTL half-duplex──> STS3215
Power:  5 V / 4 A ────────> Seeed Driver / Servo power path
Safety: AC disconnect or accessible power switch + PC torque-disable command
```

拡張時の現時点の設計案は，Bus Aを左脚，Bus Bを右脚に割り当てる構成である．通信帯域，配線，障害範囲を左右で分離できる一方，最終割当ては実配線とcycle計測後に決定する．XL330系はSTS3215系と電源・通信を分離して扱う．

## 6．作業手順

### Step 1：現物inventoryを確定する

12個のSTS3215について，serial識別子，label上の型式，減速比，現在ID，外観，仮の用途を記録する．同様にDriver Board，XL330，ATOM，電源，cableを記録する．これは，同じ外観の異仕様motorを取り違えず，試験結果を個体へ結び付けるためである．

**確認方法**：現物写真またはlabel転記と一覧を照合する．想定内訳との差分を残す．IDが読めない段階では「未確認」とし，推測値を入れない．

### Step 2：安全計画と停止手段を準備する

motorを接続する前に，作業台を片付け，linkまたはhornを外せる場合は外し，Servoを固定する．電源遮断手段を手の届く位置へ置く．software上のtorque disable手順と，それが効かない場合の物理遮断手順を決める．

**確認方法**：未通電状態で停止操作を模擬し，操作者が即時に電源を切れることを確認する．試験者，監視者，危険範囲を実験記録へ書く．

### Step 3：Driver Boardをmotorなしで認識させる

2枚のSeeed Driver Boardを1枚ずつUSB接続し，Windows Device Managerの「ポート（COMとLPT）」で接続前後の差分を確認する．boardの物理labelとCOM portを対応付ける．motorなしで行う理由は，USB認識の問題とServo busの問題を分離するためである．

**確認方法**：各boardが個別のCOM portとして現れ，抜線で対応するportが消えることを確認する．port名，driver version，USB位置を記録する．COM番号は環境依存であり固定値ではない．

### Step 4：再現可能なPython環境を用意する

Python，仮想環境，`pip`，`pyserial`，Gitを準備し，versionと依存packageを記録する．Feetech公式SDKは基準動作を得るため別途用意する．SDKの導入方法や対応OSは実施時点の公式資料で確認する．

**確認方法**：仮想環境内でPythonと`pyserial`をimportでき，対象COM portをopen・closeできることをmotorなしで確認する．環境構築記録から再作成できることを確認する．

### Step 5：STS3215を1個だけ接続する

電源OFFを確認してから，極性，connector向き，電圧を確認し，1個だけ接続する．初回は無負荷または機械的干渉のない状態とする．複数接続しない理由は，誤ID，過電流，配線不良の影響範囲を1個に限定するためである．

**確認方法**：通電直後に異臭，異音，異常発熱，予期しない運動がないことを観察する．異常があれば直ちに物理遮断し，原因確認まで再通電しない．

### Step 6：動かさずにtelemetryを読む

公式SDKを用い，port open，ping，Servo ID，present position，voltage，temperature，torque enable状態の順に確認する．最初にGoal Positionを書かない．読出しにより，通信設定と対象機器を運動riskなしで確認できる．

**確認方法**：複数回読出してIDが一定で，positionが静止範囲内，電圧が使用電源と整合し，temperatureが不自然でないことを確認する．単位とregister addressの根拠を併記する．値が対応機種で読めない場合は「非対応」と「通信失敗」を区別する．

### Step 7：現在位置基準の小角度動作を行う

現在位置を$q_0$として，

$$
q_{target}=q_0+\Delta q,\qquad |\Delta q|\leq5^\circ
$$

から開始する．速度は最低付近とし，一度に大きな目標を送らない．絶対HOMEではなく現在位置基準にするのは，zero未校正時の飛びを防ぐためである．

**確認方法**：正負方向を各1回ずつ試し，command，present position，所要時間，異音，通信error，電圧，温度を記録する．往復後にtorque disableが機能することを確認する．

### Step 8：公式SDKとpacketを理解する

正常動作したSDK内部と公式protocol資料を照合し，baud rate，ID，packet header，instruction，address，data，checksum，timeout，送受信方向切替を追跡する．logic analyzer等の使用は提案事項であり，必須ではない．

**確認方法**：ping，register read，register writeの各packetについて，byte列の各fieldを説明し，正常応答とtimeoutを区別できるようにする．推測したaddressやchecksum式を使わず，一次資料または検証結果を根拠として残す．

### Step 9：pyserial最小Driverを設計・検証する

`ping()`，`read_register()`，`write_register()`，`read_position()`，`set_position()`，`disable()`に相当する最小機能を設計する．この文書では実装しない．目的はpacket生成，serial I/O，timeout，error処理，単位変換を自分で説明できることにある．

**確認方法**：同じmotorに対するSDKと自作Driverの読出し結果を比較する．まずpingとreadのみ，次に現在位置近傍の小角度writeを試す．不正checksum，存在しないID，抜線を用いたnegative testで，無限待ちや誤成功がないことを確認する．

### Step 10：raw値をSI単位へ閉じ込める

Servo raw値を物理角度へ変換し，mechanical zero $q_0$と方向$s\in\{-1,+1\}$を適用する．概念式は

$$
q=s\,f(q_{raw}-q_{0,raw})
$$

である．$f$のscale，wrap，範囲は型式別の公式仕様と実測で確定する．raw値はDriverの外へ出さない．

**確認方法**：既知角度または治具による複数点で，commandとread-backのrad値，正方向，zeroを照合する．設定は関節ごとのconfigへ保存し，校正日と個体識別子を記録する．

### Step 11：2枚のbusと複数motorへ段階拡張する

まず1つのbusで2個，次に片脚相当の5個，最後に左右10個へ増やす．各段階でServo ID重複，電源容量，voltage drop，cycle time，timeout，temperatureを評価する．必要に応じてSync Read / Sync Writeを検討するが，最高速度より確実な観測を優先する．

**確認方法**：全motorについて，commanded IDと応答個体が一致すること，1 cycleの時間分布，error率，最低電圧，最高温度を記録する．2枚構成では片側bus障害が反対側へどう伝播するかも確認する．5 V / 4 A電源が10軸運動に十分とは確定していないため，単体試験用という位置付けを維持する．

### Step 12：XL330を単体確認する

STS3215系の基礎が成立した後，XL330-M077を1個だけ接続し，ID，position，velocity，current，voltage，temperatureを確認する．次に現在位置近傍の$\pm5^\circ$を試す．同じ手順でM288を確認し，応答差を記録する．電源・通信仕様はROBOTIS公式資料を実施時に確認し，STS3215系へ直接混在させない．

**確認方法**：各modelの通信設定，operating mode，telemetry，方向，小角度応答を記録する．M077とM288の差を同じ条件で比較する．

### Step 13：IMUを単体確認する

ATOM ESP32-PICO系nodeから，加速度$(a_x,a_y,a_z)$と角速度$(\omega_x,\omega_y,\omega_z)$をUSB serial等でPCへ送る．最初はrawまたは換算済み6軸値を確認し，姿勢推定を同時に完成させようとしない．timestampとframeを値と同じ重要度で扱う．

**確認方法**：静止状態で

$$
\sqrt{a_x^2+a_y^2+a_z^2}\approx g
$$

となること，90°ずつ向きを変えたとき重力成分が想定axisへ移ること，静止gyro biasとsample intervalを記録する．quaternionを追加する場合は成分順序，正規化，frame定義を確認する．

### Step 14：`RealRobot`へまとめる

motorとIMUの個別結果を，共通`RobotState`と`RobotCommand`へ写像する．初期`RobotCommand`は`q_target[]`のみを使用する．取得できないstateは，配列長を変えるのではなく，明示した欠損表現とvalidity情報で扱う．詳細契約は[software_architecture.md](reference/software_architecture.md)を正とする．

**確認方法**：関節順序，rad，rad/s，sensor frame，timestamp，通信statusを共通schemaで記録する．backend固有raw値が共通層へ混入していないことをreviewする．

### Step 15：安全機能を故障注入で検証する

次の安全機能を「実装予定」ではなく，試験可能な振る舞いとして定義する．数値thresholdは実測前にはDecision Pendingとする．

| 機能 | 必要な振る舞い | 代表的な試験 |
|---|---|---|
| joint limit | 範囲外指令を拒否または安全にclampし，記録する | limit直内・直外のcommand |
| velocity limit | 位置変化率または速度指令を制限する | 大step command |
| command rate limit | 突然の大角度指令をramp化または拒否する | 現在位置から遠いtarget |
| startup確認 | 現在位置取得前に駆動指令を許可しない | telemetry欠損でstartup |
| communication timeout | 更新停止時に定義済みsafe actionへ移る | command送信停止 |
| watchdog | software hangやcycle超過を検出する | process停止・遅延注入 |
| torque disable | 全対象へdisableし，結果を確認する | 通常時のdisable |
| emergency stop | PC操作と物理遮断の両方を提供する | 通信正常時・異常時 |

safe actionを「姿勢保持」とするか「torque off」とするかは，機体が組み上がると転倒riskが異なるため，状態別に後で決定する．

## 7．確認方法と記録項目

各試験では，日付，Git commit，hardware configuration，個体ID，配線，電源，software version，baud rate，command値，制限値，sample数，結果，問題，次Actionを残す．少なくとも次のmetricを採る．

- ping成功率と連続失敗数
- read / write latency，cycle timeの平均・最大・分布
- commandとread-back positionの差
- voltageの最小値，temperatureの最大値
- timeoutからsafe actionまでの時間
- emergency stop操作から確認までの時間
- IMU sample interval，静止bias，加速度norm

## 8．完了条件

- 所有hardwareの現物inventoryがあり，想定と実物の差が明記されている．
- 1個のSTS3215でSDK基準動作と自作最小Driverのping，position read，position command，disableが検証済みである．
- zero，方向，raw-to-rad変換が個体・関節ごとに記録されている．
- 1→2→5→10軸の各gateで通信と電源の記録があり，前段未完了のまま増設していない．
- XL330-M077 ×2，M288 ×2をPC側から扱うための独立系が検証済みである．
- IMUのgyro，accelが定義済みframeとunitで取得できる．
- joint limit，velocity limit，command rate limit，startup確認，timeout，watchdog，torque disable，emergency stopの試験記録がある．
- `RealRobot.read_state()`と`send_command()`に相当する共通契約へのmappingが定義されている．

## 9．トラブルシュート

### COM portが現れない

**症状** → USB接続後もportが増えない．  
**考えられる原因** → cableが充電専用，driver未導入，USB port不良，board不良．  
**確認方法** → motorを外し，別のdata cableとUSB portで接続前後を比較する．Device Managerの不明deviceも確認する．  
**対処** → 公式driverを確認し，既知正常cableで再試験する．boardを入れ替えて故障範囲を分離する．

### pingに応答しない

**症状** → portは開くがServo応答がない．  
**考えられる原因** → 電源なし，極性・配線誤り，baud rate不一致，ID不明，送受信方向切替不良．  
**確認方法** → 電源電圧を安全に測り，公式SDKのscan機能と既知設定を使う．TX packetの有無とtimeoutを記録する．  
**対処** → 通電を切って配線を修正し，1個だけで設定候補を絞る．根拠なく全registerへwriteしない．

### 通電直後に急動作する

**症状** → startup時にmotorが大きく動く．  
**考えられる原因** → 古いtarget保持，zero・方向誤り，現在位置取得前の絶対target送信，operating mode不一致．  
**確認方法** → 物理遮断後にcommand logとstartup sequenceを確認する．  
**対処** → 現在位置読出し，limit検査，small delta，torque enableの順序を強制し，無負荷単体へ戻す．

### 複数motorで通信が不安定になる

**症状** → 個数を増やすとtimeoutや誤応答が増える．  
**考えられる原因** → ID重複，電圧降下，bus負荷，cycle過密，connector不良．  
**確認方法** → 直前の安定構成へ戻し，ID，電圧，cycle timeを1要因ずつ比較する．  
**対処** → IDを個別確認し，電源とbusを分離し，通信周期を下げる．Sync機能は基礎通信が安定してから導入する．

### IMUの静止値が不自然である

**症状** → 加速度normが$g$から大きく外れる，gyroが流れる．  
**考えられる原因** → scale・unit誤り，axis mapping誤り，bias，振動，timestamp不良．  
**確認方法** → 6面静止試験，sample interval確認，raw値と換算式の比較を行う．  
**対処** → datasheet上のscaleと実設定を一致させ，bias校正を分離して記録する．

## 10．成果物

- `reference/hardware_inventory.md`の実測更新
- wiring / power diagramとport mapping
- 公式資料に根拠を持つ通信仕様memo
- STS3215，XL330，IMUの単体test log
- raw-to-SI変換，zero，directionのcalibration data
- 1，2，5，10軸の通信性能記録
- 安全機能仕様と故障注入試験結果
- `RealRobot`へのmapping仕様

## 11．次のPhaseへ渡す情報

[Phase 2](02_simulation.md)へ，関節方向，実測可動範囲，初期の速度・応答観測を渡す．[Phase 3](03_integration.md)へ，motor / sensorのdata contract，timestamp，error状態，校正値，通信性能，安全制約を渡す．CAD完成時には個体と関節の対応を[Phase 4](04_cad_integration.md)へ渡す．

## 実行チェックリスト

- [ ] Step 1：現物inventoryを確定した
- [ ] Step 2：停止手段と安全計画を確認した
- [ ] Step 3：2枚のDriver Boardをmotorなしで識別した
- [ ] Step 4：再現可能なsoftware環境を記録した
- [ ] Step 5：STS3215を1個だけ安全に接続した
- [ ] Step 6：運動前のtelemetry読出しを完了した
- [ ] Step 7：現在位置近傍の小角度往復を完了した
- [ ] Step 8：packet構造とtimeoutを説明できる
- [ ] Step 9：自作最小DriverをSDK結果と比較した
- [ ] Step 10：zero，方向，SI変換を校正した
- [ ] Step 11：1→2→5→10軸の各gateを完了した
- [ ] Step 12：XL330の型式別単体試験を完了した
- [ ] Step 13：IMUの静止・方向試験を完了した
- [ ] Step 14：`RealRobot` mappingを確認した
- [ ] Step 15：安全機能を故障注入で検証した

## Phase Completion Criteria

チェック欄の完了だけでは十分でない．第8章の全条件について，第三者が構成と設定を再現できる記録があり，通信異常時にも定義したsafe actionへ移ることを実測で示した時点で，本Phaseを完了とする．
