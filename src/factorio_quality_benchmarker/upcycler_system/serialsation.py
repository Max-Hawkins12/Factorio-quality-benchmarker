from factorio_quality_benchmarker.model import Item, Recipe

from .models import UpcyclerGraph, UpcyclerSystem


def _serialise_graph_node(
    node: Item | Recipe,
) -> dict[str, str]:

    if isinstance(node, Item):
        return {
            "type": "item",
            "name": node.name,
        }

    if isinstance(node, Recipe):
        return {
            "type": "recipe",
            "name": node.name,
        }

    raise TypeError(f"Unsupported graph node type: {type(node)}")


def _serialise_upcycler_graph(
    upcycler: UpcyclerGraph,
) -> dict:

    return {
        "start_recipe": upcycler.start_recipe.name,
        "input_materials": [item.name for item in upcycler.input_materials],
        "nodes": [_serialise_graph_node(node) for node in upcycler.graph.nodes],
        "edges": [
            {
                "source": _serialise_graph_node(source),
                "target": _serialise_graph_node(target),
            }
            for source, target in upcycler.graph.edges
        ],
    }


def serialise_upcycler_system(
    system: UpcyclerSystem,
) -> dict:

    return {
        "target": system.target.name,
        "upcyclers": [
            _serialise_upcycler_graph(upcycler) for upcycler in system.upcyclers
        ],
    }
