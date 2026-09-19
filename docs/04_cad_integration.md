# Phase 4：CADモデル統合

- Previous: [03_integration.md](03_integration.md)
- Next: [05_control.md](05_control.md)
- Overview: [00_project_overview.md](00_project_overview.md)
- Related Reference: [joint_definition.md](reference/joint_definition.md)，[coordinate_system.md](reference/coordinate_system.md)，[software_architecture.md](reference/software_architecture.md)，[decision_pending.md](reference/decision_pending.md)

## 1．目的

本Phaseでは，primitive geometryで作ったideal bipedを，CAD由来のgeometryと物性へ段階的に置き換える．joint topology，joint name，joint ordering，software interface，Controller interfaceを維持しながら，joint location，joint axis，link length，mass，center of mass（CoM），inertia tensor，visual mesh，collision geometry，joint rangeを現実へ近づける．

## 2．このPhaseが全体のどこに位置するか

[Phase 2](02_simulation.md)の10 DoF ideal modelと[Phase 3](03_integration.md)の共通contractを入力とする．CAD完成を待って前Phaseを止めるのではなく，完成時に交換できる境界を先に作る．本Phaseの成果は，[Phase 5](05_control.md)のStanding，Balance，Walkingで使うkinematics，dynamics，contact modelになる．

## 3．前提知識

- **joint center / axis**：回転中心と正の回転軸である．CAD assembly constraintとMJCF body frameの変換が必要である．
- **link frame**：各linkに固定した座標系である．CAD座標とrobot conventionの対応を明示する．
- **center of mass（CoM）**：link質量が集中したと等価にみなせる位置である．
- **inertia tensor**：剛体の回転しにくさを表す$3\times3$の対称tensorである．値だけでなく，基準点，表現frame，単位が必要である．
- **visual mesh**：表示用の詳細形状である．必ずしもcontact計算には使わない．
- **collision geometry**：接触計算用形状である．安定性と速度のため，primitiveや簡略meshを優先する．
- **regression test**：変更前に成立していた性質が変更後も保たれることを確認する試験である．

## 4．使用するハードウェア・ソフトウェア

- 完成度が管理されたCAD assembly
- linkごとのexport機能とmass property出力
- MuJoCo / MJCF
- mesh確認手段
- unit・frame変換表
- Phase 2のideal modelとbaseline test
- 実機寸法・質量を測る手段

CAD software，export形式，mesh単位，座標軸は現時点で未決定である．STLまたはOBJを候補とするが，実際の選択はmetadata保持，tool互換性，見た目を評価して決める．

## 5．システム構成

```text
CAD assembly
  ├─ joint center / axis / range
  ├─ link mass / CoM / inertia
  └─ visual mesh
          │ frame and unit conversion
          ↓
MJCF CAD model
  ├─ unchanged joint names and topology
  ├─ visual mesh
  └─ simplified collision geometry
          │
          ↓
existing MuJoCoRobot + Controller
```

```text
Ideal Model → CAD Model → Realistic Actuator Model
```

この順序は概念上の段階を示す．Phase 3で得たactuator modelをCAD modelへ適用する際も，geometry変更とactuator変更を同時に行わず，比較可能なcommitを残す．

## 6．作業手順

### Step 1：CAD受入条件を定義する

各linkが一意に識別され，assemblyのjoint関係が明確で，mass materialまたは実測massが得られる状態を受入条件とする．未完成部品や仮materialは明示する．

**確認方法**：10 DoFの全jointと全linkについて，CAD名，software名，状態，担当，source revisionを表にする．欠損値を推定で埋めない．

### Step 2：座標系と単位の変換表を作る

CAD global frame，各part frame，assembly joint frameを，$+x$ forward，$+y$ left，$+z$ upのrobot frameへ対応付ける．CADのmm，g等はMJCF用のm，kgへ変換する．

**確認方法**：原点，3本のbasis vector，scaleを既知寸法で確認する．左右partでmirror変換のdeterminantと軸符号を確認し，見た目だけで判断しない．

### Step 3：joint情報を抽出する

各jointについてcenter，axis，parent，child，zero pose，mechanical rangeを抽出する．CAD constraintの正方向とsoftware joint signが一致しない場合は，明示的な変換として記録する．

**確認方法**：$q=0$と小さな正角度の姿勢をCADとMJCFで比較する．joint nameとorderingは変更せず，mapping tableで差を吸収する．

### Step 4：link寸法と物性を抽出する

各linkについてmass $m_i$，CoM $\mathbf r_{CoM,i}$，inertia $\mathbf I_i$を取得する．inertiaはCoMまわりか，どのframe表現かを必ず記録する．CAD materialが仮の場合は「仮定」とする．cable，fastener，motor等の含有範囲も明示する．

**確認方法**：全link質量の和をCAD assembly massおよび可能なら実測総質量と比較する．inertia tensorの対称性，正定値性，桁，単位をsanity checkする．parallel-axis変換を行った場合は式と変換元を残す．

### Step 5：visual meshをexportする

linkごとにSTL，OBJ等へexportし，meshの原点，向き，scale，triangle数を記録する．visual meshは見た目の確認に用い，物理特性を暗黙に推定するsourceにしない．

**確認方法**：単体meshをrobot frameで表示し，既知寸法とbounding boxを比較する．左右・前後・上下の反転と1000倍scale errorを確認する．

### Step 6：collision modelを単純化する

CAD meshをそのままcollisionに使うことを前提にせず，box，capsule，cylinderまたは低複雑度形状で主要体積と足裏を表す．理由はsimulation高速化，接触安定性，debug容易化である．

**確認方法**：visualとのoverlap，ground contact，self-collision，足裏面積，計算時間を確認する．詳細mesh collisionを比較対象にする場合も，採用理由と性能差を残す．

### Step 7：1 linkずつMJCFへ置換する

全modelを一度に置き換えず，torsoから片脚，反対脚のように小さな単位でgeometryと物性を更新する．各置換後にmodel compile，質量，joint axis，free-fall，pendulum等のtestを行う．

**確認方法**：変更前後の差分をparameter表とplotで確認する．想定外の挙動が出たとき，最後の置換単位まで戻って原因を分離できるようにする．

### Step 8：joint rangeとself-collisionを検証する

CAD干渉と実機mechanical stopを基にrange候補を作る．CAD上で接触しないことだけを安全rangeの根拠にせず，cable，assembly tolerance，Servo limit，soft marginを考慮する．

**確認方法**：range端と中間姿勢でvisual，collision，CADを比較する．最終software joint limitは実機確認を経て決定するため，CAD値と運用値を別fieldで管理する．

### Step 9：ideal modelとのregressionを行う

joint name，ordering，state shape，command shape，HOME保持，Virtual IMU，loggerが変更前と同じcontractで機能することを確認する．物理応答が変わるのは期待されるが，software interfaceの変更は許容しない．

**確認方法**：同じtest suiteとcommand系列をideal modelとCAD modelへ適用し，interface結果と物理差を分けて報告する．

### Step 10：実機測定でCAD物性を更新する

組立後に総質量，link質量，主要寸法，可能な範囲のCoMを測り，CADとの差を記録する．製造差，cable，connector，fastenerをmodelへ反映するかは影響評価後に決める．

**確認方法**：source，測定器，精度，日付を伴うmeasured parameter表を作る．CAD値を上書きして出典を失わず，nominalとmeasuredを並べる．

## 7．確認方法と記録項目

- CAD revisionとexport設定
- CAD↔robotの4×4 transformまたは同等の定義
- joint center，axis，zero，rangeの比較
- link mass，CoM，inertiaのsourceとunit
- mesh bounding box，triangle数，scale
- collision形状，contact parameter，simulation速度
- 全model質量，HOME pose，self-collision
- ideal / CAD modelのregression結果

## 8．完了条件

- 全linkとjointにCAD-to-software mappingがある．
- mass，CoM，inertiaにsource，frame，基準点，unitが付いている．
- visual meshとsimplified collisionが分離されている．
- 全10軸のzero，axis，rangeがCAD・MJCF・Reference間で照合済みである．
- joint name，ordering，`RobotState`，`RobotCommand`，Controller interfaceを変更していない．
- ideal modelのregression suiteがCAD modelでも通り，期待される物理差が説明されている．
- 実測可能な値について，CAD nominalとの差が記録されている．

## 9．トラブルシュート

### meshが極端に大きい・小さい

**症状** → modelが1000倍程度ずれる．  
**考えられる原因** → CADのmmとMJCFのmの混同，export scaleの重複．  
**確認方法** → bounding boxを既知寸法と数値比較する．  
**対処** → 変換を一箇所に集約し，meshごとの場当たりscaleを避ける．

### joint位置やaxisが見た目と合わない

**症状** → 回転中心がずれ，linkが円弧状に外れる．  
**考えられる原因** → part frameとassembly frameの混同，transform順序，mirror符号．  
**確認方法** → joint原点とaxisを可視化し，$q=0$と小角度でCAD比較する．  
**対処** → transform chainを表に戻し，1 jointずつ修正する．

### inertia導入後にsimulationが不安定になる

**症状** → 高周波振動，compile warning，不自然な回転が出る．  
**考えられる原因** → unit，基準点，frame，非正定値tensor，極端なmass ratio．  
**確認方法** → diagonalとeigenvalue，mass，CoMを確認し，単link testへ戻す．  
**対処** → CAD export条件とparallel-axis変換を修正し，根拠なく値を丸めて隠さない．

### detailed collisionで接触が不安定になる

**症状** → 足が跳ねる，simulationが遅い，contact数が過大になる．  
**考えられる原因** → 高密度mesh，凹形状，重複面，小feature．  
**確認方法** → primitive collisionとのcontact数・速度比較を行う．  
**対処** → collisionを単純化し，visual detailと物理接触を分離する．

## 10．成果物

- CAD revision付きlink / joint mapping表
- CAD-to-robot frame・unit変換仕様
- mass，CoM，inertia table
- visual mesh一式とexport manifest
- simplified collision model
- CAD-based MJCF
- joint range・self-collision test結果
- ideal / CAD regression report
- nominal / measured parameter比較表

## 11．次のPhaseへ渡す情報

[Phase 5](05_control.md)へ，link geometry，mass，CoM，inertia，joint range，contact model，actuator model，regression結果，不確かさを渡す．未確定値は値だけでなく，control上のriskと決定予定を添える．

## 実行チェックリスト

- [ ] Step 1：CAD受入条件とrevisionを確認した
- [ ] Step 2：frame・unit変換表を作成した
- [ ] Step 3：全joint情報を抽出・照合した
- [ ] Step 4：全link物性をsource付きで取得した
- [ ] Step 5：visual meshをscale確認付きでexportした
- [ ] Step 6：collision modelを単純化した
- [ ] Step 7：1 linkずつMJCFへ置換した
- [ ] Step 8：rangeとself-collisionを検証した
- [ ] Step 9：ideal modelとのregressionを完了した
- [ ] Step 10：実測値とCAD値を比較した

## Phase Completion Criteria

第8章の全条件を満たし，CAD置換によって共通software contractが変わっておらず，すべての物性値にsource・frame・unit・不確かさが付いた時点で，本Phaseを完了とする．
