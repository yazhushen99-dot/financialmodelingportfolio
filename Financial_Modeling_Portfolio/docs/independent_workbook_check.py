"""Read-only XLSX arithmetic check. Python 3 standard library only.

Run from any folder: python docs/independent_workbook_check.py
This evaluator intentionally supports only the formulas in this work sample.
It is not a replacement for native Excel compatibility testing.
"""
from pathlib import Path
from zipfile import ZipFile
from datetime import datetime
import functools
import json
import math
import re
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
NS = {"s": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
CELLS = {}
with ZipFile(ROOT / "model/Financial_Model.xlsx") as archive:
    strings = ["".join(e.itertext()) for e in ET.fromstring(archive.read("xl/sharedStrings.xml"))]
    sheets = [e.attrib["name"] for e in ET.fromstring(archive.read("xl/workbook.xml")).find("s:sheets", NS)]
    for number, sheet in enumerate(sheets, 1):
        xml = ET.fromstring(archive.read(f"xl/worksheets/sheet{number}.xml"))
        for cell in xml.findall(".//s:c", NS):
            value = cell.findtext("s:v", namespaces=NS)
            kind = cell.attrib.get("t")
            if value is not None:
                if kind == "s":
                    value = strings[int(value)]
                elif kind == "d":
                    date = datetime.fromisoformat(value.replace("Z", "+00:00")).replace(tzinfo=None)
                    value = (date - datetime(1899, 12, 30)).total_seconds() / 86400
                elif kind not in ("str", "e"):
                    value = float(value)
            CELLS[sheet, cell.attrib["r"]] = (cell.findtext("s:f", namespaces=NS), value, kind)

TOKEN = re.compile(r'''\s*(?:((?:'[^']+'!)?\$?[A-Z]{1,3}\$?\d+(?::\$?[A-Z]{1,3}\$?\d+)?)|("(?:[^"]|"")*")|((?:\d+(?:\.\d*)?|\.\d+)(?:[Ee][+-]?\d+)?)|([A-Z]+)|(>=|<=|<>|[(),+*/^%=<>-]))''')
PRIORITY = {"=": 5, ">": 5, "<": 5, ">=": 5, "<=": 5, "<>": 5, "+": 10, "-": 10, "*": 20, "/": 20, "^": 30}


def parse(formula):
    tokens, position = [], 0
    while position < len(formula):
        match = TOKEN.match(formula, position)
        if not match:
            raise ValueError(f"Unsupported formula at {position}: {formula}")
        tokens.append(next(x for x in match.groups() if x is not None))
        position = match.end()
    cursor = 0

    def expression(minimum=0):
        nonlocal cursor
        token = tokens[cursor]
        cursor += 1
        if token in ("+", "-"):
            node = ("unary", token, expression(40))
        elif token == "(":
            node = expression()
            assert tokens[cursor] == ")"
            cursor += 1
        elif token.startswith('"'):
            node = ("literal", token[1:-1].replace('""', '"'))
        elif re.match(r"\d|\.", token):
            node = ("literal", float(token))
        elif cursor < len(tokens) and tokens[cursor] == "(":
            cursor += 1
            arguments = []
            if tokens[cursor] != ")":
                while True:
                    arguments.append(expression())
                    if tokens[cursor] != ",":
                        break
                    cursor += 1
            assert tokens[cursor] == ")"
            cursor += 1
            node = ("function", token, arguments)
        else:
            node = ("reference", token)
        while cursor < len(tokens):
            operator = tokens[cursor]
            if operator == "%":
                cursor += 1
                node = ("binary", "/", node, ("literal", 100))
                continue
            priority = PRIORITY.get(operator, -1)
            if priority < minimum:
                break
            cursor += 1
            right = expression(priority + (0 if operator == "^" else 1))
            node = ("binary", operator, node, right)
        return node

    tree = expression()
    assert cursor == len(tokens), formula
    return tree


TREES = {key: parse(value[0]) for key, value in CELLS.items() if value[0]}


def column_number(text):
    result = 0
    for character in text:
        result = result * 26 + ord(character) - 64
    return result


def column_text(number):
    result = ""
    while number:
        number, remainder = divmod(number - 1, 26)
        result = chr(65 + remainder) + result
    return result


def make_evaluator(overrides=None):
    overrides = overrides or {}

    @functools.lru_cache(None)
    def cell(sheet, address):
        key = (sheet, address)
        if key in overrides:
            return overrides[key]
        if key in TREES:
            return evaluate(TREES[key], sheet)
        return CELLS.get(key, (None, 0, None))[1] or 0

    def evaluate(node, sheet):
        kind = node[0]
        if kind == "literal":
            return node[1]
        if kind == "reference":
            reference = node[1].replace("$", "")
            if "!" in reference:
                target, reference = reference.split("!")
                target = target.strip("'")
            else:
                target = sheet
            if ":" not in reference:
                return cell(target, reference)
            start, end = reference.split(":")
            ac, ar = re.fullmatch(r"([A-Z]+)(\d+)", start).groups()
            bc, br = re.fullmatch(r"([A-Z]+)(\d+)", end).groups()
            return [cell(target, column_text(c) + str(r)) for r in range(int(ar), int(br) + 1) for c in range(column_number(ac), column_number(bc) + 1)]
        if kind == "unary":
            value = evaluate(node[2], sheet)
            return value if node[1] == "+" else -value
        if kind == "binary":
            a, b = evaluate(node[2], sheet), evaluate(node[3], sheet)
            return {"+": lambda: a + b, "-": lambda: a - b, "*": lambda: a * b, "/": lambda: a / b, "^": lambda: a ** b, "=": lambda: a == b, ">": lambda: a > b, "<": lambda: a < b, ">=": lambda: a >= b, "<=": lambda: a <= b, "<>": lambda: a != b}[node[1]]()
        function, arguments = node[1], node[2]
        if function == "IF":
            return evaluate(arguments[1] if evaluate(arguments[0], sheet) else arguments[2], sheet)
        if function == "NA":
            raise ValueError("Excel NA")
        values = [evaluate(a, sheet) for a in arguments]
        if function == "SUM":
            return sum(y for value in values for y in (value if isinstance(value, list) else [value]))
        if function == "MAX":
            return max(values)
        if function == "MIN":
            return min(values)
        if function == "EXP":
            return math.exp(values[0])
        if function == "ISNUMBER":
            return isinstance(values[0], (float, int))
        raise ValueError(f"Unsupported function: {function}")

    return cell


def main():
    metrics = json.loads((ROOT / "analysis/metrics.json").read_text())
    base = make_evaluator()
    differences, failures = [], []
    for key in TREES:
        computed, cached = base(*key), CELLS[key][1]
        if isinstance(computed, (float, int)) and isinstance(cached, (float, int)):
            differences.append(abs(computed - cached))
        elif computed != cached:
            failures.append([key, computed, cached])
    mapping = {"revenue": (9, 1), "cogs": (11, -1), "opex": (14, -1), "depreciation": (16, -1), "interest": (18, -1), "tax": (20, -1), "net_income": (21, 1), "ar": (26, 1), "inventory": (27, 1), "ap": (31, 1), "ppe": (28, 1), "cash": (25, 1), "debt": (32, 1), "equity": (33, 1), "capex": (55, 1), "dividends": (75, -1), "new_borrowing": (61, 1), "debt_repayment": (62, -1), "cfo": (41, 1), "cfi": (43, 1), "cff": (47, 1), "ebit": (17, 1), "ebitda": (15, 1), "delta_nwc": (70, 1), "ufcf": (84, 1)}
    scenario_differences = {}
    for scenario in ("Base", "Downside"):
        calculate = make_evaluator({("Assumptions", "D4"): scenario})
        expected = metrics["cases"][scenario]
        errors = []
        for index, annual in enumerate(expected["annual_forecast"]):
            for name, (row, sign) in mapping.items():
                errors.append(abs(calculate("Financials", f"{chr(73 + index)}{row}") - sign * annual[name]))
        errors += [abs(calculate("DCF", "D14") - expected["equity_value"]), abs(calculate("DCF", "D11") - expected["enterprise_value"]), abs(calculate("DCF", "G30") - calculate("DCF", "D14"))]
        scenario_differences[scenario] = max(errors)
    sensitivity_error = max(abs(base("DCF", chr(69 + j) + str(28 + i)) - value["equity_value"]) for i, row in enumerate(metrics["sensitivity"]) for j, value in enumerate(row))
    perturb = make_evaluator({("Assumptions", "M12"): metrics["assumptions"]["Base"]["revenue_growth"][-1] + .01})
    growth_effect = perturb("DCF", "D14") - base("DCF", "D14")
    bad = make_evaluator({("DCF", "D7"): .025, ("DCF", "D8"): .025})
    guard = False
    try:
        bad("DCF", "D14")
    except ValueError as error:
        guard = str(error) == "Excel NA"
    passed = not failures and max(differences) < 1e-8 and max(scenario_differences.values()) < 1e-8 and sensitivity_error < 1e-8 and abs(growth_effect) > 1e-6 and guard
    output = {"passed": passed, "formula_count": len(TREES), "max_cache_difference": max(differences), "scenario_max_differences": scenario_differences, "sensitivity_max_difference": sensitivity_error, "growth_perturbation_equity_effect": growth_effect, "wacc_growth_guard": guard, "non_numeric_mismatches": failures, "native_excel_executed": False}
    print(json.dumps(output, indent=2))
    if not passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
