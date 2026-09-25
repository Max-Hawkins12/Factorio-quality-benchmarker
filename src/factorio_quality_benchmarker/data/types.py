from typing import Any

type Prototype = dict[str, Any]
type PrototypeCollection = dict[str, Prototype]
type ParsedGameData = dict[str, PrototypeCollection]
