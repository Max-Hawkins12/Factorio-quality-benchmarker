# Raw Data Files
This directory is intended to hold the `data-raw-dump.json` directly from Factorio. It is intentionally excluded from the repo due to being over one million lines long.

Parsed data for Factorio version 2.1.14 is provided in the `data/parsed` directory, so the quality benchmark can be used as intended. However, if you wish to parse your own game data, follow the instructions below.


## Parsing Your Own Factorio Data

### Prerequisites

- [uv](https://docs.astral.sh/uv/)
- [Factorio with the Space Age DLC](https://store.steampowered.com/app/427520/Factorio/)

### Generating the Data
**Note:** In Factorio 2.0, the Quality mod must be enabled. In Factorio 2.1+, both the Quality and Recycler mods must be enabled. Using the Space Age mod is also recommended for the most complete results. 
This program has not been tested with any non-official mods. So modded data may break the parser or not be supported by the benchmarker.

1. Navigate to factorio.exe
	- For the Steam version: right-click on Factorio in your library → Properties → Installed Files → Browse... 
	- The executable is located at `Factorio/bin/x64/factorio.exe`
2. Run:
`factorio.exe --dump-data` 
3. Locate the generated `data-raw-dump.json`
	- On Windows, the default location is:  
`C:\Users\<username>\AppData\Roaming\Factorio\script-output\data-raw-dump.json`
	- On Linux/MacOS, check the `Write data path:` shown in the command output to determine the data dump location.

### Running the Parser

1. Copy `data-raw-dump.json` into `data/raw/`
2. Create `data/raw/metadata.json` using [`metadata.json.example`](./metadata.json.example) as a template.
3.  From the project root, run:  
    `uv run factorio-quality-benchmarker parse`