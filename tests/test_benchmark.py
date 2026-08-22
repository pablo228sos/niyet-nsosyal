from pathlib import Path

import pytest

from niyet.benchmark import load_benchmark
from niyet.types import IntentType


DATA = Path(__file__).parents[1] / "data" / "toy_benchmark.json"


def test_loads_benchmark():
    benchmark = load_benchmark(DATA)

    assert len(benchmark.intents) == 5
    assert len(benchmark.responders) == 4
    assert len(benchmark.matches) == 13
    assert benchmark.intents[0].kind is IntentType.ASK


def test_rejects_invalid_gold_relevance(tmp_path):
    source = DATA.read_text(encoding="utf-8").replace(
        '"gold_relevance": 3', '"gold_relevance": 4', 1
    )
    path = tmp_path / "invalid.json"
    path.write_text(source, encoding="utf-8")

    with pytest.raises(ValueError):
        load_benchmark(path)
