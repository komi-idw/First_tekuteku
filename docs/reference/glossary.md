# Glossary

- Previous: [source_traceability.md](source_traceability.md)
- Next: [../README.md](../README.md)
- Overview: [../00_project_overview.md](../00_project_overview.md)
- Related Reference: [coordinate_system.md](coordinate_system.md)，[software_architecture.md](software_architecture.md)

| Term | Definition in this project |
|---|---|
| actuator | control入力を物理的なforceまたはtorqueへ変換する要素である．Servo本体とSimulation上のmodelを含む． |
| Asset ID | hardware個体を永続的に追跡するproject内識別子である．変更可能なServo IDとは別である． |
| backend | `RobotInterface`の接続先実装である．`MuJoCoRobot`または`RealRobot`を指す． |
| backlash | 回転方向を反転した際，入力変化が出力へ伝わらない遊びである． |
| baud rate | serial通信のsymbol rateである．通信する全機器で一致が必要である． |
| CAD | Computer-Aided Designである．geometryだけでなく，joint位置やmass propertyのsourceとなる． |
| center of mass（CoM） | 質量分布を代表する重心位置である．frameと基準点を伴って記録する． |
| collision geometry | contact計算に用いる形状である．visual meshより単純化することが多い． |
| command rate limit | 連続するcommandの変化量を制限し，突然の大角度指令等を防ぐ機能である． |
| Controller | `RobotState`を受け取り`RobotCommand`を生成する上位処理である．backend固有通信を扱わない． |
| coordinate frame | 位置・方向を表す基準となる原点とaxisの組である． |
| Domain Randomization | Simulation parameterを範囲内で変動させ，policyのmodel誤差耐性を高める方法である． |
| encoder | motor軸等の位置を計測し，raw値として返すsensorである． |
| emergency stop | 異常時にactuationを速やかに停止させる手段である．software指令と物理遮断を区別する． |
| half-duplex | 同じ通信路で送信と受信を時間分割する方式である． |
| HOME | 通常動作の基準として選ぶjoint姿勢である．mechanical zeroとは限らない． |
| IMU | 加速度計とgyroscope等から慣性情報を得るsensor unitである． |
| inertia tensor | 剛体の回転慣性を表す対称tensorである．kg m²，基準点，frameが必要である． |
| joint coordinate | joint自由度を表す一般化座標$q$である．回転jointはradを用いる． |
| joint limit | jointの許容角度範囲である．mechanical，CAD，software運用rangeを区別する． |
| joint ordering | 配列`q[]`等の各indexとjoint nameの対応順序である．全層で共通にする． |
| latency | commandまたはmeasurementが伝わるまでの遅れである． |
| LIPM | Linear Inverted Pendulum Modelであり，二足の重心運動を単純化したmodelである． |
| MJCF | MuJoCo modelを記述するXML形式である． |
| MotorInterface | motorの共通最小操作を表す境界である．SimulatedMotor，STS3215Motor，XL330Motorが候補である． |
| MPC | Model Predictive Controlであり，予測modelを用いて制約付き最適化を反復する制御である． |
| MuJoCoRobot | MuJoCoを用いる`RobotInterface` backendである．原典の`SimulationRobot`に相当する． |
| PD Servo | position errorとvelocityからtorqueを作る比例微分制御modelである． |
| PPO | Proximal Policy Optimizationであり，RL algorithm候補の一つである．採用は未決定である． |
| quaternion | 3次元姿勢を4成分で表す方法である．成分順序と回転方向の定義が必要である． |
| RealRobot | STS3215，XL330，IMU等をまとめる実機側`RobotInterface` backendである． |
| Reference Implementation | 設計比較，動作確認，troubleshootに使う既存実装である．copyして本実装を置き換える対象ではない． |
| RobotCommand | Controllerからrobotへ渡す共通指令である．初期は`q_target[]`を使用する． |
| RobotInterface | `read_state()`と`send_command()`を中心とするrobot共通境界である． |
| RobotState | time，q，dq，gyro，accel，orientation等をまとめた共通状態である． |
| Servo ID | 同一bus上のServoをaddress指定する変更可能なIDである． |
| SI units | m，kg，s，rad，N等を用いる国際単位系である．Servo rawは境界で変換する． |
| Sim-to-Real | Simulationで開発したControllerまたはpolicyを実機へ移す過程である． |
| system identification | 実機の入出力dataから応答特性やmodel parameterを求める作業である． |
| timestep | physics simulationの時間刻みである．control / communication周期と区別する． |
| torque disable | motorの駆動torqueを無効化する操作である．実機状態によっては転倒を招くため，safe action設計が必要である． |
| TTL | logic-level serial信号の電気方式を指す．許容電圧と配線は機器仕様で確認する． |
| UART | start / stop bitを用いる非同期serial通信方式である． |
| validity | state要素が新鮮で有効かを示す情報である．zero値と欠損を区別する． |
| visual mesh | 表示用の形状dataである．collisionやinertiaのsourceと自動的に同一ではない． |
| watchdog | update停止やsoftware異常を監視し，定義済みsafe actionを起動する仕組みである． |
| ZMP | Zero Moment Pointであり，床反力momentの関係から歩行安定性を扱う概念である． |

## 表記規則

- product名，class名，field名は必要に応じて英字表記を維持する．
- `Simulation`は物理simulation全体，`MuJoCoRobot`は共通Interfaceの具体backendを指す．
- `Real Hardware`は物理機器側の領域，`RealRobot`はそのsoftware backendを指す．
- 「完了」はchecklist消化ではなく，各文書の`Completion Criteria`達成を意味する．

## Completion Criteria

本文で使用する専門用語が初出説明または本書へのlinkを持ち，同じ用語が複数の意味で使われていないことを完了条件とする．
