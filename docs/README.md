# First_tekuteku 技術文書

本ディレクトリは，小型二足歩行ロボット `First_tekuteku` の開発手順と設計上の共通定義を管理する．原典は「BDX型二足歩行ロボット開発 作業手順書 v0.3」である．原典中のリポジトリ名 `bdx_robot` は，本プロジェクトでは `First_tekuteku` と読み替える．

## 推奨読順

1. [プロジェクト全体像](00_project_overview.md)
2. [実機基盤](01_real_hardware.md)と[シミュレーション基盤](02_simulation.md)を交互に進める
3. [Real / Simulation統合](03_integration.md)
4. [CAD統合](04_cad_integration.md)
5. [姿勢・歩行・強化学習](05_control.md)

共通定義は `reference/` を正とする．特に，関節順序，座標系，単位，`RobotState`，`RobotCommand` をPhase文書ごとに独自定義してはならない．

## 情報の区分

- **確定事項**：本プロジェクトの方針として採用済みの事項である．
- **現時点の設計案**：実装・実験前の有力案であり，検証により変更し得る．
- **仮定**：手順を具体化するために一時的に置く条件である．
- **Decision Pending**：測定，安全評価，または設計判断を経て後で決定する事項である．一覧は[未決定事項](reference/decision_pending.md)に置く．
- **提案**：原典v0.3には明記されていないが，品質，安全性，または追跡性のために追加した事項である．

## 文書運用

- 実測値や決定事項を得たら，共通Referenceを先に更新し，各Phase文書から参照する．
- Hardware testおよびSimulation testは，[実験記録テンプレート](reference/experiment_log_template.md)を用いて記録する．
- 仕様変更時は，[原典追跡表](reference/source_traceability.md)で影響範囲を確認する．
- 既存実装はReference Implementationとして比較に用い，そのまま本実装へコピーしない．

## ナビゲーション

- Previous: なし
- Next: [00_project_overview.md](00_project_overview.md)
- Overview: [00_project_overview.md](00_project_overview.md)
- Related Reference: [software_architecture.md](reference/software_architecture.md)，[source_traceability.md](reference/source_traceability.md)
