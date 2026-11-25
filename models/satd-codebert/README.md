# SATD Detection and Classification Using CodeBERT

This project fine-tunes **Microsoft CodeBERT** to detect and classify **Self-Admitted Technical Debt (SATD)** in source-code comments.

The workflow performs two related tasks:

1. **Multiclass SATD classification**
   - NON-SATD
   - Design/Code Debt
   - Requirement Debt
   - Defect Debt
   - Test Debt
   - Documentation Debt

2. **Binary SATD detection**
   - SATD
   - NO SATD

The project uses a large multiclass dataset for training and internal evaluation, then evaluates the trained model on a separate binary-labeled comments dataset.

---
## Quick Links

### Dataset

The dataset used in this project is publicly available on Kaggle:

**CodeBERT SATD Multiclass Datasets**

https://www.kaggle.com/datasets/ahmedamir7/codebert-satd-multiclass-datasets

Dataset contents:

| File | Purpose |
|--------|--------|
| `cppsatd.csv` | Multiclass SATD training, validation, and testing dataset |
| `comment.csv` | Independent binary SATD evaluation dataset |

### Trained Model

The final fine-tuned model is publicly available on Hugging Face:

**CodeBERT SATD Multiclass**

https://huggingface.co/ahmedamirahmed/codebert-satd-multiclass

The published model includes:

- Fine-tuned CodeBERT weights
- Tokenizer files
- Label mappings
- Configuration files
- Evaluation artifacts
## Project Objectives

The project was developed to address limitations found in an earlier binary SATD classifier.

The earlier model achieved high accuracy but suffered from lower SATD recall because the dataset was strongly imbalanced toward NON-SATD comments.

The updated workflow improves the experiment by:

- Using a larger multiclass SATD dataset
- Fine-tuning `microsoft/codebert-base`
- Increasing the maximum sequence length from 128 to 256 tokens
- Applying class-weighted loss
- Supporting weighted cross-entropy and weighted focal loss
- Selecting the best checkpoint using validation macro F1
- Reporting per-class precision, recall, and F1
- Deriving binary SATD predictions from the multiclass outputs
- Evaluating the final model on a separate binary SATD dataset
- Saving the trained model, reports, predictions, and errors
- Copying the complete Kaggle working directory to Google Drive

---

## Model

The project uses:

```text
microsoft/codebert-base
```

CodeBERT is based on the RoBERTa architecture and is pretrained on natural language and programming-language data.

The pretrained encoder is reused, while a new six-class classification head is learned during fine-tuning.

### Model Configuration

| Setting | Value |
|---|---:|
| Base model | `microsoft/codebert-base` |
| Maximum sequence length | 256 tokens |
| Number of output classes | 6 |
| Task type | Single-label multiclass classification |
| Learning rate | `2e-5` |
| Weight decay | `0.01` |
| Maximum epochs | 5 |
| Training batch size | 8 |
| Evaluation batch size | 16 |
| Gradient accumulation steps | 2 |
| Effective batch size | 16 |
| Warmup ratio | 10% |
| Early-stopping patience | 2 |
| Random seed | 42 |
| Main selection metric | Validation macro F1 |

Mixed precision is selected automatically:

- FP16 is used on compatible GPUs such as NVIDIA T4 and P100.
- BF16 is used when the active GPU explicitly supports it.

---

## Datasets

### 1. Multiclass Training Dataset

The primary dataset is:

```text
cppsatd.csv
```

The Kaggle notebook reads it from:

```text
/kaggle/input/datasets/ahmedamir7/cpp-satd/cppsatd.csv
```

The important columns are:

| Column | Purpose |
|---|---|
| `commenttext` | Source-code comment given to CodeBERT |
| `annotation` | Multiclass target label |
| `projectname` | Optional repository identifier |

The final configuration uses:

```python
TEXT_COLUMN = "commenttext"
LABEL_COLUMN = "annotation"
GROUP_COLUMN = None
```

The model receives only the source-code comment text as input.

### 2. External Binary Testing Dataset

The external test dataset is:

```text
comment.csv
```

The Kaggle notebook reads it from:

```text
/kaggle/input/datasets/ahmedamir7/comment-satd/comment.csv
```

The important columns are:

| Column | Purpose |
|---|---|
| `comment` | Comment passed to the trained model |
| `satd` | Ground-truth binary label used only for evaluation |
| `type` | Existing debt-type information excluded from model input |

During external testing, the `satd` and `type` columns are explicitly hidden from the model to prevent target leakage.

The trained model receives only:

```text
comment
```

The original `satd` column is preserved separately and used after prediction to calculate binary evaluation metrics.

---
## Dataset Access

### Download from Kaggle

Dataset URL:

https://www.kaggle.com/datasets/ahmedamir7/codebert-satd-multiclass-datasets

The dataset package contains:

```text
cppsatd.csv
comment.csv
```

### Using the Dataset in Kaggle

```python
DATASET_PATH = (
    "/kaggle/input/"
    "codebert-satd-multiclass-datasets"
)

CPPSATD_DATASET = (
    f"{DATASET_PATH}/cppsatd.csv"
)

COMMENT_DATASET = (
    f"{DATASET_PATH}/comment.csv"
)
```

## Target Classes

The multiclass model uses the following fixed label order:

```text
0 → NON-SATD
1 → DESIGN/CODE DEBT
2 → REQUIREMENT
3 → DEFECT
4 → TEST
5 → DOCUMENTATION
```

The fixed order is stored in the model configuration and in:

```text
label_mapping.json
```

### Label Standardization

The preprocessing pipeline standardizes alternative labels before training.

Examples include:

```text
non satd            → NON-SATD
no satd             → NON-SATD
design debt         → DESIGN/CODE DEBT
code debt           → DESIGN/CODE DEBT
requirement debt    → REQUIREMENT
defect debt         → DEFECT
bug debt            → DEFECT
test debt           → TEST
documentation debt  → DOCUMENTATION
```

The pipeline stops before training if unexpected or missing classes are detected.

---

## Data Preparation

The workflow performs the following preprocessing steps:

1. Loads the CSV file.
2. Keeps the comment, label, and optional repository columns.
3. Removes records with missing comments or labels.
4. Converts comments and labels to strings.
5. Normalizes repeated whitespace.
6. Removes empty comments.
7. Removes exact duplicate comment-label pairs.
8. Standardizes label names.
9. Validates the six expected classes.
10. Assigns deterministic integer label IDs.
11. Creates stratified training, validation, and test partitions.

### Dataset Split

The default split is:

- 70% training
- 15% validation
- 15% test

The split is stratified using the multiclass target, preserving the class distribution as closely as possible.

```python
TEST_SIZE = 0.15
VALIDATION_SIZE = 0.15
SEED = 42
```

An optional repository-aware split is also implemented. When enabled, complete repositories are placed in separate partitions to provide a stronger cross-project generalization test.

```python
USE_GROUP_SPLIT = False
```

---

## Tokenization

Comments are tokenized using the CodeBERT tokenizer.

```python
MAX_LENGTH = 256
```

The tokenizer applies:

- CodeBERT subword tokenization
- Special tokens
- Truncation at 256 tokens
- Dynamic batch padding

Dynamic padding is performed by `DataCollatorWithPadding`, so each batch is padded only to its longest sequence rather than padding the entire dataset to 256 tokens.

A token-length analysis is performed on up to 50,000 randomly sampled comments. It reports:

- Median length
- 75th percentile
- 90th percentile
- 95th percentile
- 99th percentile
- Maximum length
- Percentage longer than 128 tokens
- Percentage longer than 256 tokens

This analysis supports the decision to increase the maximum sequence length from 128 to 256.

---

## Handling Class Imbalance

The dataset contains a dominant NON-SATD class and significantly smaller SATD classes.

The workflow calculates class weights using the training partition only. Validation and test labels are not used when calculating weights.

Three weighting strategies are supported:

### Square-Root Inverse Frequency

```python
WEIGHT_STRATEGY = "sqrt"
```

This is the recommended baseline. It reduces majority-class dominance without assigning excessively large weights to very small classes.

### Balanced Inverse Frequency

```python
WEIGHT_STRATEGY = "balanced"
```

This applies full inverse-frequency correction and may improve minority recall, but it can overcorrect when some classes are extremely rare.

### Effective-Number Weighting

```python
WEIGHT_STRATEGY = "effective"
```

This uses the effective number of samples to calculate long-tail class weights.

The final weights are:

1. Normalized to have an average near 1
2. Clipped to a configurable range

```python
MIN_CLASS_WEIGHT = 0.25
MAX_CLASS_WEIGHT = 10.0
```

The calculated values are stored in:

```text
class_weights.csv
```

---

## Supported Loss Functions

The custom `ImbalanceAwareTrainer` supports two loss functions.

### Weighted Cross-Entropy

```python
LOSS_TYPE = "weighted_ce"
```

This is the recommended first experiment and the configured loss in the final workflow.

### Weighted Focal Loss

```python
LOSS_TYPE = "weighted_focal"
FOCAL_GAMMA = 2.0
```

Focal loss reduces the contribution of easy examples and focuses training on harder or misclassified samples.

---

## Recommended Experiments

For a fair comparison, keep the data split, seed, model, sequence length, learning rate, batch size, and number of epochs unchanged.

Change only the class-weight strategy and loss function.

| Experiment | Weight strategy | Loss |
|---|---|---|
| A | `sqrt` | `weighted_ce` |
| B | `balanced` | `weighted_ce` |
| C | `sqrt` | `weighted_focal` |

The recommended starting experiment is:

```python
WEIGHT_STRATEGY = "sqrt"
LOSS_TYPE = "weighted_ce"
```

Compare the experiments using validation macro F1 and minority-class recall rather than overall accuracy.

Each experiment must start from a fresh copy of `microsoft/codebert-base`. A model already fine-tuned in a previous experiment must not be reused as the starting point for another loss comparison.

---

## Training

The model is trained using the Hugging Face `Trainer` API through a custom imbalance-aware trainer.

The training workflow includes:

- Class-weighted loss
- Gradient accumulation
- Mixed-precision training
- Periodic validation
- Periodic checkpoint saving
- Early stopping
- Best-checkpoint restoration
- Macro F1 model selection
- Automatic compatibility handling for different Transformers versions

Warmup steps are calculated manually from:

```text
number of training examples
training batch size
gradient accumulation steps
number of epochs
warmup ratio
```

This avoids compatibility problems with Transformers versions that do not accept `warmup_ratio` directly.

### Training Output Directory

All generated files are written under:

```text
/kaggle/working/codebert_cppsatd_multiclass
```

The final model and tokenizer are saved with:

```python
trainer.save_model(OUTPUT_DIR)
tokenizer.save_pretrained(OUTPUT_DIR)
```

---

## Multiclass Evaluation

The internal test set is evaluated as a six-class classification task.

The workflow reports:

- Accuracy
- Balanced accuracy
- Macro precision
- Macro recall
- Macro F1
- Weighted precision
- Weighted recall
- Weighted F1
- Per-class precision
- Per-class recall
- Per-class F1
- Raw confusion matrix
- Row-normalized confusion matrix

### Why Macro F1 Is the Main Metric

Overall accuracy can be dominated by the large NON-SATD class.

Macro F1 calculates the F1 score independently for every class and gives all classes equal importance. It is therefore more suitable for selecting a model on this imbalanced multiclass problem.

---

## Derived Binary Evaluation

The six-class predictions are converted into a binary SATD decision.

```text
NON-SATD      → NO SATD
Any debt type → SATD
```

The resulting binary evaluation reports:

- NO SATD precision, recall, and F1
- SATD precision, recall, and F1
- Accuracy
- Balanced accuracy
- Binary confusion matrix
- SATD PR-AUC

This makes it possible to compare the new multiclass model with the earlier binary SATD classifier.

---

## External Evaluation on `comment.csv`

The trained multiclass model is applied to the independent `comment.csv` dataset.

### Leakage Prevention

The following columns are removed from model input:

```text
satd
type
```

Only the `comment` column is tokenized and passed to CodeBERT.

The hidden `satd` label is restored only after inference for binary evaluation.

### Batch Inference

Predictions are generated in GPU batches:

```python
INFERENCE_BATCH_SIZE = 32
```

If GPU memory is insufficient, the value can be reduced to 16 or 8.

### External Prediction Outputs

For each valid comment, the workflow generates:

- `predicted_satd`
- `predicted_satd_type`
- `prediction_confidence`
- `satd_probability`
- `non_satd_probability`
- One probability column for each multiclass category
- Normalized actual binary SATD label
- Whether the prediction was correct
- Error type for incorrect predictions

The binary result is generated using:

```text
Predicted NON-SATD → no
Predicted debt type → yes
```

---

## Error Analysis

The workflow saves and analyzes incorrectly classified examples.

### Multiclass Error Analysis

The internal test output includes:

- Original comment
- True class
- Predicted class
- Confidence
- Probability for every class
- Correct/incorrect indicator

The most frequent true-class and predicted-class confusion pairs are also calculated.

### Binary Error Analysis

Binary errors are divided into:

```text
False Negative: missed SATD
False Positive: predicted SATD
```

False negatives are especially important because they represent technical-debt comments missed by the model.

---

## Saved Files

The model directory can contain:

```text
codebert_cppsatd_multiclass/
├── config.json
├── model.safetensors
├── tokenizer.json
├── tokenizer_config.json
├── special_tokens_map.json
├── vocab.json
├── merges.txt
├── label_mapping.json
├── class_weights.csv
├── train_results.json
├── validation_results.json
├── test_results.json
├── trainer_state.json
├── test_classification_report.txt
├── test_classification_report.csv
├── test_predictions.csv
├── test_misclassifications.csv
├── binary_satd_classification_report.txt
├── satd_binary_predictions.csv
└── satd_binary_errors.csv
```

Depending on the active Transformers version, model weights may be saved as:

```text
model.safetensors
```

or:

```text
pytorch_model.bin
```

---

## Google Drive Backup

The final workflow connects Kaggle to Google Drive using PyDrive2.

Google Drive is not mounted as a Kaggle filesystem. Instead, the workflow uses the Google Drive API to recreate the local directory structure and upload each file.

The complete source folder is:

```text
/kaggle/working
```

The corresponding Google Drive destination is:

```text
My Drive/SATD_Project/working
```

The recursive backup cell:

- Recreates all local subfolders in Google Drive
- Uploads new files
- Updates existing files with the same name
- Preserves the relative folder structure
- Retries temporary upload failures
- Excludes OAuth credential files

The excluded security-sensitive files are:

```text
client_secrets.json
google_drive_credentials.json
```

These files contain reusable authorization information and must never be uploaded with model artifacts.

### Backup Behavior

The backup operation performs copy/update synchronization:

- New local files are uploaded
- Modified local files are updated
- Existing Drive folders are reused
- Files deleted locally are not automatically deleted from Drive

Run the recursive backup cell again after training and evaluation have completed.

Do not close the Kaggle session until the backup reports:

```text
KAGGLE WORKING FOLDER COPY FINISHED
Failed uploads: 0
```

---

## Model Archive

The workflow creates a ZIP archive of the final model directory:

```text
/kaggle/working/codebert_cppsatd_multiclass.zip
```

The archive can be downloaded from Kaggle Output or copied to Google Drive through the recursive backup process.

Checkpoint folders can make the complete output several gigabytes. For inference-only distribution, a smaller archive should contain:

- Model weights
- `config.json`
- Tokenizer files
- Label mapping
- Class weights
- Evaluation reports
- Prediction outputs

Optimizer and scheduler states are needed only when resuming interrupted training.

---

## Loading the Saved Model

```python
import torch

from transformers import (
    AutoModelForSequenceClassification,
    AutoTokenizer,
)

MODEL_PATH = (
    "/kaggle/working/"
    "codebert_cppsatd_multiclass"
)

device = torch.device(
    "cuda" if torch.cuda.is_available() else "cpu"
)

tokenizer = AutoTokenizer.from_pretrained(
    MODEL_PATH
)

model = (
    AutoModelForSequenceClassification
    .from_pretrained(MODEL_PATH)
    .to(device)
)

model.eval()

print("Model loaded successfully.")
print("Device:", device)
print("Labels:", model.config.id2label)
```

---
## Using the Published Hugging Face Model

The final model is available at:

https://huggingface.co/ahmedamirahmed/codebert-satd-multiclass

### Install Dependencies

```bash
pip install transformers torch safetensors
```

### Load the Published Model

```python
from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
)

MODEL_ID = (
    "ahmedamirahmed/"
    "codebert-satd-multiclass"
)

tokenizer = AutoTokenizer.from_pretrained(
    MODEL_ID
)

model = (
    AutoModelForSequenceClassification
    .from_pretrained(MODEL_ID)
)

print(model.config.id2label)
```

## Predicting One Comment

```python
import torch


def predict_satd_type(comment):
    comment = str(comment).strip()

    if not comment:
        raise ValueError(
            "The comment cannot be empty."
        )

    encoded_comment = tokenizer(
        comment,
        return_tensors="pt",
        truncation=True,
        max_length=256,
        padding=True,
    )

    encoded_comment = {
        key: value.to(device)
        for key, value in encoded_comment.items()
    }

    with torch.no_grad():
        logits = model(
            **encoded_comment
        ).logits

        probabilities = torch.softmax(
            logits,
            dim=-1,
        )[0]

    predicted_id = int(
        probabilities.argmax().item()
    )

    predicted_label = (
        model.config.id2label[
            predicted_id
        ]
    )

    all_probabilities = {
        model.config.id2label[class_id]:
        float(probability.item())

        for class_id, probability
        in enumerate(probabilities)
    }

    non_satd_probability = (
        all_probabilities.get(
            "NON-SATD",
            0.0,
        )
    )

    return {
        "predicted_label": predicted_label,
        "confidence": float(
            probabilities[predicted_id].item()
        ),
        "binary_satd": (
            "no"
            if predicted_label == "NON-SATD"
            else "yes"
        ),
        "satd_probability": float(
            1.0 - non_satd_probability
        ),
        "all_probabilities": (
            all_probabilities
        ),
    }
```

Example:

```python
example_comment = """
TODO: This workaround should be removed when the parser
supports nested template arguments correctly.
"""

print(
    predict_satd_type(
        example_comment
    )
)
```

---
## Binary SATD Mapping

The model predicts one of six classes:

| ID | Label |
|----|--------|
| 0 | NON-SATD |
| 1 | DESIGN/CODE DEBT |
| 2 | REQUIREMENT |
| 3 | DEFECT |
| 4 | TEST |
| 5 | DOCUMENTATION |

For binary SATD detection:

```text
NON-SATD      → NO SATD
Any debt type → SATD
```

## Installation

Kaggle already includes NumPy, pandas, scikit-learn, Matplotlib, Seaborn, and PyTorch.

Install only the required Hugging Face packages:

```bash
pip install transformers datasets accelerate
```

For Google Drive backup:

```bash
pip install PyDrive2
```

Avoid unnecessarily upgrading Kaggle’s core NumPy, pandas, Matplotlib, and scikit-learn packages because this can create dependency conflicts with the preconfigured Kaggle environment.

---

## Recommended Hardware

A Kaggle GPU accelerator is strongly recommended.

Suitable configurations include:

- NVIDIA T4
- NVIDIA P100
- Newer GPUs with BF16 support

For approximately 16 GB of GPU memory, begin with:

```python
TRAIN_BATCH_SIZE = 8
EVAL_BATCH_SIZE = 16
GRADIENT_ACCUMULATION_STEPS = 2
```

If CUDA runs out of memory:

```python
TRAIN_BATCH_SIZE = 4
EVAL_BATCH_SIZE = 8
GRADIENT_ACCUMULATION_STEPS = 4
USE_GRADIENT_CHECKPOINTING = True
```

This preserves an effective batch size of 16 while reducing peak GPU-memory usage.

---

## Reproducibility

The workflow fixes the random seed across:

- Python
- NumPy
- PyTorch
- CUDA
- Hugging Face Transformers
- Dataset splitting

```python
SEED = 42
```

For a fair comparison between experiments:

- Reuse the same train, validation, and test split
- Keep the seed unchanged
- Keep sequence length unchanged
- Keep learning rate and batch configuration unchanged
- Start from a fresh pretrained CodeBERT model
- Change only the class-weight or loss configuration being tested

---

## Important Limitations

1. **Class imbalance remains a central challenge.**  
   Weighted loss reduces the effect of imbalance but does not create new information for rare classes.

2. **Very rare SATD categories may remain difficult to classify.**  
   Per-class recall and F1 should always be inspected.

3. **Sequence truncation can remove useful information.**  
   Comments longer than 256 tokens are truncated.

4. **Random splitting may overestimate cross-project generalization.**  
   Repository-aware or leave-one-project-out evaluation provides a stronger test.

5. **Binary labels cannot fully validate SATD subtypes.**  
   The external `comment.csv` dataset can verify SATD versus NO SATD, but subtype evaluation requires trusted multiclass labels.

6. **High-confidence predictions are not automatically correct.**  
   Model-generated SATD subtypes should be manually reviewed before being reused as training labels.

7. **Google Drive backup is not deletion synchronization.**  
   Files removed from `/kaggle/working` remain in Drive unless deleted separately.

---

## Future Improvements

Potential next steps include:

- Leave-one-repository-out cross-validation
- Hierarchical classification:
  1. SATD versus NON-SATD
  2. SATD subtype classification
- Manual annotation of high-value external comments
- Active learning based on low-confidence and disagreement examples
- Controlled pseudo-labeling with manually verified SATD subtypes
- Confidence calibration
- Threshold optimization using the validation set
- Comparison with GraphCodeBERT and UniXcoder
- Inclusion of preceding and succeeding code context
- Hyperparameter optimization for focal-loss gamma
- Experiment tracking using MLflow or Weights & Biases
- Refactoring the notebook into reusable Python modules
- Automated unit and integration tests

---

## Project Structure

```text
models/
└── satd-codebert/
    ├── README.md
    │
    ├── notebooks/
    │   ├── satd-v2-multi-class-codebert-256-final.ipynb
    │   └── test_model.py
    │
    ├── outputs/
    │   └── .gitkeep
    │
    ├── results/
    │   ├── all_results.json
    │   ├── binary_satd_classification_report.txt
    │   ├── class_weights.csv
    │   ├── config.json
    │   ├── label_mapping.json
    │   ├── test_classification_report.txt
    │   ├── test_results.json
    │   ├── tokenizer.json
    │   ├── tokenizer_config.json
    │   ├── train_results.json
    │   ├── trainer_state.json
    │   └── validation_results.json
    │
    └── docs/
```

Datasets are hosted on Kaggle:

https://www.kaggle.com/datasets/ahmedamir7/codebert-satd-multiclass-datasets

The trained model is hosted on Hugging Face:

https://huggingface.co/ahmedamirahmed/codebert-satd-multiclass

## End-to-End Workflow

```text
cppsatd.csv
    ↓
Cleaning and label standardization
    ↓
Stratified train/validation/test split
    ↓
Training-set class-weight calculation
    ↓
CodeBERT tokenization at 256 tokens
    ↓
Multiclass CodeBERT fine-tuning
    ↓
Best checkpoint selected using validation macro F1
    ↓
Six-class internal test evaluation
    ↓
Derived binary SATD evaluation
    ↓
Load independent comment.csv
    ↓
Hide satd and type columns from the model
    ↓
Batch inference using comment text only
    ↓
Binary and multiclass prediction outputs
    ↓
Error analysis and report generation
    ↓
Save all artifacts under /kaggle/working
    ↓
Recursively copy /kaggle/working to Google Drive
```
## Reproducing the Experiments

1. Download the dataset from Kaggle.
2. Open the training notebook.
3. Configure the dataset paths.
4. Train or fine-tune CodeBERT.
5. Evaluate the multiclass test set.
6. Evaluate the external `comment.csv` dataset.
7. Save the final model.
8. Compare the results against the published Hugging Face model.

### Resources

**Dataset**

https://www.kaggle.com/datasets/ahmedamir7/codebert-satd-multiclass-datasets

**Model**

https://huggingface.co/ahmedamirahmed/codebert-satd-multiclass

## Acknowledgments

This project uses:

- Microsoft CodeBERT
- Hugging Face Transformers
- Hugging Face Datasets
- PyTorch
- scikit-learn
- pandas
- NumPy
- Matplotlib
- Seaborn
- Kaggle Notebooks
- PyDrive2
- Google Drive API

