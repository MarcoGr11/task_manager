---
title: Журнал ADR
owner: MarcoGr11
status: published
review_date: 2027-05-26
tags:
  - architecture
  - adr
---

# Журнал архітектурних рішень (ADR)

## Правила

- **Нумерація.** `ADR-NNNN`, чотири цифри, без пропусків і повторного використання. Файл `docs/architecture/adr/NNNN-короткий-слаг.md`.
- **Статуси.**
    - `Proposed`: рішення запропоновано, ще не діє;
    - `Accepted`: рішення діє;
    - `Superseded by ADR-NNNN`: рішення замінене новим.
- **Незмінність.** Після `Accepted` текст ADR не редагується. Змінити рішення можна лише новим ADR з рядком «Замінює ADR-NNNN». У старому ADR змінюється тільки рядок статусу на `Superseded by ADR-NNNN`.
- Статус ADR записано в полі `adr_status` front matter і в рядку «Статус» тексту. Поле `status` front matter описує стан сторінки (`published`), а не рішення.

## Реєстр

| ADR | Рішення | Статус | Дата |
|---|---|---|---|
| [[architecture/adr/0001-json-file-storage]] | JSON-файли як сховище | Accepted | 2026-09-13 |
| [[architecture/adr/0002-notifier-retry-fallback]] | Retry + Fallback нотифікатора | Accepted | 2026-09-27 |
| [[architecture/adr/0003-openapi-as-source-of-truth]] | OpenAPI як єдине джерело правди API | Accepted | 2026-11-27 |
| [[architecture/adr/0004-docs-as-code-mkdocs]] | Documentation as Code: MkDocs Material + GitHub Pages | Accepted | 2026-11-27 |

Відоме порушення до введення правила: ADR-0002 відредаговано в коміті `fa8b468` (ЛР10), коли додали `NOTIFIER_TIMEOUT_SECONDS`. За чинним правилом таку зміну треба було б оформити новим ADR. Міграція формату в ЛР11 (front matter, wikilinks, відступи списків, статус `Прийнято` → `Accepted`) суті рішень ADR-0001 і ADR-0002 не змінює.

Пов'язані документи: [[architecture/sdd]], [[architecture/isd]], [[developer/standards]].
