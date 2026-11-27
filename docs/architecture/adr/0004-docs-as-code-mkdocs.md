---
title: "ADR-0004: Documentation as Code на MkDocs Material"
owner: MarcoGr11
status: published
adr_status: Accepted
review_date: 2027-05-26
tags:
  - architecture
  - adr
  - ops
---

# ADR-0004: Documentation as Code на MkDocs Material

- **Номер:** 0004
- **Статус:** Accepted, 2026-11-27.
- **Компонент:** [[architecture/isd#isd-cicd|ISD: CI/CD]]

## Контекст

Після ЛР10 документація була набором Markdown-файлів без збірки, без перевірки посилань і без публікації. Лінки, що зламалися, ніхто не помічав.

## Розглянуті альтернативи

| Варіант | За | Проти |
|---|---|---|
| Markdown у репозиторії без збірки | нуль інструментів | немає перевірки посилань, навігації, пошуку |
| **MkDocs Material + GitHub Pages (обрано)** | Python-стек проєкту, `--strict` ловить мертві посилання, плагіни для Mermaid, Swagger UI, mkdocstrings, wikilinks | ще одна збірка в CI |
| Sphinx | autodoc з коробки | reStructuredText або MyST, складніша конфігурація |
| Wiki GitHub | редагування в браузері | поза репозиторієм і поза рев'ю |

## Рішення

`mkdocs.yml` у корені. Плагіни:

- search, tags;
- ezlinks для wikilinks, mermaid2;
- git-revision-date-localized;
- swagger-ui-tag, mkdocstrings.

`.github/workflows/docs.yml` запускає markdownlint, Spectral і `mkdocs build --strict`, а з `master` деплоїть на GitHub Pages.

## Наслідки

- **Плюси:**
    - мертве посилання або відсутня сторінка роблять CI червоним;
    - сайт публікується автоматично;
    - Obsidian читає той самий каталог як Vault.
- **Мінуси:**
    - wikilinks не рендеряться на GitHub у перегляді файлу, лише на сайті і в Obsidian;
    - потрібні Node-інструменти в CI.

Пов'язані документи: [[architecture/adr/index]], [CONTRIBUTING](../../developer/CONTRIBUTING.md).
