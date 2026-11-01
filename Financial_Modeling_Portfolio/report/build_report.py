"""Build the editable report from the portfolio's computed reference results."""
from pathlib import Path
import json
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

ROOT = Path(__file__).resolve().parents[1]
M = json.loads((ROOT / 'analysis/metrics.json').read_text())
B, D = M['cases']['Base'], M['cases']['Downside']
doc = Document()
sec = doc.sections[0]
sec.page_width, sec.page_height = Inches(8.5), Inches(11)
sec.top_margin, sec.bottom_margin = Inches(.65), Inches(.6)
sec.left_margin, sec.right_margin = Inches(.75), Inches(.75)
styles = doc.styles
for border in styles.element.xpath('.//w:pBdr'):
    border.getparent().remove(border)
for name in ['Normal', 'Title', 'Subtitle', 'Heading 1', 'Heading 2']:
    styles[name].font.name = 'Calibri'
    styles[name].font.color.rgb = RGBColor(0,0,0)
styles['Normal'].font.size = Pt(10)
styles['Normal'].paragraph_format.space_after = Pt(7)
styles['Normal'].paragraph_format.line_spacing = 1.08
styles['Title'].font.size = Pt(27)
styles['Title'].paragraph_format.space_after = Pt(8)
styles['Subtitle'].font.size = Pt(12)
styles['Heading 1'].font.size = Pt(17)
styles['Heading 1'].paragraph_format.space_before = Pt(12)
styles['Heading 1'].paragraph_format.space_after = Pt(7)
styles['Heading 2'].font.size = Pt(11)
styles['Heading 2'].paragraph_format.space_before = Pt(8)
styles['Heading 2'].paragraph_format.space_after = Pt(5)
doc.core_properties.title = 'Corporate Valuation and Cash Flow Forecasting'
doc.core_properties.subject = 'Financial modeling and data analysis portfolio demonstration'
doc.core_properties.author = 'Prepared for Yazhu Shen'

def para(text, style=None):
    return doc.add_paragraph(text, style)

def heading(text, level=1):
    return doc.add_heading(text, level)

def table(headers, rows, widths=None):
    t = doc.add_table(rows=1, cols=len(headers))
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = False
    if widths is None: widths = [7/len(headers)]*len(headers)
    for c,w in zip(t.columns, widths): c.width=Inches(w)
    for i,h in enumerate(headers): t.rows[0].cells[i].text=str(h)
    for row in rows:
        cells=t.add_row().cells
        for i,v in enumerate(row): cells[i].text=str(v)
    for ri,row in enumerate(t.rows):
        for ci,cell in enumerate(row.cells):
            cell.width = Inches(widths[ci])
            cell.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER
            tcPr=cell._tc.get_or_add_tcPr()
            shd=OxmlElement('w:shd'); shd.set(qn('w:fill'), '17324D' if ri==0 else ('F2F6F8' if ri%2 else 'FFFFFF'));tcPr.append(shd)
            margins=OxmlElement('w:tcMar')
            for side in ['top','left','bottom','right']:
                item=OxmlElement('w:'+side);item.set(qn('w:w'),'95');item.set(qn('w:type'),'dxa');margins.append(item)
            tcPr.append(margins)
            borders=OxmlElement('w:tcBorders')
            for side in ['top','left','bottom','right']:
                e=OxmlElement('w:'+side);e.set(qn('w:val'),'single');e.set(qn('w:sz'),'4');e.set(qn('w:color'),'D9D9D9');borders.append(e)
            tcPr.append(borders)
            for p in cell.paragraphs:
                p.paragraph_format.space_after=Pt(0)
                p.paragraph_format.line_spacing=1.03
                p.alignment=WD_ALIGN_PARAGRAPH.LEFT if ci==0 else WD_ALIGN_PARAGRAPH.CENTER
                for run in p.runs:
                    run.font.size=Pt(9)
                    if ri==0:run.font.bold=True;run.font.color.rgb=RGBColor(255,255,255)
        trPr=row._tr.get_or_add_trPr()
        cant=OxmlElement('w:cantSplit');trPr.append(cant)
        if ri==0: repeat=OxmlElement('w:tblHeader');trPr.append(repeat)
    para('')
    return t

def image(name, caption, width=6.8):
    p=doc.add_paragraph();p.paragraph_format.space_after=Pt(3)
    p.add_run().add_picture(str(ROOT/'visuals'/name),width=Inches(width))
    p=para(caption);p.paragraph_format.space_after=Pt(8)
    for r in p.runs:r.font.size=Pt(8);r.font.color.rgb=RGBColor.from_string('526373')

def money(v):return f'{v:,.1f}'
def pct(v):return f'{100*v:.1f}%'

footer=sec.footer.paragraphs[0]
footer.alignment=WD_ALIGN_PARAGRAPH.RIGHT
run=footer.add_run('NORTHSTAR  |  SYNTHETIC WORK SAMPLE  |  ');run.font.size=Pt(8);run.font.color.rgb=RGBColor.from_string('526373')
fld=OxmlElement('w:fldSimple');fld.set(qn('w:instr'),'PAGE');footer._p.append(fld)

# PAGE 1
para('FINANCE AND DATA ANALYSIS', 'Subtitle')
doc.add_heading('Corporate Valuation and Cash Flow Forecasting',0)
para('Northstar Industrial Components', 'Subtitle')
para('Prepared for Yazhu Shen  |  Portfolio work sample  |  November 2026')
para('This case demonstrates a complete path from operating data to a financial model and valuation. It uses a fictional manufacturer and deterministic simulated data. The valuation date is 31 December 2025; all financial amounts are in USD millions.')
heading('What the analysis shows')
gap=1-D['equity_value']/B['equity_value']
para(f"The base case produces an illustrative equity value of ${money(B['equity_value'])} million. Slower growth, weaker margins and a larger working capital requirement reduce it to ${money(D['equity_value'])} million in the downside case, a {pct(gap)} decrease. These are scenario outputs, not estimates for an actual company.")
table(['Measure','Base','Downside'],[
    ['2026 revenue',money(B['annual_forecast'][0]['revenue']),money(D['annual_forecast'][0]['revenue'])],
    ['2026 unlevered free cash flow',money(B['annual_forecast'][0]['ufcf']),money(D['annual_forecast'][0]['ufcf'])],
    ['Enterprise value',money(B['enterprise_value']),money(D['enterprise_value'])],
    ['Equity value',money(B['equity_value']),money(D['equity_value'])],
], [3.8,1.6,1.6])
image('model_revenue_scenarios.png','Simulated historical revenue and scenario projections. The 2026 base uses the selected revenue model; later growth rates are explicit analyst assumptions.',6.65)

# PAGE 2
doc.add_page_break()
heading('Forecasting revenue')
para('The source contains 96 monthly observations from January 2018 through December 2025. The first 84 observations estimate the models; the last 12 are reserved for a chronological validation window. Monthly records and their split labels are supplied as CSV files.')
heading('Model specification',2)
para('The driver regression estimates log revenue from a time trend, an industrial activity index and monthly seasonal indicators. A trend and seasonality regression and a seasonal naive forecast provide benchmarks. HC1 standard errors address heteroskedasticity, but not serial correlation. The regression describes association rather than causation.')
table(['Model','RMSE\nUSD m','MAE\nUSD m','MAPE'],[
    [name, f"{v['rmse_musd']:.3f}", f"{v['mae_musd']:.3f}",f"{v['mape_pct']:.2f}%"]
    for name,v in M['model_metrics'].items()
], [3.4,1.2,1.2,1.2])
image('model_forecast_validation.png','2025 held-out observations and model predictions, in USD millions per month. The driver regression is conditional on the observed industrial index.',6.65)
heading('How to interpret the result',2)
para(f"The driver regression has the lowest validation RMSE and is used for the 2026 projection. Its annual revenue projection is ${money(M['2026_revenue_forecast'])} million, or {pct(M['2026_revenue_growth'])} growth over simulated 2025. The future industrial index rises by an assumed 0.10 points per month from December 2025.")
para('Validation uses the observed 2025 industrial index and excludes errors in forecasting that driver. Exponentiated log predictions are monthly conditional medians, with no smearing adjustment. Their annual sum is a planning projection, not an estimated annual conditional mean or median. Selection and evaluation share one holdout window; rolling validation and an untouched final test would provide stronger evidence of forecast performance [2].')

# PAGE 3
doc.add_page_break()
heading('Building the financial model')
para('One scenario selector activates either Base or Downside assumptions. The same forecast schedules calculate both cases; source history stays unchanged. Revenue and margins drive the income statement, while receivable, inventory and payable days determine operating working capital.')
table(['Schedule','Model treatment'],[
 ['Income statement','Revenue less cost of sales, operating expenses, depreciation, interest and taxes'],
 ['Balance sheet','Cash, receivables, inventory and net PP&E; payables, debt and equity'],
 ['Cash flow','Net income plus depreciation less change in working capital; capital spending, debt repayment and dividends'],
 ['Debt and interest','Interest on opening debt; fixed annual principal repayment with an editable borrowing assumption'],
 ['Reconciliation','Cash rolls forward from cash flows; equity rolls forward from earnings less dividends'],
], [1.65,5.35])
heading('Valuing the operating cash flows',2)
para('Unlevered free cash flow equals EBIT after operating taxes plus depreciation, less capital expenditure and the change in noncash operating working capital. Year-end cash flows are discounted at the assumed 9.5% WACC. The terminal value grows 2030 free cash flow at 2.5% and discounts that perpetuity back five years. The approach follows the distinction between firm cash flows and equity cash flows described by Damodaran [1].')
table(['Valuation bridge','Base','Downside'],[
 ['PV of 2026 to 2030 cash flows',money(B['pv_explicit_fcf']),money(D['pv_explicit_fcf'])],
 ['PV of terminal value',money(B['pv_terminal_value']),money(D['pv_terminal_value'])],
 ['Enterprise value',money(B['enterprise_value']),money(D['enterprise_value'])],
 ['Add valuation date cash',money(B['opening_cash']),money(D['opening_cash'])],
 ['Less valuation date debt',money(B['opening_debt']),money(D['opening_debt'])],
 ['Equity value',money(B['equity_value']),money(D['equity_value'])],
], [3.8,1.6,1.6])
para(f"Terminal value accounts for {pct(B['terminal_share'])} of base enterprise value. The workbook therefore includes a WACC and terminal growth sensitivity grid. Its central cell reproduces the active DCF equity value. WACC and terminal growth are assumptions, not market estimates.")
para('The terminal calculation is a simplified continuation of final-year cash flow; it does not model a separate steady-state reinvestment or return-on-capital transition. All valuation-date cash is treated as non-operating. Negative earnings do not generate an immediate tax benefit, and the model excludes acquisitions, leases, FX and deferred taxes.')

# PAGE 4
doc.add_page_break()
heading('Reviewing and reproducing the work')
para('The portfolio separates executed calculations from source scripts that require proprietary applications. The scripts and data are supplied so a reviewer can inspect the method, reproduce the reference analysis and test the financial model.')
table(['Component','Evidence included','Execution status'],[
 ['Excel model','Editable formulas, assumptions, DCF and sensitivity','Calculated and checked; see validation records'],
 ['Python reference','Data generator, regressions, forecasts and financial calculations','Executed in the supplied build'],
 ['Stata','Native do-file and CSV inputs','Script supplied; native Stata run pending'],
 ['EViews','Native program and CSV inputs','Script supplied; native EViews run pending'],
 ['Power Query','M query and source files','Query supplied; load and refresh in Excel'],
 ['Communication','Editable Word report and PowerPoint presentation','Rendered and visually reviewed'],
], [1.15,3.35,2.5])
heading('A short review path',2)
for text in [
 'Open model/Financial_Model.xlsx and review the summary. Follow its formula links to the forecast and DCF calculations.',
 'Change the single scenario selector to Downside. Review the changes in 2026 cash generation, the cash balance and equity value, then return to Base.',
 'Change one input, such as collection days or WACC. Check the relevant schedule and the sensitivity grid rather than inspecting only the headline result.',
 'Run analysis/reproduce_analysis.py to regenerate the reference results. Compare analysis/forecast_validation.csv with the chart and metrics in this report.',
 'Use docs/native_tools.md to run Stata, EViews and Power Query locally. Compare native outputs with the Python reference before claiming cross-application agreement.'
]:
    para(text,'List Number')
heading('Model checks',2)
para('The review covers source totals, chronological training and validation splits, forecast errors, balance sheet equality, cash and equity roll-forwards, debt and interest consistency, the DCF bridge and sensitivity direction. Independent review results and any remaining limitations are recorded in docs/independent_review.md. Workbook inspection results are supplied with the model.')
heading('Method references',2)
para('[1] Damodaran, A. An introduction to valuation. NYU Stern. https://pages.stern.nyu.edu/~adamodar/New_Home_Page/background/valintro.htm')
para('[2] Hyndman, R. J., and Athanasopoulos, G. Forecasting: Principles and Practice, 3rd edition. Chapter 5, evaluating forecast accuracy. https://otexts.com/fpp3/toolbox.html')
for p in doc.paragraphs:
    if p.text.startswith('[1]') or p.text.startswith('[2]'):
        for r in p.runs:r.font.size=Pt(8)

out=ROOT/'report/Portfolio_Report.docx'
doc.save(out)
print(out)
