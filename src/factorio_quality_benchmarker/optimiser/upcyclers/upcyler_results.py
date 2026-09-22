from collections import defaultdict
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field

from factorio_quality_benchmarker.game.engine import QualityAmounts
from factorio_quality_benchmarker.game.models import Item, Quality, Recipe
from factorio_quality_benchmarker.optimiser.cache import get_from_cache
from factorio_quality_benchmarker.optimiser.recipes import (
    RecipeConfiguration,
    RecipeConfigurationCache,
)
from factorio_quality_benchmarker.optimiser.simulation import Qualified

from .constants import EMPTY_QUALITY_AMOUNTS
from .models import (
    GraphConfiguration,
    GraphFrontiers,
    GraphState,
    ProductionGraph,
    RecipeGraph,
    UpcyclerResult,
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

    return GraphState(
        available={
            material: state.available.get(material, EMPTY_QUALITY_AMOUNTS)
            - consumes.get(material, EMPTY_QUALITY_AMOUNTS)
            + produces.get(material, EMPTY_QUALITY_AMOUNTS)
            for material in materials
            if isinstance(material, Item)
        },
        configurations=state.configurations
        | {Qualified(recipe, quality): configuration},
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
        if not recipe.ingredient_items:
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


# Legendary/input Methods
def _initial_state_throughput_ignored(
    recipe_configuration: RecipeConfiguration,
) -> GraphState:
    return GraphState(
        available=dict(recipe_configuration.metrics.input_materals_per_craft),
        configurations={},
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

    item_inputs = configuration.metrics.input_items_per_craft

    throughput = (
        min(
            state.available[material][quality] / item_inputs[material][quality]
            for material in item_inputs
        )
        if item_inputs
        else 1.0
    )

    return _advance_state(state, configuration, throughput, quality, recipe)


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


# Legendary/second Methods
def _get_throughput(
    state: GraphState,
    configuration: RecipeConfiguration,
    quality: Quality,
) -> float:
    item_inputs = configuration.metrics.input_items_per_craft

    return min(
        (
            min(
                state.available[material][quality] / item_inputs[material][quality]
                for material in item_inputs
            )
            if item_inputs
            else 1.0
        ),
        configuration.metrics.crafts_per_second,
    )


def _initial_state_throughput_observed(
    configuration: RecipeConfiguration,
) -> GraphState:
    throughput = configuration.metrics.crafts_per_second

    return GraphState(
        available={
            material: amounts.scale(throughput)
            for material, amounts in configuration.metrics.input_materals_per_craft.items()
        },
        configurations={},
    )


def _get_configurations_throughput_observed(
    state: GraphState | None,
    recipe: Recipe,
    quality: Quality,
    recipe_configuration_cache: RecipeConfigurationCache,
) -> tuple[RecipeConfiguration, ...]:
    configurations = recipe_configuration_cache.get(recipe)[quality]

    limited_crafts_per_second = (
        None if state is None else _get_throughput(state, configurations[0], quality)
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
        _get_throughput(state, configuration, quality),
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


# Graph evaluation
def _legendary_per_input(
    state: GraphState,
    target: Item,
    graph: RecipeGraph,
    qualities: Mapping[str, Quality],
) -> float:

    legendary_output = state.available[target][qualities["legendary"]]

    if isinstance(graph, UpcyclingGraph) and graph.is_self_recycling:
        net_input = 1.0 - state.available[target][qualities["normal"]]
        return legendary_output / net_input

    return legendary_output


def _legendary_per_second(
    state: GraphState,
    target: Item,
    graph: RecipeGraph,
    qualities: Mapping[str, Quality],
) -> float:
    return state.available[target][qualities["legendary"]]


def _next_state(
    state: GraphState | None,
    next_graph: RecipeGraph,
    next_graph_qualities: tuple[Quality, ...],
) -> GraphState:

    return GraphState(
        available={
            material: QualityAmounts(
                {
                    quality: amount
                    for quality, amount in quality_amounts.amounts.items()
                    if quality in next_graph_qualities
                }
            )
            for material, quality_amounts in state.available.items()
            for material in next_graph.input_items
        },
        configurations={},
    )


def _evaluate_graph(
    state: GraphState,
    graph: RecipeGraph,
    qualities: Mapping[str, Quality],
    configurations: Mapping[Qualified[Recipe], RecipeConfiguration],
    advance_state: Callable[
        [GraphState, RecipeConfiguration, Quality, Recipe],
        GraphState,
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


def _evaluate_per_input(
    state: GraphState | None,
    graph: RecipeGraph,
    qualities: Mapping[str, Quality],
    configurations: Mapping[Qualified[Recipe], RecipeConfiguration],
) -> GraphState:
    return _evaluate_graph(
        state=state,
        graph=graph,
        qualities=qualities,
        configurations=configurations,
        advance_state=_advance_state_throughput_ignored,
    )


def _evaluate_per_second(
    target: Item,
    graph: RecipeGraph,
    qualities: Mapping[str, Quality],
    configurations: Mapping[Qualified[Recipe], RecipeConfiguration],
) -> float:
    return _evaluate_graph(
        target=target,
        graph=graph,
        qualities=qualities,
        configurations=configurations,
        initial_state=_initial_state_throughput_observed,
        advance_state=_advance_state_throughput_observed,
        metric=_legendary_per_second,
    )


@dataclass(slots=True)
class UpcyclerResultsCache:
    qualities: Mapping[str, Quality]
    recipe_cache: RecipeConfigurationCache
    upcycler_system_cache: UpcyclerSystemCache

    _upcycler_frontiers: dict[UpcyclingGraph, GraphFrontiers] = field(
        default_factory=dict
    )
    _production_frontiers: dict[ProductionGraph, GraphFrontiers] = field(
        default_factory=dict
    )

    _production_before_frontiers: dict[ProductionGraph, GraphFrontiers] = field(
        default_factory=dict
    )
    _production_after_frontiers: dict[ProductionGraph, GraphFrontiers] = field(
        default_factory=dict
    )

    _results_cache: dict[Item, set[UpcyclerResult]] = field(
        default_factory=lambda: defaultdict(set)
    )
    _searched: set[Item] = field(default_factory=set)

    def _discover(self, item: Item) -> None:

        upcycler_frontiers = self._load_upcycler(
            self.upcycler_system_cache.get(item)[0].upcycler
        )
        print(f"Per input frontiers: {len(upcycler_frontiers.per_input)}")
        for recipe, config in upcycler_frontiers.per_input[0].configurations.items():
            print(f"Recipe: {recipe.name}")
            print(
                f"Config: Modules: {[module.name for module in config.machine_configuration.modules.modules]} Beacons: {[module.name for module in config.machine_configuration.beacons.modules]}"
            )
        print()
        print(f"Per second frontiers: {len(upcycler_frontiers.per_second)}")
        for recipe, config in upcycler_frontiers.per_second[0].configurations.items():
            print(f"Recipe: {recipe.name}")
            print(
                f"Config: Modules: {[module.name for module in config.machine_configuration.modules.modules]} Beacons: {[module.name for module in config.machine_configuration.beacons.modules]}"
            )

        for system in self.upcycler_system_cache.get(item):
            upcycler_frontiers = self._load_upcycler(system.upcycler)

            if system.before_production_graph is not None:
                before = self._load_production(system.before_production_graph)

                state = _evaluate_graph(
                    state=_initial_state_throughput_ignored(
                        self.recipe_cache.get(
                            system.before_production_graph.start_recipe
                        ),
                    ),
                    graph=system.before_production_graph,
                    qualities=self.qualities,
                    configurations=before.per_second[0].configurations,
                    advance_state=_advance_state_throughput_ignored,
                )

            if system.after_production_graph is not None:
                after = self._load_production(system.after_production_graph)

            # Graphs must be scaled and evaluated

            # If before -> ucycler.inputs = before.outputs
            #   Need to be careful. state.available may contain buffered items -> need to evaluate output items: {qualified[item] -> amount} or {item -> QualifiedAmount}
            # If after -> after.inputs = upcycler.outputs
            #   Just use state.available in legendary.

            # Then final output:
            #   If after: after.available[legendary target]
            #   else: upcycler.available[legendary target] unless self recycling, then upcycler.available[legendary target]/1.0 - available[normal target]

            # Store results for every result of the graph (caching)

        self._searched.add(item)

    def get(self, item: Item) -> tuple[UpcyclerResult, ...]:
        if item not in self._searched:
            self._discover(item)

        return tuple(self._results_cache[item])

    def _load_upcycler(self, upcycler: UpcyclingGraph) -> GraphFrontiers:
        initial_qualities = tuple(self.qualities.values())

        return get_from_cache(
            cache=self._upcycler_frontiers,
            key=upcycler,
            calculate=lambda: GraphFrontiers(
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

    def _load_production(self, production_graph: ProductionGraph) -> GraphFrontiers:
        initial_qualities = tuple(self.qualities.values())

        return get_from_cache(
            cache=self._production_frontiers,
            key=production_graph,
            calculate=lambda: GraphFrontiers(
                per_input=_graph_per_input_frontier(
                    graph=production_graph,
                    qualities=self.qualities,
                    initial_qualities=initial_qualities,
                    recipe_configuration_cache=self.recipe_cache,
                ),
                per_second=_graph_per_second_frontier(
                    graph=production_graph,
                    qualities=self.qualities,
                    initial_qualities=initial_qualities,
                    recipe_configuration_cache=self.recipe_cache,
                ),
            ),
        )

    def _load_before(self, production_graph: ProductionGraph) -> GraphFrontiers:
        initial_qualities = (self.qualities["normal"],)

        return get_from_cache(
            cache=self._production_before_frontiers,
            key=production_graph,
            calculate=lambda: GraphFrontiers(
                per_input=_graph_per_input_frontier(
                    graph=production_graph,
                    qualities=self.qualities,
                    initial_qualities=initial_qualities,
                    recipe_configuration_cache=self.recipe_cache,
                ),
                per_second=_graph_per_second_frontier(
                    graph=production_graph,
                    qualities=self.qualities,
                    initial_qualities=initial_qualities,
                    recipe_configuration_cache=self.recipe_cache,
                ),
            ),
        )

    def _load_after(self, production_graph: ProductionGraph) -> GraphFrontiers:
        initial_qualities = (self.qualities["legendary"],)

        return get_from_cache(
            cache=self._production_after_frontiers,
            key=production_graph,
            calculate=lambda: GraphFrontiers(
                per_input=_graph_per_input_frontier(
                    graph=production_graph,
                    qualities=self.qualities,
                    initial_qualities=initial_qualities,
                    recipe_configuration_cache=self.recipe_cache,
                ),
                per_second=_graph_per_second_frontier(
                    graph=production_graph,
                    qualities=self.qualities,
                    initial_qualities=initial_qualities,
                    recipe_configuration_cache=self.recipe_cache,
                ),
            ),
        )
