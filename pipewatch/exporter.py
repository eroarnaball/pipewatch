"""Export pipeline run reports to various output formats."""

from __future__ import annotations

import csv
import io
import json
from pathlib import Path
from typing import Union

from pipewatch.reporter import RunReport


def export_json(report: RunReport, path: Union[str, Path]) -> None:
    """Write a RunReport to a JSON file."""
    path = Path(path)
    data = report.to_dict()
    path.write_text(json.dumps(data, indent=2, default=str))


def export_csv(report: RunReport, path: Union[str, Path]) -> None:
    """Write a RunReport's evaluations to a CSV file."""
    path = Path(path)
    buf = io.StringIO()
    fieldnames = ["metric", "value", "status", "timestamp"]
    writer = csv.DictWriter(buf, fieldnames=fieldnames)
    writer.writeheader()
    for ev in report.evaluations:
        writer.writerow({
            "metric": ev.metric.name,
            "value": ev.metric.value,
            "status": ev.status.value,
            "timestamp": ev.metric.timestamp,
        })
    path.write_text(buf.getvalue())


def export_report(report: RunReport, path: Union[str, Path], fmt: str = "json") -> None:
    """Dispatch export to the correct format handler."""
    fmt = fmt.lower()
    if fmt == "json":
        export_json(report, path)
    elif fmt == "csv":
        export_csv(report, path)
    else:
        raise ValueError(f"Unsupported export format: {fmt!r}. Choose 'json' or 'csv'.")
