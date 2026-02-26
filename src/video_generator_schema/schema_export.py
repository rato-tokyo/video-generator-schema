import json
from pathlib import Path

from .models.meta import Meta
from .models.mouth import MouthData
from .models.review import Review


def export_json_schemas(
    output_dir: str | Path | None = None,
) -> dict[str, dict]:
    """Export JSON Schemas for all input models.

    Returns a dict mapping model name to its JSON Schema dict.
    If *output_dir* is provided, also writes individual ``.schema.json`` files.
    """
    schemas: dict[str, dict] = {
        "Meta": Meta.model_json_schema(),
        "Review": Review.model_json_schema(),
        "MouthData": MouthData.model_json_schema(),
    }

    if output_dir is not None:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        for name, schema in schemas.items():
            path = output_dir / f"{name}.schema.json"
            path.write_text(
                json.dumps(schema, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )

    return schemas
