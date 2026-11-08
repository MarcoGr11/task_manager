# Financial Ledger

## 1. Вхідні параметри

| Параметр | Значення |
|---|---|
| Project key | ansible_awx |
| ncloc | 72621 |
| sqale_index, хв | 10797 |
| HOURLY_RATE | 40 |
| OVERLOAD_COEFF | 1.3 |
| DISCOUNT_RATE | 0.01 |

## 2. Principal і Cost of Delay

- Principal = sqale_index / 60 * HOURLY_RATE * OVERLOAD_COEFF = 9357.40
- Cost of Delay на місяць = ncloc / 100 * HOURLY_RATE = 29048.40

## 3. Таблиця по місяцях

| Місяць | Коефіцієнт дисконтування | Щомісячний ефект | Кумулятивний NPV |
|---|---|---|---|
| 1 | 0.990099 | 28760.79 | 19403.39 |
| 2 | 0.980296 | 28476.03 | 47879.42 |
| 3 | 0.970590 | 28194.09 | 76073.51 |
| 4 | 0.960980 | 27914.94 | 103988.46 |
| 5 | 0.951466 | 27638.56 | 131627.01 |
| 6 | 0.942045 | 27364.91 | 158991.92 |

## 4. Вердикт

Місяць окупності (Payback Period): 1. NPV_6 = 158991.92.

## 5. Quality Gate

**PASS**: NPV > 0 за 6 місяців.
