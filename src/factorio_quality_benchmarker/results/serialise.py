from __future__ import annotations

import json
from collections.abc import Mapping

from factorio_quality_benchmarker.game.engine import QualityAmounts
from factorio_quality_benchmarker.game.models import Fluid, Item, Material, Module
from factorio_quality_benchmarker.optimiser.simulation import Qualified
from factorio_quality_benchmarker.optimiser.upcyclers import (
    GraphConfiguration,
    RecipeGraph,
    ResultMetrics,
    UpcyclerResult,
)

from .models import ConfigurationRow, ResultRow


def _to_json(value: object) -> str:
    return json.dumps(
        value,
        separators=(",", ":"),
        sort_keys=True,
    )


def serialise_quality_amounts(amounts: QualityAmounts) -> dict[str, float]:
    return {
        quality.name: amount
        for quality, amount in amounts.amounts.items()
        if amount != 0
    }


def serialise_materials(materials: Mapping[Material, QualityAmounts]) -> str:
    return _to_json(
        {
            material.name: serialise_quality_amounts(amounts)
            for material, amounts in materials.items()
            if any(amounts.amounts.values())
        }
    )


def serialise_fluids(materials: Mapping[Fluid, QualityAmounts]) -> str:
    return _to_json(
        {
            fluid.name: serialise_quality_amounts(amounts)
            for fluid, amounts in materials.items()
            if any(amounts.amounts.values())
        }
    )


def serialise_legendary_output(outputs: Mapping[Item, float]) -> str:
    return _to_json(
        {item.name: amount for item, amount in outputs.items() if amount != 0}
    )


def serialise_modules(modules: tuple[Qualified[Module], ...]) -> str:
    return _to_json(
        [
            {
                "module": module.entity.name,
                "quality": module.quality.name,
            }
            for module in modules
            if module.entity.name != "empty"
        ]
    )


def serialise_graph(graph: RecipeGraph | None) -> str:
    if graph is None:
        return ""

    return _to_json([recipe.name for recipe in graph.ordered_recipes])


def serialise_metrics(
    metrics: ResultMetrics,
) -> dict[str, str]:
    return {
        "legendary_output": serialise_legendary_output(metrics.legendary_output),
        "initial_inputs": serialise_materials(metrics.initial_inputs),
        "initial_input_utilisation": str(metrics.initial_input_utilisation),
        "upstream_fluid_inputs": serialise_fluids(metrics.upstream_fluid_inputs),
        "fluid_outputs": serialise_fluids(metrics.fluid_outputs),
    }


def result_row(
    *,
    result_id: int,
    target: Item,
    result: UpcyclerResult,
    per_input_configuration_id: int,
    per_second_configuration_id: int,
) -> ResultRow:
    pi_pi = serialise_metrics(result.per_input.legendary_per_input)
    pi_ps = serialise_metrics(result.per_input.legendary_per_second)

    ps_pi = serialise_metrics(result.per_second.legendary_per_input)
    ps_ps = serialise_metrics(result.per_second.legendary_per_second)

    system = result.system

    return ResultRow(
        result_id=result_id,
        target=target.name,
        upcycler=system.upcycler.recycled_item.name,
        upcycler_graph=serialise_graph(system.upcycler),
        before_graph=serialise_graph(system.before_production_graph),
        after_graph=serialise_graph(system.after_production_graph),
        per_input_configuration_id=per_input_configuration_id,
        per_input_legendary_per_input=pi_pi["legendary_output"],
        per_input_initial_inputs_per_input=pi_pi["initial_inputs"],
        per_input_initial_input_utilisation_per_input=pi_pi[
            "initial_input_utilisation"
        ],
        per_input_upstream_fluid_inputs_per_input=pi_pi["upstream_fluid_inputs"],
        per_input_fluid_outputs_per_input=pi_pi["fluid_outputs"],
        per_input_legendary_per_second=pi_ps["legendary_output"],
        per_input_initial_inputs_per_second=pi_ps["initial_inputs"],
        per_input_initial_input_utilisation_per_second=pi_ps[
            "initial_input_utilisation"
        ],
        per_input_upstream_fluid_inputs_per_second=pi_ps["upstream_fluid_inputs"],
        per_input_fluid_outputs_per_second=pi_ps["fluid_outputs"],
        per_second_configuration_id=per_second_configuration_id,
        per_second_legendary_per_input=ps_pi["legendary_output"],
        per_second_initial_inputs_per_input=ps_pi["initial_inputs"],
        per_second_initial_input_utilisation_per_input=ps_pi[
            "initial_input_utilisation"
        ],
        per_second_upstream_fluid_inputs_per_input=ps_pi["upstream_fluid_inputs"],
        per_second_fluid_outputs_per_input=ps_pi["fluid_outputs"],
        per_second_legendary_per_second=ps_ps["legendary_output"],
        per_second_initial_inputs_per_second=ps_ps["initial_inputs"],
        per_second_initial_input_utilisation_per_second=ps_ps[
            "initial_input_utilisation"
        ],
        per_second_upstream_fluid_inputs_per_second=ps_ps["upstream_fluid_inputs"],
        per_second_fluid_outputs_per_second=ps_ps["fluid_outputs"],
    )


def configuration_rows(
    configuration_id: int,
    configuration: GraphConfiguration,
) -> list[ConfigurationRow]:
    rows: list[ConfigurationRow] = []

    for qualified_recipe, recipe_configuration in configuration.configurations.items():
        machine = recipe_configuration.machine_configuration

        rows.append(
            ConfigurationRow(
                configuration_id=configuration_id,
                recipe=qualified_recipe.entity.name,
                recipe_quality=qualified_recipe.quality.name,
                crafter=recipe_configuration.crafter.entity.name,
                crafter_quality=recipe_configuration.crafter.quality.name,
                machine_modules=serialise_modules(machine.modules.modules),
                num_beacons=machine.beacons.num_beacons,
                beacon_modules=serialise_modules(machine.beacons.modules),
            )
        )

    return rows
