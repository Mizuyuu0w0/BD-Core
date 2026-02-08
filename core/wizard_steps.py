import pandas as pd
from core.utils import get_user_input, BACK_SIGNAL

class WizardSteps:
    """
    [Template Pattern] 
    Each step is a distinct method. 
    Graph-specific sub-logic (like subtypes) is handled via `_resolve_subtype`.
    """
    def __init__(self, wizard_instance):
        self.wiz = wizard_instance
        self.df = wizard_instance.df
        self.columns = wizard_instance.columns

    def _get_subtypes(self, graph_type):
        """
        [Extensibility Point]
        Return a dict of subtypes for a given graph type.
        Structure: { "1": ("Description", "internal_value"), ... }
        Return None if no subtypes exist.
        """
        if graph_type == "Heatmap":
            return {
                "1": ("Correlation Matrix (Sample-Sample Similarity)", "correlation"),
                "2": ("Expression Heatmap (Raw Gene Values)", "expression")
            }
        
        # [Reserved for Future] 
        # You can easily add Violin plot support here:
        # if graph_type == "Box":
        #    return {
        #        "1": ("Box Plot", "box"),
        #        "2": ("Violin Plot", "violin")
        #    }
        
        return None


    def get_valid_value(self, prompt):
        """Helper to get column index or name"""
        while True:
            val_raw = get_user_input(prompt)
            if val_raw == BACK_SIGNAL: return BACK_SIGNAL
            
            val = val_raw.strip()
            # 1. Try Index
            try:
                idx = int(val)
                if 0 <= idx < len(self.columns):
                    return idx
                print(f"(!) Error: Index must be between 0 and {len(self.columns)-1}.")
                continue
            except ValueError:
                pass
            
            # 2. Try Column Name (Case-insensitive)
            col_lower = [c.lower() for c in self.columns]
            if val.lower() in col_lower:
                return col_lower.index(val.lower())
                
            print("(!) Error: Please enter a valid index ID or column name.")

    def _get_valid_choice(self, prompt, valid_map, default_key=None):
        """
        Helper: Strictly validate input against a map of valid options.
        valid_map: dict { "1": value, "2": value }
        Returns: (key, value) or BACK_SIGNAL
        """
        keys = list(valid_map.keys())
        options_str = "/".join(keys)
        # Construct prompt like "Choice (1/2, Default 1)" if not provided
        
        while True:
            val = get_user_input(prompt)
            if val == BACK_SIGNAL: return BACK_SIGNAL
            
            val = val.strip()
            if not val and default_key:
                val = default_key
            
            # Case-insensitive check for values (robustness)
            # e.g. user types "Expression" instead of "2"
            if val in valid_map:
                return val, valid_map[val]
            
            # Try matching values (keys are "1", "2")
            # We also want to support typing "Box" for "1"
            # Inverted map for value matching
            # This is complex, let's keep it simple: Key matching primarily.
            # But the original code supported "box" for "1".
            
            # Let's support case-insensitive key interaction
            if val.lower() in [k.lower() for k in keys]:
                # find the actual key
                for k in keys:
                    if k.lower() == val.lower():
                        return k, valid_map[k]
            
            print(f"(!) Invalid choice. Please enter one of: {options_str}")

    def _handle_heatmap_subtype(self, config):
        """
        Sub-logic for Heatmap configuration.
        [State Machine v1.2] Defines linear steps to allow granular 'Back' navigation.
        Steps: 0=Mode, 1=Normalization (Expression only), 2=Clustering
        """
        step = 0
        while step >= 0:
            # --- Step 0: Mode Selection ---
            if step == 0:
                print("\n[Heatmap Mode]")
                print(" [1] Correlation Matrix (Sample vs Sample similarity)")
                print(" [2] Expression Heatmap (Gene vs Sample raw values)")
                
                choice_map = {"1": "correlation", "2": "expression"}
                res = self._get_valid_choice("Choice (1-2, Default 1)", choice_map, "1")
                
                if res == BACK_SIGNAL: return BACK_SIGNAL # Exit Sub-logic
                _, mode_val = res
                config['heatmap_mode'] = mode_val
                
                if mode_val == 'correlation':
                    config['cluster'] = True
                    config.pop('z_score', None)
                    return True # Correlation has no more steps
                else:
                    step = 1 # Go to Normalization
            
            # --- Step 1: Normalization (Expression Only) ---
            elif step == 1:
                print("\n[Normalization]")
                print(" [0] None (Plot Raw Values)")
                print(" [1] Z-Score Rows (Standardize Genes)")
                print(" [2] Z-Score Columns (Standardize Samples)")
                
                z_map = {"0": None, "1": 0, "2": 1}
                z_res = self._get_valid_choice("Choice (0-2, Default 0)", z_map, "0")
                
                if z_res == BACK_SIGNAL: 
                    step = 0 # Back to Mode
                    continue

                _, z_val = z_res
                config['z_score'] = z_val
                step = 2 # Go to Clustering

            # --- Step 2: Clustering (Expression Only) ---
            elif step == 2:
                clust_map = {"y": True, "n": False}
                c_res = self._get_valid_choice("Cluster Columns/Rows? (y/n, default: y)", clust_map, "y")
                
                if c_res == BACK_SIGNAL:
                    step = 1 # Back to Normalization
                    continue

                _, c_val = c_res
                config['cluster'] = c_val
                return True # Done

        return BACK_SIGNAL # Should not reach here normally

    def run_step_1(self, config):
        """Select Graph Type & Subtype"""
        while True:
            print("\n[Step 1/4] Select Graph Type:")
            print(" [1] Box Plot")
            print(" [2] Scatter Plot")
            print(" [3] Volcano Plot")
            print(" [4] Heatmap")
            
            graph_map = {"1":"Box","2":"Scatter","3":"Volcano","4":"Heatmap"}
            
            # Use stricter helper
            # We can also support "box", "scatter" by expanding the map keys or rely on helper 
            # Helper handles exact keys. To support names, we need a smarter map or just rely on IDs for robustness.
            # Let's stick to IDs for simplicity + Reliability.
            
            res = self._get_valid_choice("Choice (1-4)", graph_map)
            if res == BACK_SIGNAL: return BACK_SIGNAL
            
            _, graph_selected = res
            config['graph'] = graph_selected
            
            # [Context Clear] Remove previous graph-specific keys to prevent residue
            if graph_selected != "Heatmap":
                config.pop('heatmap_mode', None)
                config.pop('z_score', None)
                config.pop('cluster', None)
            
            # Subtype Logic
            if graph_selected == "Heatmap":
                sub_res = self._handle_heatmap_subtype(config)
                if sub_res == BACK_SIGNAL: 
                    continue # Loop back to Graph Type
            
            return True # Success

    def run_step_2(self, config):
        """Variable Mapping"""
        graph_selected = config['graph']
        print(f"\n[Step 2/4] Variable Mapping ({graph_selected})")
        
        # Smart Data Preview
        print(f"{'ID':<4} | {'Column Name':<25} | {'Type':<10} | {'Sample (First Value)':<20}")
        print("-" * 70)
        for i, col in enumerate(self.columns):
            dtype = str(self.df[col].dtype)
            sample = str(self.df[col].iloc[0])[:20]
            print(f" {i:<3} | {col:<25} | {dtype:<10} | {sample:<20}")
        print("-" * 70)
        # Helper: is_numeric
        def is_numeric_col(col_name):
            try:
                if pd.api.types.is_numeric_dtype(self.df[col_name]): return True
                if pd.to_numeric(self.df[col_name], errors='coerce').notna().mean() > 0.5: return True
                valid_series = self.df[col_name].dropna().astype(str)
                if len(valid_series) == 0: return False
                return valid_series.str.match(r'^\s*[-+]?\.?\d').mean() > 0.5
            except:
                return False
        # --- HEATMAP LOGIC ---
        if graph_selected == "Heatmap":
            mode = config.get('heatmap_mode', 'correlation')
            print(f"\n[Heatmap: {mode.capitalize()}] Select numeric columns.")
            print("Type column ID/Name. Tip: Type 'all' for all numeric, or '1-10' for range.")
            print("Enter 'done' to finish. Type 'undo' to remove last. Type 'b' to go back/clear all.")
            
            selected_cols = []
            while True:
                prompt = f"Select Column {len(selected_cols)+1} (or 'done')"
                val_raw = get_user_input(prompt)
                
                # [UX Fix] 'b' means Go Back entirely (Abandon Selection)
                if val_raw == BACK_SIGNAL:
                    if selected_cols:
                         print("(!) Going back will discard current selection.")
                         conf = get_user_input("Confirm go back? (y/n, default: y)")
                         if conf.lower() == 'n': continue
                    return BACK_SIGNAL # Go back to Step 1

                val = val_raw.strip()
                
                # [UX Fix] 'undo' means Remove Last
                if val.lower() == 'undo':
                     if selected_cols:
                         removed = selected_cols.pop()
                         print(f"Removed '{removed}'.")
                     else:
                         print("Nothing to undo.")
                     continue
                
                if val.lower() == 'done' or val == '':
                    if len(selected_cols) < 2:
                        if val == '':
                             print("(!) Heatmap requires at least 2 columns. Please select more.")
                             continue
                        else:
                             print("(!) Heatmap requires at least 2 columns.")
                             continue
                    break
                
                # [Optimization] Support 'all' to select all available numeric columns
                if val.lower() == 'all':
                    added_count = 0
                    for c in self.columns:
                        if is_numeric_col(c) and c not in selected_cols:
                            selected_cols.append(c)
                            added_count += 1
                    print(f"Added {added_count} new columns. Total: {len(selected_cols)}.")
                    continue

                # [Optimization] Support Range (e.g. 1-10)
                if '-' in val and val.replace('-','').isdigit():
                    try:
                        start, end = map(int, val.split('-'))
                        # Correct order
                        if start > end: start, end = end, start
                        
                        added_count = 0
                        for idx in range(start, end + 1):
                            if 0 <= idx < len(self.columns):
                                col_name = self.columns[idx]
                                if is_numeric_col(col_name) and col_name not in selected_cols:
                                    selected_cols.append(col_name)
                                    added_count += 1
                        print(f"Added {added_count} columns from range {start}-{end}.")
                        continue
                    except:
                        pass # Fallback to normal check
                
                # Check ID/Name
                col_found = None
                if val.isdigit() and 0 <= int(val) < len(self.columns):
                    col_found = self.columns[int(val)]
                elif val in self.columns:
                     col_found = val
                if not col_found:
                    for c in self.columns:
                        if c.lower() == val.lower():
                            col_found = c; break
                
                if col_found:
                     if is_numeric_col(col_found):
                         if col_found not in selected_cols:
                             selected_cols.append(col_found)
                             print(f"Added: {col_found}")
                         else:
                             print("(!) Already selected.")
                     else:
                         print(f"(!) Column '{col_found}' is not numeric.")
                else:
                     print("(!) Invalid column ID or Name.")
            config['selected_columns'] = selected_cols
            # Placeholders for compatibility
            config['xlabel'] = "Samples" 
            config['ylabel'] = "Genes/Variables"
            return True

        # --- STANDARD LOGIC (Box/Scatter/Volcano) ---
        # Select X
        x_idx = self.get_valid_value(f"Select X-axis (ID or Name)")
        if x_idx == BACK_SIGNAL: return BACK_SIGNAL
        
        # Select Y
        while True:
            y_idx = self.get_valid_value(f"Select Y-axis (ID or Name)")
            if y_idx == BACK_SIGNAL: return BACK_SIGNAL
            
            col_name = self.columns[y_idx]
            if is_numeric_col(col_name):
                break
            else:
                print(f" [Error] Column '{col_name}' is not numeric.")
        config['xlabel'] = self.columns[x_idx]
        config['ylabel'] = self.columns[y_idx]
        return True

    def run_step_3(self, config):
        """Data Transformation"""
        graph_selected = config['graph']
        
        # [Update] Allow Heatmap to use transformation (e.g. Log2 for counts)
        # Only Volcano strictly requires specific pre-calc (Log2FC), so maybe skip there?
        # Actually Volcano expects pre-calculated Log2FC usually, or raw.
        # Let's only skip for Volcano for now if strictly needed, or just allow all.
        # Original logic skipped both.
        
        if graph_selected in ['Volcano']:
             print(f"\n[Step 3/4] Data Transformation: Auto-skipped for {graph_selected}.")
             config['model'] = 'linear'
             return True
            
        print("\n[Step 3/4] Data Transformation (Model):")
        print(" [1] Linear | [2] Log2 | [3] Log10 | [4] Natural Log (Ln)")
        while True:
            t_raw = get_user_input("Choice (1-4, Default Linear)")
            if t_raw == BACK_SIGNAL: return BACK_SIGNAL
            
            t_choice = t_raw.strip() or "1"
            transform_map = {"1":"linear","2":"log2","3":"log10","4":"ln"}
            
            # [Robustness] Allow typing "Log2"
            t_clean = t_choice.lower()
            name_map = {v:k for k,v in transform_map.items()} # linear -> 1
            
            if t_choice in transform_map:
                config['model'] = transform_map[t_choice]
                return True
            elif t_clean in name_map:
                 config['model'] = transform_map[name_map[t_clean]]
                 return True
            
            print("(!) Invalid choice.")

    def run_step_4(self, config):
        """Metadata"""
        print("\n[Step 4/4] Metadata:")
        
        # Title
        title_raw = get_user_input(f"Show Title? (y/n, default: n)")
        if title_raw == BACK_SIGNAL: return BACK_SIGNAL
        
        title_q = title_raw.strip().lower() or 'n'
        if title_q == 'y':
            title_raw = get_user_input(f"Enter Title (default: {config.get('ylabel','')} Analysis)")
            if title_raw == BACK_SIGNAL: return BACK_SIGNAL # Retry Step 4
            config['title'] = title_raw.strip() or f"{config.get('ylabel','')} Analysis"
        else:
            config['title'] = None
        # Legend
        legend_raw = get_user_input(f"Show Legend? (y/n, default: n)")
        if legend_raw == BACK_SIGNAL: return BACK_SIGNAL # Back to Title
        
        legend_q = legend_raw.strip().lower() or 'n'
        if legend_q == 'y':
            config['legend'] = True
            legend_name_raw = get_user_input(f"Enter Legend Name (default: {config.get('ylabel','')})")
            if legend_name_raw == BACK_SIGNAL: return BACK_SIGNAL # Back to Legend query
            config['legend_name'] = legend_name_raw.strip() or config.get('ylabel','')
        else:
            config['legend'] = False
            config['legend_name'] = None
            
        return True