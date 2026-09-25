from collections import defaultdict
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from itertools import product

from factorio_quality_benchmarker.game.engine import QualityAmounts
from factorio_quality_benchmarker.game.models import (
    Fluid,
    Item,
    Quality,
    Recipe,
)
from factorio_quality_benchmarker.optimiser.cache import get_from_cache
from factorio_quality_benchmarker.optimiser.recipes import (
    RecipeConfiguration,
    RecipeConfigurationCache,
)
from factorio_quality_benchmarker.optimiser.simulation import Qualified

from .constants import EMPTY_QUALITY_AMOUNTS
from .models import (
    ConfigurationResult,
    GraphConfiguration,
    GraphState,
    ProductionGraph,
    RecipeGraph,
    ResultMetrics,
    UpcyclerResult,
    UpcyclerSystem,
    UpcyclingGraph,
)
from .pareto import (
    add_state_to_frontier,
    get_frontier_recipe_configurations_throughput_ignored,
    get_frontier_recipe_configurations_throughput_observed,
)
from .upcycler_systems import UpcyclerSystemCache


# Generic Helpers
def _recipes_at_legendary(graph: RecipeGraph) -> tuple[Recipe, ...]:
    if isinstance(graph, UpcyclingGraph) and graph.is_self_recycling:
        return tuple(
            recipe for recipe in graph.ordered_recipes if recipe != graph.end_recipe
        )

    return graph.ordered_recipes


def _advance_state(
    state: GraphState,
    configuration: RecipeConfiguration,
    throughput: float,
    quality: Quality,
    recipe: Recipe,
) -> GraphState:
    if throughput == 0:
        return state

    produces = {
        material: amounts.scale(throughput)
        for material, amounts in configuration.metrics.output_per_craft.items()
    }

    consumes = {
        material: amounts.scale(throughput)
        for material, amounts in configuration.metrics.input_per_craft.items()
    }

    materials = state.available.keys() | consumes.keys() | produces.keys()

    fluid_inputs = dict(state.fluid_inputs)
    fluid_outputs = dict(state.fluid_outputs)

    for material, amounts in consumes.items():
        if isinstance(material, Fluid):
            fluid_inputs[material] = (
                fluid_inputs.get(material, EMPTY_QUALITY_AMOUNTS) + amounts
            )

    for material, amounts in produces.items():
        if isinstance(material, Fluid):
            fluid_outputs[material] = (
                fluid_outputs.get(material, EMPTY_QUALITY_AMOUNTS) + amounts
            )

    return GraphState(
        available={
            material: state.available.get(material, EMPTY_QUALITY_AMOUNTS)
            - consumes.get(material, EMPTY_QUALITY_AMOUNTS)
            + produces.get(material, EMPTY_QUALITY_AMOUNTS)
            for material in materials
        },
        configurations=state.configurations
        | {Qualified(recipe, quality): configuration},
        item_inputs=state.item_inputs,
        fluid_inputs=fluid_inputs,
        fluid_outputs=fluid_outputs,
    )


def _get_frontier_states(
    states: list[GraphState],
    recipes: tuple[Recipe, ...],
    quality: Quality,
    recipe_configuration_cache: RecipeConfigurationCache,
    frontier_configurations: Callable[
        [GraphState | None, Recipe, Quality, RecipeConfigurationCache],
        tuple[RecipeConfiguration, ...],
    ],
    advance_state: Callable[
        [GraphState, RecipeConfiguration, Quality, Recipe],
        GraphState,
    ],
) -> list[GraphState]:
    for recipe in recipes:
        if not recipe.ingredient_materials:
            continue

        next_states: list[GraphState] = []

        for state in states:
            if all(amounts[quality] == 0 for amounts in state.available.values()):
                add_state_to_frontier(next_states, state, quality)
                continue

            for configuration in frontier_configurations(
                state, recipe, quality, recipe_configuration_cache
            ):
                next_state = advance_state(
                    state,
                    configuration,
                    quality,
                    recipe,
                )
                add_state_to_frontier(next_states, next_state, quality)

        states = next_states

    return states


def _graph_frontier(
    graph: RecipeGraph,
    qualities: Mapping[str, Quality],
    initial_qualities: tuple[Quality, ...],
    recipe_configuration_cache: RecipeConfigurationCache,
    initial_state: Callable[[RecipeConfiguration], GraphState],
    get_frontier_configurations: Callable[
        [GraphState | None, Recipe, Quality, RecipeConfigurationCache],
        tuple[RecipeConfiguration, ...],
    ],
    advance_state: Callable[
        [GraphState, RecipeConfiguration, Quality, Recipe],
        GraphState,
    ],
) -> tuple[GraphConfiguration, ...]:

    start_recipe = graph.start_recipe
    initial_quality = initial_qualities[0]

    states = [
        advance_state(
            initial_state(configuration),
            configuration,
            initial_quality,
            start_recipe,
        )
        for configuration in get_frontier_configurations(
            None,
            start_recipe,
            initial_quality,
            recipe_configuration_cache,
        )
    ]

    for quality in qualities.values():
        recipes = (
            _recipes_at_legendary(graph)
            if quality == qualities["legendary"]
            else graph.ordered_recipes
        )

        if quality == initial_quality or quality not in initial_qualities:
            recipes = tuple(recipe for recipe in recipes if recipe != start_recipe)

        if recipes:
            states = _get_frontier_states(
                states=states,
                recipes=recipes,
                quality=quality,
                recipe_configuration_cache=recipe_configuration_cache,
                frontier_configurations=get_frontier_configurations,
                advance_state=advance_state,
            )

    return tuple(
        GraphConfiguration(
            configurations=state.configurations.copy(),
        )
        for state in states
    )


# Legendary/input Frontier Methods
def _get_unlimited_throughput(
    state: GraphState,
    configuration: RecipeConfiguration,
    quality: Quality,
) -> float:
    inputs = configuration.metrics.input_per_craft
    outputs = configuration.metrics.output_per_craft

    relevant_inputs = {
        material: amounts
        for material, amounts in inputs.items()
        if isinstance(material, Item) and amounts[quality] > 0
    }

    if not relevant_inputs:
        return 1.0

    return min(
        state.available.get(material, EMPTY_QUALITY_AMOUNTS)[quality]
        / (amounts[quality] - outputs.get(material, EMPTY_QUALITY_AMOUNTS)[quality])
        for material, amounts in relevant_inputs.items()
    )


def _initial_state_throughput_ignored(
    configuration: RecipeConfiguration,
) -> GraphState:

    return GraphState(
        available=dict(configuration.metrics.input_per_craft),
        configurations={},
        item_inputs=configuration.metrics.input_items_per_craft,
        fluid_inputs=configuration.metrics.input_fluids_per_craft,
        fluid_outputs={},
    )


def _get_configurations_throughput_ignored(
    state: GraphState | None,
    recipe: Recipe,
    quality: Quality,
    recipe_configuration_cache: RecipeConfigurationCache,
) -> tuple[RecipeConfiguration, ...]:
    return get_frontier_recipe_configurations_throughput_ignored(
        recipe_configuration_cache.get(recipe)[quality],
        quality,
    )


def _advance_state_throughput_ignored(
    state: GraphState,
    configuration: RecipeConfiguration,
    quality: Quality,
    recipe: Recipe,
) -> GraphState:

    return _advance_state(
        state,
        configuration,
        _get_unlimited_throughput(state, configuration, quality),
        quality,
        recipe,
    )


def _graph_per_input_frontier(
    graph: RecipeGraph,
    qualities: Mapping[str, Quality],
    initial_qualities: tuple[Quality, ...],
    recipe_configuration_cache: RecipeConfigurationCache,
) -> tuple[GraphConfiguration, ...]:

    return _graph_frontier(
        graph=graph,
        qualities=qualities,
        initial_qualities=initial_qualities,
        recipe_configuration_cache=recipe_configuration_cache,
        initial_state=_initial_state_throughput_ignored,
        get_frontier_configurations=_get_configurations_throughput_ignored,
        advance_state=_advance_state_throughput_ignored,
    )


# Legendary/second Frontier Methods
def _get_speed_limited_throughput(
    state: GraphState,
    configuration: RecipeConfiguration,
    quality: Quality,
) -> float:
    return min(
        _get_unlimited_throughput(state, configuration, quality),
        configuration.metrics.crafts_per_second,
    )


def _initial_state_throughput_observed(
    configuration: RecipeConfiguration,
) -> GraphState:

    throughput = configuration.metrics.crafts_per_second

    return GraphState(
        available={
            material: amounts.scale(throughput)
            for material, amounts in configuration.metrics.input_per_craft.items()
        },
        configurations={},
        item_inputs={
            item: amounts.scale(throughput)
            for item, amounts in configuration.metrics.input_items_per_craft.items()
        },
        fluid_inputs={
            fluid: amounts.scale(throughput)
            for fluid, amounts in configuration.metrics.input_fluids_per_craft.items()
        },
        fluid_outputs={},
    )


def _get_configurations_throughput_observed(
    state: GraphState | None,
    recipe: Recipe,
    quality: Quality,
    recipe_configuration_cache: RecipeConfigurationCache,
) -> tuple[RecipeConfiguration, ...]:
    configurations = recipe_configuration_cache.get(recipe)[quality]

    limited_crafts_per_second = (
        None
        if state is None
        else _get_speed_limited_throughput(state, configurations[0], quality)
    )

    return get_frontier_recipe_configurations_throughput_observed(
        configurations,
        quality,
        limited_crafts_per_second,
    )


def _advance_state_throughput_observed(
    state: GraphState,
    configuration: RecipeConfiguration,
    quality: Quality,
    recipe: Recipe,
) -> GraphState:

    return _advance_state(
        state,
        configuration,
        _get_speed_limited_throughput(state, configuration, quality),
        quality,
        recipe,
    )


def _graph_per_second_frontier(
    graph: RecipeGraph,
    qualities: Mapping[str, Quality],
    initial_qualities: tuple[Quality, ...],
    recipe_configuration_cache: RecipeConfigurationCache,
) -> tuple[GraphConfiguration, ...]:

    return _graph_frontier(
        graph=graph,
        qualities=qualities,
        initial_qualities=initial_qualities,
        recipe_configuration_cache=recipe_configuration_cache,
        initial_state=_initial_state_throughput_observed,
        get_frontier_configurations=_get_configurations_throughput_observed,
        advance_state=_advance_state_throughput_observed,
    )


# Graph Evaluation Method
def _evaluate_graph(
    state: GraphState,
    graph: RecipeGraph,
    qualities: Mapping[str, Quality],
    configurations: Mapping[Qualified[Recipe], RecipeConfiguration],
    advance_state: Callable[
        [GraphState, RecipeConfiguration, Quality, Recipe], GraphState
    ],
) -> GraphState:
    for quality in qualities.values():
        recipes = (
            _recipes_at_legendary(graph)
            if quality == qualities["legendary"]
            else graph.ordered_recipes
        )

        for recipe in recipes:
            configuration = configurations.get(Qualified(recipe, quality))

            if configuration is not None:
                state = advance_state(
                    state,
                    configuration,
                    quality,
                    recipe,
                )

    return state


# System Evaluation Methods
def _legendary_output(
    state: GraphState,
    graph: RecipeGraph,
    qualities: Mapping[str, Quality],
) -> Mapping[Item, float]:
    return {
        product: state.available.get(product, EMPTY_QUALITY_AMOUNTS)[
            qualities["legendary"]
        ]
        for product in graph.end_recipe.product_items
    }


def _next_state_for_system(
    state: GraphState,
    next_graph: RecipeGraph,
    pass_through_qualities: tuple[Quality, ...],
) -> GraphState:
    return GraphState(
        available={
            material: QualityAmounts(
                {
                    quality: amount
                    for quality, amount in quality_amounts.amounts.items()
                    if quality in pass_through_qualities
                }
            )
            for material, quality_amounts in state.available.items()
            if material in next_graph.input_materials
        },
        configurations={},
        item_inputs=state.item_inputs,
        fluid_inputs=state.fluid_inputs,
        fluid_outputs=state.fluid_outputs,
    )


def _initial_state_for_system(
    graph: RecipeGraph,
    configuration: GraphConfiguration,
    qualities: Mapping[str, Quality],
    initial_state: Callable[[RecipeConfiguration], GraphState],
) -> GraphState:

    return initial_state(
        configuration.configurations[Qualified(graph.start_recipe, qualities["normal"])]
    )


@dataclass(frozen=True, slots=True)
class _SystemResult:
    whole_configuration: GraphConfiguration
    upcycler_configuration: GraphConfiguration
    before_configuration: GraphConfiguration | None
    after_configuration: GraphConfiguration | None

    metrics: ResultMetrics


def _evaluate_system_configuration(
    system: UpcyclerSystem,
    upcycler: GraphConfiguration,
    before: GraphConfiguration | None,
    after: GraphConfiguration | None,
    qualities: Mapping[str, Quality],
    initial_state: Callable[[RecipeConfiguration], GraphState],
    advance_state: Callable[
        [GraphState, RecipeConfiguration, Quality, Recipe],
        GraphState,
    ],
) -> _SystemResult:

    if before is not None:
        assert system.before_production_graph is not None

        state = _initial_state_for_system(
            system.before_production_graph, before, qualities, initial_state
        )

        state = _evaluate_graph(
            graph=system.before_production_graph,
            qualities=qualities,
            configurations=before.configurations,
            state=state,
            advance_state=advance_state,
        )

        state = _next_state_for_system(
            state, system.upcycler, tuple(qualities.values())
        )
    else:
        state = _initial_state_for_system(
            system.upcycler, upcycler, qualities, initial_state
        )

    state = _evaluate_graph(
        graph=system.upcycler,
        qualities=qualities,
        configurations=upcycler.configurations,
        state=state,
        advance_state=advance_state,
    )

    final_graph: RecipeGraph = system.upcycler

    if after is not None:
        assert system.after_production_graph is not None

        state = _next_state_for_system(
            state, system.after_production_graph, (qualities["legendary"],)
        )

        state = _evaluate_graph(
            graph=system.after_production_graph,
            qualities=qualities,
            configurations=after.configurations,
            state=state,
            advance_state=advance_state,
        )

        final_graph = system.after_production_graph

    whole_configuration = {}

    if before is not None:
        whole_configuration.update(before.configurations)

    whole_configuration.update(upcycler.configurations)

    if after is not None:
        whole_configuration.update(after.configurations)

    return _SystemResult(
        whole_configuration=GraphConfiguration(configurations=whole_configuration),
        upcycler_configuration=upcycler,
        before_configuration=before,
        after_configuration=after,
        metrics=ResultMetrics(
            legendary_output=_legendary_output(state, final_graph, qualities),
            material_inputs=state.material_inputs,
            fluid_outputs=state.fluid_outputs,
        ),
    )


def _evaluate_system(
    target: Item,
    system: UpcyclerSystem,
    upcycler: tuple[GraphConfiguration, ...],
    before: tuple[GraphConfiguration, ...] | None,
    after: tuple[GraphConfiguration, ...] | None,
    qualities: Mapping[str, Quality],
    initial_state: Callable[[RecipeConfiguration], GraphState],
    advance_state: Callable[
        [GraphState, RecipeConfiguration, Quality, Recipe],
        GraphState,
    ],
) -> _SystemResult:
    before_configurations = before or (None,)
    after_configurations = after or (None,)

    best: _SystemResult | None = None

    for before_config, upcycler_config, after_config in product(
        before_configurations,
        upcycler,
        after_configurations,
    ):
        result = _evaluate_system_configuration(
            system=system,
            before=before_config,
            upcycler=upcycler_config,
            after=after_config,
            qualities=qualities,
            initial_state=initial_state,
            advance_state=advance_state,
        )

        if (
            best is None
            or result.metrics.legendary_output[target]
            > best.metrics.legendary_output[target]
        ):
            best = result

    assert best is not None
    return best


@dataclass(frozen=True, slots=True)
class _GraphFrontiers:
    per_input: tuple[GraphConfiguration, ...]
    per_second: tuple[GraphConfiguration, ...]


@dataclass(slots=True)
class UpcyclerResultsCache:
    qualities: Mapping[str, Quality]
    recipe_cache: RecipeConfigurationCache
    upcycler_system_cache: UpcyclerSystemCache

    _upcycler_frontiers: dict[UpcyclingGraph, _GraphFrontiers] = field(
        default_factory=dict
    )
    _production_frontiers: dict[
        tuple[ProductionGraph, tuple[Quality, ...]],
        _GraphFrontiers,
    ] = field(default_factory=dict)

    _results_cache: dict[Item, set[UpcyclerResult]] = field(
        default_factory=lambda: defaultdict(set)
    )
    _searched: set[Item] = field(default_factory=set)

    def _discover(self, item: Item) -> None:
        for system in self.upcycler_system_cache.get(item):
            upcycler_frontiers = self._load_upcycler(system.upcycler)

            before_frontiers = (
                self._load_production(
                    system.before_production_graph,
                    (self.qualities["normal"],),
                )
                if system.before_production_graph is not None
                else None
            )

            after_frontiers = (
                self._load_production(
                    system.after_production_graph,
                    (self.qualities["legendary"],),
                )
                if system.after_production_graph is not None
                else None
            )

            per_input = _evaluate_system(
                target=item,
                system=system,
                upcycler=upcycler_frontiers.per_input,
                before=(
                    before_frontiers.per_input if before_frontiers is not None else None
                ),
                after=(
                    after_frontiers.per_input if after_frontiers is not None else None
                ),
                qualities=self.qualities,
                initial_state=_initial_state_throughput_ignored,
                advance_state=_advance_state_throughput_ignored,
            )

            per_second = _evaluate_system(
                target=item,
                system=system,
                upcycler=upcycler_frontiers.per_second,
                before=(
                    before_frontiers.per_second
                    if before_frontiers is not None
                    else None
                ),
                after=(
                    after_frontiers.per_second if after_frontiers is not None else None
                ),
                qualities=self.qualities,
                initial_state=_initial_state_throughput_observed,
                advance_state=_advance_state_throughput_observed,
            )

            for output in system.output_items:
                self._results_cache[output].add(
                    UpcyclerResult(
                        system=system,
                        per_input=ConfigurationResult(
                            configuration=per_input.whole_configuration,
                            legendary_per_input=per_input.metrics,
                            legendary_per_second=_evaluate_system_configuration(
                                system=system,
                                upcycler=per_input.upcycler_configuration,
                                before=per_input.before_configuration,
                                after=per_input.after_configuration,
                                qualities=self.qualities,
                                initial_state=_initial_state_throughput_observed,
                                advance_state=_advance_state_throughput_observed,
                            ).metrics,
                        ),
                        per_second=ConfigurationResult(
                            configuration=per_second.whole_configuration,
                            legendary_per_input=_evaluate_system_configuration(
                                system=system,
                                upcycler=per_second.upcycler_configuration,
                                before=per_second.before_configuration,
                                after=per_second.after_configuration,
                                qualities=self.qualities,
                                initial_state=_initial_state_throughput_ignored,
                                advance_state=_advance_state_throughput_ignored,
                            ).metrics,
                            legendary_per_second=per_second.metrics,
                        ),
                    )
                )

    def get(self, item: Item) -> tuple[UpcyclerResult, ...]:
        if item not in self._searched:
            self._discover(item)

            self._searched.add(item)

        return tuple(self._results_cache[item])

    def _load_upcycler(self, upcycler: UpcyclingGraph) -> _GraphFrontiers:
        initial_qualities = tuple(self.qualities.values())

        return get_from_cache(
            cache=self._upcycler_frontiers,
            key=upcycler,
            calculate=lambda: _GraphFrontiers(
                per_input=_graph_per_input_frontier(
                    graph=upcycler,
                    qualities=self.qualities,
                    initial_qualities=initial_qualities,
                    recipe_configuration_cache=self.recipe_cache,
                ),
                per_second=_graph_per_second_frontier(
                    graph=upcycler,
                    qualities=self.qualities,
                    initial_qualities=initial_qualities,
                    recipe_configuration_cache=self.recipe_cache,
                ),
            ),
        )

    def _load_production(
        self,
        production_graph: ProductionGraph,
        initial_qualities: tuple[Quality, ...],
    ) -> _GraphFrontiers:
        return get_from_cache(
            cache=self._production_frontiers,
            key=(production_graph, initial_qualities),
            calculate=lambda: _GraphFrontiers(
                per_input=_graph_per_input_frontier(
                    production_graph,
                    self.qualities,
                    initial_qualities,
                    self.recipe_cache,
                ),
                per_second=_graph_per_second_frontier(
                    production_graph,
                    self.qualities,
                    initial_qualities,
                    self.recipe_cache,
                ),
            ),
        )
