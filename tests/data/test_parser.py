import json

import pytest

from factorio_quality_benchmarker.data import raw_data_parser


# Tests for metadata validation
def test_valid_factorio_20_metadata():
    metadata = {
        "factorio_version": "2.0.10",
        "source_file": "data-raw-dump.json",
        "active_mods": ["Quality"],
    }

    raw_data_parser._validate_metadata_fields(metadata)


def test_valid_factorio_21_metadata():
    metadata = {
        "factorio_version": "2.1.0",
        "source_file": "data-raw-dump.json",
        "active_mods": ["Quality", "Recycler"],
    }

    raw_data_parser._validate_metadata_fields(metadata)


@pytest.mark.parametrize(
    "missing_field",
    ["factorio_version", "source_file", "active_mods"],
)
def test_metadata_requires_fields(missing_field):
    metadata = {
        "factorio_version": "2.1.0",
        "source_file": "data-raw-dump.json",
        "active_mods": ["Quality", "Recycler"],
    }
    del metadata[missing_field]

    with pytest.raises(
        ValueError,
        match=f"Missing required field in metadata: {missing_field}",
    ):
        raw_data_parser._validate_metadata_fields(metadata)


def test_metadata_rejects_unsupported_version():
    metadata = {
        "factorio_version": "3.0.0",
        "source_file": "data-raw-dump.json",
        "active_mods": ["Quality", "Recycler"],
    }

    with pytest.raises(ValueError, match="Unsupported Factorio version: 3.0"):
        raw_data_parser._validate_metadata_fields(metadata)


def test_factorio_20_requires_quality_mod():
    metadata = {
        "factorio_version": "2.0.10",
        "source_file": "data-raw-dump.json",
        "active_mods": [],
    }

    with pytest.raises(ValueError, match="Missing required mods"):
        raw_data_parser._validate_metadata_fields(metadata)


def test_factorio_21_requires_quality_mod():
    metadata = {
        "factorio_version": "2.1.0",
        "source_file": "data-raw-dump.json",
        "active_mods": ["Recycler"],
    }

    with pytest.raises(ValueError, match="Missing required mods"):
        raw_data_parser._validate_metadata_fields(metadata)


def test_factorio_21_requires_recycler_mod():
    metadata = {
        "factorio_version": "2.1.0",
        "source_file": "data-raw-dump.json",
        "active_mods": ["Quality"],
    }

    with pytest.raises(ValueError, match="Missing required mods"):
        raw_data_parser._validate_metadata_fields(metadata)


def test_metadata_allows_extra_mods():
    metadata = {
        "factorio_version": "2.1.0",
        "source_file": "data-raw-dump.json",
        "active_mods": ["Quality", "Recycler", "some-other-mod"],
    }

    raw_data_parser._validate_metadata_fields(metadata)


# Tests for required quality and recycler mechanics
def test_quality_and_recycler_are_required():
    raw_data = {
        "quality": {"normal": {}},
        "furnace": {"recycler": {"name": "recycler"}},
    }

    raw_data_parser._validate_quality_and_recycler_present(raw_data)


@pytest.mark.parametrize(
    "raw_data",
    [
        {},
        {"quality": {}},
        {"quality": [], "furnace": {"recycler": {"name": "recycler"}}},
    ],
)
def test_quality_is_required(raw_data):
    with pytest.raises(ValueError, match="Quality mechanic is missing"):
        raw_data_parser._validate_quality_and_recycler_present(raw_data)


@pytest.mark.parametrize(
    "raw_data",
    [
        {"quality": {"normal": {}}},
        {"quality": {"normal": {}}, "furnace": {}},
        {"quality": {"normal": {}}, "furnace": {"recycler": {}}},
    ],
)
def test_recycler_is_required(raw_data):
    with pytest.raises(ValueError, match="Recycler mechanic is missing"):
        raw_data_parser._validate_quality_and_recycler_present(raw_data)


# Test for parser behaviour
def test_parse_prototypes_selects_requested_fields():
    raw_data = {
        "item": {
            "iron-plate": {
                "name": "iron-plate",
                "type": "item",
                "ignored": "value",
            }
        }
    }

    result = raw_data_parser._parse_prototypes(
        raw_data,
        ["item"],
        ["name", "type"],
    )

    assert result == {
        "iron-plate": {
            "name": "iron-plate",
            "type": "item",
        }
    }


def test_parse_prototypes_adds_none_for_missing_fields():
    raw_data = {"item": {"iron-plate": {"name": "iron-plate"}}}

    result = raw_data_parser._parse_prototypes(
        raw_data,
        ["item"],
        ["name", "type"],
    )

    assert result["iron-plate"] == {
        "name": "iron-plate",
        "type": None,
    }


# Test using minimal dataset all files are created
@pytest.fixture
def minimal_raw_data():
    return {
        "item": {
            "iron-plate": {
                "name": "iron-plate",
                "type": "item",
            }
        },
        "fluid": {
            "water": {
                "name": "water",
                "type": "fluid",
            }
        },
        "recipe": {
            "iron-plate": {
                "name": "iron-plate",
                "categories": ["crafting"],
                "ingredients": [],
                "results": [],
                "energy_required": 3.2,
                "allow_productivity": True,
                "allow_quality": True,
                "surface_conditions": None,
            }
        },
        "assembling-machine": {
            "assembling-machine-1": {
                "name": "assembling-machine-1",
                "crafting_categories": ["crafting"],
                "crafting_speed": 0.5,
            }
        },
        "furnace": {
            "recycler": {
                "name": "recycler",
                "crafting_categories": ["recycling"],
            }
        },
        "mining-drill": {
            "burner-mining-drill": {
                "name": "burner-mining-drill",
                "resource_categories": ["basic-solid"],
            }
        },
        "quality": {
            "normal": {
                "name": "normal",
                "level": 0,
            }
        },
        "beacon": {
            "beacon": {
                "name": "beacon",
                "module_slots": 2,
            }
        },
        "planet": {
            "nauvis": {
                "name": "nauvis",
                "surface_properties": {},
            }
        },
        "surface": {
            "space": {
                "name": "space",
                "surface_properties": {},
            }
        },
    }


def test_parse_data_into_files_writes_expected_outputs(tmp_path, minimal_raw_data):
    raw_data_parser._parse_data_into_files(minimal_raw_data, tmp_path)

    items = json.loads((tmp_path / "items.json").read_text())
    fluids = json.loads((tmp_path / "fluids.json").read_text())
    recipes = json.loads((tmp_path / "recipes.json").read_text())
    crafting_machines = json.loads((tmp_path / "crafting_machines.json").read_text())

    print(items)

    assert items == {
        "iron-plate": {
            "name": "iron-plate",
            "type": "item",
        },
    }

    assert fluids == {
        "water": {
            "name": "water",
            "type": "fluid",
        },
    }

    assert recipes["iron-plate"]["name"] == "iron-plate"
    assert recipes["iron-plate"]["energy_required"] == 3.2

    assert "assembling-machine-1" in crafting_machines
    assert not "recycler" in crafting_machines


def test_perform_parsing_reads_and_writes_files(
    tmp_path, monkeypatch, minimal_raw_data
):
    monkeypatch.chdir(tmp_path)

    raw_path = tmp_path / "data" / "raw"
    raw_path.mkdir(parents=True)

    metadata = {
        "factorio_version": "2.1.0",
        "source_file": "data-raw-dump.json",
        "active_mods": ["Quality", "Recycler"],
    }

    (raw_path / "metadata.json").write_text(json.dumps(metadata))
    (raw_path / "data-raw-dump.json").write_text(json.dumps(minimal_raw_data))

    raw_data_parser.perform_parsing()

    parsed_path = tmp_path / "data" / "parsed"

    assert (parsed_path / "metadata.json").exists()
    assert (parsed_path / "items.json").exists()
    assert (parsed_path / "fluids.json").exists()
    assert (parsed_path / "recipes.json").exists()
    assert (parsed_path / "crafting_machines.json").exists()

    parsed_metadata = json.loads((parsed_path / "metadata.json").read_text())

    assert parsed_metadata == metadata
