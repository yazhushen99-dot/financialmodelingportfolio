# Financial model build notes

Open `Financial_Model.xlsx` in Excel and change `Assumptions!D4` between Base and Downside. The financial model and DCF use native formulas. The workbook is supplied with Base selected. Blue inputs are editable; cross-sheet formulas are green. Review the Checks sheet after edits.

The analysis can be reproduced independently without the workbook builder:

```
python -m pip install -r analysis/requirements.txt
python analysis/reproduce_analysis.py
```

The Python script generates the deterministic synthetic source files, statistical estimates, annual reference forecasts and charts. It does not create the XLSX. Monthly regression coefficients in the workbook are imported estimates; editing historical monthly data does not automatically refit them. The 2026 future-driver inputs do feed the existing fitted equation in Excel. The financial assumptions continue to recalculate normally.

`build_workbook.mjs` is the source used to author and verify the workbook. It requires Node.js and the `@oai/artifact-tool` package. That package/runtime is not bundled. In an environment where it is available, run:

```
node model/build_workbook.mjs
```

An optional first argument overrides the portfolio root directory. This is a build source, not a requirement for opening or editing the workbook. It recreates the XLSX from `analysis/workbook_payload.json` and repeats its scenario and formula tests.

Validation performed: artifact-engine recalculation, both scenarios against independent Python reference values, later-period driver perturbation, blank unselected/selected assumptions, invalid WACC/g, sensitivity center, historical revenue ties and formula-error scan. The final workbook was rendered and visually checked. Native Excel, LibreOffice, Stata and EViews execution was not performed in this environment. The package includes separate independent reference review results.

The workbook uses editable chart series with source-cell references plus populated export caches. Native Excel uses these references to update charts after model edits. Native Excel chart behavior was not tested here.
