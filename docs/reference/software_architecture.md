# Software Architecture

- Previous: [coordinate_system.md](coordinate_system.md)
- Next: [experiment_log_template.md](experiment_log_template.md)
- Overview: [../00_project_overview.md](../00_project_overview.md)
- Related Reference: [joint_definition.md](joint_definition.md)，[coordinate_system.md](coordinate_system.md)，[decision_pending.md](decision_pending.md)

## 1．設計目標

同一ControllerからSimulationとReal Hardwareを切り替えられる構造を作る．共通化するのは，状態と指令の意味，単位，順序，時刻，error表現である．device固有の能力差やfaultを隠すことではない．学習目的を損なう過度な抽象化を避け，1 DoFの最小実装から必要に応じてrefactoringする．

```text
Controller
    │
    ↓
RobotInterface
 ├─ MuJoCoRobot
 │    └─ SimulatedMotor[]
 └─ RealRobot
      ├─ STS3215Motor[]
      ├─ XL330Motor[]
      └─ IMU
```

## 2．基本control loop

```python
state = robot.read_state()
command = controller.update(state)
robot.send_command(command)
```

実際のloopでは，state validity，timestamp，deadline，safety statusを確認する．上記は責務を示す最小形であり，error処理を省略してよいという意味ではない．

## 3．RobotState contract

| Field | Shape | Unit | 必須性 | 意味 |
|---|---:|---|---|---|
| `time` | scalar | s | 必須 | stateが表すmonotonic time |
| `q` | N | rad | 必須 | joint orderingに従う位置 |
| `dq` | N | rad/s | 必須 | 同じorderingの速度 |
| `gyro` | 3 | rad/s | 基盤完成時必須 | 定義済みsensor frameの角速度 |
| `accel` | 3 | m/s² | 基盤完成時必須 | 定義済みsensor frameの加速度 |
| `orientation` | 4 | dimensionless | 基盤完成時必須 | 定義済みquaternion |
| `motor_temperature` | N | °C | 実機診断 | 未対応要素はvalidityで示す |
| `motor_voltage` | N | V | 実機診断 | 各motorまたはbusの電圧 |
| `motor_current_or_load` | N | device変換後の物理単位優先 | optional | model差をmetadataに示す |
| `communication_status` | structured | — | 実機必須 | age，timeout，error等 |

Nはactive joint countであり，初期は10，将来は14を想定する．値がない場合に配列長を変えない．欠損表現，validity mask，error codeは実装前に確定する．

## 4．RobotCommand contract

| Field | Shape | Unit | 初期利用 | 方針 |
|---|---:|---|---|---|
| `q_target` | N | rad | 使用 | 初期の唯一のcontrol target |
| `dq_target` | N | rad/s | 将来 | 意味とbackend supportを定義して追加 |
| `torque_target` | N | N m | 将来 | hardware能力と安全設計後に追加 |
| `torque_limit` | N | N m | 将来 | device limitへのmappingを定義して追加 |

commandには生成時刻またはsequenceを持たせ，stale commandを検出する案を採用する．具体schemaは実装時のDecision Pendingである．NaN，Inf，shape不一致，limit外を送信前に拒否する．

## 5．RobotInterface責務

概念methodは次である．

- `read_state()`：共通unit・ordering・frameへ変換した最新stateとstatusを返す．
- `send_command(command)`：validate，limit，rate limit後にbackendへ送る．
- `disable()`：可能な範囲でactuationを無効化し，結果statusを返す．
- lifecycle：connect，initialize，close等は実装時に明示する．

`RealRobot`は複数busとIMUをまとめる．partial readを成功扱いで隠さず，各subsystemのage・validityを表す．`MuJoCoRobot`はphysics stepの責務を持つか，外部loopがstepするかを一意に決める．

## 6．MotorInterface責務

```text
MotorInterface
 ├─ SimulatedMotor
 ├─ STS3215Motor
 └─ XL330Motor
```

最小能力はposition read，velocity read，position target，disableである．ただし，STS3215とXL330のtelemetry・operating mode差を無理に同一methodへ押し込めず，共通最小能力とbackend diagnosticsを分ける．Servo raw，register address，packetはDriver内部に閉じ込める．

## 7．構成情報

構成情報には次を持たせる．形式は将来のYAML等を想定するが，本作業範囲では実装しない．

- joint nameとordering
- motor Asset ID，Servo ID，bus
- zero raw，direction，scale
- mechanical / software limit
- HOME pose
- communication setting
- IMU frame transform
- backend選択
- actuator parameter

secretやmachine固有COM番号と，project共通parameterを分離する．実験logには使用したconfig snapshotまたはhashを残す．

## 8．安全層

安全は一層へ集中させず，次の防御を重ねる．

1. command生成時のController制約
2. RobotInterfaceでのshape，finite，joint，velocity，rate検査
3. Driverでのdevice rangeとtimeout
4. watchdogとemergency stop
5. 物理的な電源遮断

Simulation backendでも同じinvalid command testを行う．実機固有のtemperature，voltage，communication faultは共通Safety Supervisorへ通知する．

## 9．logging

共通logは，stateとcommandを同じ関節順序で保存する．最低限，time，backend，q，dq，q_target，gyro，accel，orientation，validity，error statusを持つ．metadataとしてcommit，config，hardware inventory，software version，experiment IDを結び付ける．CSVは初期の可搬形式候補であるが，schema versionを必ず持たせる．

## 10．禁止するcoupling

- ControllerがCOM port，Servo ID，registerを知ること
- ControllerがMuJoCo joint indexを直接知ること
- plot script内でjoint signを修正すること
- backendごとに異なるjoint orderingを許容すること
- `None`やzeroを区別せず欠損sensor値として使うこと
- Viewer updateをcontrol timingとして使うこと

## 11．architecture検証

- contract test：同じcommand / state fixtureを各backendへ適用する．
- schema test：shape，unit metadata，joint nameを検査する．
- fault test：timeout，partial failure，NaN，limit外，stale commandを注入する．
- regression test：ideal，CAD，actuator modelで同じAPI testを実行する．

## Completion Criteria

共通contractが文書化され，全backendが同じcontract testを通り，backend固有情報がControllerへ漏れず，faultが隠蔽されない時点でarchitecture基盤完成とする．
