import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Add parent dir
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from main import main

class TestMainLoop(unittest.TestCase):
    
    def setUp(self):
        # Create a dummy file for discovery
        self.dummy_file = "dummy_test_data_v2.xlsx"
        with open(self.dummy_file, "w") as f:
            f.write("dummy")
            
    def tearDown(self):
        # Cleanup
        if os.path.exists(self.dummy_file):
            os.remove(self.dummy_file)

    @patch('main.get_user_input')
    @patch('main.AnalysisWizard')
    @patch('main.DataCleaner') # Mock Cleaner to avoid reading the garbage dummy file
    @patch('main.ForgivingParser') # Mock Parser too
    @patch('main.setup_args')
    def test_main_exit_after_wizard_cancel(self, mock_setup_args, mock_parser_cls, mock_cleaner_cls, mock_wizard_cls, mock_input):
        """
        Test that main() exits if wizard is cancelled and user says 'n' to restart.
        Using real file discovery.
        """
        # 1. Setup Args
        mock_args = MagicMock()
        mock_args.mode = 'human'
        mock_args.config = None
        mock_args.input = None # Trigger auto-discovery
        mock_setup_args.return_value = mock_args

        # 2. Setup Parser (to handle smart_load_data)
        # We need smart_load_data to return a dummy df so Wizard doesn't crash on init
        mock_parser_instance = MagicMock()
        mock_parser_cls.return_value = mock_parser_instance
        mock_parser_instance.smart_load_data.return_value = MagicMock() # raw_df

        # 3. Setup Wizard
        mock_wizard_instance = MagicMock()
        mock_wizard_cls.return_value = mock_wizard_instance
        # Wizard.run() returns None (cancelled)
        mock_wizard_instance.run.return_value = None

        # 4. Setup User Input for Restart
        # prompt: "Restart wizard? (y/n)" -> "n"
        mock_input.return_value = 'n'

        # 5. Run main
        # We assume main() will find self.dummy_file
        try:
            main()
        except SystemExit:
            pass
        
        # 6. Verify assertions
        # Should have called wizard.run()
        if mock_wizard_instance.run.call_count == 0:
            print("Unknown Error: Wizard was not triggered. Check if file discovery worked.")
            
        mock_wizard_instance.run.assert_called_once()
        
        # Should have asked to restart
        # We check if get_user_input was called with something containing "Restart"
        # call_args_list might capture multiple calls if input was called elsewhere?
        # But here we expect only one call to restart? 
        # Actually main.py might print "Multiple data files" if more than one. 
        # We should ensure we are the only xlsx/csv file or handle selection.
        # But avoiding that complexity is better.
        
        # Check calls to get_user_input
        # We expect at least one call with "Restart"
        found_restart = False
        for call in mock_input.call_args_list:
            args, _ = call
            if "Restart" in args[0]:
                found_restart = True
                break
        self.assertTrue(found_restart, "Should have asked to restart")
        
        # Should exit loop.
        self.assertEqual(mock_wizard_instance.run.call_count, 1)

if __name__ == '__main__':
    unittest.main()
