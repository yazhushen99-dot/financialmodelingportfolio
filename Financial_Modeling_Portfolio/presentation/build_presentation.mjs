/**
 * Build the editable five-slide portfolio deck from analysis/metrics.json.
 * Run: node presentation/build_presentation.mjs [portfolio-root]
 * Requires @oai/artifact-tool. CODEX_PRIMARY_RUNTIME_NODE_MODULES may identify
 * the bundled installation. Codex validation also requires the presentation
 * skill's container_tools/artifact_tool_utils.mjs and its bundled validators,
 * plus CODEX_PRIMARY_RUNTIME_PYTHON. Set CODEX_PRESENTATIONS_SKILL_ROOT to
 * override the default skill location. Without those helpers, the deck still
 * exports, but validation is explicitly reported as not run. PDF conversion
 * falls back to LibreOffice when CODEX_PRIMARY_RUNTIME_ROOT is available.
 * Numbers are read from the accompanying analysis;
 * chart data are static snapshots, while the separate XLSX is the live model.
 */
import fs from 'node:fs/promises';
import path from 'node:path';
import {spawnSync} from 'node:child_process';
import { fileURLToPath, pathToFileURL } from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(process.argv[2] || path.join(here, '..'));
const out = path.join(root, 'presentation');
const previews = path.join(root, 'visuals', 'slides');
const build = path.resolve(process.env.PORTFOLIO_SLIDE_BUILD_DIR || path.join(root, '.presentation-build'));
await Promise.all([out, previews, build].map(p => fs.mkdir(p, {recursive:true})));
const bundle = process.env.CODEX_PRIMARY_RUNTIME_NODE_MODULES;
const moduleUrl = bundle ? pathToFileURL(path.join(bundle, '@oai/artifact-tool/dist/artifact_tool.mjs')).href : '@oai/artifact-tool';
const {Presentation, PresentationFile} = await import(moduleUrl);
const metrics = JSON.parse(await fs.readFile(path.join(root,'analysis/metrics.json'),'utf8'));
const validation = JSON.parse(await fs.readFile(path.join(root,'analysis/python_validation.json'),'utf8'));
const csv = (await fs.readFile(path.join(root,'analysis/forecast_validation.csv'),'utf8')).trim().split(/\r?\n/);
const keys = csv.shift().split(',');
const monthly = csv.map(line => Object.fromEntries(line.split(',').map((v,i)=>[keys[i],i ? Number(v) : v])));
const base = metrics.cases.Base, down = metrics.cases.Downside;
const money = n => '$' + n.toFixed(1) + 'm';
const num = n => n.toFixed(3);
const pct = (n,d=1) => (100*n).toFixed(d)+'%';
const FONT='DejaVu Sans';
const C={navy:'#102A43',teal:'#087F8C',ink:'#243B53',muted:'#526D82',light:'#E8F0F4',rule:'#D8E2EA',white:'#FFFFFF',rust:'#AA603E'};
const p=Presentation.create({slideSize:{width:1280,height:720}});

function text(slide,name,value,x,y,w,h,size=24,color=C.ink,bold=false,align='left'){
 const shape=slide.shapes.add({name,geometry:'textbox',position:{left:x,top:y,width:w,height:h},fill:'none',line:{style:'solid',fill:'none',width:0}});
 shape.text=value;
 shape.text.style={typeface:FONT,fontSize:size,color,bold,alignment:align,verticalAlignment:'top',autoFit:'none',wrap:'square',insets:0};
 return shape;
}
function line(slide,y,color=C.rule){
 return slide.shapes.add({name:'horizontal-rule',geometry:'rect',position:{left:64,top:y,width:1152,height:1},fill:color,line:{style:'solid',fill:'none',width:0}});
}
function slide(title,subtitle=''){
 const s=p.slides.add(); s.background.fill=C.white;
 text(s,'title',title,64,47,1152,60,42,C.navy,true);
 if(subtitle) text(s,'subtitle',subtitle,64,117,1152,38,20,C.muted);
 line(s,650);
 text(s,'provenance','Yazhu Shen  |  Fictional company • simulated data • demonstration',64,668,1090,23,15,C.muted);
 text(s,'folio',String(p.slides.items.length),1155,667,60,25,16,C.muted,false,'right');
 return s;
}
function table(s,values,x,y,w,h,colwidths,font=21){
 const t=s.tables.add({rows:values.length,columns:values[0].length,left:x,top:y,width:w,height:h,columnWidths:colwidths,values});
 t.borders.assign({style:'solid',fill:C.rule,width:1});
 for(let r=0;r<values.length;r++) for(let c=0;c<values[0].length;c++){
  const cell=t.getCell(r,c);cell.fill=r===0?C.navy:(r%2===1?C.white:'#F3F7FA');
  cell.text.style={typeface:FONT,fontSize:font,color:r===0?C.white:C.ink,bold:r===0,verticalAlignment:'middle',insets:12,wrap:'square',autoFit:'none'};
 }
 return t;
}
function chart(s,name,categories,series,x,y,w,h,{min=0,max,unit=50}={}){
 const ch=s.charts.add('line',{
  name,position:{left:x,top:y,width:w,height:h},categories,lineOptions:{smooth:false},
  series:series.map((a)=>({name:a.name,values:a.values.map(n=>Number(n.toFixed(6))),line:{style:'solid',fill:a.color,width:3},marker:{symbol:'circle',size:4,fill:a.color}})),
  hasLegend:true,legend:{position:'bottom',overlay:false,textStyle:{typeface:FONT,fontSize:17}},
  xAxis:{textStyle:{typeface:FONT,fontSize:17},line:{style:'solid',fill:C.rule,width:1}},
  yAxis:{min,...(max!==undefined?{max}:{}),majorUnit:unit,numberFormatCode:'0',textStyle:{typeface:FONT,fontSize:17},majorGridlines:{style:'solid',fill:C.rule,width:1}},
  chartFill:C.white,chartLine:{style:'solid',fill:'none',width:0},plotAreaFill:C.white,plotAreaLine:{style:'solid',fill:'none',width:0}
 });
 return ch;
}

// 1 — A dedicated cover with a specific work sample, not a client claim.
{
 const s=p.slides.add();s.background.fill=C.navy;
 text(s,'eyebrow','FINANCIAL ANALYSIS PORTFOLIO',64,67,1152,38,21,'#7CD0D0',true);
 text(s,'cover-title','Financial modeling\nand cash-flow forecasting',64,159,1135,166,57,C.white,true);
 text(s,'cover-company',metrics.company,64,358,1152,47,30,C.white);
 text(s,'cover-purpose','A traceable work sample: monthly revenue analysis, linked financial\nstatements, scenario testing and discounted cash-flow valuation.',64,426,1152,85,25,'#D5E2EB');
 text(s,'author','Yazhu Shen',64,574,780,39,25,C.white,true);
 text(s,'scope','96 monthly observations  |  2026–2030 projections',64,617,1152,30,20,'#B8CDDA');
 text(s,'disclosure','Fictional company and simulated data. Prepared as a skills demonstration.',64,670,1152,25,15,'#B8CDDA');
 s.speakerNotes.text='Purpose: demonstrate a reproducible analytical workflow using a fictional company and deterministic simulated data. This is not evidence of an actual client engagement or past employment. All reported outputs come from analysis/metrics.json and the included Python reference implementation. The Excel workbook is a separate interactive artifact; slide charts contain editable snapshots.';
}

// 2 — Native table emphasizes analytical hand-offs and review points.
{
 const s=slide('From monthly data to a valuation','Each stage has a visible input, output and review point.');
 table(s,[
  ['Stage','Model output','Review point'],
  ['1  Prepare the data','96 monthly observations\n2018–2025','Dates, units and duplicate checks'],
  ['2  Compare forecasts','Driver regression, trend/seasonal\nand seasonal-naive benchmark','84 training months; 12 holdout months'],
  ['3  Build the financial model','Linked income statement, balance\nsheet and cash-flow projections','Cash roll-forward and balance checks'],
  ['4  Value and stress-test','Unlevered cash flows, DCF\nand Base/Downside scenarios','WACC, terminal growth and liquidity']
 ],64,179,1152,376,[310,455,387],21);
 text(s,'workflow-note','2026 revenue uses the selected statistical model. 2027–2030 growth rates are explicit scenario assumptions.',64,582,1152,48,20,C.muted);
 s.speakerNotes.text='Sources: data/monthly_operating_data.csv (or corresponding source CSV supplied in data/), analysis/reproduce_analysis.py and analysis/metrics.json. Data split: 2018-01 to 2024-12 training, 2025-01 to 2025-12 holdout. The driver validation uses observed holdout industrial_index, so accuracy is conditional on realized predictors. The 2026 industrial-index path is an assumed scenario, not observed data. All cash is treated as non-operating for the equity bridge. See the model notes for simplifications.';
}

// 3 — Exact computed out-of-sample comparison, with its main limitation.
{
 const s=slide('Driver regression has the lowest holdout error','2025 conditional validation • monthly revenue, USD millions');
 chart(s,'Holdout actual and fitted forecast',monthly.map(d=>new Date(d.date).toLocaleString('en',{month:'short',timeZone:'UTC'})),[
  {name:'Actual (simulated)',values:monthly.map(d=>d.revenue_musd),color:C.navy},
  {name:'Driver regression',values:monthly.map(d=>d.driver_regression),color:C.teal}
 ],64,176,698,358,{min:15,max:35,unit:5});
 table(s,[
  ['Model','RMSE'],
  ['Driver regression',num(metrics.model_metrics['Driver regression'].rmse_musd)],
  ['Trend + seasonality',num(metrics.model_metrics['Trend and seasonality'].rmse_musd)],
  ['Seasonal naive',num(metrics.model_metrics['Seasonal naive'].rmse_musd)]
 ],800,190,416,250,[289,127],20);
 text(s,'mape-label','Driver MAPE',800,465,416,30,20,C.muted);
 text(s,'mape-value',metrics.model_metrics['Driver regression'].mape_pct.toFixed(2)+'%',800,500,416,61,43,C.teal,true);
 text(s,'validation-caveat','The driver model uses realized holdout index values. This measures conditional accuracy;\nadditional rolling-window tests are needed before operational use.',64,579,1152,54,20,C.muted);
 s.speakerNotes.text='Sources: analysis/forecast_validation.csv; analysis/metrics.json:model_metrics; analysis/python_validation.json. Training n=84, holdout n=12. Driver training R-squared='+metrics.training_driver_r2+'. Model selection is descriptive: the same holdout selects and compares the models, so this is not an untouched final test. Forecasts exponentiate log predictions without a smearing adjustment and represent a conditional median. RMSE is measured in USD millions; MAPE is in percent. Reference on accuracy and out-of-sample evaluation: https://otexts.com/fpp3/accuracy.html .';
}

// 4 — Chart plus a native valuation table; no duplicated numerical chart table.
{
 const s=slide('Downside enterprise value falls '+pct(1-down.enterprise_value/base.enterprise_value),'Scenario forecasts • USD millions • valuation date 31 December 2025');
 text(s,'chart-heading','Revenue projection',64,174,698,32,23,C.navy,true);
 chart(s,'Scenario revenue',base.annual_forecast.map(d=>String(d.year)),[
  {name:'Base',values:base.annual_forecast.map(d=>d.revenue),color:C.teal},
  {name:'Downside',values:down.annual_forecast.map(d=>d.revenue),color:C.rust}
 ],64,213,698,325,{min:250,max:450,unit:50});
 table(s,[
  ['DCF output','Base','Downside'],
  ['Enterprise value',base.enterprise_value.toFixed(1),down.enterprise_value.toFixed(1)],
  ['Equity value',base.equity_value.toFixed(1),down.equity_value.toFixed(1)],
  ['2026 free cash flow',base.annual_forecast[0].ufcf.toFixed(1),down.annual_forecast[0].ufcf.toFixed(1)],
  ['Terminal share of EV',pct(base.terminal_share),pct(down.terminal_share)]
 ],789,182,427,304,[185,107,135],19);
 text(s,'assumptions','Both cases: WACC '+pct(base.wacc)+'; terminal growth '+pct(base.terminal_growth)+'.',789,506,427,58,19,C.muted);
 text(s,'valuation-interpretation','Slower growth, lower margins and weaker working-capital efficiency drive the downside.\nTerminal value contributes '+pct(base.terminal_share)+' of base EV, making long-run assumptions especially important.',64,579,1152,54,20,C.muted);
 s.speakerNotes.text='Source: analysis/metrics.json:cases and assumptions. DCF uses year-end discounting, 2026–2030 explicit unlevered cash flows and a terminal perpetuity growing 2030 cash flow by 2.5%. WACC is 9.5% in both scenarios. Equity value equals enterprise value + opening cash of '+base.opening_cash+' − opening debt of '+base.opening_debt+'. Downside financing costs affect net income and cash but do not directly enter the unlevered-FCF calculation; the WACC assumption is held constant. Base 2026 revenue grows '+pct(metrics['2026_revenue_growth'])+'; later years are scenarios. Sources for methodology: https://pages.stern.nyu.edu/~adamodar/New_Home_Page/lectures/approach.html ; https://www.cfainstitute.org/insights/professional-learning/refresher-readings/2026/free-cash-flow-valuation .';
}

// 5 — Execution status is explicit; supplied scripts are not vendor results.
{
 const s=slide('A model reviewers can inspect and rerun','Editable deliverables and a reproducible reference analysis');
 table(s,[
  ['Tool / artifact','Purpose','Execution status'],
  ['Excel workbook','Linked statements, DCF, scenarios','Formula checks supplied with model'],
  ['Python reference analysis','Regression, holdout tests, model checks','Executed; outputs included'],
  ['Stata / EViews scripts','Equivalent estimation and forecast steps','Supplied; vendor runtimes not run'],
  ['Power Query M script','Import and prepare source data','Supplied; native refresh not run'],
  ['Word / PowerPoint','Explain methods and decision implications','Editable documents included']
 ],64,178,1152,336,[284,433,435],20);
 text(s,'reviewer-heading','Suggested review',64,544,1152,30,22,C.navy,true);
 text(s,'reviewer-steps','Switch the workbook scenario. Inspect the cash and balance checks. Trace the DCF to free cash flow.\nRerun the Python analysis, then compare the exported metrics with the presentation.',64,588,1152,51,20,C.ink);
 s.speakerNotes.text='The actual executed reference implementation is analysis/reproduce_analysis.py, using NumPy least squares and explicit HC1 covariance. Python validation confirms 96 unique monthly dates, separated training/holdout dates, full-rank design matrix and financial-statement identities to floating-point precision. Native Stata/EViews and Power Query files are illustrative equivalents that require verification in those vendor applications. Do not interpret the deck as a claim that those vendor scripts were executed. Workbook formula-check status should be read together with the delivered QA report. Slide charts are editable data snapshots and do not refresh automatically from the workbook.';
}

// Export editable package and preview assets. Private validators run in Codex.
const candidate=path.join(build,'candidate.pptx');
await (await PresentationFile.exportPptx(p)).save(candidate);
for(let i=0;i<p.slides.items.length;i++){
 const png=await p.export({slide:p.slides.items[i],format:'png',scale:1});
 await fs.writeFile(path.join(previews,`slide-${i+1}.png`),new Uint8Array(await png.arrayBuffer()));
}
let pdfExported=false;
try {
 const pdf=await p.export({format:'pdf'});
 await fs.writeFile(path.join(out,'Portfolio_Presentation.pdf'),new Uint8Array(await pdf.arrayBuffer()));
 pdfExported=true;
} catch(error) {
 console.warn('Optional PDF export unavailable:',error.message);
}
const final=path.join(out,'Portfolio_Presentation.pptx');
const skill=path.resolve(process.env.CODEX_PRESENTATIONS_SKILL_ROOT || '/root/.codex/skills/builtins/presentations');
if(process.env.CODEX_PRIMARY_RUNTIME_PYTHON && await fs.access(path.join(skill,'container_tools/artifact_tool_utils.mjs')).then(()=>true).catch(()=>false)){
 const {finalizePresentation}=await import(pathToFileURL(path.join(skill,'container_tools/artifact_tool_utils.mjs')).href);
 const result=await finalizePresentation({
  explicitTotalSlideCount:5,requiredNativeTableOwnerSlides:[2,3,4,5],requiredNativeChartOwnerSlides:[3,4],
  materializeLiteralChartWorkbooks:true,workspaceDir:process.env.PORTFOLIO_SLIDE_WORKSPACE || root,candidatePath:candidate,finalPath:path.join(out,`Portfolio_Presentation.validated-${Date.now()}.pptx`),
  pythonExecutable:process.env.CODEX_PRIMARY_RUNTIME_PYTHON,
  integrityValidatorPath:path.join(skill,'container_tools/inspect_presentation_package_integrity.py'),
  layoutValidatorPath:path.join(skill,'container_tools/inspect_presentation_layout_geometry.py'),
  layoutArgs:['--expected-slide-size-emu','12192000,6858000','--validate-bullet-geometry','--validate-heading-fit',...[2,3,4,5].flatMap(n=>['--require-native-table-slide',String(n)])],
  fontPolicy:{basis:'design',families:[FONT]},verifyArtifactToolImport:true,receiptPath:path.join(build,`validation-${Date.now()}.json`)
 });
 await fs.copyFile(result.finalPath,final);
 await fs.unlink(result.finalPath);
 console.log(JSON.stringify({pptx:final,pdf:pdfExported ? path.join(out,'Portfolio_Presentation.pdf') : null,slides:p.slides.items.length,checks:'passed'}));
}else{
 await fs.copyFile(candidate,final);
 console.log(JSON.stringify({pptx:final,pdf:pdfExported ? path.join(out,'Portfolio_Presentation.pdf') : null,slides:p.slides.items.length,checks:'not run outside Codex'}));
}
if(!pdfExported && process.env.CODEX_PRIMARY_RUNTIME_ROOT){
 const soffice=path.join(process.env.CODEX_PRIMARY_RUNTIME_ROOT,'dependencies/bin/override/soffice');
 const conversion=spawnSync(soffice,[`-env:UserInstallation=${pathToFileURL(path.join(build,'lo-profile')).href}`,'--headless','--convert-to','pdf','--outdir',out,final],{encoding:'utf8'});
 if(conversion.status!==0) throw new Error('Optional PDF conversion failed: '+conversion.stderr);
 console.log(JSON.stringify({pdf:path.join(out,'Portfolio_Presentation.pdf'),renderer:'LibreOffice'}));
}
