---
title: CONTRIBUTING
owner: MarcoGr11
status: published
review_date: 2027-02-25
tags:
  - developer
---

# Як робити внесок

1. Гілка від `master`: `feat/...`, `fix/...`, `docs/...`.
2. Локальне середовище: [[developer/local-setup]]. Стандарти: [[developer/standards]].
3. Зміна коду і документації в одному коміті (правило з [[developer/maintenance]]).
4. Push гілки запускає `.github/workflows/docs.yml` (markdownlint, Spectral, `mkdocs build --strict`). Червоний Job блокує злиття.
5. Злиття в `master` публікує сайт на GitHub Pages.

## Чек-лист docs-or-don't-merge

Pull request не зливається, поки не відмічено все, що стосується зміни:

- [ ] Змінено поведінку, видиму назовні: оновлено сторінку в `docs/` (README, [[architecture/sdd]], [[architecture/isd]] або developer-сторінку).
- [ ] Змінено маршрут, параметр, код відповіді чи формат: оновлено `docs/api/openapi.yaml`, Spectral дає 0 errors, `info.version` піднято за SemVer.
- [ ] Нова змінна оточення: рядок в [[architecture/isd]] §3 і в `.env.example`.
- [ ] Архітектурне рішення: новий ADR у [[architecture/adr/index|журналі]], старий не редаговано.
- [ ] Запис у `CHANGELOG.md` у розділі `Unreleased`.
- [ ] У змінених сторінках актуальні `status` і `review_date`.
- [ ] `mkdocs build --strict` і `python scripts/doc_audit.py` проходять локально.

Критерії готовності (Definition of Done) наведено в README репозиторію.
