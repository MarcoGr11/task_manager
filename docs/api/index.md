---
title: API
owner: MarcoGr11
status: published
review_date: 2027-02-25
tags:
  - api
---

# Рівень 3: API

Ця сторінка рендериться прямо з `docs/api/openapi.yaml` і не копіює контракт (SSOT, [[architecture/adr/0003-openapi-as-source-of-truth|ADR-0003]]). Щоб змінити API, змінюйте YAML: Spectral перевіряє його в CI.

- Сирий файл: [openapi.yaml](openapi.yaml).
- Довідник модулів з docstring: [[api/reference]].
- Перевірка дрейфу і дефекти: [[api/drift]].
- Запуск сервера для «Try it out»: [[developer/local-setup]].

<swagger-ui src="./openapi.yaml"/>
