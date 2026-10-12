from typing import TypedDict


class ResultRow(TypedDict):
    result_id: int
    target: str

    upcycler: str
    upcycler_graph: str
    before_graph: str
    after_graph: str

    per_input_configuration_id: int
    per_input_legendary_per_input: str
    per_input_initial_inputs_per_input: str
    per_input_initial_input_utilisation_per_input: str
    per_input_upstream_fluid_inputs_per_input: str
    per_input_fluid_outputs_per_input: str
    per_input_legendary_per_second: str
    per_input_initial_inputs_per_second: str
    per_input_initial_input_utilisation_per_second: str
    per_input_upstream_fluid_inputs_per_second: str
    per_input_fluid_outputs_per_second: str

    per_second_configuration_id: int
    per_second_legendary_per_input: str
    per_second_initial_inputs_per_input: str
    per_second_initial_input_utilisation_per_input: str
    per_second_upstream_fluid_inputs_per_input: str
    per_second_fluid_outputs_per_input: str
    per_second_legendary_per_second: str
    per_second_initial_inputs_per_second: str
    per_second_initial_input_utilisation_per_second: str
    per_second_upstream_fluid_inputs_per_second: str
    per_second_fluid_outputs_per_second: str


class ConfigurationRow(TypedDict):
    configuration_id: int
    recipe: str
    recipe_quality: str
    crafter: str
    crafter_quality: str
    machine_modules: str
    num_beacons: int
    beacon_modules: str
