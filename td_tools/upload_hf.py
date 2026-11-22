#!/usr/bin/env python3
"""
upload_hf.py - publish the combined data mart (~/td-mart) as a Hugging Face dataset.

One-time setup:
    pip install huggingface_hub
    export HF_TOKEN=hf_xxx        # a WRITE token from https://huggingface.co/settings/tokens

Check first (builds the upload folder, uploads nothing):
    python upload_hf.py --mart ~/td-mart --repo-id <your-hf-name>/td-forecasting-mart --dry-run

Upload (PRIVATE by default - only you can see it; add --public when the doctor agrees):
    python upload_hf.py --mart ~/td-mart --repo-id <your-hf-name>/td-forecasting-mart

What is uploaded:
    mart_project / mart_module / mart_file / mart_all_levels  .parquet  (the data)
    data_dictionary.csv, manifest.json, validation_report.txt, diagnostics/  (documentation)
    README.md = the mart's README with a Hugging Face header (license, tags, one viewer
                tab per level)
The CSV copies are left out (same data as the Parquet files); add --with-csv to include them.
Running it again updates the same dataset (a new commit; old versions stay in its history).
"""
import argparse, os, shutil, sys, tempfile

LEVELS = ("project", "module", "file")

HEADER = """---
license: {license}
pretty_name: Technical Debt Forecasting Data Mart
language:
- en
tags:
- software-engineering
- technical-debt
- sonarqube
- code-metrics
- time-series
size_categories:
- 100K<n<1M
configs:
- config_name: project
  data_files: mart_project.parquet
  default: true
- config_name: module
  data_files: mart_module.parquet
- config_name: file
  data_files: mart_file.parquet
---

> Weekly snapshots of open-source Java projects measured with SonarQube, CKJM Extended, Halstead,
> Java Driller and git, at project, module and file level, for technical-debt forecasting.
> Method follows Tsoukalas et al. (2020), *Technical debt forecasting: An empirical study on
> open-source repositories*, Journal of Systems and Software 170:110777,
> https://doi.org/10.1016/j.jss.2020.110777. Values are measured from each project's own git
> history; the paper's published data is used only as a benchmark.
>
> Load one level: `datasets.load_dataset("{repo_id}", "file")`, or
> `pandas.read_parquet("hf://datasets/{repo_id}/mart_file.parquet")`.

"""


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--mart", default="~/td-mart", help="folder written by build_mart.py")
    ap.add_argument("--repo-id", required=True, help="<hf user or org>/<dataset name>")
    ap.add_argument("--public", action="store_true", help="make the dataset public (default: private)")
    ap.add_argument("--license", default="cc-by-4.0",
                    help="dataset license shown on Hugging Face (default cc-by-4.0)")
    ap.add_argument("--with-csv", action="store_true", help="also upload the CSV copies")
    ap.add_argument("--dry-run", action="store_true", help="build the upload folder and stop")
    a = ap.parse_args()
    mart = os.path.expanduser(a.mart)

    # 1. the mart must be complete
    need = [f"mart_{l}.parquet" for l in LEVELS] + ["README.md", "data_dictionary.csv"]
    missing = [n for n in need if not os.path.exists(os.path.join(mart, n))]
    if missing:
        sys.exit(f"missing in {mart}: {missing}\n"
                 "-> pip install pyarrow, then: python run_repos.py repos.csv --mart-only")

    # 2. upload folder: data + docs + README with the Hugging Face header
    stage = tempfile.mkdtemp(prefix="hf_mart_")
    skip_ext = () if a.with_csv else (".csv",)
    keep_csv = {"data_dictionary.csv"}
    for root, dirs, files in os.walk(mart):
        rel = os.path.relpath(root, mart)
        for fn in files:
            if fn == "README.md" and rel == ".":
                continue
            if fn.endswith(".zip"):
                continue
            if fn.endswith(skip_ext) and fn not in keep_csv and rel == ".":
                continue
            dst = os.path.join(stage, rel, fn)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(os.path.join(root, fn), dst)
    with open(os.path.join(mart, "README.md")) as f:
        body = f.read()
    with open(os.path.join(stage, "README.md"), "w") as f:
        f.write(HEADER.format(license=a.license, repo_id=a.repo_id) + body)

    total = 0
    print("will upload:")
    for root, _, files in os.walk(stage):
        for fn in sorted(files):
            p = os.path.join(root, fn)
            total += os.path.getsize(p)
            if os.path.dirname(os.path.relpath(p, stage)) == "":
                print(f"  {os.path.relpath(p, stage):32s} {os.path.getsize(p) / 1e6:8.1f} MB")
    n_diag = sum(len(f) for _, _, f in os.walk(os.path.join(stage, "diagnostics")))
    print(f"  diagnostics/ ({n_diag} files)\n  total {total / 1e6:.1f} MB -> "
          f"{'PUBLIC' if a.public else 'PRIVATE'} dataset {a.repo_id}")
    if a.dry_run:
        print(f"dry run: nothing uploaded. Folder to inspect: {stage}")
        return

    # 3. upload
    token = os.environ.get("HF_TOKEN")
    if not token:
        sys.exit("set HF_TOKEN first: export HF_TOKEN=hf_...  (a WRITE token)")
    try:
        from huggingface_hub import HfApi
    except ImportError:
        sys.exit("pip install huggingface_hub")
    api = HfApi(token=token)
    api.create_repo(a.repo_id, repo_type="dataset", private=not a.public, exist_ok=True)
    api.upload_folder(folder_path=stage, repo_id=a.repo_id, repo_type="dataset",
                      commit_message="Update TD data mart")
    shutil.rmtree(stage, ignore_errors=True)
    print(f"done: https://huggingface.co/datasets/{a.repo_id}")


if __name__ == "__main__":
    main()
