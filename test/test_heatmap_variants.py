
import pandas as pd
import numpy as np
import os
import sys
# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import shutil
from plugins.heatmap import HeatmapPlugin
from core.artifact_manager import ArtifactManager

from core.artifact_manager import ArtifactManager
from pathlib import Path

# --- Test Artifact Manager ---
# Inherits from REAL ArtifactManager to test PDF/XLSX generation
class TestAM(ArtifactManager):
    def __init__(self, run_id):
        # Bypass standard init to enforce fixed test paths
        self.run_id = run_id
        self.config = {}
        self.timestamp = "TEST_TIME"
        self.sandbox_dir = Path(f"test_real_output_{run_id}")
        self.mode = "TEST_REAL"
        self.mode = "TEST_REAL"
        
        # [Fix] Match real ArtifactManager structure
        self.audit_log = {
            "RunID": self.run_id,
            "Timestamp": self.timestamp,
            "OutputMode": self.mode,
            "Environment": "CLI",
            "Operations": [],
            "InputHash": "TEST_HASH" # Mock hash
        }
        
        self.audit_log = {
            "RunID": self.run_id,
            "Timestamp": self.timestamp,
            "OutputMode": self.mode,
            "Environment": "CLI",
            "Operations": [],
            "InputHash": "TEST_HASH"
        }
        
        # Clean previous
        if self.sandbox_dir.exists():
            shutil.rmtree(self.sandbox_dir)
        self.sandbox_dir.mkdir(parents=True)
        
        print(f"[{run_id}] Sandbox created at: {self.sandbox_dir}")

    # We do NOT override save_figure or save_data, so it uses the REAL logic.


# --- Data Generation ---
def generate_data(rows=20, cols=5):
    """Generate random expression data"""
    data = np.random.rand(rows, cols) * 10 # Scale up
    columns = [f"Sample_{i+1}" for i in range(cols)]
    index = [f"Gene_{i+1}" for i in range(rows)]
    return pd.DataFrame(data, columns=columns, index=index)

def test_heatmap_variants():
    print("=== Starting Heatmap Variants Test ===\n")
    
    # 1. Setup Data
    df = generate_data()
    print(f"Data Shape: {df.shape}")
    print(f"Columns: {df.columns.tolist()}")

    # --- Test Case 1: Correlation Mode ---
    print("\n--- Test Case 1: Correlation Mode (Sample-Sample) ---")
    am_corr = TestAM("HEATMAP_CORR")
    config_corr = {
        'graph': 'Heatmap',
        'heatmap_mode': 'correlation',
        'subtype': 'correlation', 
        'cluster': True,
        'selected_columns': df.columns.tolist()
    }
    
    try:
        plugin = HeatmapPlugin(am_corr, config_corr, df)
        plugin.run()
        am_corr.close() # Flush audit log
        print(">> SUCCESS: Correlation Heatmap ran without errors.")
        
        # Verify Files
        expected_pdf = am_corr.sandbox_dir / "Heatmap Graph (Correlation Matrix).pdf"
        expected_xlsx = am_corr.sandbox_dir / "Heatmap Graph (Correlation Matrix) Data.xlsx"
        expected_json = am_corr.sandbox_dir / "audit_log.json"
        
        if expected_pdf.exists(): print(f"   [OK] PDF Generated: {expected_pdf}")
        else: print(f"   [FAIL] PDF Missing: {expected_pdf}")
            
        if expected_xlsx.exists(): print(f"   [OK] XLSX Generated: {expected_xlsx}")
        else: print(f"   [FAIL] XLSX Missing: {expected_xlsx}")

        if expected_json.exists(): print(f"   [OK] JSON Generated: {expected_json}")
        else: print(f"   [FAIL] JSON Missing: {expected_json}")

    except Exception as e:
        print(f">> FAILURE: {e}")
        import traceback
        traceback.print_exc()

    # --- Test Case 2: Expression Mode (Clustered + Z-Score Rows) ---
    print("\n--- Test Case 2: Expression Mode (Clustered + Z-Score Rows) ---")
    am_expr = TestAM("HEATMAP_EXPR_CLUST")
    config_expr = {
        'graph': 'Heatmap',
        'heatmap_mode': 'expression',
        'subtype': 'expression',
        'z_score': 0, # Row z-score
        'cluster': True,
        'selected_columns': df.columns.tolist()
    }
    
    try:
        plugin = HeatmapPlugin(am_expr, config_expr, df)
        plugin.run()
        am_expr.close() # Flush audit log
        print(">> SUCCESS: Expression Heatmap (Clustered) ran without errors.")
        
        expected_pdf = am_expr.sandbox_dir / "Heatmap Graph (Expression Heatmap).pdf"
        expected_xlsx = am_expr.sandbox_dir / "Heatmap Graph (Expression Heatmap) Data.xlsx"
        expected_json = am_expr.sandbox_dir / "audit_log.json"
        
        if expected_pdf.exists(): print(f"   [OK] PDF Generated: {expected_pdf}")
        else: print(f"   [FAIL] PDF Missing: {expected_pdf}")
        
        if expected_xlsx.exists(): print(f"   [OK] XLSX Generated: {expected_xlsx}")
        else: print(f"   [FAIL] XLSX Missing: {expected_xlsx}")
        
        if expected_json.exists(): print(f"   [OK] JSON Generated: {expected_json}")
        else: print(f"   [FAIL] JSON Missing: {expected_json}")

    except Exception as e:
        print(f">> FAILURE: {e}")
        import traceback
        traceback.print_exc()

    # --- Test Case 3: Expression Mode (Unclustered + Raw Values) ---
    print("\n--- Test Case 3: Expression Mode (Unclustered + Raw Values) ---")
    am_raw = TestAM("HEATMAP_EXPR_RAW")
    config_raw = {
        'graph': 'Heatmap',
        'heatmap_mode': 'expression',
        'subtype': 'expression',
        'z_score': None,
        'cluster': False,
        'selected_columns': df.columns.tolist()
    }
    
    try:
        plugin = HeatmapPlugin(am_raw, config_raw, df)
        plugin.run()
        am_raw.close() # Flush audit log
        print(">> SUCCESS: Expression Heatmap (Unclustered) ran without errors.")
        
        expected_pdf = am_raw.sandbox_dir / "Heatmap Graph (Expression Heatmap).pdf"
        expected_xlsx = am_raw.sandbox_dir / "Heatmap Graph (Expression Heatmap) Data.xlsx"
        expected_json = am_raw.sandbox_dir / "audit_log.json"
        
        if expected_pdf.exists(): print(f"   [OK] PDF Generated: {expected_pdf}")
        else: print(f"   [FAIL] PDF Missing: {expected_pdf}")
        
        if expected_xlsx.exists(): print(f"   [OK] XLSX Generated: {expected_xlsx}")
        else: print(f"   [FAIL] XLSX Missing: {expected_xlsx}")

        if expected_json.exists(): print(f"   [OK] JSON Generated: {expected_json}")
        else: print(f"   [FAIL] JSON Missing: {expected_json}")

    except Exception as e:
        print(f">> FAILURE: {e}")
        import traceback
        traceback.print_exc()

    print("\n=== Test Complete ===")

if __name__ == "__main__":
    test_heatmap_variants()
