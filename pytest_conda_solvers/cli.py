from pathlib import Path

import msgspec
import typer

from .models import TestModule


app = typer.Typer(help="CLI tool for pytest-conda-solvers")


@app.command()
def generate_schemas(output: Path | None = None, compact: bool = False):
    schema = msgspec.json.schema(TestModule)
    compact_representation = msgspec.json.encode(schema).decode("utf-8")
    representation = (
        compact_representation
        if compact
        else msgspec.json.format(compact_representation)
    )
    if output is None:
        print(representation)
    else:
        output.write_text(representation)


if __name__ == "__main__":
    app()
