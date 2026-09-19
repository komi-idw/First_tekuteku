# Coordinate System and Units

- Previous: [joint_definition.md](joint_definition.md)
- Next: [software_architecture.md](software_architecture.md)
- Overview: [../00_project_overview.md](../00_project_overview.md)
- Related Reference: [glossary.md](glossary.md)

## 1．基本座標系

本プロジェクトは右手系を用い，robotが基準姿勢で立つときのbase conventionを次とする．

$$
+x:\ \text{forward},\qquad +y:\ \text{left},\qquad +z:\ \text{up}
$$

これはSimulation，CAD変換，共通state，説明図の基準である．各sensorやServo固有frameは境界でこのconventionへ変換する．

## 2．frame命名

| Frame | 意味 | 状態 |
|---|---|---|
| `world` | Simulationまたは実験環境に固定したframe | $+z$ upを確定 |
| `base` / `torso` | torsoに固定したrobot基準frame | 原点位置はCAD後に確定 |
| `imu` | IMU sensor固有frame | mounting pose未決定 |
| link frames | 各linkに固定したframe | CAD後に確定 |
| joint frames | joint centerとaxisを表すframe | CAD後に確定 |

`base`と`torso`を同一frame名に統一するか，別frameとして固定変換を持つかはDecision Pendingである．実装前に一方を選び，曖昧なaliasを残さない．

## 3．SI単位

| Quantity | Unit | Symbol example |
|---|---|---|
| angle | rad | $q$ |
| angular velocity | rad/s | $\dot q,\omega$ |
| angular acceleration | rad/s² | $\dot\omega$ |
| position / length | m | $\mathbf p$ |
| linear velocity | m/s | $\mathbf v$ |
| linear acceleration | m/s² | $\mathbf a$ |
| mass | kg | $m$ |
| force | N | $\mathbf F$ |
| torque | N m | $\tau$ |
| inertia | kg m² | $\mathbf I$ |
| time | s | $t$ |
| temperature | °C | diagnostic only |
| voltage | V | diagnostic only |

degree，mm，g，Servo raw等は入力資料やUIでは使用し得るが，共通計算へ入る前に変換する．log metadataにはunitを明記する．

## 4．回転とquaternion

quaternionの成分順序は，実装採用libraryを確認後に`[w,x,y,z]`または`[x,y,z,w]`のいずれかへ確定する．現時点では未決定であり，配列だけを見て推測してはならない．あわせて，orientationが「worldに対するbodyの姿勢」か「bodyからworldへの回転」かを確定する．

共通contract確定時には次を必須metadataとする．

- component order
- active / passive rotation
- source frameとtarget frame
- normalization条件
- quaternionの$q$と$-q$が同じ姿勢を表すことへの連続化方針

Euler角は表示・debugに使えるが，共通stateの基本表現はquaternionとする．

## 5．IMU convention

- `gyro[3]`は共通IMUまたはbase frame表現のrad/sとする．どちらを採るかはmounting確定時に決める．
- `accel[3]`はm/s²とする．specific forceかworld linear accelerationかを明示する．Real IMUとMuJoCo sensorの重力扱いを同一視しない．
- `orientation[4]`は第4章で確定したquaternion contractに従う．
- sample timestamp，frame transform，bias calibrationを値と同時に記録する．

## 6．変換の責務

```text
Device / CAD native convention
             │
             ↓ boundary conversion
First_tekuteku common convention
             │
             ↓
Controller / Logger / Evaluation
```

Controller内部で特定motorだけ符号反転する，plot時にdegreeへ直して元unitを失う等の場当たり変換を禁止する．変換は設定とtestを持つ境界moduleへ集約する．

## 7．検証姿勢

- 原点姿勢：全joint $q=0$の物理的意味を確認する．
- 単軸正回転：各jointの小さな$q>0$を確認する．
- IMU六面静止：重力成分とaxisを確認する．
- 単軸回転：gyro signとorientation変化を確認する．
- 既知寸法：CAD / mesh / MJCFのm換算を確認する．

## Completion Criteria

全frameの原点・axis，quaternion contract，IMUの重力扱いが決定され，Real / Sim / CADの既知姿勢testで同じ結果へ変換できた時点で本定義を確定する．
