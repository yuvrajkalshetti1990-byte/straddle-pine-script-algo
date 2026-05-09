from __future__ import annotations

import argparse
import csv
import json
import math
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
SNAPSHOT_FILE = ROOT / "pythonbackend" / "data" / "last-close-strikes.json"
BOT_HISTORICAL_DIR = ROOT / "My_Algo_Bot" / "historical_data"

EMPTY_INDICATORS = {
    "roc": None,
    "rsi": None,
    "minusDI": None,
    "plusDI": None,
    "adx": None,
    "chop": None,
}

INDICATOR_LABELS = [
    ("roc", "ROC"),
    ("rsi", "RSI"),
    ("minusDI", "-DI"),
    ("plusDI", "+DI"),
    ("adx", "ADX"),
    ("chop", "CHOP"),
]

TABLE_COLUMNS = [
    ("strike", "STRIKE"),
    ("open", "OPEN"),
    ("ltp", "LTP"),
    ("change", "CHANGE"),
    ("lead", "LEAD"),
    ("regime", "REGIME"),
    ("indReg", "IND.REG"),
    ("tMode", "T.MODE"),
    ("tType", "T.TYPE"),
]

TEXT_REPLACEMENTS = str.maketrans(
    {
        "\u25b2": "^",
        "\u25bc": "v",
        "\u2191": "up",
        "\u2193": "down",
        "\u2014": "-",
    }
)


def to_float(value: Any) -> float | None:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return None
    return numeric if math.isfinite(numeric) else None


def normalize_indicators(indicators: dict[str, Any] | None) -> dict[str, float | None]:
    source = indicators if isinstance(indicators, dict) else {}
    return {
        "roc": to_float(source.get("roc")),
        "rsi": to_float(source.get("rsi")),
        "minusDI": to_float(source.get("minusDI", source.get("di_minus"))),
        "plusDI": to_float(source.get("plusDI", source.get("di_plus"))),
        "adx": to_float(source.get("adx")),
        "chop": to_float(source.get("chop")),
    }


def has_indicator_values(indicators: dict[str, Any] | None) -> bool:
    normalized = normalize_indicators(indicators)
    return any(value is not None for value in normalized.values())


def format_number(value: Any, digits: int = 2) -> str:
    numeric = to_float(value)
    if numeric is None:
        return "--"
    if numeric.is_integer():
        return str(int(numeric))
    return f"{numeric:.{digits}f}".rstrip("0").rstrip(".")


def format_indicator(value: Any) -> str:
    return format_number(value, 1)


def read_snapshot() -> dict[str, Any] | None:
    if not SNAPSHOT_FILE.exists():
        return None

    try:
        with SNAPSHOT_FILE.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Could not parse snapshot JSON: {SNAPSHOT_FILE} ({exc})") from exc

    return payload if isinstance(payload, dict) else None


def resolve_selected_row(rows: list[dict[str, Any]], strike: float | None) -> dict[str, Any] | None:
    if not rows:
        return None

    if strike is not None:
        return min(
            rows,
            key=lambda row: abs((to_float(row.get("strike")) or strike) - strike),
        )

    atm = next((row for row in rows if row.get("isATM")), None)
    return atm or rows[len(rows) // 2]


def candle_file_strike(path: Path) -> float | None:
    match = re.match(r"candles_(\d+(?:\.\d+)?)_straddle_", path.name)
    return to_float(match.group(1)) if match else None


def find_bot_candle_file(strike: float | None) -> Path | None:
    files = list(BOT_HISTORICAL_DIR.glob("candles_*_straddle_*.csv"))
    if not files:
        return None

    if strike is None:
        return max(files, key=lambda path: path.stat().st_mtime)

    return min(
        files,
        key=lambda path: (
            abs((candle_file_strike(path) or strike) - strike),
            -path.stat().st_mtime,
        ),
    )


def mean_finite(values: list[float | None]) -> float | None:
    finite = [value for value in values if value is not None and math.isfinite(value)]
    return sum(finite) / len(finite) if finite else None


def rma(values: list[float | None], length: int) -> list[float | None]:
    result: list[float | None] = [None] * len(values)

    if length <= 0 or len(values) < length:
        return result

    seed = mean_finite(values[:length])
    if seed is None:
        return result

    result[length - 1] = seed
    alpha = 1.0 / length

    for index in range(length, len(values)):
        value = values[index]
        previous = result[index - 1]

        if value is None or previous is None:
            result[index] = None
        else:
            result[index] = alpha * value + (1 - alpha) * previous

    return result


def calc_roc(closes: list[float], length: int = 9) -> list[float | None]:
    output: list[float | None] = [None] * len(closes)

    for index, close in enumerate(closes):
        if index < length:
            continue

        previous = closes[index - length]
        if previous and previous != 0:
            output[index] = ((close - previous) / previous) * 100

    return output


def calc_rsi(closes: list[float], length: int = 14) -> list[float | None]:
    changes: list[float | None] = [None]

    for index in range(1, len(closes)):
        changes.append(closes[index] - closes[index - 1])

    gains = [None if change is None else max(change, 0.0) for change in changes]
    losses = [None if change is None else max(-change, 0.0) for change in changes]

    avg_gain = rma(gains, length)
    avg_loss = rma(losses, length)

    output: list[float | None] = []

    for gain, loss in zip(avg_gain, avg_loss):
        if gain is None or loss is None:
            output.append(None)
        elif loss == 0:
            output.append(100.0)
        elif gain == 0:
            output.append(0.0)
        else:
            rs = gain / loss
            output.append(100 - (100 / (1 + rs)))

    return output


def true_ranges(highs: list[float], lows: list[float], closes: list[float]) -> list[float | None]:
    output: list[float | None] = []

    for index, high in enumerate(highs):
        if index == 0:
            output.append(None)
            continue

        previous_close = closes[index - 1]

        output.append(
            max(
                high - lows[index],
                abs(high - previous_close),
                abs(lows[index] - previous_close),
            )
        )

    return output


def calc_dmi(
    highs: list[float],
    lows: list[float],
    closes: list[float],
    length: int = 14,
) -> tuple[list[float | None], list[float | None], list[float | None]]:
    plus_dm: list[float | None] = []
    minus_dm: list[float | None] = []

    for index in range(len(highs)):
        if index == 0:
            plus_dm.append(0.0)
            minus_dm.append(0.0)
            continue

        up_move = highs[index] - highs[index - 1]
        down_move = lows[index - 1] - lows[index]

        plus_dm.append(up_move if up_move > down_move and up_move > 0 else 0.0)
        minus_dm.append(down_move if down_move > up_move and down_move > 0 else 0.0)

    tr = true_ranges(highs, lows, closes)

    tr_rma = rma(tr, length)
    plus_rma = rma(plus_dm, length)
    minus_rma = rma(minus_dm, length)

    plus_di: list[float | None] = []
    minus_di: list[float | None] = []
    dx: list[float | None] = []

    for tr_value, plus_value, minus_value in zip(tr_rma, plus_rma, minus_rma):
        if tr_value is None or plus_value is None or minus_value is None or tr_value == 0:
            plus_di.append(None)
            minus_di.append(None)
            dx.append(None)
            continue

        plus_di_value = 100 * plus_value / tr_value
        minus_di_value = 100 * minus_value / tr_value

        plus_di.append(plus_di_value)
        minus_di.append(minus_di_value)

        denominator = plus_di_value + minus_di_value
        dx.append(
            0.0
            if denominator == 0
            else 100 * abs(plus_di_value - minus_di_value) / denominator
        )

    adx = rma(dx, length)

    return plus_di, minus_di, adx


def calc_chop(
    highs: list[float],
    lows: list[float],
    closes: list[float],
    length: int = 14,
) -> list[float | None]:
    tr = true_ranges(highs, lows, closes)
    output: list[float | None] = [None] * len(closes)

    for index in range(length - 1, len(closes)):
        window_tr = tr[index - length + 1 : index + 1]

        if any(value is None for value in window_tr):
            continue

        highest = max(highs[index - length + 1 : index + 1])
        lowest = min(lows[index - length + 1 : index + 1])

        price_range = highest - lowest
        tr_sum = sum(value for value in window_tr if value is not None)

        if price_range > 0 and tr_sum > 0:
            output[index] = 100 * math.log10(tr_sum / price_range) / math.log10(length)

    return output


def find_exact_candle_row(
    rows: list[dict[str, Any]],
    target_open: float | None,
    target_close: float | None,
) -> dict[str, Any] | None:
    if target_open is None or target_close is None:
        return None

    candidates: list[dict[str, Any]] = []

    for row in rows:
        row_open = to_float(row.get("open"))
        row_close = to_float(row.get("close"))
        if row_open is None or row_close is None:
            continue

        if abs(row_close - target_close) <= 0.1 and abs(row_open - target_open) <= 0.5:
            candidates.append(row)

    if not candidates:
        return None

    return min(
        candidates,
        key=lambda row: (
            abs(to_float(row.get("close")) - target_close)
            + abs(to_float(row.get("open")) - target_open)
        ),
    )


def load_bot_reference_indicators(
    strike: float | None,
    selected_row: dict[str, Any] | None = None,
    target_open: float | None = None,
    target_ltp: float | None = None,
) -> tuple[dict[str, float | None], str]:
    path = find_bot_candle_file(strike)

    if path is None:
        return EMPTY_INDICATORS.copy(), f"missing: {BOT_HISTORICAL_DIR}"

    with path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))

    if not rows:
        return EMPTY_INDICATORS.copy(), str(path)

    matched_row = find_exact_candle_row(rows, target_open, target_ltp)
    if matched_row is None:
        print(f"No exact candle found for open={target_open} close={target_ltp}")
        return EMPTY_INDICATORS.copy(), f"no exact candle found in {path}"

    stored = normalize_indicators(
        {
            "roc": matched_row.get("roc"),
            "rsi": matched_row.get("rsi"),
            "di_minus": matched_row.get("di_minus"),
            "di_plus": matched_row.get("di_plus"),
            "adx": matched_row.get("adx"),
            "chop": matched_row.get("chop"),
        }
    )

    print(
        f"Matched candle: open={matched_row.get('open')} "
        f"close={matched_row.get('close')} "
        f"time={matched_row.get('datetime') or matched_row.get('timestamp') or '--'}"
    )

    if has_indicator_values(stored):
        return stored, f"exact match from {path}"

    print(f"Exact candle found, but stored indicators are missing in {path}")
    return EMPTY_INDICATORS.copy(), f"exact match row missing indicators in {path}"


def display_cell(row: dict[str, Any], key: str) -> str:
    value = row.get(key)

    if key == "strike":
        return format_number(value, 0)

    if key in {"open", "ltp", "change"}:
        return format_number(value, 2)

    return str(value).translate(TEXT_REPLACEMENTS) if value not in (None, "") else "--"


def print_dashboard_table(rows: list[dict[str, Any]], selected_row: dict[str, Any] | None) -> None:
    selected_strike = to_float((selected_row or {}).get("strike"))

    rendered = [
        [display_cell(row, key) for key, _header in TABLE_COLUMNS]
        for row in rows
    ]

    headers = [header for _key, header in TABLE_COLUMNS]

    widths = [
        max(len(headers[index]), *(len(row[index]) for row in rendered))
        if rendered
        else len(headers[index])
        for index in range(len(headers))
    ]

    print("  ".join(header.ljust(widths[index]) for index, header in enumerate(headers)))
    print("  ".join("-" * width for width in widths))

    for row, rendered_row in zip(rows, rendered):
        marker = (
            ">"
            if selected_strike is not None
            and to_float(row.get("strike")) == selected_strike
            else " "
        )

        print(
            marker
            + " "
            + "  ".join(
                value.ljust(widths[index])
                for index, value in enumerate(rendered_row)
            )
        )


def print_indicator_footer(indicators: dict[str, Any]) -> None:
    normalized = normalize_indicators(indicators)

    parts = [
        f"ROC {format_indicator(normalized['roc'])}",
        f"RSI {format_indicator(normalized['rsi'])}",
        f"-DI {format_indicator(normalized['minusDI'])}",
        f"+DI {format_indicator(normalized['plusDI'])}",
        "ADX -",
        f"CHOP {format_indicator(normalized['chop'])}",
    ]

    print(" | ".join(parts))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Print strike table output and ROC/RSI/DI/ADX/CHOP footer using My_Algo_Bot reference data.",
    )

    parser.add_argument(
        "--strike",
        type=float,
        default=None,
        help="Strike to center/select. Defaults to ATM row.",
    )

    parser.add_argument(
        "--open",
        type=float,
        default=None,
        help="Match candle open value from screenshot/table.",
    )

    parser.add_argument(
        "--ltp",
        type=float,
        default=None,
        help="Match candle close/LTP value from screenshot/table.",
    )

    parser.add_argument(
        "--bot-only",
        action="store_true",
        help="Ignore cached backend snapshot table and print only My_Algo_Bot reference indicators.",
    )

    return parser.parse_args()


def main() -> None:
    args = parse_args()

    snapshot = None if args.bot_only else read_snapshot()
    rows = snapshot.get("strikes", []) if isinstance(snapshot, dict) else []

    selected_row = resolve_selected_row(rows, args.strike)
    selected_strike = to_float((selected_row or {}).get("strike")) or args.strike

    bot_indicators, bot_source = load_bot_reference_indicators(
        selected_strike,
        selected_row,
        target_open=args.open,
        target_ltp=args.ltp,
    )

    output_indicators = bot_indicators
    output_source = bot_source

    print("=== Strike output test ===")
    print(f"My_Algo_Bot ref: {bot_source}")
    print(f"Output source: {output_source}")

    if rows and not args.bot_only:
        print_dashboard_table(rows, selected_row)
        print()
    else:
        print("No cached strike rows found; showing indicator footer only.")
        print()

    print("=== ROC RSI DI ADX CHOP ===")
    print_indicator_footer(output_indicators)

    normalized = normalize_indicators(output_indicators)

    required_keys = ["roc", "rsi", "minusDI", "plusDI", "chop"]

    missing = [
        label
        for key, label in INDICATOR_LABELS
        if key in required_keys and to_float(normalized[key]) is None
    ]

    if missing:
        raise SystemExit(f"Missing indicator values: {', '.join(missing)}")


if __name__ == "__main__":
    main()