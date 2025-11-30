# Recommender Backtest Results

**Evaluation Date:** 2025-11-30 17:57:04

**Number of Trades:** 5

**Trades with 1M returns:** 5

**Trades with 3M returns:** 5

---

## 1-Month Horizon

### Directional Accuracy (non-Hold trades)

| Strategy | Accuracy | N Trades |
|----------|----------|----------|
| Model | 0.0% | 4 |
| Human | 33.3% | 3 |
| Baseline (Always Long) | 60.0% | 5 |

### Average P&L per Trade

| Strategy | Avg P&L |
|----------|----------|
| Model | -3.18% |
| Human | -1.16% |
| Baseline | -0.10% |

### Cumulative P&L

| Strategy | Cumulative P&L |
|----------|-----------------|
| Model | -15.91% |
| Human | -5.80% |
| Baseline | -0.51% |

### Model vs Human Comparison

- **Model correct, Human wrong:** 0
- **Human correct, Model wrong:** 1

## 3-Month Horizon

### Directional Accuracy (non-Hold trades)

| Strategy | Accuracy | N Trades |
|----------|----------|----------|
| Model | 0.0% | 4 |
| Human | 33.3% | 3 |
| Baseline (Always Long) | 60.0% | 5 |

### Average P&L per Trade

| Strategy | Avg P&L |
|----------|----------|
| Model | -2.30% |
| Human | +0.18% |
| Baseline | +1.30% |

### Cumulative P&L

| Strategy | Cumulative P&L |
|----------|-----------------|
| Model | -11.49% |
| Human | +0.89% |
| Baseline | +6.51% |

### Model vs Human Comparison

- **Model correct, Human wrong:** 0
- **Human correct, Model wrong:** 1

---

## Trading Rules

### Signal Mapping

- **StrongBuy / Buy** → +1 (go long)
- **Sell / UnderPerform** → -1 (go short)
- **Hold** → 0 (no position)

### P&L Calculation

- P&L = signal × future_return
- Baseline strategy: always long (+1) for all dates

### Return Calculation

- 1M return: price at (rec_date + 21 trading days) / price at rec_date - 1
- 3M return: price at (rec_date + 63 trading days) / price at rec_date - 1
