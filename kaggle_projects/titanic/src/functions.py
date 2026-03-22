import os
import pandas as pd
from pathlib import Path

from titanic.src.formats import RequestTestOutput, ResponseTestOutput


def test_output(message: RequestTestOutput) -> ResponseTestOutput:
    base_dir = Path('./')
    output_filepath = base_dir / message.output_filepath
    reference_filepath = base_dir / message.reference_filepath

    assert os.path.exists(output_filepath)    
    assert os.path.exists(reference_filepath)
    
    ref_df = pd.read_csv(reference_filepath)
    out_df = pd.read_csv(output_filepath)
    assert ref_df.shape == out_df.shape, f"Shape mismatch: {ref_df.shape} != {out_df.shape}"
    assert set(ref_df.columns) == set(out_df.columns), f"Columns mismatch: {set(ref_df.columns)} != {set(out_df.columns)}"
    assert out_df.dtypes.equals(ref_df.dtypes), f"Types mismatch: {out_df.dtypes} != {ref_df.dtypes}"
    
    return ResponseTestOutput(
        status="success",
        **message.model_dump()
    )