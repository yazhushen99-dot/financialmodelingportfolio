# Native tool reproduction

This is a synthetic professional work sample for Northstar Industrial Components, a fictional company. All revenue, financial statements and economic drivers are simulated. These files demonstrate a workflow; they are not evidence of a past client engagement.

## What has and has not run

The reference data, model coefficients, conditional forecasts and validation metrics were calculated by `analysis/reproduce_analysis.py` using NumPy. The Stata `.do`, EViews `.prg` and Power Query `.pq` files have been reviewed against their official documentation, but **have not been executed in Stata, EViews or Excel Power Query in this environment**. The shipped workbook contains prepared source tables; the M query is supplied separately and is not an embedded live connection. No native application execution logs or native output screenshots are included.

## Model specification and sample control

- Observations: 96 monthly records, January 2018 through December 2025.
- Training: January 2018 through December 2024, 84 observations.
- Validation: January through December 2025, 12 observations.
- Driver model: log revenue on an intercept, linear time trend, industrial index and eleven monthly indicators. January is the base month.
- Benchmark: log revenue on an intercept, time trend and the same monthly indicators.
- Simple benchmark: revenue from the same month one year earlier.
- Model comparison uses level-revenue MAE, RMSE and MAPE over the fixed validation window. Units for MAE/RMSE are USD millions; MAPE is percent.
- The driver validation uses the **realized industrial index** in 2025. This measures conditional prediction performance, not an ex-ante forecast of the economy. The assumed future index in 2026 is visible in `data/future_drivers.csv`.
- Level predictions are `exp(predicted log revenue)` without a smearing adjustment. They are conditional-median forecasts, not bias-corrected conditional means. Summed monthly medians are a planning input, not an assertion about the expected annual total.
- HC1 heteroskedasticity-robust standard errors are provided for regression coefficients. HC1 does not correct serial correlation and does not establish causality. No claim of forecast accuracy outside this synthetic example is made.
- After validation, regressions are refit on all 96 observed months and produce twelve 2026 forecasts. Future revenue remains missing in the combined input, so it cannot enter either fit.

## Stata

Target: Stata 17 or later. No third-party commands are required.

1. Extract the entire portfolio, keeping its directory structure.
2. In Stata, change directory to the portfolio root and run:

```stata
do scripts/northstar_forecast.do
```

Alternatively, pass the root path:

```stata
do "C:/work/finance_portfolio/scripts/northstar_forecast.do" "C:/work/finance_portfolio"
```

The script validates date uniqueness, monthly continuity, observation counts and split labels. It then estimates both regression models, evaluates the holdout and refits the models. `vce(robust)` uses the finite-sample HC1 adjustment. Results are written under `analysis/native_stata/`: a genuine `run.log`, metrics and prediction CSVs, the full-driver coefficient CSV and a `.dta` analysis dataset. These files are produced only when you execute Stata.

## EViews

Target: EViews 14 on Windows. Earlier versions may not support the explicit `cov=hc, hctype=hc1` option.

1. Set EViews' default working directory to the extracted portfolio root. For example, type `cd "C:\work\finance_portfolio"` in the command window.
2. Open `scripts/northstar_forecast.prg` and run the program.
3. Review `validation_metrics`, the four equation objects and the future forecast series.

The program imports `data/model_input_combined.csv`, which must retain its supplied chronological order. It assigns a monthly structure beginning January 2018. It uses the same omitted month and regressor order as the reference. Native outputs are `analysis/eviews_validation_metrics.csv`, `analysis/eviews_annual_forecasts.csv` and `analysis/eviews_northstar_analysis.wf1`. These are not pre-created or claimed to have run.

## Compare native outputs with the reference

After running one of the native programs, use standard Python:

```text
python scripts/check_native_parity.py --tool stata
python scripts/check_native_parity.py --tool eviews
```

This comparison uses a relative tolerance of `1e-7` and an absolute tolerance of `1e-6`. Missing native outputs are reported as `NOT RUN`, never as a pass. Exit code 0 means checked outputs match; 1 means a numerical/key mismatch; 2 means native output is missing. The checker does not launch either application or certify model suitability.

## Excel Power Query

1. Open Excel with Power Query support. Create a Blank Query through Data > Get Data > From Other Sources.
2. Open Advanced Editor. Paste `scripts/Consolidate_Financial_and_Operating_Data.pq`.
3. Change the `RootFolder` value to the extracted portfolio path.
4. Name the query `Northstar_Financial_Operating_Reconciliation` and load it as a table.

The query applies explicit column types, checks duplicate dates and invalid revenue, aggregates monthly operating data by year, checks duplicate financial years, and merges that output with the annual financial statements. It reports a revenue reconciliation difference and status for each year, with a `0.000001` USD-million rounding tolerance. The merged output retains the financial statement line items and the monthly observation count. It does not silently discard exceptions or modify the source CSVs.

## Official syntax references

Accessed November 1, 2026.

- Stata, *Import and export delimited text data*: https://www.stata.com/manuals/dimportdelimited.pdf
- Stata, *Regress - Linear regression*: https://www.stata.com/manuals/rregress.pdf
- EViews, *wfopen*: https://www.eviews.com/help/content/commandcmd-wfopen.html
- EViews, *pagestruct*: https://www.eviews.com/help/content/commandcmd-pagestruct.html
- EViews, *Equation / least squares options*: https://www.eviews.com/help/content/equationcmd.html
- EViews, *Equation forecast*: https://www.eviews.com/help/content/equationcmd-forecast.html
- EViews, *Table save*: https://www.eviews.com/help/content/tablecmd-save.html
- Microsoft, *Power Query table functions*: https://learn.microsoft.com/en-us/powerquery-m/table-functions
- Microsoft, *Combine multiple data sources*: https://support.microsoft.com/en-us/excel/learn-to-combine-multiple-data-sources-power-query
