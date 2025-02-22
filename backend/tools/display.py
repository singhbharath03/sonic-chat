import math

from functools import partial
from typing import Optional

from tools.typing import DisplayValue_
from chaindata.constants import ONE_TRILLION


POWER_LABELS = [(12, "T"), (9, "B"), (6, "M"), (6, "MN"), (3, "K")]
VERY_SMALL_CUTOFF = 1e-2
SUBSCRIPT_DIGITS = ["₀", "₁", "₂", "₃", "₄", "₅", "₆", "₇", "₈", "₉"]


def show_exponent_after_n_digits(x, n=6, num_sig_digs=None):
    if x == 0:
        return "0"

    if num_sig_digs is None:
        num_sig_digs = 3

    # 1.45892e(+|-)x
    notation_abuse = f"{x:.{num_sig_digs - 1}e}"
    base, exponent = notation_abuse.split("e")
    base = int(base.replace(".", ""))
    exponent = int(exponent)

    while base % 10 == 0:
        base = base / 10
        exponent = exponent + 1

    if abs(exponent) > n:
        return f"{x:.{num_sig_digs}e}"
    if exponent < 0:
        f_count = -exponent + num_sig_digs - 1
        return f"{x:.{f_count}f}"

    return f"{x}"


def round_to_n_sig_dig(x, n):
    if x == 0:
        return x
    float_res = round(x, -int(math.floor(math.log10(x))) + (n - 1))
    if int(float_res) == float_res:
        return int(float_res)

    return float_res


def round_to_multiple_of(x, multiple=5):
    return multiple * round(x / multiple)


def money_approx(
    amount,
    prefix="$",
    approximate_values=False,
    suffix="",
    sig_digs: Optional[int] = 3,
    round_multiple_of=None,
    positive_sign=False,
    empty_one=False,
    skip_sign=False,
    scientific_notation_after_n_digits=6,
):
    prefix = prefix or ""
    suffix = " " + suffix if suffix else ""
    if amount >= 0:
        if positive_sign:
            sign = "+"
        else:
            sign = ""
    else:
        sign = "-"
    if skip_sign:
        sign = ""

    amount = abs(amount)

    if round_multiple_of is not None:
        rounding_fn = partial(round_to_multiple_of, multiple=round_multiple_of)
        # multiple rounding will give 0 for very small values
        approximate_values = True
    else:
        rounding_fn = partial(round_to_n_sig_dig, n=sig_digs)

    if amount >= 1000 * ONE_TRILLION:
        # use scientific notation for very large values
        return f"{sign}{prefix}{amount:.{scientific_notation_after_n_digits}e}{suffix}"

    if amount >= 1000:
        for power, label in POWER_LABELS:
            divisor = int(math.pow(10, power))
            multiple = amount / divisor
            multiple = rounding_fn(multiple)
            if multiple >= 1:
                return f"{sign}{prefix}{multiple}{label}{suffix}"

    elif amount > 10:
        approx_amount = rounding_fn(amount)
        if approx_amount:
            return f"{sign}{prefix}{approx_amount}{suffix}"

    if amount < 0.01 and approximate_values:
        # No sign when value is almost zero
        return f"~{prefix}0{suffix}"
    elif amount < VERY_SMALL_CUTOFF:
        amount = very_small_number_formatting(amount, rounding_fn, sig_digs)
        return f"{sign}{prefix}{amount}{suffix}"
    else:
        # Don't round very small qty to zero
        amount = rounding_fn(amount)

    # Don't round very small qty to zero
    if approximate_values and not amount:
        return f"~{prefix}0{suffix}"

    if empty_one and amount == 1 and not suffix:
        return ""

    amount = show_exponent_after_n_digits(
        amount, n=scientific_notation_after_n_digits, num_sig_digs=sig_digs
    )
    return f"{sign}{prefix}{amount}{suffix}"


def very_small_number_formatting(amount, rounding_fn, num_sig_digs: Optional[int] = 4):
    if amount > 1:
        raise ValueError("amount must be less than 1")

    if amount == 0:
        negative_exp = 0
        return "0"
    else:
        negative_exp = abs(int(math.floor(math.log10(amount))))

    suffix_num = rounding_fn(round(amount * 10 ** (negative_exp + num_sig_digs - 1)))
    subscript = num_to_subscript(negative_exp - 1)

    return f"0.0{subscript}{suffix_num}"


def num_to_subscript(num):
    if num == 0:
        return SUBSCRIPT_DIGITS[0]

    result = []
    while num > 0:
        result.append(SUBSCRIPT_DIGITS[num % 10])
        num = num // 10

    return "".join(result[::-1])


def percent_view(perc, delta_view=True, skip_sign=True):
    direction = perc / abs(perc) if perc else 0
    sign = "+" if direction == +1 else ("-" if direction == -1 else "")
    ret = {}
    if delta_view:
        ret["direction"] = direction
    elif sign == "+":
        sign = ""
    ret["value"] = perc
    perc = round_to_n_sig_dig(abs(perc), 2)
    if perc < 0.01:
        perc = 0
    elif perc > 1000 or perc < 1:
        perc = money_approx(perc, prefix="", approximate_values=True)

    if skip_sign:
        ret["display_value"] = str(perc) + "%"
    else:
        ret["display_value"] = sign + str(perc) + "%"

    return ret


def metric_approx_dv(value: Optional[float]) -> Optional[DisplayValue_]:
    if value is None:
        return None

    sig_digs = 3
    if abs(value) < 1:
        sig_digs = 2
    return DisplayValue_(
        value=value,
        display_value=money_approx(
            value,
            sig_digs=sig_digs,
            prefix="",
            suffix="",
            approximate_values=False,
        ),
    )


def money_approx_dv(value: Optional[float]) -> Optional[DisplayValue_]:
    if value is None:
        return None

    sig_digs = 3
    if abs(value) < 1:
        sig_digs = 2

    return DisplayValue_(
        value=value,
        display_value=money_approx(
            value,
            sig_digs=sig_digs,
            prefix="$",
            suffix="",
            approximate_values=False,
        ),
    )
