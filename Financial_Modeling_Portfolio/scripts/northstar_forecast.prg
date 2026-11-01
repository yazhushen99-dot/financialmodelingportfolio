' Northstar Industrial Components | EViews reproduction
' Synthetic demonstration. Target: EViews 14, Windows.
' Status: source reviewed against official documentation; native run not performed.
' Before running, set EViews default directory to the extracted portfolio root.
' Example in command window: cd "C:\work\finance_portfolio"
' The input CSV is sorted monthly, Jan 2018-Dec 2026, with 2026 revenue blank.
'
' Outputs are written into the existing analysis folder with an eviews_ prefix.

wfopen(type=text) "data/model_input_combined.csv" delim=comma
pagestruct(freq=m, start=2018m01)
smpl @all
series ln_revenue = log(revenue_musd)
series m2 = (month=2)
series m3 = (month=3)
series m4 = (month=4)
series m5 = (month=5)
series m6 = (month=6)
series m7 = (month=7)
series m8 = (month=8)
series m9 = (month=9)
series m10 = (month=10)
series m11 = (month=11)
series m12 = (month=12)

' January is the omitted month. HC1 matches Stata regress,vce(robust).
' Holdout predictions use realized industrial_index, a conditional forecast.
smpl 2018m01 2024m12
equation driver_train.ls(cov=hc, hctype=hc1) ln_revenue c trend industrial_index m2 m3 m4 m5 m6 m7 m8 m9 m10 m11 m12
equation trend_train.ls(cov=hc, hctype=hc1) ln_revenue c trend m2 m3 m4 m5 m6 m7 m8 m9 m10 m11 m12

smpl 2025m01 2025m12
driver_train.forecast(f=na) ln_driver_holdout
trend_train.forecast(f=na) ln_trend_holdout
series pred_driver = exp(ln_driver_holdout)
series pred_trend = exp(ln_trend_holdout)
series pred_naive = revenue_musd(-12)

' exp(log forecast) is used without a bias/smearing correction.
' Forecasts are conditional medians in revenue units, not corrected means.
scalar driver_n = @obs(pred_driver)
scalar driver_mae = @mean(@abs(revenue_musd-pred_driver))
scalar driver_rmse = @sqrt(@mean((revenue_musd-pred_driver)^2))
scalar driver_mape = 100*@mean(@abs((revenue_musd-pred_driver)/revenue_musd))
scalar trend_n = @obs(pred_trend)
scalar trend_mae = @mean(@abs(revenue_musd-pred_trend))
scalar trend_rmse = @sqrt(@mean((revenue_musd-pred_trend)^2))
scalar trend_mape = 100*@mean(@abs((revenue_musd-pred_trend)/revenue_musd))
scalar naive_n = @obs(pred_naive)
scalar naive_mae = @mean(@abs(revenue_musd-pred_naive))
scalar naive_rmse = @sqrt(@mean((revenue_musd-pred_naive)^2))
scalar naive_mape = 100*@mean(@abs((revenue_musd-pred_naive)/revenue_musd))

table(4,5) validation_metrics
validation_metrics(1,1) = "model"
validation_metrics(1,2) = "n"
validation_metrics(1,3) = "mae_musd"
validation_metrics(1,4) = "rmse_musd"
validation_metrics(1,5) = "mape_pct"
validation_metrics(2,1) = "driver"
validation_metrics(2,2) = driver_n
validation_metrics(2,3) = driver_mae
validation_metrics(2,4) = driver_rmse
validation_metrics(2,5) = driver_mape
validation_metrics(3,1) = "trend"
validation_metrics(3,2) = trend_n
validation_metrics(3,3) = trend_mae
validation_metrics(3,4) = trend_rmse
validation_metrics(3,5) = trend_mape
validation_metrics(4,1) = "naive"
validation_metrics(4,2) = naive_n
validation_metrics(4,3) = naive_mae
validation_metrics(4,4) = naive_rmse
validation_metrics(4,5) = naive_mape
validation_metrics.save(t=csv, f) "analysis/eviews_validation_metrics.csv"

' Only now refit both models using all 96 known observations.
smpl 2018m01 2025m12
equation driver_full.ls(cov=hc, hctype=hc1) ln_revenue c trend industrial_index m2 m3 m4 m5 m6 m7 m8 m9 m10 m11 m12
equation trend_full.ls(cov=hc, hctype=hc1) ln_revenue c trend m2 m3 m4 m5 m6 m7 m8 m9 m10 m11 m12
smpl 2026m01 2026m12
driver_full.forecast(f=na) ln_driver_future
trend_full.forecast(f=na) ln_trend_future
series forecast_driver = exp(ln_driver_future)
series forecast_trend = exp(ln_trend_future)
series forecast_naive = revenue_musd(-12)
scalar forecast_2026_driver = @sum(forecast_driver)
scalar forecast_2026_trend = @sum(forecast_trend)
scalar forecast_2026_naive = @sum(forecast_naive)
table(4,2) annual_forecasts
annual_forecasts(1,1) = "model"
annual_forecasts(1,2) = "2026_revenue_musd"
annual_forecasts(2,1) = "driver"
annual_forecasts(2,2) = forecast_2026_driver
annual_forecasts(3,1) = "trend"
annual_forecasts(3,2) = forecast_2026_trend
annual_forecasts(4,1) = "naive"
annual_forecasts(4,2) = forecast_2026_naive
annual_forecasts.save(t=csv, f) "analysis/eviews_annual_forecasts.csv"

' Retain all raw data, equations, diagnostics and forecasts for review.
smpl @all
wfsave "analysis/eviews_northstar_analysis.wf1"
show validation_metrics
