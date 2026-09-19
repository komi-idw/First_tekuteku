# Hardware Inventory

- Previous: [../05_control.md](../05_control.md)
- Next: [joint_definition.md](joint_definition.md)
- Overview: [../00_project_overview.md](../00_project_overview.md)
- Related Reference: [decision_pending.md](decision_pending.md)，[experiment_log_template.md](experiment_log_template.md)

## 1．目的

所有hardware，個体識別，仕様根拠，接続系統，確認状態を一元管理する．本表の「想定」は現物確認の代わりではない．確認日，確認者，写真またはlabel転記，使用試験へのlinkを追加して運用する．

## 2．現時点のinventory

| Category | Item | Variant / rating | Quantity | Status | Intended use |
|---|---|---:|---:|---|---|
| Servo | STS3215 C001 | reduction 1:345 | 7 | 想定，label未照合 | leg candidate |
| Servo | STS3215 C044 | reduction 1:191 | 2 | 想定，label未照合 | leg candidate |
| Servo | STS3215 C046 | reduction 1:147 | 3 | 想定，label未照合 | leg candidate |
| Driver | Seeed Studio Bus Servo Driver Board for XIAO v1.0 | USB / TTL bus | 2 | 所有，port未確認 | STS3215 Bus A / B候補 |
| Power | SO-101付属AC adapter | 5 V，4 A | 1 | 所有 | 初期単体motor試験 |
| Servo | DYNAMIXEL XL330-M077 | model固有仕様は公式資料参照 | 2 | 所有 | 将来の頭部・首候補 |
| Servo | DYNAMIXEL XL330-M288 | model固有仕様は公式資料参照 | 2 | 所有 | 将来の頭部・首候補 |
| Controller | ROBOTIS OpenRB系board | exact model未記録 | 1系統 | 所有 | XL330 interface候補 |
| IMU node | M5Stack ATOM ESP32-PICO系 | MPU系IMU搭載 | 1系統 | 所有，exact sensor未確認 | USB IMU node |
| MCU | NUCLEO-F303K8 | STM32系 | 所有数未記録 | 所有，当面不使用 | 将来の低layer realtime制御候補 |

STS3215は合計12個，XL330は合計4個である．脚部10軸への個体割当て，残り2個の用途，頭部4軸へのXL330割当ては未決定である．

## 3．個体記録template

| Asset ID | Label / model | Reduction | Current ID | Bus / port | Firmware | Joint assignment | Condition | Verified date | Evidence |
|---|---|---|---:|---|---|---|---|---|---|
| STS-01 | 未確認 | 未確認 | 未確認 | 未確認 | 未確認 | Decision Pending | 未確認 | — | — |

各motorに再利用可能な物理labelを付ける．Servo IDは変更可能な設定であるため，Asset IDと同一視しない．

## 4．接続・電源上の制約

- STS3215系とXL330系は，初期段階では電源・通信系を分離する．
- 5 V / 4 A adapterは初期単体試験に使用する．10軸同時運転に十分であるとは確定していない．
- connector pinout，極性，許容電圧は，通電前に現物表示とメーカー一次資料で照合する．
- 2枚のSeeed Driverを左右busへ割り当てる案は，通信・配線・障害分離のための現時点の設計案である．
- NUCLEO-F303K8等へrealtime処理を移すかは，PC直接制御のcycle・jitter・安全性を測定してから決める．

## 5．受入チェックリスト

- [ ] 全STS3215のlabelと減速比を現物確認した
- [ ] 全Servoへ一意のAsset IDを付けた
- [ ] 現在IDとbaud rateを1個ずつ確認した
- [ ] 2枚のSeeed DriverとCOM portを対応付けた
- [ ] 電源label，極性，cable，connectorを記録した
- [ ] XL330の個体，model，IDを記録した
- [ ] ATOMとMPU系IMUのexact modelを記録した
- [ ] 写真または同等のevidenceへlinkした

## Completion Criteria

全個体を設定変更可能なIDではなく物理Asset IDで追跡でき，電源・通信・型式・試験結果が対応付いた時点でinventory確定とする．
