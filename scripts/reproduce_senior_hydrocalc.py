"""Reproduce senior-student HydroCalculator results for CG model teaching.

This script intentionally leaves the original CG_data files untouched. It reads
the existing input table, applies the HydroCalculator formulas mirrored from the
local UI implementation, and writes reproducible outputs under results/.
"""

from __future__ import annotations

import argparse
import csv
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "CG_data" / "泉水蒸发dateput.csv"
DEFAULT_REFERENCE = ROOT / "CG_data" / "泉水蒸发dateput_hydrocalc_output.csv"
DEFAULT_EXTENDED_REFERENCE = ROOT / "CG_data" / "result缙云山湖库泉20250927.csv"
DEFAULT_RESULTS = ROOT / "results"

INPUT_HEADERS = [
    "hydrocal=Sample name",
    "opc",
    "T",
    "h",
    "d2HP",
    "d18OP",
    "d2HL",
    "d18OL",
    "d2HA",
    "d18OA",
    "d2HR",
    "d18OR",
    "CkH",
    "CkO",
    "LEL",
    "comment",
]

OUTPUT_HEADERS = [
    *INPUT_HEADERS,
    "     ",
    "EkH",
    "EkO",
    "EplusH",
    "EplusO",
    "EH",
    "EO",
    "aplusH",
    "aplusO",
    "dstarH",
    "dstarO",
    "mH",
    "mO",
    "x",
    "    ",
    "EI_H",
    "EI_O",
    "f_H",
    "f_O",
]

CORE_FIELDS = ["d2HA", "d18OA", "x", "EI_H", "EI_O", "f_H", "f_O"]
REQUIRED_FOR_OPC3 = ["T", "h", "d2HP", "d18OP", "d2HL", "d18OL", "d2HR", "d18OR", "LEL"]


@dataclass
class RunResult:
    input_path: Path
    reference_path: Path
    extended_reference_path: Path
    reproduction_path: Path
    comparison_path: Path
    warnings_path: Path
    extended_profile_path: Path
    summary_path: Path
    row_count: int
    pass_count: int
    warning_count: int
    extended_row_count: int
    first_row: dict[str, object]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Reproduce and compare senior-student HydroCalculator results."
    )
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT, help="HydroCalculator input CSV.")
    parser.add_argument(
        "--reference",
        type=Path,
        default=DEFAULT_REFERENCE,
        help="HydroCalculator output CSV used as comparison reference.",
    )
    parser.add_argument(
        "--extended-reference",
        type=Path,
        default=DEFAULT_EXTENDED_REFERENCE,
        help="Extended senior-student result CSV used for research-meaning teaching.",
    )
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_RESULTS, help="Directory for output files.")
    parser.add_argument("--ckh", type=float, default=12.5, help="Default CkH if missing in the input table.")
    parser.add_argument("--cko", type=float, default=14.2, help="Default CkO if missing in the input table.")
    parser.add_argument(
        "--tolerance",
        type=float,
        default=0.00015,
        help="Rounded 4-decimal absolute tolerance for comparison fields.",
    )
    return parser.parse_args()


def read_csv(path: Path) -> list[dict[str, str]]:
    last_error: UnicodeDecodeError | None = None
    for encoding in ("utf-8-sig", "gb18030", "cp936"):
        try:
            with path.open("r", encoding=encoding, newline="") as f:
                return list(csv.DictReader(f))
        except UnicodeDecodeError as exc:
            last_error = exc
    if last_error is not None:
        raise last_error
    return []


def to_number(value: object, fallback: float = 0.0) -> float:
    if value is None:
        return fallback
    text = str(value).strip()
    if text == "":
        return fallback
    try:
        number = float(text)
    except ValueError:
        return fallback
    return number if math.isfinite(number) else fallback


def round_away(value: float, digits: int = 4) -> float:
    if not math.isfinite(value):
        return value
    factor = 10**digits
    rounded = math.floor(abs(value) * factor + 0.5 + 1e-12) / factor
    return math.copysign(rounded, value if value != 0 else 1)


def format_value(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            return str(value)
        return str(round_away(value, 4)).rstrip("0").rstrip(".")
    return str(value)


def aplus_h(t_c: float) -> float:
    tk = t_c + 273.15
    exponent = (
        (1158.8 * tk**3) / 1e9
        - (1620.1 * tk**2) / 1e6
        + (794.84 * tk) / 1000
        - 161.04
        + (2.9992 * 10**9) / tk**3
    )
    return math.exp(exponent / 1000)


def aplus_o(t_c: float) -> float:
    tk = t_c + 273.15
    exponent = -7.685 + (6.7123 * 1000) / tk - (1.6664 * 1e6) / tk**2 + (0.35041 * 10**9) / tk**3
    return math.exp(exponent / 1000)


def eplus(alpha: float) -> float:
    return (alpha - 1) * 1000


def ek(h: float, ck: float) -> float:
    return (1 - h) * ck


def evap_enrichment(ek_value: float, eplus_value: float, alpha: float) -> float:
    return ek_value + eplus_value / alpha


def dstar(h: float, da: float, e_value: float) -> float:
    return (h * da + e_value) / (h - e_value / 1000)


def m_value(h: float, e_value: float, ek_value: float) -> float:
    return (h - e_value / 1000) / (1 - h + ek_value / 1000)


def ei(d_lake: float, d_input: float, d_star: float, m_val: float) -> float:
    return (d_lake - d_input) / ((d_star - d_lake) * m_val)


def f_value(d_lake: float, d_star: float, d_input: float, m_val: float) -> float:
    ratio = (d_lake - d_star) / (d_input - d_star)
    if ratio < 0:
        return float("nan")
    return 1 - ratio ** (1 / m_val)


def da_from_rain(alpha: float, d_rain: float, eplus_value: float) -> float:
    return (d_rain - eplus_value) / alpha


def da_from_rain_and_x(x: float, d_rain: float, eplus_value: float) -> float:
    return (d_rain - eplus_value * x) / (1 + (x * eplus_value) / 1000)


def slope_from_x(x: float, values: dict[str, float]) -> float:
    h_moist = da_from_rain_and_x(x, values["d2HR"], values["EplusH"])
    o_moist = da_from_rain_and_x(x, values["d18OR"], values["EplusO"])
    h_term = (
        values["h"] * (h_moist / 1000 - values["d2HR"] / 1000)
        + (1 + values["d2HR"] / 1000) * (values["EH"] / 1000)
    ) / (values["h"] - values["EH"] / 1000)
    o_term = (
        values["h"] * (o_moist / 1000 - values["d18OR"] / 1000)
        + (1 + values["d18OR"] / 1000) * (values["EO"] / 1000)
    ) / (values["h"] - values["EO"] / 1000)
    return h_term / o_term


def find_x_for_lel(values: dict[str, float], target_lel: float) -> float:
    best_diff = 1000.0
    selected = 1.0
    target = round_away(target_lel, 4)

    for i in range(6000, 10001):
        x = round_away(i / 10000, 4)
        slope = round_away(slope_from_x(x, values), 4)
        diff = slope - target

        if diff == 0:
            selected = x
            break

        if abs(diff) > abs(best_diff):
            selected = x
            break

        best_diff = diff
        selected = x

    return selected


def validation_warnings(record: dict[str, str], row_number: int) -> list[dict[str, str]]:
    sample = record.get("hydrocal=Sample name", "")
    warnings = []
    if str(record.get("opc", "")).strip() != "3":
        warnings.append(
            {
                "row_index": str(row_number),
                "sample_name": sample,
                "level": "warning",
                "field": "opc",
                "message": "This teaching workflow expects opc=3: rain endpoint + LEL.",
            }
        )
    for field in REQUIRED_FOR_OPC3:
        if str(record.get(field, "")).strip() == "":
            warnings.append(
                {
                    "row_index": str(row_number),
                    "sample_name": sample,
                    "level": "error",
                    "field": field,
                    "message": "Required input field is missing.",
                }
            )
    h_value = to_number(record.get("h", ""))
    if h_value > 1:
        warnings.append(
            {
                "row_index": str(row_number),
                "sample_name": sample,
                "level": "warning",
                "field": "h",
                "message": "Relative humidity should be a 0-1 fraction, not percent.",
            }
        )
    return warnings


def compute_row(input_record: dict[str, str], default_ckh: float, default_cko: float) -> dict[str, object]:
    row: dict[str, object] = {}
    for header in INPUT_HEADERS:
        row[header] = input_record.get(header, "")
    row["CkH"] = row["CkH"] if str(row["CkH"]).strip() != "" else default_ckh
    row["CkO"] = row["CkO"] if str(row["CkO"]).strip() != "" else default_cko
    row["     "] = ""
    row["    "] = ""

    values = {
        "T": to_number(row["T"]),
        "h": to_number(row["h"]),
        "d2HP": to_number(row["d2HP"]),
        "d18OP": to_number(row["d18OP"]),
        "d2HL": to_number(row["d2HL"]),
        "d18OL": to_number(row["d18OL"]),
        "d2HA": to_number(row["d2HA"]),
        "d18OA": to_number(row["d18OA"]),
        "d2HR": to_number(row["d2HR"]),
        "d18OR": to_number(row["d18OR"]),
        "CkH": to_number(row["CkH"]),
        "CkO": to_number(row["CkO"]),
        "LEL": to_number(row["LEL"]),
    }

    values["EkH"] = ek(values["h"], values["CkH"])
    values["EkO"] = ek(values["h"], values["CkO"])
    values["aplusH"] = aplus_h(values["T"])
    values["aplusO"] = aplus_o(values["T"])
    values["EplusH"] = eplus(values["aplusH"])
    values["EplusO"] = eplus(values["aplusO"])
    values["EH"] = evap_enrichment(values["EkH"], values["EplusH"], values["aplusH"])
    values["EO"] = evap_enrichment(values["EkO"], values["EplusO"], values["aplusO"])

    option = str(row["opc"]).strip()
    if option == "2":
        values["d2HA"] = da_from_rain(values["aplusH"], values["d2HR"], values["EplusH"])
        values["d18OA"] = da_from_rain(values["aplusO"], values["d18OR"], values["EplusO"])
    elif option == "3":
        values["x"] = find_x_for_lel(values, values["LEL"])
        values["d18OA"] = da_from_rain_and_x(values["x"], values["d18OR"], values["EplusO"])
        values["d2HA"] = da_from_rain_and_x(values["x"], values["d2HR"], values["EplusH"])
    else:
        values["x"] = ""

    values["dstarH"] = dstar(values["h"], values["d2HA"], values["EH"])
    values["dstarO"] = dstar(values["h"], values["d18OA"], values["EO"])
    values["mH"] = m_value(values["h"], values["EH"], values["EkH"])
    values["mO"] = m_value(values["h"], values["EO"], values["EkO"])
    values["EI_H"] = ei(values["d2HL"], values["d2HP"], values["dstarH"], values["mH"])
    values["EI_O"] = ei(values["d18OL"], values["d18OP"], values["dstarO"], values["mO"])
    values["f_H"] = f_value(values["d2HL"], values["dstarH"], values["d2HP"], values["mH"])
    values["f_O"] = f_value(values["d18OL"], values["dstarO"], values["d18OP"], values["mO"])

    for key, value in values.items():
        row[key] = value

    for key in ["T", "h", "d2HP", "d18OP", "d2HL", "d18OL", "d2HA", "d18OA", "d2HR", "d18OR", "CkH", "CkO", "LEL"]:
        row[key] = to_number(row[key])

    return {header: row.get(header, "") for header in OUTPUT_HEADERS}


def write_csv(path: Path, headers: Iterable[str], rows: Iterable[dict[str, object]]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(headers), extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: format_value(value) for key, value in row.items()})


def compare_rows(
    computed_rows: list[dict[str, object]],
    reference_rows: list[dict[str, str]],
    tolerance: float,
) -> list[dict[str, object]]:
    comparison = []
    row_count = min(len(computed_rows), len(reference_rows))
    for index in range(row_count):
        computed = computed_rows[index]
        reference = reference_rows[index]
        out: dict[str, object] = {
            "row_index": index + 1,
            "sample_name": computed.get("hydrocal=Sample name", ""),
        }
        max_abs_diff = 0.0
        status = "pass"
        for field in CORE_FIELDS:
            comp_value = round_away(to_number(computed.get(field, "")), 4)
            ref_raw = reference.get(field, "")
            ref_value = round_away(to_number(ref_raw), 4) if str(ref_raw).strip() != "" else float("nan")
            diff = comp_value - ref_value if math.isfinite(ref_value) else float("nan")
            abs_diff = abs(diff) if math.isfinite(diff) else float("nan")
            if math.isfinite(abs_diff):
                max_abs_diff = max(max_abs_diff, abs_diff)
                if abs_diff > tolerance:
                    status = "check"
            else:
                status = "check"
            out[f"{field}_calc"] = comp_value
            out[f"{field}_ref"] = ref_value
            out[f"{field}_diff"] = diff
        out["max_abs_diff_core"] = max_abs_diff
        out["status"] = status
        comparison.append(out)
    return comparison


def classify_water_type(sample_name: str) -> str:
    if sample_name.startswith("水库水"):
        return "reservoir"
    if sample_name.startswith("湖水"):
        return "lake"
    if "泉" in sample_name:
        return "spring"
    return "other"


def average_available(*values: object) -> float | str:
    numbers = [to_number(value) for value in values if str(value).strip() != ""]
    if not numbers:
        return ""
    return sum(numbers) / len(numbers)


def profile_extended_reference(rows: list[dict[str, str]]) -> list[dict[str, object]]:
    profile = []
    for index, row in enumerate(rows, start=1):
        sample_name = row.get("hydrocal=Sample name", "")
        steady_average = average_available(row.get("EI_H", ""), row.get("EI_O", ""))
        nonsteady_average = average_available(row.get("f_H", ""), row.get("f_O", ""))
        profile.append(
            {
                "row_index": index,
                "sample_name": sample_name,
                "water_type": classify_water_type(sample_name),
                "T": row.get("T", ""),
                "h": row.get("h", ""),
                "LEL": row.get("LEL", ""),
                "EI_H": row.get("EI_H", ""),
                "EI_O": row.get("EI_O", ""),
                "EI_average": steady_average,
                "f_H": row.get("f_H", ""),
                "f_O": row.get("f_O", ""),
                "f_average": nonsteady_average,
                "teaching_use": "Compare water type, date, LEL, and evaporation strength.",
            }
        )
    return profile


def write_summary(result: RunResult) -> None:
    first = result.first_row

    def display_path(path: Path) -> str:
        try:
            return path.relative_to(ROOT).as_posix()
        except ValueError:
            return path.as_posix()

    summary = f"""# 学姐数据 HydroCalculator 复现摘要

## 使用数据

- 输入表: `{display_path(result.input_path)}`
- 结果对照表: `{display_path(result.reference_path)}`
- 扩展对照表: `{display_path(result.extended_reference_path)}`
- 复现输出: `{display_path(result.reproduction_path)}`
- 核对表: `{display_path(result.comparison_path)}`
- 警告表: `{display_path(result.warnings_path)}`
- 扩展画像表: `{display_path(result.extended_profile_path)}`

## 核心结果

- 样本数: {result.row_count}
- 核心字段核对通过: {result.pass_count}/{result.row_count}
- 输入警告/错误记录: {result.warning_count}
- 扩展结果表样本数: {result.extended_row_count}

## 第一行样例

样品 `{first.get("hydrocal=Sample name", "")}` 使用 `opc={first.get("opc", "")}`，表示已知降水端元和 LEL，由模型反推空气水汽同位素。

| 指标 | 复现值 | 意义 |
|---|---:|---|
| d2HA | {format_value(first.get("d2HA"))} | 反推空气水汽 δ²H |
| d18OA | {format_value(first.get("d18OA"))} | 反推空气水汽 δ¹⁸O |
| x | {format_value(first.get("x"))} | 为匹配 LEL 搜索得到的大气水汽调节参数 |
| EI_H | {format_value(first.get("EI_H"))} | 基于 δ²H 的稳态蒸发/入流比 |
| EI_O | {format_value(first.get("EI_O"))} | 基于 δ¹⁸O 的稳态蒸发/入流比 |
| f_H | {format_value(first.get("f_H"))} | 基于 δ²H 的非稳态蒸发损失比例 |
| f_O | {format_value(first.get("f_O"))} | 基于 δ¹⁸O 的非稳态蒸发损失比例 |

## 解释口径

- 同位素单位统一为 per mil VSMOW。
- 相对湿度 `h` 使用 0-1 小数。
- `EI` 数值越大，说明稳态口径下蒸发消耗相对入流越强。
- `f` 数值越大，说明非稳态口径下水体蒸发损失比例越高。
- 如果 `EI_H` 和 `EI_O` 或 `f_H` 和 `f_O` 差异明显，优先检查 LEL、温湿度、端元选择和样品是否代表同一过程。
"""
    result.summary_path.write_text(summary, encoding="utf-8")


def run() -> RunResult:
    args = parse_args()
    input_path = args.input.resolve()
    reference_path = args.reference.resolve()
    extended_reference_path = args.extended_reference.resolve()
    out_dir = args.out_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    input_rows = read_csv(input_path)
    reference_rows = read_csv(reference_path)
    extended_reference_rows = read_csv(extended_reference_path) if extended_reference_path.exists() else []

    warnings: list[dict[str, str]] = []
    computed_rows = []
    for index, row in enumerate(input_rows, start=1):
        warnings.extend(validation_warnings(row, index))
        computed_rows.append(compute_row(row, args.ckh, args.cko))

    reproduction_path = out_dir / "senior_hydrocalc_reproduction.csv"
    comparison_path = out_dir / "senior_hydrocalc_comparison.csv"
    warnings_path = out_dir / "senior_hydrocalc_warnings.csv"
    extended_profile_path = out_dir / "senior_extended_reference_profile.csv"
    summary_path = out_dir / "senior_hydrocalc_summary.md"

    comparison_rows = compare_rows(computed_rows, reference_rows, args.tolerance)
    comparison_headers = ["row_index", "sample_name", "max_abs_diff_core", "status"]
    for field in CORE_FIELDS:
        comparison_headers.extend([f"{field}_calc", f"{field}_ref", f"{field}_diff"])

    write_csv(reproduction_path, OUTPUT_HEADERS, computed_rows)
    write_csv(comparison_path, comparison_headers, comparison_rows)
    write_csv(warnings_path, ["row_index", "sample_name", "level", "field", "message"], warnings)
    write_csv(
        extended_profile_path,
        [
            "row_index",
            "sample_name",
            "water_type",
            "T",
            "h",
            "LEL",
            "EI_H",
            "EI_O",
            "EI_average",
            "f_H",
            "f_O",
            "f_average",
            "teaching_use",
        ],
        profile_extended_reference(extended_reference_rows),
    )

    result = RunResult(
        input_path=input_path,
        reference_path=reference_path,
        extended_reference_path=extended_reference_path,
        reproduction_path=reproduction_path,
        comparison_path=comparison_path,
        warnings_path=warnings_path,
        extended_profile_path=extended_profile_path,
        summary_path=summary_path,
        row_count=len(computed_rows),
        pass_count=sum(1 for row in comparison_rows if row["status"] == "pass"),
        warning_count=len(warnings),
        extended_row_count=len(extended_reference_rows),
        first_row=computed_rows[0] if computed_rows else {},
    )
    write_summary(result)
    return result


if __name__ == "__main__":
    run_result = run()
    print(f"Rows: {run_result.row_count}")
    print(f"Core comparison passed: {run_result.pass_count}/{run_result.row_count}")
    print(f"Warnings: {run_result.warning_count}")
    print(f"Extended rows: {run_result.extended_row_count}")
    print(f"Reproduction: {run_result.reproduction_path}")
    print(f"Comparison: {run_result.comparison_path}")
    print(f"Extended profile: {run_result.extended_profile_path}")
    print(f"Summary: {run_result.summary_path}")
