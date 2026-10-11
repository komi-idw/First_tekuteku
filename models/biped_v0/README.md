# biped_v0 MJCF（CAD由来・強化学習テスト用）

Fusionの試作アセンブリ `biped_v0` から生成した10 DoFのMJCFである．[Phase 4](../../docs/04_cad_integration.md)の手順に沿ってCADから書き出したが，ここに含まれる数値の多くは**仮値（PROVISIONAL）**である．強化学習のパイプラインを試すためのモデルとして使い，最終値として扱わない．寸法を改良した版は別のCAD・別のディレクトリで管理する予定である．

## 1．ファイル

| Path | 内容 |
|---|---|
| `scene.xml` | 床・ライト付きのscene．simulationとRLではこのファイルを読む |
| `biped_v0.xml` | ロボット本体（**生成物．手で編集しない**） |
| `meshes/*.stl` | visual mesh（body frame，m） |
| `cad_export/biped_v0_v4_properties.json` | Fusionから書き出した生データ（CAD world frame，mm / g / g·mm²）．質量・CoM・慣性・関節原点と軸 |
| `cad_export/meshes_cad/*.stl` | Fusionから書き出したmesh（CAD world frame，mm，as-built姿勢） |
| `cad_export/joint_axis_mapping.json` | CAD上の関節軸とMJCF上の関節軸の対応 |
| `../../tools/cad_to_mjcf.py` | `cad_export/` → `biped_v0.xml` + `meshes/` の変換スクリプト |
| `../../tests/test_biped_v0_model.py` | 回帰チェック |

```bash
uv sync --extra sim
uv run --extra sim python tools/cad_to_mjcf.py            # 再生成
uv run --extra sim python tests/test_biped_v0_model.py    # 確認
uv run --extra sim python -m mujoco.viewer --mjcf models/biped_v0/scene.xml
```

meshは合計で約2.6 MBなので，Git LFSは使っていない．

## 2．Source

| Item | Value |
|---|---|
| CAD | Fusion `nisoku_hokou_challenge / biped_v0` **v4**（2026-10-11） |
| Servo CAD | `sts3215` v3．公称質量 55 g（メーカー公称 55±1 g）になるよう密度を 1.519 g/cm³ に設定 |
| 3D printed parts | 材料 `PLA_print`，密度 0.80 g/cm³（PLA中実 約1.24 g/cm³ にinfillを見込んだ仮値） |
| Mesh | Fusion TriangleMeshCalculator，Low quality |
| 総質量 | **0.635 kg**（サーボ 10 × 55 g + PLA 約 85 g） |

Fusion側のjoint名は本リポジトリの名前（`left_hip_yaw` …）に変更済みである．componentはロボット自身の向きで `_L`（CAD +X 側）/ `_R`（CAD −X 側）に付け直した．

## 3．座標系と単位の変換

[coordinate_system.md](../../docs/reference/coordinate_system.md)の +x forward，+y left，+z up に合わせる．

| Robot | CAD (Fusion) |
|---|---|
| +x（前） | +Z |
| +y（左） | +X |
| +z（上） | +Y |

$\mathbf p_{robot} = R\,\mathbf p_{CAD}$，$R=\begin{bmatrix}0&0&1\\1&0&0\\0&1&0\end{bmatrix}$（$\det R=+1$），$\mathbf I_{robot}=R\,\mathbf I_{CAD}R^T$．単位は mm→m，g→kg，g·mm²→kg·m² に変換する．

- 前方向はユーザー確認済みである（足裏の長い側がつま先．膝は後ろ向きに曲がる鳥脚型）．
- 慣性は「CoMまわり」の値を使う．Fusionの主慣性・主軸から組み立て，原点まわりのXYZ慣性と平行軸の定理で照合している（変換スクリプト内でassert）．
- `torso` frameの原点はCADの原点（main_body中心付近）とした（DP-019 仮）．IMU siteもここに置いた（DP-016 仮）．

## 4．Link

| MJCF body | Fusion component | mass [g] |
|---|---|---:|
| `torso` | `main_body`（hip yaw サーボ ×2 含む） | 134.6 |
| `{left,right}_hip_yaw_link` | `yaw_to_roll_body_{L,R}`（hip roll サーボ含む） | 61.4 |
| `{left,right}_hip_roll_link` | `roll_to_pitch_body_{L,R}` | 2.0 |
| `{left,right}_thigh_link` | `pitch_to_knee_body_{L,R}`（hip pitch・knee サーボ含む） | 114.2 |
| `{left,right}_shin_link` | `ankle_{L,R}`（ankle サーボ含む） | 57.3 |
| `{left,right}_foot_link` | `foot_{L,R}` | 15.4 |

**モデルに入っていないもの**：battery，制御基板，IMU基板，cable，ネジ類（DP-005，DP-015）．実機は 0.635 kg より重くなる．学習時は torso 質量とCoMのdomain randomizationを推奨する（例：torso +0〜200 g）．

## 5．Joint

ordering は [joint_definition.md](../../docs/reference/joint_definition.md) の index 0〜9 と同じである（`qpos[7:17]`，`qvel[6:16]`，`ctrl[0:10]`）．

| Index | Joint | Axis (robot) | CAD軸との符号 | Range [rad]（仮） |
|---:|---|---|---:|---|
| 0 | `left_hip_yaw` | +z | −1 | −0.5 〜 0.5 |
| 1 | `left_hip_roll` | +x | +1 | −0.4 〜 0.4 |
| 2 | `left_hip_pitch` | +y | −1 | −1.0 〜 1.0 |
| 3 | `left_knee_pitch` | +y | +1 | −1.3 〜 0.6 |
| 4 | `left_ankle_pitch` | +y | +1 | −1.0 〜 1.0 |
| 5 | `right_hip_yaw` | +z | −1 | −0.5 〜 0.5 |
| 6 | `right_hip_roll` | +x | +1 | −0.4 〜 0.4 |
| 7 | `right_hip_pitch` | +y | +1 | −1.0 〜 1.0 |
| 8 | `right_knee_pitch` | +y | −1 | −1.3 〜 0.6 |
| 9 | `right_ankle_pitch` | +y | −1 | −1.0 〜 1.0 |

- **正方向（DP-009 提案）**：左右とも robot frame の右手系で yaw +z，roll +x，pitch +y とした．hip pitch を正にすると脚は後ろへ振れ，hip roll を正にすると足は +y（左）へ動く．「CAD軸との符号」はFusionのas-built jointの正方向との関係で，実機のservo `direction` を校正するときの参考にする．
- **zero（DP-013）**：$q=0$ はCADのas-built姿勢である．この姿勢では hip pitch 20°，knee 40° 曲がっている．膝は $q_{knee}=+0.698$ rad で伸び切るので，上限は 0.6 rad とした．
- **range（DP-010）**：CAD干渉・cable・機械stopは**未確認**の仮値である．`ctrlrange` も同じ値にしている．
- 屈む姿勢の例：hip pitch +0.3，knee −0.6，ankle +0.3（足裏を水平に保つには ankle = −(hip + knee)）．

## 6．Actuator（すべて仮値．DP-002，DP-012，Phase 3）

| Parameter | Value | 根拠 |
|---|---|---|
| type | MuJoCo `position`（目標角 $q_{target}$ [rad] を入力） | `RobotCommand.q_target` と同じ意味 |
| `kp` / `kv` | 8.0 N·m/rad / 0.2 N·m·s/rad | 仮値．実機のstep response同定で置き換える |
| `forcerange` | ±1.9 N·m | STS3215 C001（1:345）のstall 19.5 kgf·cm @7.4 V |
| `armature` / `damping` / `frictionloss` | 0.005 / 0.05 / 0.03 | 仮値 |

- 在庫には C044（1:191）と C046（1:147）も含まれ，どの関節に割り当てるかは未決定である（DP-001，DP-002）．減速比が小さい型はtorqueが小さく，速度が大きい．
- **速度上限はMJCFで表現していない**．無負荷速度は 0.238 s/60° @6 V（約 4.4 rad/s）である．RL側で action の rate limit を入れることを推奨する．
- 5 V / 4 A adapter で駆動すると，torque は上表より下がる（DP-005）．

## 7．Contact と Sensor

- collision は簡略形状である．torso と hip yaw link は box，thigh と shin は関節間方向に合わせた box，足は厚さ 5 mm の sole box（friction 0.8，仮値）．visual mesh（group 2）と collision（group 3）は分けてある．
- home姿勢では自己干渉なし．左右の脚どうしの衝突は有効である．
- 床のgeomは `scene.xml` にある．

| Sensor | Dim | 内容 |
|---|---:|---|
| `imu_gyro` | 3 | torso の角速度 [rad/s]，site frame |
| `imu_accel` | 3 | 加速度 [m/s²]．MuJoCoの accelerometer は静止時に +9.81 z を返す（specific force．DP-018） |
| `imu_quat` | 4 | world に対する torso の姿勢．MuJoCoの順序 `[w, x, y, z]`（DP-017） |
| `imu_linvel` | 3 | torso の線速度（site frame）．実機では直接測れないので privileged 観測として扱う |
| `{left,right}_foot_touch` | 1 | 足裏の法線力の合計 [N] |

## 8．Simulation設定

- `timestep` 0.002 s（500 Hz），`implicitfast`．control period は未決定である（DP-007）．
- keyframe `home`：base高さ 0.2145 m，全関節 0（足裏が床に接する）．
- 確認済み（`tests/test_biped_v0_model.py`）：
  - joint・actuator の名前と順序
  - 総質量がCADと一致すること
  - meshのスケールと左右
  - home で足裏が床に接し，干渉がないこと
  - 関節の正方向
  - home で10 s 自立すること（足裏の力の合計 ≒ 体重）
  - 屈んだ姿勢を torque 上限内で保持できること
- 参考値：random action 20 episode で NaN なし．CPU 1コアで約 38,000 step/s（実時間の約 76 倍）．

## 9．未決定のまま仮に置いた値

| DP | 内容 | このモデルでの扱い |
|---|---|---|
| DP-002 / DP-012 | servo の割当てと torque | 全関節を C001 相当として扱う |
| DP-005 / DP-015 | battery と最終質量 | battery・電装なし |
| DP-009 | 関節の正方向 | 右手系 yaw +z / roll +x / pitch +y |
| DP-010 | joint limit | 上の表の仮値 |
| DP-013 | zero と HOME | CAD as-built 姿勢 = 0 = HOME |
| DP-016 / DP-019 | IMU の取付位置，base と torso | torso 原点 = CAD 原点 = IMU |
| DP-017 / DP-018 | quaternion の順序，accel の重力の扱い | MuJoCo の既定（`[w,x,y,z]`，specific force） |
