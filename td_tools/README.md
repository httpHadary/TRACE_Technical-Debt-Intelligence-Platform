# td_tools – TD data collection pipeline

Rebuilds the dataset of Tsoukalas et al. (2020), "Technical debt forecasting:
An empirical study on open-source repositories", at project, module and file
level (SonarQube + CKJM + Halstead + git history + Java Driller), and packs the
results into data marts for the forecasting work.

- Setup and running: [RUN_GUIDE.md](RUN_GUIDE.md)
- Differences from the root pipeline: [PIPELINE_COMPARISON.md](PIPELINE_COMPARISON.md)
- SonarQube server: `docker/docker-compose.yml`

Quick start (run from this folder):
    python3 -m venv .venv && source .venv/bin/activate
    pip install -r requirements.txt
    python run_repos.py repos.csv --dry-run
