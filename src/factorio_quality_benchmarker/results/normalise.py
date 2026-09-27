from collections.abc import Mapping
from dataclasses import dataclass

from factorio_quality_benchmarker.game.engine import QualityAmounts
from factorio_quality_benchmarker.game.models import Item, Material
from factorio_quality_benchmarker.optimiser.upcyclers import (
    ResultMetrics,
    UpcyclerResult,
)


@dataclass(frozen=True, slots=True)
class NormalisedMetrics:
    legendary_output: Mapping[Item, float]
    material_inputs: Mapping[Material, QualityAmounts]


SECONDS_PER_HOUR = 3_600

READABLE_SCALES = (
    1,
    10,
    100,
    1_000,
    10_000,
    100_000,
    1_000_000,
)


def _readable_scale(legendary_output: float) -> float:
    for scale in READABLE_SCALES:
        if legendary_output * scale >= 1:
            return scale

    return READABLE_SCALES[-1]


def _format_number(value: float) -> str:
    if value >= 100:
        return f"{value:,.0f}"

    if value >= 10:
        return f"{value:,.1f}"

    if value >= 1:
        return f"{value:,.2f}"

    return f"{value:.3g}"


def _display_name(name: str) -> str:
    return name.replace("-", " ").title()


def _format_inputs(
    inputs: Mapping[Material, QualityAmounts],
    *,
    per_hour: bool,
) -> str:
    parts: list[str] = []
    suffix = "/h" if per_hour else ""

    for material, amounts in inputs.items():
        for quality, amount in amounts.amounts.items():
            if amount == 0:
                continue

            quality_prefix = (
                "" if quality.name == "normal" else f"{_display_name(quality.name)} "
            )

            parts.append(
                f"{_format_number(amount)} "
                f"{quality_prefix}{_display_name(material.name)}{suffix}"
            )

    return " + ".join(parts)


def _format_outputs(
    outputs: Mapping[Item, float],
    *,
    per_hour: bool,
) -> str:
    suffix = "/h" if per_hour else ""

    return " + ".join(
        f"{_format_number(amount)} Legendary {_display_name(item.name)}{suffix}"
        for item, amount in outputs.items()
        if amount != 0
    )


def _normalise_metrics(
    metrics: ResultMetrics,
    *,
    scale: float,
    per_hour: bool,
) -> NormalisedMetrics:
    time_scale = SECONDS_PER_HOUR if per_hour else 1.0

    input_scale = scale * time_scale

    if per_hour:
        input_scale *= metrics.initial_input_utilisation

    return NormalisedMetrics(
        legendary_output={
            item: amount * scale * time_scale
            for item, amount in metrics.legendary_output.items()
        },
        material_inputs={
            material: amounts.scale(input_scale)
            for material, amounts in metrics.initial_inputs.items()
        },
    )


def format_readable_metrics(
    metrics: ResultMetrics,
    *,
    scale: float,
    per_hour: bool,
) -> str:
    normalised = _normalise_metrics(
        metrics,
        scale=scale,
        per_hour=per_hour,
    )

    return (
        f"{_format_outputs(normalised.legendary_output, per_hour=per_hour)}"
        f" / "
        f"{_format_inputs(normalised.material_inputs, per_hour=per_hour)}"
    )


def markdown_table(
    target: Item,
    result: UpcyclerResult,
) -> str:
    per_input_metrics = (
        result.per_input.legendary_per_input,
        result.per_second.legendary_per_input,
    )
    per_second_metrics = (
        result.per_input.legendary_per_second,
        result.per_second.legendary_per_second,
    )

    per_input_scale = _readable_scale(
        min(metrics.legendary_output[target] for metrics in per_input_metrics)
    )
    per_hour_scale = _readable_scale(
        min(
            metrics.legendary_output[target] * SECONDS_PER_HOUR
            for metrics in per_second_metrics
        )
    )

    rows = [
        (
            "Input-optimal",
            format_readable_metrics(
                result.per_input.legendary_per_input,
                scale=per_input_scale,
                per_hour=False,
            ),
            format_readable_metrics(
                result.per_input.legendary_per_second,
                scale=per_hour_scale,
                per_hour=True,
            ),
        ),
        (
            "Throughput-optimal",
            format_readable_metrics(
                result.per_second.legendary_per_input,
                scale=per_input_scale,
                per_hour=False,
            ),
            format_readable_metrics(
                result.per_second.legendary_per_second,
                scale=per_hour_scale,
                per_hour=True,
            ),
        ),
    ]

    lines = [
        "| Configuration | Legendary / input craft | Legendary / hour |",
        "| --- | --- | --- |",
    ]

    lines.extend(
        f"| {name} | {per_input} | {per_second} |"
        for name, per_input, per_second in rows
    )

    return "\n".join(lines)
