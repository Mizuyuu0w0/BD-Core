
import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Add parent dir to path to import core
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.wizard import AnalysisWizard
from core.utils import BACK_SIGNAL

class TestBackFlow(unittest.TestCase):
    def setUp(self):
        # Mock DF
        self.mock_df = MagicMock()
        self.mock_df.columns = ["Gene", "S1", "S2"]
        # Mock numeric check
        self.mock_df.__getitem__.return_value.dtype = 'float'
        
    @patch('core.wizard_steps.get_user_input')
    @patch('core.utils.get_user_input')
    def test_full_back_flow(self, mock_utils_input, mock_steps_input):
        """
        Simulate user going to Step 4 and then backing out all the way.
        Inputs flow:
        Step 1: "4" (Heatmap) -> Subtype "1" (Corr) -> Done (Step 1 Complete)
        Step 2: "all" (Select Cols) -> "done" (Finish Selection) -> (Step 2 Complete)
        Step 3: "1" (Linear) -> (Step 3 Complete)
        Step 4: "b" (Back from Title?) -> Go to Step 3
        Step 3: "b" (Back from Trans?) -> Go to Step 2
        Step 2: "b" (Back from Mapping?) -> Confirm "y" -> Go to Step 1
        Step 1: "b" (Back from Graph?) -> Exit
        """
        
        # We need to coordinate inputs. 
        # Wizard.run() logic:
        # Step 1: Graph(4) -> Subtype(1)
        # Step 2: Heatmap cols -> "all" -> "done"
        # Step 3: Transformation -> "1"
        # Step 4: Title? -> "b"
        # -- Back to Step 3 --
        # Step 3: Transformation -> "b"
        # -- Back to Step 2 --
        # Step 2: Heatmap cols -> "b" -> Confirm "y"
        # -- Back to Step 1 --
        # Step 1: Graph -> "b"
        
        inputs = [
            # Forward
            "4", "1",       # Step 1
            "all", "done",  # Step 2
            "1",            # Step 3 (Transformation)
                            # Step 4 (Title) -> "b"
            BACK_SIGNAL,    
            
            # Backward
            BACK_SIGNAL,    # Step 3 (Trans) -> "b"
            BACK_SIGNAL,    # Step 2 (Mapping) -> "b" (No confirm needed as selected_cols is cleared on re-entry)
            BACK_SIGNAL     # Step 1 (Graph) -> "b" -> Exit
        ]
        
        # Side effect needs to pop inputs
        input_iter = iter(inputs)
        def side_effect(prompt, *args, **kwargs):
            try:
                val = next(input_iter)
                print(f"[MockInput] Prompt: '{prompt}' -> Input: '{val}'")
                return val
            except StopIteration:
                return "1" # Fallback
            
        mock_steps_input.side_effect = side_effect
        mock_utils_input.side_effect = side_effect
        # WizardSteps uses core.utils.get_user_input, so mocking that should be enough if imported correctly.
        # But WizardSteps imports it directly. So we verify patch target.
        # We patched core.wizard_steps.get_user_input above.
        
        wizard = AnalysisWizard(self.mock_df)
        
        # Run
        config = wizard.run()
        
        # Verify
        self.assertIsNone(config)
        print("\nSUCCESS: Wizard exited cleanly without generating config.")

if __name__ == '__main__':
    unittest.main()
