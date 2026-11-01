/*
Northstar Industrial Components | Stata reproducibility script
Synthetic demonstration data. This is not a client engagement or employer record.
Target: Stata 17 or later, no community packages required.
Status: source reviewed; not executed in a native Stata installation here.
Run from the portfolio root: do scripts/northstar_forecast.do
Or pass the portfolio path: do scripts/northstar_forecast.do "C:/path/portfolio"
*/

version 17.0
clear all
set more off
args root
if `"`root'"' == "" local root "."
cd `"`root'"'
capture mkdir "analysis/native_stata"
capture log close _all
log using "analysis/native_stata/run.log", text replace

import delimited using "data/model_input_combined.csv", clear varnames(1) stringcols(1) encoding(utf8)
confirm numeric variable revenue_musd industrial_index month trend
generate double daily_date = daily(date, "YMD")
assert !missing(daily_date)
generate int mdate = mofd(daily_date)
format mdate %tm
isid mdate
sort mdate
assert _N == 108
assert mdate == ym(2018, 1) + _n - 1
assert month == month(dofm(mdate))
assert trend == _n
assert !missing(industrial_index, month, trend)
assert revenue_musd > 0 & !missing(revenue_musd) if mdate <= ym(2025, 12)
assert missing(revenue_musd) if mdate >= ym(2026, 1)
assert split == "train" if mdate <= ym(2024, 12)
assert split == "validation" if inrange(mdate, ym(2025, 1), ym(2025, 12))
assert split == "forecast" if mdate >= ym(2026, 1)
tsset mdate, monthly
generate double ln_revenue = ln(revenue_musd)

* Holdout is a fixed, untouched twelve-month 2025 test window.
* Validation uses realized 2025 industrial_index: conditional forecast, not an
* ex-ante macro forecast. No model is selected on fitted-sample R-squared.
regress ln_revenue c.trend c.industrial_index ib1.month if split == "train", vce(robust)
assert e(N) == 84
estimates store driver_train
predict double ln_driver_holdout if split == "validation", xb
generate double pred_driver = exp(ln_driver_holdout)

regress ln_revenue c.trend ib1.month if split == "train", vce(robust)
assert e(N) == 84
estimates store trend_train
predict double ln_trend_holdout if split == "validation", xb
generate double pred_trend = exp(ln_trend_holdout)
generate double pred_naive = L12.revenue_musd if split == "validation"

* Explicit retransformation: exp(log forecast), no smearing correction.
* These are conditional-median level forecasts, not bias-corrected means.
tempfile scoredata
tempname scores
postfile `scores' str20 model double n mae_musd rmse_musd mape_pct using "`scoredata'", replace
foreach model in driver trend naive {
    generate double ae_`model' = abs(revenue_musd - pred_`model') if split == "validation"
    generate double se_`model' = (revenue_musd - pred_`model')^2 if split == "validation"
    generate double ape_`model' = 100 * ae_`model' / revenue_musd if split == "validation"
    quietly summarize ae_`model' if split == "validation", meanonly
    scalar mae_`model' = r(mean)
    scalar n_`model' = r(N)
    assert n_`model' == 12
    quietly summarize se_`model' if split == "validation", meanonly
    scalar rmse_`model' = sqrt(r(mean))
    quietly summarize ape_`model' if split == "validation", meanonly
    scalar mape_`model' = r(mean)
    post `scores' ("`model'") (n_`model') (mae_`model') (rmse_`model') (mape_`model')
}
postclose `scores'
preserve
use "`scoredata'", clear
format mae_musd rmse_musd mape_pct %12.6f
list, noobs
export delimited using "analysis/native_stata/validation_metrics.csv", replace
restore

preserve
keep if split == "validation"
keep date revenue_musd pred_driver pred_trend pred_naive
export delimited using "analysis/native_stata/validation_predictions.csv", replace
restore

* Final refit uses 96 observed months only AFTER holdout scores are computed.
* Export both models. Review the fixed holdout results before choosing one.
regress ln_revenue c.trend c.industrial_index ib1.month if split != "forecast", vce(robust)
assert e(N) == 96
estimates store driver_full
predict double ln_driver_future if split == "forecast", xb
generate double forecast_driver = exp(ln_driver_future)
matrix b = e(b)
matrix V = e(V)
local terms : colnames b
tempfile coefficientdata
tempname coefficients
postfile `coefficients' str40 term double coefficient se_hc1 using "`coefficientdata'", replace
local j = 1
foreach term of local terms {
    post `coefficients' ("`term'") (b[1,`j']) (sqrt(V[`j',`j']))
    local ++j
}
postclose `coefficients'
preserve
use "`coefficientdata'", clear
export delimited using "analysis/native_stata/driver_full_coefficients.csv", replace
restore

regress ln_revenue c.trend ib1.month if split != "forecast", vce(robust)
assert e(N) == 96
estimates store trend_full
predict double ln_trend_future if split == "forecast", xb
generate double forecast_trend = exp(ln_trend_future)
generate double forecast_naive = L12.revenue_musd if split == "forecast"
preserve
keep if split == "forecast"
assert !missing(forecast_driver, forecast_trend, forecast_naive)
keep date industrial_index month trend forecast_driver forecast_trend forecast_naive
export delimited using "analysis/native_stata/forecast_2026.csv", replace
restore
save "analysis/native_stata/northstar_analysis.dta", replace
log close
