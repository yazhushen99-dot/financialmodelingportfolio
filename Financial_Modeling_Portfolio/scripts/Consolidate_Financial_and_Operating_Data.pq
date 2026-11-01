// Northstar Industrial Components | Power Query M
// Synthetic source files. Import this as an Excel Blank Query.
// Edit RootFolder to the extracted portfolio folder; retain the /data paths.
// The shipped XLSX contains prepared data, not an embedded live Power Query.
let
    RootFolder = "C:/work/finance_portfolio",
    ReadCsv = (RelativePath as text) as table =>
        Table.PromoteHeaders(
            Csv.Document(
                File.Contents(RootFolder & "/" & RelativePath),
                [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]
            ),
            [PromoteAllScalars = true]
        ),
    OperatingRaw = ReadCsv("data/monthly_operating_data.csv"),
    OperatingTyped = Table.TransformColumnTypes(
        OperatingRaw,
        {{"date", type date}, {"revenue_musd", type number},
         {"industrial_index", type number}, {"month", Int64.Type},
         {"trend", Int64.Type}, {"split", type text}},
        "en-US"
    ),
    OperatingChecked =
        if Table.RowCount(OperatingTyped) <> Table.RowCount(Table.Distinct(OperatingTyped, {"date"}))
        then error "Duplicate operating dates: review the input CSV."
        else if Table.RowCount(Table.SelectRows(OperatingTyped,
            each [date] = null or [revenue_musd] = null or [revenue_musd] <= 0)) > 0
        then error "Missing date or non-positive revenue: review the input CSV."
        else OperatingTyped,
    OperatingWithYear = Table.AddColumn(OperatingChecked, "year", each Date.Year([date]), Int64.Type),
    OperatingAnnual = Table.Group(
        OperatingWithYear, {"year"},
        {{"operating_revenue_musd", each List.Sum([revenue_musd]), type number},
         {"months_in_year", each Table.RowCount(_), Int64.Type},
         {"mean_industrial_index", each List.Average([industrial_index]), type number}}
    ),
    FinancialRaw = ReadCsv("data/historical_financials.csv"),
    FinancialTyped = Table.TransformColumnTypes(
        FinancialRaw,
        {{"year", Int64.Type}, {"revenue", type number}, {"cogs", type number},
         {"opex", type number}, {"depreciation", type number}, {"interest", type number},
         {"tax", type number}, {"net_income", type number}, {"ar", type number},
         {"inventory", type number}, {"ap", type number}, {"ppe", type number},
         {"cash", type number}, {"debt", type number}, {"equity", type number},
         {"capex", type number}, {"dividends", type number},
         {"new_borrowing", type number}, {"debt_repayment", type number}},
        "en-US"
    ),
    FinancialChecked =
        if Table.RowCount(FinancialTyped) <> Table.RowCount(Table.Distinct(FinancialTyped, {"year"}))
        then error "Duplicate financial years: review the input CSV."
        else FinancialTyped,
    Joined = Table.NestedJoin(
        FinancialChecked, {"year"}, OperatingAnnual, {"year"}, "OperatingData", JoinKind.LeftOuter
    ),
    Expanded = Table.ExpandTableColumn(
        Joined, "OperatingData", {"operating_revenue_musd", "months_in_year", "mean_industrial_index"}
    ),
    WithDifference = Table.AddColumn(
        Expanded, "revenue_reconciliation_musd",
        each if [operating_revenue_musd] = null then null else [revenue] - [operating_revenue_musd],
        type number
    ),
    WithStatus = Table.AddColumn(
        WithDifference, "reconciliation_status",
        each if [operating_revenue_musd] = null then "NO OPERATING MATCH"
        else if [months_in_year] <> 12 then "INCOMPLETE YEAR"
        else if Number.Abs([revenue_reconciliation_musd]) <= 0.000001 then "RECONCILED"
        else "REVIEW DIFFERENCE",
        type text
    ),
    WithUnits = Table.AddColumn(WithStatus, "currency_and_units", each "USD millions", type text),
    Result = Table.Sort(WithUnits, {{"year", Order.Ascending}})
in
    Result
