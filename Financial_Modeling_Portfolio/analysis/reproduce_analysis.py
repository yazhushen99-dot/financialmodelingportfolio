"""Reproduce a fictional financial-modeling portfolio. No real company data.
Run: python analysis/reproduce_analysis.py (Python 3, numpy, pandas, matplotlib).
The XLSX is a separate editable implementation; this script is its independent check.
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
for folder in ['data', 'analysis', 'visuals']:
    (ROOT / folder).mkdir(exist_ok=True)


def design(df, driver=True):
    x = [np.ones(len(df)), df.trend.to_numpy(float)]
    names = ['constant', 'trend']
    if driver:
        x.append(df.industrial_index.to_numpy(float))
        names.append('industrial_index')
    for month in range(2, 13):
        x.append((df.month.to_numpy() == month).astype(float))
        names.append(f'month_{month:02d}')
    return np.column_stack(x), names


def ols(df, driver=True):
    x, names = design(df, driver)
    y = np.log(df.revenue_musd.to_numpy(float))
    beta, _, rank, _ = np.linalg.lstsq(x, y, rcond=None)
    residuals = y - x @ beta
    n, k = x.shape
    inv = np.linalg.inv(x.T @ x)
    covariance = n / (n-k) * inv @ ((x * residuals[:, None]).T @ (x * residuals[:, None])) @ inv
    se = np.sqrt(np.diag(covariance))
    r2 = 1 - np.sum(residuals**2) / np.sum((y-y.mean())**2)
    return {'beta': beta, 'se': se, 'names': names, 'n': n, 'rank': int(rank), 'r2': float(r2), 'adj_r2': float(1-(1-r2)*(n-1)/(n-k))}


def forecast(df, fit, driver=True):
    return np.exp(design(df, driver)[0] @ fit['beta'])


def score(actual, pred):
    error = pred-actual
    return {'rmse_musd': float(np.sqrt(np.mean(error**2))), 'mae_musd': float(np.mean(abs(error))), 'mape_pct': float(np.mean(abs(error/actual))*100)}


def generate_sources():
    rng = np.random.default_rng(20261101)
    dates = pd.date_range('2018-01-01', '2025-12-01', freq='MS')
    t = np.arange(1, 97)
    macro = 100 + 0.11*t + 3*np.sin(t/5.0) + rng.normal(0, .75, len(t))
    # Known synthetic process; break in 2020 is an illustrative demand shock.
    macro[(dates.year == 2020) & (dates.month >= 3) & (dates.month <= 8)] -= 9
    season = np.array([-.07,-.04,.01,.03,.05,.04,-.02,-.03,.04,.06,.03,-.10])
    logrev = .95 + .0055*t + .016*macro + season[dates.month-1] + rng.normal(0, .022, len(t))
    df = pd.DataFrame({'date': dates.strftime('%Y-%m-%d'), 'revenue_musd': np.exp(logrev), 'industrial_index': macro, 'month': dates.month, 'trend': t, 'split': np.where(dates.year < 2025,'train','validation')})
    df.to_csv(ROOT/'data/monthly_operating_data.csv', index=False, float_format='%.12f')
    future = pd.DataFrame({'date':pd.date_range('2026-01-01','2026-12-01',freq='MS').strftime('%Y-%m-%d'), 'industrial_index':np.linspace(macro[-1]+.10,macro[-1]+1.20,12), 'month':np.arange(1,13),'trend':np.arange(97,109)})
    future.to_csv(ROOT/'data/future_drivers.csv', index=False, float_format='%.12f')
    combined=pd.concat([df,future.assign(revenue_musd=np.nan,split='forecast')[df.columns]],ignore_index=True)
    combined.to_csv(ROOT/'data/model_input_combined.csv',index=False,float_format='%.12f')
    annual = df.assign(year=pd.to_datetime(df.date).dt.year).groupby('year').revenue_musd.sum()
    history=[]
    prev={'revenue':annual[2020]/1.03,'cash':25.,'ar':annual[2020]/1.03*.15,'inventory':annual[2020]/1.03*.55*.18,'ap':annual[2020]/1.03*.55*.14,'ppe':100.,'debt':90.}
    prev['equity']=prev['cash']+prev['ar']+prev['inventory']+prev['ppe']-prev['ap']-prev['debt']
    for y in range(2020,2026):
        revenue=float(annual[y]); cogs=revenue*(.58-(y-2020)*.003); opex=revenue*.23
        depreciation=prev['ppe']*.09; interest=prev['debt']*.055
        tax=max(revenue-cogs-opex-depreciation-interest,0)*.25
        ni=revenue-cogs-opex-depreciation-interest-tax
        ar=revenue*.15; inventory=cogs*.18; ap=cogs*.14; capex=revenue*.06
        debt_repayment=5.; new_borrowing=0.; dividends=max(ni,0)*.40
        dnwc=ar+inventory-ap-(prev['ar']+prev['inventory']-prev['ap'])
        cfo=ni+depreciation-dnwc; cfi=-capex; cff=new_borrowing-debt_repayment-dividends
        cash=prev['cash']+cfo+cfi+cff; debt=prev['debt']-debt_repayment
        ppe=prev['ppe']+capex-depreciation; equity=prev['equity']+ni-dividends
        row=dict(year=y,revenue=revenue,cogs=cogs,opex=opex,depreciation=depreciation,interest=interest,tax=tax,net_income=ni,ar=ar,inventory=inventory,ap=ap,ppe=ppe,cash=cash,debt=debt,equity=equity,capex=capex,dividends=dividends,new_borrowing=new_borrowing,debt_repayment=debt_repayment)
        assert abs(cash+ar+inventory+ppe-ap-debt-equity)<1e-9
        history.append(row); prev=row
    pd.DataFrame(history).to_csv(ROOT/'data/historical_financials.csv',index=False,float_format='%.12f')
    return df,future,history


def financial_case(history, assumptions, wacc=.095, g=.025):
    prev=history[-1].copy(); rows=[]
    for i,year in enumerate(range(2026,2031)):
        a={k:v[i] for k,v in assumptions.items()}
        revenue=prev['revenue']*(1+a['revenue_growth']); cogs=revenue*(1-a['gross_margin']); opex=revenue*a['opex_pct']
        depreciation=prev['ppe']*a['da_rate']; interest=prev['debt']*a['interest_rate']; ebit=revenue-cogs-opex-depreciation
        tax=max(ebit-interest,0)*a['tax_rate']; ni=ebit-interest-tax
        ar=revenue*a['dso']/365; inventory=cogs*a['dio']/365; ap=cogs*a['dpo']/365
        capex=revenue*a['capex_pct']; ppe=prev['ppe']+capex-depreciation
        new_borrowing=a['new_borrowing']; debt_repayment=min(prev['debt'],a['debt_repayment']); debt=prev['debt']+new_borrowing-debt_repayment
        dividends=max(ni,0)*a['payout']; dnwc=ar+inventory-ap-(prev['ar']+prev['inventory']-prev['ap'])
        cfo=ni+depreciation-dnwc; cfi=-capex; cff=new_borrowing-debt_repayment-dividends
        cash=prev['cash']+cfo+cfi+cff; equity=prev['equity']+ni-dividends
        ufcf=ebit-max(ebit,0)*a['tax_rate']+depreciation-capex-dnwc
        row=dict(year=year,revenue=revenue,cogs=cogs,opex=opex,depreciation=depreciation,interest=interest,tax=tax,net_income=ni,ar=ar,inventory=inventory,ap=ap,ppe=ppe,cash=cash,debt=debt,equity=equity,capex=capex,dividends=dividends,new_borrowing=new_borrowing,debt_repayment=debt_repayment,cfo=cfo,cfi=cfi,cff=cff,ebit=ebit,ebitda=ebit+depreciation,delta_nwc=dnwc,ufcf=ufcf,balance_check=cash+ar+inventory+ppe-ap-debt-equity,cash_check=cash-prev['cash']-cfo-cfi-cff)
        rows.append(row);prev=row
    pv=sum(r['ufcf']/(1+wacc)**(i+1) for i,r in enumerate(rows)); terminal=rows[-1]['ufcf']*(1+g)/(wacc-g); tvpv=terminal/(1+wacc)**5
    ev=pv+tvpv;equity=ev+history[-1]['cash']-history[-1]['debt']
    return {'annual_forecast':rows,'enterprise_value':ev,'equity_value':equity,'pv_explicit_fcf':pv,'terminal_value':terminal,'pv_terminal_value':tvpv,'terminal_share':tvpv/ev,'wacc':wacc,'terminal_growth':g,'opening_cash':history[-1]['cash'],'opening_debt':history[-1]['debt'],'max_balance_error':max(abs(r['balance_check']) for r in rows),'max_cash_error':max(abs(r['cash_check']) for r in rows)}


def main():
    df,future,history=generate_sources()
    train=df[df.split=='train'];valid=df[df.split=='validation'];actual=valid.revenue_musd.to_numpy()
    dfit=ols(train,True);tfit=ols(train,False)
    predictions={'Driver regression':forecast(valid,dfit,True),'Trend and seasonality':forecast(valid,tfit,False),'Seasonal naive':df[df.date.str.startswith('2024')].revenue_musd.to_numpy()}
    scores={name:score(actual,p) for name,p in predictions.items()}
    selected=min(scores,key=lambda n:scores[n]['rmse_musd'])
    full_driver=ols(df,True);full_trend=ols(df,False)
    future_preds={'Driver regression':forecast(future,full_driver,True),'Trend and seasonality':forecast(future,full_trend,False),'Seasonal naive':valid.revenue_musd.to_numpy()}
    annual2026=float(future_preds[selected].sum()); growth=annual2026/history[-1]['revenue']-1
    coefrows=[]
    for model,fit,scope in [('Driver regression',dfit,'training'),('Trend and seasonality',tfit,'training'),('Driver regression',full_driver,'full_refit'),('Trend and seasonality',full_trend,'full_refit')]:
        for n,b,se in zip(fit['names'],fit['beta'],fit['se']):coefrows.append({'model':model,'scope':scope,'term':n,'coefficient':b,'hc1_standard_error':se,'n':fit['n'],'r_squared':fit['r2']})
    pd.DataFrame(coefrows).to_csv(ROOT/'analysis/model_results.csv',index=False,float_format='%.12f')
    valout=valid[['date','revenue_musd']].copy()
    for name,p in predictions.items():valout[name.lower().replace(' ','_')]=p
    valout.to_csv(ROOT/'analysis/forecast_validation.csv',index=False,float_format='%.12f')
    futout=future.copy()
    for name,p in future_preds.items():futout[name.lower().replace(' ','_')]=p
    futout.to_csv(ROOT/'analysis/forecast_2026.csv',index=False,float_format='%.12f')
    base={'revenue_growth':[growth,.065,.055,.045,.04],'gross_margin':[.44,.445,.45,.45,.45],'opex_pct':[.23,.228,.225,.225,.225],'da_rate':[.09]*5,'interest_rate':[.055]*5,'tax_rate':[.25]*5,'dso':[54,53,52,52,52],'dio':[65,64,63,63,63],'dpo':[51]*5,'capex_pct':[.065,.065,.06,.06,.06],'debt_repayment':[5]*5,'new_borrowing':[0]*5,'payout':[.4]*5}
    down={'revenue_growth':[growth-.08,.02,.025,.03,.035],'gross_margin':[.40,.405,.41,.415,.42],'opex_pct':[.245,.243,.24,.238,.235],'da_rate':[.09]*5,'interest_rate':[.075]*5,'tax_rate':[.25]*5,'dso':[65,64,63,62,60],'dio':[78,76,74,72,70],'dpo':[51]*5,'capex_pct':[.055]*5,'debt_repayment':[5]*5,'new_borrowing':[0]*5,'payout':[.2]*5}
    cases={'Base':financial_case(history,base),'Downside':financial_case(history,down)}
    metrics={'company':'Northstar Industrial Components','data_status':'Fictional company and deterministic simulated data; skill demonstration, not employment evidence.','currency':'USD millions','valuation_date':'2025-12-31','training_period':'2018-01 to 2024-12','validation_period':'2025-01 to 2025-12','training_n':84,'validation_n':12,'selected_model':selected,'selection_rule':'Lowest 2025 holdout RMSE; selection is descriptive and should be confirmed on additional rolling windows.','retransformation':'exp(predicted log revenue), no smearing correction; forecasts represent conditional median, not unbiased conditional mean.','future_macro_assumption':'2026 industrial_index increases by 0.10 per month from December2025; hypothetical input known at forecast origin, not observed 2026 values.','2026_revenue_forecast':annual2026,'2026_revenue_growth':growth,'model_metrics':scores,'training_driver_r2':dfit['r2'],'assumptions':{'Base':base,'Downside':down},'historical_financials':history,'cases':cases,'sensitivity':[[{'wacc':w,'g':g,'equity_value':financial_case(history,base,w,g)['equity_value']}for g in [.015,.02,.025,.03,.035]]for w in [.075,.085,.095,.105,.115]],'model_notes':['Annual year-end discounting; terminal perpetuity grows 2030 unleveredFCF at2.5%.','Taxes=25% of positive taxable earnings; no tax-loss carryforwards or tax benefit for losses.','Interest uses opening debt; cash earns no interest.','D&A=9% of opening netPP&E is an illustrative calibrated aggregate depreciation driver, not an asset-vintage schedule.','No acquisitions, leases, FX, goodwill, or other assets/liabilities. All cash is treated as non-operating in the EV-to-equity bridge.','Closing cash is derived from operating/investing/financing cashflows; equity rolls from retained earnings, not a balancing plug.','2027–2030 growth assumptions are analyst scenarios, not statistical forecasts.','Validation uses observed holdout industrial_index, so the driver-model test is conditional on realized predictors; 2026 projection is conditional on assumed predictors.']}
    metrics['model_notes'].append('Terminal value extrapolates final-year FCF without separately normalizing reinvestment to terminal growth; a steady-state return-on-invested-capital analysis is outside this illustration.')
    metrics['model_notes'].append('The annual forecast is the sum of monthly conditional medians, used as a planning total; it is not a formal annual conditional mean or median. HC1 addresses heteroskedasticity, not serial correlation.')
    (ROOT/'analysis/metrics.json').write_text(json.dumps(metrics,indent=2),encoding='utf-8')
    pd.DataFrame([dict(scenario=case,**row) for case,result in cases.items() for row in result['annual_forecast']]).to_csv(ROOT/'analysis/annual_forecast.csv',index=False,float_format='%.12f')
    payload={'metrics':metrics,'monthly':df.to_dict(orient='records'),'future':futout.to_dict(orient='records'),'validation':valout.to_dict(orient='records'),'coefficients':coefrows}
    (ROOT/'analysis/workbook_payload.json').write_text(json.dumps(payload,indent=2),encoding='utf-8')
    checks={'training_rank':dfit['rank'],'driver_parameter_count':len(dfit['names']),'monthly_rows':len(df),'dates_unique':bool(df.date.is_unique),'validation_has_no_training_dates':bool(set(train.date).isdisjoint(valid.date)),'historical_balance_max_error':max(abs(r['cash']+r['ar']+r['inventory']+r['ppe']-r['ap']-r['debt']-r['equity']) for r in history),'cases':{c:{'balance_max_error':v['max_balance_error'],'cash_max_error':v['max_cash_error']}for c,v in cases.items()}}
    assert dfit['rank']==len(dfit['names'])
    assert checks['dates_unique'] and checks['validation_has_no_training_dates']
    assert all(v['max_balance_error']<1e-8 and v['max_cash_error']<1e-8 for v in cases.values())
    pert={k:list(v)for k,v in base.items()};pert['revenue_growth'][-1]+=.01
    assert abs(financial_case(history,pert)['equity_value']-cases['Base']['equity_value'])>1e-6
    checks['later_period_growth_perturbation_changes_equity']=True
    checks['python_engine']='NumPy least squares and explicit HC1 covariance; deterministic source seed20261101'
    (ROOT/'analysis/python_validation.json').write_text(json.dumps(checks,indent=2))
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False})
    fig,ax=plt.subplots(figsize=(9,4.2));x=np.arange(12)
    ax.plot(x,actual,label='Synthetic actual',color='#172E49',linewidth=2.4)
    for name,color in [('Driver regression','#008577'),('Trend and seasonality','#BA6B2A'),('Seasonal naive','#8293A8')]:ax.plot(x,predictions[name],label=name,color=color,linewidth=1.6,linestyle='--'if name!='Driver regression'else'-')
    ax.set_xticks(x,['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']);ax.set_ylabel('Revenue (USD millions)');ax.set_title('2025 holdout forecast comparison',loc='left',weight='bold');ax.legend(ncol=2,frameon=False,fontsize=9);ax.grid(axis='y',alpha=.15);fig.tight_layout();fig.savefig(ROOT/'visuals/model_forecast_validation.png',dpi=180);plt.close(fig)
    fig,ax=plt.subplots(figsize=(9,4.2));years=list(range(2021,2031));h=[r['revenue']for r in history[1:]]
    ax.plot(years[:5],h,color='#172E49',marker='o',label='Synthetic history')
    for name,col in [('Base','#008577'),('Downside','#BA6B2A')]:ax.plot(years[4:],[h[-1]]+[r['revenue']for r in cases[name]['annual_forecast']],marker='o',color=col,label=name)
    ax.axvline(2025.5,color='#B8C2CF',linestyle=':');ax.set_xticks(years);ax.set_ylabel('Revenue (USD millions)');ax.set_title('Revenue scenarios',loc='left',weight='bold');ax.legend(frameon=False);ax.grid(axis='y',alpha=.15);fig.tight_layout();fig.savefig(ROOT/'visuals/model_revenue_scenarios.png',dpi=180);plt.close(fig)
    print(json.dumps({'selected_model':selected,'2026_revenue_forecast':annual2026,'2026_growth':growth,'scores':scores,'cases':{k:{'EV':v['enterprise_value'],'Equity':v['equity_value'],'FCF2030':v['annual_forecast'][-1]['ufcf']}for k,v in cases.items()}},indent=2))

if __name__=='__main__':main()
