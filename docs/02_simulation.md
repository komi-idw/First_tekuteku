# Phase 2：MuJoCo Simulation基盤

- Previous: [01_real_hardware.md](01_real_hardware.md)
- Next: [03_integration.md](03_integration.md)
- Overview: [00_project_overview.md](00_project_overview.md)
- Related Reference: [joint_definition.md](reference/joint_definition.md)，[coordinate_system.md](reference/coordinate_system.md)，[software_architecture.md](reference/software_architecture.md)，[experiment_log_template.md](reference/experiment_log_template.md)

## 1．目的

本Phaseでは，MuJoCoとMJCFを一段ずつ理解し，既存MicroduckのMJCFをコピーせずに10 DoF二足modelを構築する．Groundから始め，Free Body，1 DoF Pendulum，Torque Input，PD Servo，`SimulatedMotor`，Single Leg，10 DoF Biped，Virtual IMUの順に進む．CAD完成前はbox，capsule，cylinder等のprimitive geometryを使い，構造とinterfaceを先に検証する．

## 2．このPhaseが全体のどこに位置するか

本Phaseは，[Phase 1](01_real_hardware.md)と並行して，実機を壊さずに運動方程式，controller，関節定義を検証できる環境を作る．1 DoFの実機試験とSimulationを対応させ，片脚・二足への拡張時にも同じjoint orderingを使う．成果物である`MuJoCoRobot`，ideal model，virtual IMUは，[Phase 3](03_integration.md)の共通Interfaceと，[Phase 4](04_cad_integration.md)のCAD置換基準になる．

## 3．前提知識

- **MuJoCo**：多関節機構，contact，actuator，sensorを扱う物理simulation engineである．
- **MJCF**：MuJoCo modelを記述するXML形式である．body，joint，geom，actuator，sensor等を階層的に表す．
- **body**：位置・姿勢・質量特性を持つ剛体frameである．親子関係がkinematic treeを作る．
- **joint**：親bodyに対する子bodyの自由度である．hingeではaxis，range，damping等を定義する．
- **geom**：visualまたはcollisionに用いる形状である．初期はprimitiveを使う．
- **actuator**：jointへ入力を与える要素である．制御入力と物理的な力・torqueの関係を明示する．
- **joint coordinate**：jointの一般化座標$q$である．hingeでは通常radで表す．
- **timestep**：physics solverを進める時間刻みである．controller update intervalと同一とは限らない．
- **PD制御**：位置誤差と速度を用い，$\tau=K_p(q_d-q)-K_d\dot q$でtorqueを作る基本制御である．
- **sensor frame**：sensor値を表現する座標系である．world frameとbody frameを区別する．

## 4．使用するハードウェア・ソフトウェア

- Windows PC
- Pythonと独立した仮想環境
- MuJoCo Python package
- NumPy
- plot作成手段
- text editor，Git，実験記録

package version，MuJoCo version，OS，CPU/GPUは実験記録へ残す．既存Microduck，Open Duck Mini等のmodelは比較・troubleshootに限って参照し，本modelへ無批判にcopyしない．APIやMJCF仕様は実施時点のMuJoCo公式documentationを正とする．

## 5．システム構成

```text
Controller q_target
        │
        ↓
SimulatedMotor / actuator model
        │ torque or actuator input
        ↓
MuJoCo model ──contact── Ground
        │
        ├── q, dq
        ├── virtual gyro / accel
        └── body orientation
        ↓
RobotState in SI units
```

physics timestep，sensor sample，controller update，render updateを区別する．render速度を制御周期の基準にしてはならない．

## 6．作業手順

### Step 1：MuJoCo環境とViewerを確認する

隔離したPython環境へMuJoCoとNumPyを導入し，公式の最小exampleまたは同等のviewerを起動する．この段階では自作modelの問題とinstallationの問題を混ぜない．

**確認方法**：MuJoCo version，Python version，起動手順を記録し，空またはsample sceneが一定時間errorなく進むことを確認する．headless実行が必要かは後で決める．

### Step 2：Groundだけの最小MJCFを作る

`<mujoco>`，`<worldbody>`，`<geom>`の役割を理解し，ground planeだけを表示する．座標系は右手系，$+x$ forward，$+y$ left，$+z$ upを本プロジェクトのconventionとする．

**確認方法**：Viewerでgroundが期待する向きに表示され，model load時のwarningがないことを確認する．modelのlength，mass，angle unit設定を記録する．

### Step 3：Free Bodyを落下させる

空中にboxを1個置き，free jointを用いて重力下で落下させる．gravity，timestep，collision，mass，initial poseの影響を一つずつ観察する．

**確認方法**：boxの高さと速度を時系列に記録し，落下後にgroundと接触することを確認する．timestepだけを変えた比較で結果が極端に破綻しないことを確認する．

### Step 4：1 DoF Pendulumを作る

fixed base，hinge joint，linkからなる最小modelを作る．bodyの原点，joint位置，axis，geom位置の関係を理解する．重力だけで運動させる．

**確認方法**：Pythonから$q$と$\dot q$をSI単位で取得し，初期角度から振れることを記録する．joint axisを可視化または既知姿勢で確認する．energy減衰を入れる場合は，dampingを明示する．

### Step 5：外力torqueを直接与える

hingeへ既知のtorque $\tau$を与え，

$$
\tau\rightarrow\ddot q\rightarrow\dot q\rightarrow q
$$

の関係を観察する．位置Servoを使う前に入力がどこへ作用するかを理解することが目的である．

**確認方法**：正負のconstantまたはpulse torqueで加速度方向がjoint signと一致することを確認する．input，$q$，$\dot q$を同じtimestampで保存する．

### Step 6：理想PD Servoを作る

制御則を

$$
\tau=K_p(q_d-q)-K_d\dot q
$$

とし，$q_d$を入力，$\tau$をactuator入力とする．初期modelではfriction，delay，backlash，saturationを入れない．複雑な非理想性を同時に入れると，基礎的な符号やgainの誤りを切り分けられないためである．

**確認方法**：$q_d=0$で静止すること，正のstepで正方向へ動くこと，gain変更によるriseとdampingの傾向が説明できることを確認する．

### Step 7：1 DoF step responseを記録する

例として$q_d:0^\circ\rightarrow30^\circ$のstepを入力し，target position，actual position，velocity，torqueをplotする．数値はmodelのjoint range内であることを先に確認する．

**確認方法**：rise time，overshoot，settling time，steady-state errorを定義して測る．simulation timeとwall-clock timeを区別し，初期条件とgainを記録する．「収束した」の判定幅と継続時間を事前に決める．

### Step 8：`SimulatedMotor`へ分離する

1 DoFで確認したPD処理を，共通`MotorInterface`へ接続できる`SimulatedMotor`として整理する．`read_position()`，`read_velocity()`，`set_position(q)`，`disable()`に相当する意味を実機側と合わせる．disable時のSimulation挙動は，zero torque等として明示する．

**確認方法**：直接MuJoCo配列を操作するtestとInterface経由のtestが同じ結果になることを確認する．raw indexを上位Controllerへ公開しない．

### Step 9：`MuJoCoRobot`の最小版を作る

`read_state()`と`send_command()`を持つSimulation backendを設計する．初期は1 DoFでよい．state timestampはMuJoCo simulation timeを使い，配列の関節順序を明示する．

**確認方法**：`RobotCommand.q_target`を送り，次stepの`RobotState.q`，`dq`へ一貫して反映されることを確認する．配列長不一致とNaNを拒否するnegative testを設ける．

### Step 10：primitive geometryで片脚5 DoFを作る

次のkinematic chainを作る．

```text
Body
 └─ Hip Yaw
     └─ Hip Roll
         └─ Hip Pitch
             └─ Upper Leg
                 └─ Knee Pitch
                     └─ Lower Leg
                         └─ Ankle Pitch
                             └─ Foot
```

形状はbox，capsule，cylinderに限定する．寸法，質量，inertiaはCAD前の仮定であり，値ごとに仮定と明記する．ここでの目的は最終外観ではなく，topology，joint axis，interfaceの検証である．

**確認方法**：body tree，joint数，DoF数，総質量，初期姿勢をprogramから列挙し，期待値と照合する．

### Step 11：片脚を1軸ずつ検証する

hip yaw，hip roll，hip pitch，knee pitch，ankle pitchを1軸ずつ動かし，他軸はzeroまたは保持とする．各軸で$q=0$，$+30^\circ$，$-30^\circ$を確認する．ただし仮のjoint rangeを超える場合は範囲内の小角度へ置き換える．

**確認方法**：正方向の物理的意味を[関節定義](reference/joint_definition.md)と照合し，各姿勢の画像または数値を残す．joint originとaxisの誤りをvisual meshなしで修正する．

### Step 12：二足10 DoFへ拡張する

片脚の検証完了後に反対脚を追加し，left 5軸，right 5軸の10 DoFとする．単純な文字列置換でmirrorせず，world conventionに対する各axisと正方向を確認する．

**確認方法**：全10軸を1軸ずつ動かし，joint ordering，name，axis，signを表と自動列挙で照合する．左右の同一動作とmirror動作を区別する．

### Step 13：HOME姿勢を定義する

10要素の$\mathbf q_{home}$をconfigへ置く．これは現時点の設計案であり，CAD rangeと実機zero校正後に更新し得る．HOMEは見た目ではなく，joint ordering，unit，安全範囲を伴うdataとして扱う．

**確認方法**：zero状態からrate-limitedにHOMEへ移行し，self-collision，ground penetration，joint limit violationがないことを確認する．実機へ転用する前に実機現在位置との差を検査する．

### Step 14：足裏接触を設定する

footとgroundのfriction，restitution，contact stiffness，contact dampingを設定する．初期段階で数値を過度に追い込まず，不自然な滑りや跳ねがない基準modelを作る．visual geometryとcollision geometryを分けられる構造にする．

**確認方法**：静止接触，軽い落下，水平外力等の条件でpenetration，slip，bounceを観測する．parameter，timestep，solver設定をセットで記録する．

### Step 15：Virtual IMUを追加する

torso bodyへMuJoCo sensorを配置し，angular velocity，linear acceleration，orientationを取得する．Real Hardwareと同じbody frame，unit，quaternion conventionへ変換する．

**確認方法**：静止状態の加速度norm，既知角速度の回転，既知姿勢のquaternionを確認する．重力を含むか除くか，sensor原点の回転加速度を含むかを明記する．

### Step 16：共通ControllerでHOME保持する

最初のcontrollerはWalkingではなく，$\mathbf q_d=\mathbf q_{home}$を与えるHold Position Controllerとする．同じcontroller contractを`MuJoCoRobot`と将来の`RealRobot`に接続する．

**確認方法**：初期姿勢を複数変え，収束，limit，torque，contactを記録する．異常command，古いcommand，更新停止を模擬し，Simulationでも共通safe behaviorを確認する．

## 7．確認方法と記録項目

各Stepでmodel file，Git commit，MuJoCo / Python version，timestep，solver，initial state，controller interval，gain，random seed，実行時間，結果plot，warningを記録する．定量確認の最低項目は次である．

- model load時のwarning / error
- DoF数，body数，総質量，joint range
- $q$，$\dot q$，$\tau$，$q_d$のtime series
- step responseのrise，overshoot，settling，steady-state error
- contact penetration，slip，bounce
- sensor sample interval，accel norm，quaternion norm
- physics stepとcontroller stepの実時間比

## 8．完了条件

- Ground，Free Body，1 DoF Pendulumを自作MJCFで再現できる．
- torque入力から$q,\dot q$までを説明し，PD step responseを記録できる．
- `SimulatedMotor`と`MuJoCoRobot`が共通contractに接続できる．
- primitive geometryの片脚5 DoFを1軸ずつ検証済みである．
- 10 DoF二足modelのjoint ordering，axis，signがReferenceと一致する．
- 足裏接触とVirtual IMUが定義済みframe・unitで機能する．
- Hold Position Controllerを使い，初期条件を含む再現可能なlogがある．
- 既存robot repositoryのMJCFを本modelの代替としてcopyしていない．

## 9．トラブルシュート

### modelがloadできない

**症状** → XML parse errorまたはmodel compile errorが出る．  
**考えられる原因** → tag階層，name重複，単位，参照先，inertia不正．  
**確認方法** → 最後に動いた最小modelとの差分を小さくし，error位置と公式schemaを照合する．  
**対処** → 1要素ずつ追加し，warningを放置しない．

### jointが想定外の方向へ動く

**症状** → 正commandで逆方向または別axisに回る．  
**考えられる原因** → axis vector，body frame，joint origin，左右mirrorの誤り．  
**確認方法** → 他軸を固定し，小角度の正負commandとframe表示で確認する．  
**対処** → Referenceの物理的な正方向を基準にaxisを修正し，Controller側で場当たり的に符号反転しない．

### PD制御が発散・振動する

**症状** → positionが収束せず，torqueが大きく振動する．  
**考えられる原因** → sign誤り，過大gain，timestep，damping不足，unit誤り．  
**確認方法** → $q_d-q$，$\dot q$，$\tau$をplotし，低gain・小stepへ戻す．  
**対処** → signとunitを先に直し，$K_p$，$K_d$，timestepを1要因ずつ調整する．

### 足が滑る・跳ねる

**症状** → 静止姿勢でもslip，bounce，penetrationが大きい．  
**考えられる原因** → friction，contact parameter，timestep，質量・inertia，collision形状．  
**確認方法** → 単純foot単体testへ戻し，接触数とforceを記録する．  
**対処** → collisionを単純化し，solverとtimestepを含めて1項目ずつ調整する．

### Virtual IMUが実機conventionと合わない

**症状** → 静止重力axisや回転方向が逆になる．  
**考えられる原因** → body/world frame混同，quaternion順序，重力の扱い，sensor pose．  
**確認方法** → 既知の静止6面姿勢と単軸回転を用いる．  
**対処** → sensor境界で明示変換し，共通`RobotState`のconventionを変更しない．

## 10．成果物

- Ground，Free Body，1 DoF，片脚，10 DoFの各MJCF
- torque入力，PD Servo，`SimulatedMotor`，`MuJoCoRobot`の設計・test
- 1 DoF step response plotとmetric
- joint-by-joint姿勢確認記録
- HOME姿勢config
- contact parameterとtest log
- Virtual IMU mapping仕様
- 共通ControllerによるHOME保持log

## 11．次のPhaseへ渡す情報

[Phase 3](03_integration.md)へ，`MuJoCoRobot`のdata contract，simulation timestamp，joint ordering，$q,\dot q$，actuator input，Virtual IMU，baseline logを渡す．[Phase 4](04_cad_integration.md)へ，ideal modelのtopology，仮定したgeometry・mass・inertia，CAD置換前のregression testを渡す．

## 実行チェックリスト

- [ ] Step 1：MuJoCo環境とViewerを確認した
- [ ] Step 2：GroundだけのMJCFを作成した
- [ ] Step 3：Free Bodyの落下と接触を記録した
- [ ] Step 4：1 DoF Pendulumから$q,\dot q$を取得した
- [ ] Step 5：正負torqueの作用を確認した
- [ ] Step 6：理想PD Servoを確認した
- [ ] Step 7：step responseを定量評価した
- [ ] Step 8：`SimulatedMotor`へ分離した
- [ ] Step 9：最小`MuJoCoRobot`を確認した
- [ ] Step 10：primitive片脚5 DoFを作成した
- [ ] Step 11：片脚を1軸ずつ確認した
- [ ] Step 12：二足10 DoFを全軸確認した
- [ ] Step 13：HOME姿勢を定義した
- [ ] Step 14：足裏接触を確認した
- [ ] Step 15：Virtual IMUを確認した
- [ ] Step 16：共通ControllerでHOME保持した

## Phase Completion Criteria

第8章の全条件に対して，model，設定，version，初期条件，plotを含む再現可能な記録が存在し，全10軸とVirtual IMUがReferenceの座標・単位・順序に一致した時点で，本Phaseを完了とする．
