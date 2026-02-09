
import pandas as pd
import numpy as np
import os
import shutil
import sys
from pathlib import Path

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.artifact_manager import ArtifactManager
from plugins.boxplot import BoxplotPlugin
from plugins.scatter import ScatterPlugin
from plugins.volcano import VolcanoPlugin

# --- Test Artifact Manager ---
class TestAM(ArtifactManager):
    def __init__(self, run_id):
        self.run_id = run_id
        self.config = {}
        self.timestamp = "TEST_TIME"
        self.sandbox_dir = Path(f"test_summary_output_{run_id}")
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
        
        if self.sandbox_dir.exists():
            shutil.rmtree(self.sandbox_dir)
        self.sandbox_dir.mkdir(parents=True)
        print(f"[{run_id}] Sandbox: {self.sandbox_dir}")

def test_summary_txt():
    print("=== Verifying summary.txt Generation ===\n")

    # 1. Box Plot
    print("--- 1. Box Plot ---")
    df_box = pd.DataFrame({
        'x': ['A']*5 + ['B']*5,
        'y': np.random.rand(10)
    })
    # Sort carefully to avoid string/int issues if any
    
    am_box = TestAM("BOX_TEST")
    config_box = {'graph': 'Box', 'xlabel': 'Group', 'ylabel': 'Value'}
    try:
        BoxplotPlugin(am_box, config_box, df_box).run()
        am_box.close() # Critical: Write audit log
        
        if (am_box.sandbox_dir / "summary.txt").exists():
            print("   [OK] summary.txt exists.")
        else:
            print("   [FAIL] summary.txt missing.")
            
        if (am_box.sandbox_dir / "audit_log.json").exists():
            print("   [OK] audit_log.json exists.")
            import json
            with open(am_box.sandbox_dir / "audit_log.json", 'r') as f:
                print(f"   [Content] {json.load(f)}")
        else:
            print("   [FAIL] audit_log.json missing.")
            
    except Exception as e:
        print(f"   [ERROR] {e}")
        import traceback
        traceback.print_exc()

    # 2. Scatter Plot
    print("\n--- 2. Scatter Plot ---")
    df_scatter = pd.DataFrame({
        'x': np.random.rand(10),
        'y': np.random.rand(10)
    })
    am_scatter = TestAM("SCATTER_TEST")
    config_scatter = {'graph': 'Scatter', 'xlabel': 'X', 'ylabel': 'Y'}
    try:
        ScatterPlugin(am_scatter, config_scatter, df_scatter).run()
        am_scatter.close()
        
        if (am_scatter.sandbox_dir / "summary.txt").exists():
            print("   [OK] summary.txt exists.")
        else:
            print("   [FAIL] summary.txt missing.")

        if (am_scatter.sandbox_dir / "audit_log.json").exists():
            print("   [OK] audit_log.json exists.")
        else:
            print("   [FAIL] audit_log.json missing.")

    except Exception as e:
        print(f"   [ERROR] {e}")

    # 3. Volcano Plot
    print("\n--- 3. Volcano Plot ---")
    df_volcano = pd.DataFrame({
        'x': np.random.randn(20), # Log2FC
        'y': np.random.rand(20)   # P-value
    })
    am_volcano = TestAM("VOLCANO_TEST")
    config_volcano = {'graph': 'Volcano', 'xlabel': 'Log2FC', 'ylabel': 'P-value', 'title': 'Volcano Test'}
    try:
        VolcanoPlugin(am_volcano, config_volcano, df_volcano).run()
        am_volcano.close()
        
        if (am_volcano.sandbox_dir / "summary.txt").exists():
            print("   [OK] summary.txt exists.")
        else:
            print("   [FAIL] summary.txt missing.")
            
        if (am_volcano.sandbox_dir / "audit_log.json").exists():
            print("   [OK] audit_log.json exists.")
        else:
            print("   [FAIL] audit_log.json missing.")

    except Exception as e:
        print(f"   [ERROR] {e}")

    print("\n=== Verification Complete ===")

if __name__ == "__main__":
    test_summary_txt()
