from collections.abc import Mapping, Sequence
from pathlib import Path

import pandas as pd

from factorio_quality_benchmarker.game.models import Item
from factorio_quality_benchmarker.optimiser.upcyclers import UpcyclerResult

from .models import ConfigurationRow, ResultRow
from .serialise import configuration_rows, result_row


def export_results(
    results: Mapping[Item, Sequence[UpcyclerResult]],
    output_dir: Path,
) -> None:
    result_rows: list[ResultRow] = []
    configuration_rows_: list[ConfigurationRow] = []

    next_result_id = 0
    next_configuration_id = 0

    for target, target_results in results.items():
        for result in target_results:
            per_input_id = next_configuration_id
            next_configuration_id += 1

            configuration_rows_.extend(
                configuration_rows(
                    per_input_id,
                    result.per_input.configuration,
                )
            )

            per_second_id = next_configuration_id
            next_configuration_id += 1

            configuration_rows_.extend(
                configuration_rows(
                    per_second_id,
                    result.per_second.configuration,
                )
            )

            result_rows.append(
                result_row(
                    result_id=next_result_id,
                    target=target,
                    result=result,
                    per_input_configuration_id=per_input_id,
                    per_second_configuration_id=per_second_id,
                )
            )

            next_result_id += 1

    output_dir.mkdir(parents=True, exist_ok=True)

    pd.DataFrame(result_rows).to_csv(
        output_dir / "results.csv",
        index=False,
    )

    pd.DataFrame(configuration_rows_).to_csv(
        output_dir / "configurations.csv",
        index=False,
    )
