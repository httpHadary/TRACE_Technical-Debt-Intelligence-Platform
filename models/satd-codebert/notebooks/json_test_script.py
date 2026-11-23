"""
Test the local multiclass CodeBERT SATD model.

The script returns one JSON object per comment using the planned
TRACE SATD detection schema.

Examples
--------
Run the built-in example:

    python test_model.py

Test one comment:

    python test_model.py \
        --comment "TODO: Remove this dependency cycle"

Include repository metadata:

    python test_model.py \
        --comment "TODO: Remove this dependency cycle" \
        --repository-id "shop-backend" \
        --commit-sha "full-git-commit-sha" \
        --file-path "src/orders/OrderService.java" \
        --language "Java" \
        --line-start 142 \
        --line-end 143

Use a different local model:

    python test_model.py \
        --model-path "D:\\path\\to\\model"
"""

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Optional

import torch
from transformers import (
    AutoModelForSequenceClassification,
    AutoTokenizer,
)


# test_model.py is located in:
# models/satd-codebert/notebooks/
#
# The model is located in:
# models/satd-codebert/outputs/codebert_cppsatd_multiclass/
PROJECT_DIRECTORY = Path(__file__).resolve().parent.parent

DEFAULT_MODEL_PATH = (
    PROJECT_DIRECTORY
    / "outputs"
    / "codebert_cppsatd_multiclass"
)

DEFAULT_MAX_LENGTH = 256

DEFAULT_COMMENT = (
    "TODO: Remove this dependency cycle"
)


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Test the local multiclass CodeBERT SATD model "
            "and output a TRACE-compatible JSON object."
        )
    )

    parser.add_argument(
        "--model-path",
        type=Path,
        default=DEFAULT_MODEL_PATH,
        help=(
            "Path to the local Hugging Face model directory. "
            f"Default: {DEFAULT_MODEL_PATH}"
        ),
    )

    parser.add_argument(
        "--comment",
        type=str,
        default=DEFAULT_COMMENT,
        help="Source-code comment to classify.",
    )

    parser.add_argument(
        "--satd-id",
        type=str,
        default=None,
        help=(
            "Existing SATD record ID. If omitted, a stable test ID "
            "is generated from the comment and available metadata."
        ),
    )

    parser.add_argument(
        "--repository-id",
        type=str,
        default=None,
        help="Repository identifier supplied by the future scanner.",
    )

    parser.add_argument(
        "--commit-sha",
        type=str,
        default=None,
        help="Full Git commit SHA supplied by the future scanner.",
    )

    parser.add_argument(
        "--file-path",
        type=str,
        default=None,
        help="Source file path supplied by the future scanner.",
    )

    parser.add_argument(
        "--language",
        type=str,
        default=None,
        help="Programming language supplied by the future scanner.",
    )

    parser.add_argument(
        "--line-start",
        type=int,
        default=None,
        help="First source line occupied by the comment.",
    )

    parser.add_argument(
        "--line-end",
        type=int,
        default=None,
        help="Last source line occupied by the comment.",
    )

    parser.add_argument(
        "--max-length",
        type=int,
        default=DEFAULT_MAX_LENGTH,
        help=(
            "Maximum CodeBERT sequence length. "
            f"Default: {DEFAULT_MAX_LENGTH}"
        ),
    )

    parser.add_argument(
        "--remediation-minutes",
        type=int,
        default=None,
        help=(
            "Optional reviewed remediation estimate. "
            "The model does not generate this field."
        ),
    )

    return parser.parse_args()


def validate_model_directory(
    model_path: Path,
) -> None:
    """Verify that the folder contains a loadable local model."""

    if not model_path.exists():
        raise FileNotFoundError(
            "Model directory was not found:\n"
            f"{model_path.resolve()}\n\n"
            "Expected default location:\n"
            f"{DEFAULT_MODEL_PATH.resolve()}"
        )

    if not model_path.is_dir():
        raise NotADirectoryError(
            "The model path is not a directory:\n"
            f"{model_path.resolve()}"
        )

    required_files = [
        "config.json",
        "tokenizer_config.json",
    ]

    missing_files = [
        filename
        for filename in required_files
        if not (model_path / filename).exists()
    ]

    has_model_weights = any(
        (model_path / filename).exists()
        for filename in (
            "model.safetensors",
            "pytorch_model.bin",
        )
    )

    if missing_files:
        raise FileNotFoundError(
            "The model directory is missing:\n"
            + "\n".join(
                f"- {filename}"
                for filename in missing_files
            )
        )

    if not has_model_weights:
        raise FileNotFoundError(
            "No model weights were found. Expected one of:\n"
            "- model.safetensors\n"
            "- pytorch_model.bin"
        )


def normalize_label(label: str) -> str:
    """Normalize a configured model label for reliable comparison."""

    return (
        str(label)
        .strip()
        .upper()
        .replace("_", " ")
        .replace("-", " ")
    )


def find_non_satd_id(
    id2label: dict[int, str],
) -> int:
    """Find the output ID corresponding to NON-SATD."""

    accepted_names = {
        "NON SATD",
        "NONSATD",
        "NO SATD",
    }

    matches = [
        class_id
        for class_id, label in id2label.items()
        if normalize_label(label) in accepted_names
    ]

    if len(matches) != 1:
        raise ValueError(
            "Expected exactly one NON-SATD class, but found "
            f"{len(matches)}.\n"
            f"Model mapping: {id2label}"
        )

    return matches[0]


def map_category(model_label: str) -> Optional[str]:
    """
    Convert the model's multiclass label into the public API category.

    NON-SATD has no SATD category, so it returns None.
    """

    normalized = normalize_label(model_label)

    category_mapping = {
        "DESIGN/CODE DEBT": "DESIGN",
        "DESIGN CODE DEBT": "DESIGN",
        "DESIGN/CODE": "DESIGN",
        "DESIGN CODE": "DESIGN",
        "CODE DEBT": "DESIGN",
        "DESIGN DEBT": "DESIGN",

        "REQUIREMENT DEBT": "REQUIREMENT",
        "REQUIREMENT": "REQUIREMENT",

        "DEFECT DEBT": "DEFECT",
        "DEFECT": "DEFECT",
        "BUG DEBT": "DEFECT",

        "TEST DEBT": "TEST",
        "TEST": "TEST",
        "TESTING DEBT": "TEST",

        "DOCUMENTATION DEBT": "DOCUMENTATION",
        "DOCUMENTATION": "DOCUMENTATION",
        "DOCUMENT DEBT": "DOCUMENTATION",
    }

    return category_mapping.get(normalized)


def create_satd_id(
    comment: str,
    repository_id: Optional[str],
    commit_sha: Optional[str],
    file_path: Optional[str],
    line_start: Optional[int],
) -> str:
    """
    Generate a stable temporary SATD identifier.

    This is suitable for testing. In the final system, the persistence
    layer may replace it with a database-generated identifier.
    """

    identity_parts = [
        repository_id or "",
        commit_sha or "",
        file_path or "",
        str(line_start) if line_start is not None else "",
        comment,
    ]

    identity_text = "|".join(identity_parts)

    short_hash = hashlib.sha256(
        identity_text.encode("utf-8")
    ).hexdigest()[:12]

    return f"satd-{short_hash}"


class SATDPredictor:
    """Load the local model once and classify source-code comments."""

    def __init__(
        self,
        model_path: Path,
        max_length: int = 256,
    ) -> None:
        validate_model_directory(model_path)

        self.model_path = model_path.resolve()
        self.max_length = max_length

        self.device = torch.device(
            "cuda"
            if torch.cuda.is_available()
            else "cpu"
        )

        self.tokenizer = AutoTokenizer.from_pretrained(
            str(self.model_path),
            local_files_only=True,
        )

        self.model = (
            AutoModelForSequenceClassification
            .from_pretrained(
                str(self.model_path),
                local_files_only=True,
            )
            .to(self.device)
        )

        self.model.eval()

        self.id2label = {
            int(class_id): str(label)
            for class_id, label
            in self.model.config.id2label.items()
        }

        self.non_satd_id = find_non_satd_id(
            self.id2label
        )

    def classify(
        self,
        comment: str,
    ) -> dict[str, Any]:
        """Return raw model classification information."""

        comment = str(comment).strip()

        if not comment:
            raise ValueError(
                "The comment cannot be empty."
            )

        encoded_comment = self.tokenizer(
            comment,
            return_tensors="pt",
            truncation=True,
            max_length=self.max_length,
            padding=True,
        )

        encoded_comment = {
            key: value.to(self.device)
            for key, value in encoded_comment.items()
        }

        with torch.inference_mode():
            logits = self.model(
                **encoded_comment
            ).logits

            probabilities = torch.softmax(
                logits,
                dim=-1,
            )[0]

        predicted_id = int(
            probabilities.argmax().item()
        )

        predicted_model_label = self.id2label[
            predicted_id
        ]

        predicted_score = float(
            probabilities[predicted_id].item()
        )

        is_satd = (
            predicted_id != self.non_satd_id
        )

        return {
            "predicted_id": predicted_id,
            "model_label": predicted_model_label,
            "is_satd": is_satd,
            "category": (
                map_category(predicted_model_label)
                if is_satd
                else None
            ),
            "score": predicted_score,
        }


def build_output_record(
    predictor: SATDPredictor,
    comment: str,
    satd_id: Optional[str] = None,
    repository_id: Optional[str] = None,
    commit_sha: Optional[str] = None,
    file_path: Optional[str] = None,
    language: Optional[str] = None,
    line_start: Optional[int] = None,
    line_end: Optional[int] = None,
    remediation_minutes: Optional[int] = None,
) -> dict[str, Any]:
    """
    Build the final TRACE-compatible SATD detection record.

    Fields unavailable to the model remain null until repository
    mining, source parsing, explanation, review, or estimation
    components provide them.
    """

    comment = str(comment).strip()

    classification = predictor.classify(
        comment
    )

    if satd_id is None:
        satd_id = create_satd_id(
            comment=comment,
            repository_id=repository_id,
            commit_sha=commit_sha,
            file_path=file_path,
            line_start=line_start,
        )

    public_label = (
        "SATD"
        if classification["is_satd"]
        else "NON_SATD"
    )

    return {
        "satd_id": satd_id,
        "repository_id": repository_id,
        "commit_sha": commit_sha,
        "file_path": file_path,
        "language": language,
        "line_start": line_start,
        "line_end": line_end,
        "comment": comment,

        "classification": {
            "label": public_label,
            "category": classification["category"],
            "score": round(
                classification["score"],
                6,
            ),
            "score_type": (
                "uncalibrated_model_score"
            ),
        },

        "evidence": {
            # The classifier does not produce a faithful natural-language
            # explanation. Leave this null instead of inventing one.
            "explanation": None,
            "source": "SOURCE_COMMENT",
        },

        "review_status": (
            "DETECTED_UNVERIFIED"
            if classification["is_satd"]
            else "NOT_DETECTED_UNVERIFIED"
        ),

        # This requires later estimation or human review.
        "remediation_minutes": remediation_minutes,
    }


def main() -> int:
    args = parse_arguments()

    try:
        predictor = SATDPredictor(
            model_path=args.model_path,
            max_length=args.max_length,
        )

        output_record = build_output_record(
            predictor=predictor,
            comment=args.comment,
            satd_id=args.satd_id,
            repository_id=args.repository_id,
            commit_sha=args.commit_sha,
            file_path=args.file_path,
            language=args.language,
            line_start=args.line_start,
            line_end=args.line_end,
            remediation_minutes=(
                args.remediation_minutes
            ),
        )

        # Standard output contains JSON only.
        # This allows another service to parse the script output directly.
        print(
            json.dumps(
                output_record,
                indent=2,
                ensure_ascii=False,
            )
        )

        return 0

    except Exception as error:
        # Errors go to stderr so stdout remains valid JSON on success.
        print(
            json.dumps(
                {
                    "error": {
                        "type": type(error).__name__,
                        "message": str(error),
                    }
                },
                indent=2,
                ensure_ascii=False,
            ),
            file=sys.stderr,
        )

        return 1


if __name__ == "__main__":
    raise SystemExit(main())