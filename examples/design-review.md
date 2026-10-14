# 設計の相談

情報システム部 山田
2026 年 10 月 14 日

---

## 今の構成

![今の構成](design-review/fig1-now.flow)
集計基盤から先は、社外の取引先に渡る。

---

## 受付は 1 から 3 に分かれる

![受付の分かれ方](design-review/fig2-split.flow)

---

## 保存先は 2 つの集計から使われる

![保存先と集計](design-review/fig3-span.flow)

---

## 送る側と受ける側

![送る側と受ける側](design-review/fig4-sides.flow)
店舗から取込までは、検証のあとで送信する。

---

## 今の形と案の形

![今の形](design-review/fig5-now.flow)
|||
![案の形](design-review/fig5-plan.flow)

---

## 外部への参照

![外部への参照](design-review/fig6-detour.flow)

---

## 保存先の一覧

![保存先の一覧](design-review/fig7-list.flow)
