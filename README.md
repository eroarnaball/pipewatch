# pipewatch

A lightweight CLI for monitoring and alerting on data pipeline health metrics.

---

## Installation

```bash
pip install pipewatch
```

Or install from source:

```bash
git clone https://github.com/yourname/pipewatch.git && cd pipewatch && pip install -e .
```

---

## Usage

Monitor a pipeline by pointing pipewatch at your metrics endpoint or log source:

```bash
pipewatch monitor --source my_pipeline --interval 30
```

Set alert thresholds and get notified when metrics fall outside expected ranges:

```bash
pipewatch watch \
  --source my_pipeline \
  --metric row_count \
  --min 1000 \
  --alert-email ops@example.com
```

Check the status of all monitored pipelines at a glance:

```bash
pipewatch status
```

Run `pipewatch --help` to see all available commands and options.

---

## Configuration

pipewatch looks for a config file at `~/.pipewatch/config.yaml`. You can specify a custom path with the `--config` flag.

```yaml
pipelines:
  - name: my_pipeline
    source: postgresql://localhost/mydb
    schedule: "*/15 * * * *"
    alerts:
      slack_webhook: https://hooks.slack.com/...
```

---

## License

This project is licensed under the [MIT License](LICENSE).