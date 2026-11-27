---
title: "Runbooks і каталог алертів"
owner: MarcoGr11
status: published
review_date: 2027-02-25
tags:
  - ops
---

# Runbooks і каталог алертів

Правила алертів лежать у `monitoring/alerts.yml`: їх підключає `monitoring/prometheus.yml` (`rule_files`). Перевірка `promtool check rules` дала `SUCCESS: 6 rules found` (2026-11-27, після RFC-001). Пороги SLO описано в `docs/slo.yaml`, а пояснення до них у [[slo]].

## Каталог алертів

| Назва | Умова (PromQL, скорочено) | Серйозність | Роль | Runbook |
|---|---|---|---|---|
| `TaskStoreReadErrors` | частка 5xx серед `/tasks*` > 5% за 5 хв, тримається 2 хв | SEV1 | SRE on-call | [[runbooks/RB-001#t1]] |
| `TaskStoreShrink` | `task_store_records` < 0.9 × max за 15 хв або `NaN` (сховище не читається), тримається 1 хв | SEV2 | SRE on-call | [[runbooks/RB-001#t2]] |
| `AvailabilityBudgetFastBurn` | `1 − 2xx/(усі − 4xx)` за 1 год > 14.4 × 0.5% (2% місячного бюджету за годину) | SEV2 | SRE on-call | [[runbooks/RB-001#t1]], [[slo#policy]] |
| `LatencySLOBreach` | частка `/tasks*` ≤ 0.3 с за 10 хв < 95% (p95 > 300 мс) | SEV3 | L2 розробник | [[maintenance-plan#known-issues]] |
| `NotifierFallbackRatio` | частка `notifier_delivery_total{result!="delivered"}` за 2 хв > 5%, тримається 1 хв | SEV2 | SRE on-call | [[maintenance-plan#known-issues]] (K-1: перезапуск нотифікатора і replay) |
| `ApiDown` | `up{job="task_manager"} == 0` протягом 1 хв | SEV1 | SRE on-call | [[maintenance-plan#escalation]] |

Відповідність тригерів RB-001 алертам: T1 відповідає `TaskStoreReadErrors` (з вторинною ознакою `AvailabilityBudgetFastBurn`), T2 відповідає `TaskStoreShrink`. Тригерів RB-001 без алерту немає.

## Runbooks

| ID | Операція | Автоматизація | Останній drill |
|---|---|---|---|
| [[runbooks/RB-001]] | відновлення JSON-сховищ з резервної копії | 2 (скрипт, рішення за людиною) | 2026-11-27, RTO 1349 мс |
