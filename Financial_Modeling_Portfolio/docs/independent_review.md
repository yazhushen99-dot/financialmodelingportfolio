# Independent portfolio review

PASS: 34 independent source-data, regression, financial-math and exported-workbook checks complete.

Independent NumPy QR regression, QR-based HC1 covariance, source-CSV reconciliation and separately coded financial calculations; source algorithm reviewed without invoking its fit/model functions. Exported XLSX formulas separately parsed and evaluated from XML, including Base/Downside and a final-year growth perturbation; caches reconciled.

Run the read-only workbook arithmetic check with: python docs/independent_workbook_check.py (Python 3 standard library only). This reproduces the XLSX formula and scenario checks; the source-data/regression checks above were a separate independent review.

## Executed checks

- PASS — Synthetic status disclosed: Fictional company and deterministic simulated data; skill demonstration, not employment evidence.
- PASS — Monthly input structure: 96 unique, uninterrupted months
- PASS — Chronological train and holdout: 84 training months: 2018-2024; 12 holdout months: 2025
- PASS — Positive complete revenue: No missing input cells; revenue positive for logarithm
- PASS — Driver regression training coefficients and HC1: Independent QR OLS/HC1; n=84, k=14, residual df=70
- PASS — Driver regression full-refit coefficients and HC1: Independent QR OLS/HC1; n=96, k=14, residual df=82
- PASS — Trend and seasonality training coefficients and HC1: Independent QR OLS/HC1; n=84, k=13, residual df=71
- PASS — Trend and seasonality full-refit coefficients and HC1: Independent QR OLS/HC1; n=96, k=13, residual df=83
- PASS — Driver regression holdout metrics: {'rmse_musd': 0.6617590715214173, 'mae_musd': 0.6049186350113507, 'mape_pct': 2.5343355551487683}
- PASS — Trend and seasonality holdout metrics: {'rmse_musd': 1.0342972824783914, 'mae_musd': 0.7918309906060962, 'mape_pct': 3.461362887330286}
- PASS — Seasonal naive holdout metrics: {'rmse_musd': 2.1493834857684906, 'mae_musd': 1.859768411415166, 'mape_pct': 7.49267289445537}
- PASS — Response not used in holdout fitting: Independent fit uses training rows only; source code reviewed for matching split
- PASS — Realized holdout predictor caveat: Holdout driver values are observed 2025 data; conditional validation, not ex-ante predictor forecast
- PASS — Log retransformation caveat: exp(predicted log revenue), no smearing correction; forecasts represent conditional median, not unbiased conditional mean.
- PASS — 2026 conditional forecast and annual total: Independent annual sum = 329.339117624571 USDm
- PASS — 2026 assumed driver: Future driver equals December 2025 plus 0.10 per month
- PASS — Monthly to annual historical revenue: 2020-2025 annual source revenue reconciles to monthly source
- PASS — Historical statements and rolls: Max residual = 2e-12 USDm
- PASS — Base financial statements and FCFF: All annual financial values independently recomputed; max difference 9.95e-13 USDm
- PASS — Base DCF and as-of bridge: EV 563.249366627, equity 540.462236209; 2025-12-31 cash/debt bridge
- PASS — Downside financial statements and FCFF: All annual financial values independently recomputed; max difference 9.95e-13 USDm
- PASS — Downside DCF and as-of bridge: EV 387.979505694, equity 365.192375276; 2025-12-31 cash/debt bridge
- PASS — WACC/g sensitivity and center: 25 independently reproduced values; max difference 4.55e-13 USDm
- PASS — Terminal reinvestment limitation disclosed: Simple final-year FCFF perpetuity; no normalized steady-state ROIC/reinvestment schedule
- PASS — Workbook formula recalculation from exported XML: All 866 exported formulas independently recalculated. ISO-date cells normalized to Excel serial dates. Maximum numeric cache difference 3.410605131648481e-13; no nonnumeric mismatches. Executed docs/independent_workbook_check.py.
- PASS — Workbook cached error cells: No cached error cells
- PASS — Workbook Base formulas vs independent reference: All 25 mapped financial metrics per forecast year plus EV/equity; max difference 1.14e-13 USDm
- PASS — Workbook Base sensitivity center: Center matches active DCF
- PASS — Workbook Downside formulas vs independent reference: All 25 mapped financial metrics per forecast year plus EV/equity; max difference 1.14e-13 USDm
- PASS — Workbook Downside sensitivity center: Center matches active DCF
- PASS — Workbook full sensitivity grid: All 25 values reconcile; max difference 3.41e-13 USDm
- PASS — Workbook final-year growth perturbation: 2030 Base growth +1pp changes equity from 540.462236 to 538.471931
- PASS — Workbook WACC / growth guard: WACC equal to terminal growth produces NA
- PASS — Workbook synthetic disclosure: All eight worksheets identify the synthetic work sample

## Scope and limitations

- Illustrative fictional company with simulated data; not verification of employment or independent authorship.
- Holdout driver regression uses realized 2025 industrial index. Results measure conditional prediction, not a genuine ex-ante forecast of all inputs.
- One 12-month holdout is used for model selection; no further untouched test set or rolling-window validation is supplied.
- Exponentiated log forecasts represent conditional medians without a smearing correction. Summing monthly medians is a scenario planning total, not a formally estimated annual conditional mean or median.
- HC1 addresses heteroskedasticity, not serial correlation; synthetic time-series results do not establish real-world causal effects.
- Terminal value extrapolates final-year FCFF without a normalized terminal reinvestment/ROIC schedule; sensitivity is material.
- Higher debt interest changes earnings and cash. Unlevered FCFF at fixed WACC is correctly independent of debt interest, so interest stress alone does not directly reduce the DCF.
- Native Stata, EViews, Excel and Power Query were not executed. XLSX formulas/caches independently inspected and recalculated by a limited Python evaluator covering functions present, not native Excel.
