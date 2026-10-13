# Night batch migration report
^ 夜間バッチの移行報告
IT Systems Dept, Yamada
^ 情報システム部 山田
October 9, 2026
^ 2026 年 10 月 9 日

---

The nightly batch now runs in 50 minutes instead of 4 hours.
^ 夜間バッチの実行時間は 4 時間から 50 分に縮んだ。

---

## What we changed
^ 移行でやったこと

- Moved three old servers onto one new server
^ 旧サーバー 3 台を新しい 1 台に集約した
- Retries after a failure are now **automatic**
^ 失敗時の再実行を自動にした
- Only the monthly report stays on the old system
^ 月次の集計だけは旧方式のまま残した

---

## How the night run flows
^ 夜間の処理の流れ

![歯車](icon:gear)
It starts at 1 a.m. and totals sales, then stock.
^ 毎晩 1 時に起動し、売上と在庫を順に集計する。

---

## Run time before and after
^ 実行時間の変化

| Job | Before | After |
^ | 処理 | 移行前 | 移行後 |
|---|---|---|
| Sales totals | 2 h 10 min | 25 min |
^ | 売上集計 | 2 時間 10 分 | 25 分 |
| Stock totals | 1 h 30 min | 15 min |
^ | 在庫集計 | 1 時間 30 分 | 15 分 |

---

## What is left
^ 残った作業

- Monthly report moves in November
^ 月次集計の移行は 11 月
- Old servers go at the end of December
^ 旧サーバーの撤去は 12 月末
|||
Yamada owns the contact point, and two people share the night calls.
^ 窓口は山田が務め、夜間の呼び出しは 2 人の交代制にする。
