$ErrorActionPreference = "Stop"
$env:PYTHONPATH = "E:\code visualize\codeviz-local"
python -m apps.cli.main --config "E:\code visualize\codeviz-local\configs\default.yaml"
