import logging 
import pandas as pd
from core.utils import get_user_input, BACK_SIGNAL
from core.wizard_steps import WizardSteps

logger = logging.getLogger(__name__)

class AnalysisWizard:
    """
    BioDiagnosis Interactive Wizard (v1.1)
    Orchestrator: Delegates actual logic to WizardSteps.
    """
    def __init__(self, data_df):
        self.df = data_df
        self.columns = list(data_df.columns)
        # Use WizardSteps to handle logic, pass self as context
        self.steps_logic = WizardSteps(self)

    def run(self):
        print("\n" + "="*40)
        print(" BioData Interactive Wizard v1.1")
        print("="*40)
        
        config = {}
        step = 1
        
        while step <= 4:
            # Step Switcher
            if step == 1:
                # Step 1: Graph Selection
                res = self.steps_logic.run_step_1(config)
                if res == BACK_SIGNAL: return None # Exit Wizard
                if res is False: continue # Stay on Step 1
                step += 1
            
            elif step == 2:
                # Step 2: Variable Mapping
                res = self.steps_logic.run_step_2(config)
                if res == BACK_SIGNAL: step -= 1; continue
                step += 1

            elif step == 3:
                # Step 3: Transformation
                res = self.steps_logic.run_step_3(config)
                if res == BACK_SIGNAL: step -= 1; continue
                step += 1

            elif step == 4:
                # Step 4: Metadata
                res = self.steps_logic.run_step_4(config)
                if res == BACK_SIGNAL: step -= 1; continue
                step += 1

        print("\n" + "="*40)
        print("Configuration captured! Ready to analyze.")
        print("-"*40 + "\n")

        return config