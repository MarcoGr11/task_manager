---
title: Task Manager
owner: MarcoGr11
status: published
review_date: 2027-02-25
tags:
  - developer
---

# Task Manager: документація

Сайт зібрано з каталогу `docs/` репозиторію (Documentation as Code). Призначення системи описано в README репозиторію, тут лише карта рівнів.

| Рівень | Розділ | Для кого | Головне питання |
|---|---|---|---|
| 1 | Огляд (ця сторінка, README) | усі | що це і куди йти далі |
| 2 | [Розробник](developer/index.md) | розробники, QA | як запустити, як робити внесок, які стандарти |
| 3 | [API](api/index.md) | інтегратори, QA | які контракти, як викликати |
| 4 | [Архітектура](architecture/index.md) | архітектор, DevOps | як спроєктовано, де працює, чому так |
| 5 | [Експлуатація](maintenance-plan.md) | SRE, on-call, CCB | як підтримувати, що робити при збої, як змінювати |

Кожен факт живе в одному місці: маршрути тільки в `docs/api/openapi.yaml`, змінні оточення тільки в [[architecture/isd]], процеси і правила тільки в [CONTRIBUTING](developer/CONTRIBUTING.md).
