
import unittest
from unittest.mock import MagicMock, patch
import pandas as pd
from core.wizard_steps import WizardSteps
from core.utils import BACK_SIGNAL

class TestWizardLogic(unittest.TestCase):
    def setUp(self):
        # Mock Wizard Instance
        self.mock_wiz = MagicMock()
        self.mock_wiz.df = pd.DataFrame()
        self.mock_wiz.columns = []
        self.steps = WizardSteps(self.mock_wiz)
        self.config = {}

    @patch('core.wizard_steps.get_user_input')
    def test_heatmap_state_machine_flow(self, mock_input):
        """Test Happy Path: Expression -> Norm -> Cluster -> Done"""
        # Inputs: 
        # 1. "2" (Expression)
        # 2. "0" (No Norm)
        # 3. "y" (Cluster)
        mock_input.side_effect = ["2", "0", "y"]
        
        res = self.steps._handle_heatmap_subtype(self.config)
        
        self.assertTrue(res)
        self.assertEqual(self.config['heatmap_mode'], 'expression')
        self.assertEqual(self.config['z_score'], None)
        self.assertEqual(self.config['cluster'], True)
        print("Test 1 (Happy Path): Passed")

    @patch('core.wizard_steps.get_user_input')
    def test_heatmap_back_logic(self, mock_input):
        """Test Back Logic: Expression -> Norm -> BACK -> Mode -> Correlation"""
        # Inputs:
        # 1. "2" (Expression) -> Go to Norm
        # 2. "b" (Back) -> Go back to Mode
        # 3. "1" (Correlation) -> Done
        mock_input.side_effect = ["2", BACK_SIGNAL, "1"]
        
        # Reset config
        self.config = {}
        res = self.steps._handle_heatmap_subtype(self.config)
        
        self.assertTrue(res)
        self.assertEqual(self.config['heatmap_mode'], 'correlation')
        self.assertTrue(self.config.get('cluster', False)) # Corr default
        print("Test 2 (Back Logic): Passed")

    @patch('core.wizard_steps.get_user_input')
    def test_heatmap_deep_back_logic(self, mock_input):
        """Test Deep Back: Expression -> Norm -> Cluster -> BACK -> Norm -> BACK -> Mode -> Exit"""
        # Inputs:
        # 1. "2" (Expression)
        # 2. "0" (Norm 0)
        # 3. "b" (Back from Cluster) -> Go to Norm
        # 4. "b" (Back from Norm) -> Go to Mode
        # 5. "b" (Back from Mode) -> Exit Function
        mock_input.side_effect = ["2", "0", BACK_SIGNAL, BACK_SIGNAL, BACK_SIGNAL]
        
        self.config = {}
        res = self.steps._handle_heatmap_subtype(self.config)
        
        self.assertEqual(res, BACK_SIGNAL)
        print("Test 3 (Deep Back): Passed")

if __name__ == '__main__':
    try:
        unittest.main(argv=['first-arg-is-ignored'], exit=False)
    except Exception as e:
        print(f"Tests failed: {e}")
