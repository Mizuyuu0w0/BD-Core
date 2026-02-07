import logging 
import pandas as pd
import re
from pathlib import Path
from core.utils import get_user_input, BACK_SIGNAL

# [NEW COMPONENT] 交互式向导，实现最低代码出图逻辑
logger = logging.getLogger(__name__)

class AnalysisWizard:
    """
    BioDiagnosis Interactive Wizard (v1.0)
    引导用户在没有 .bd 文件的情况下完成分析配置。
    """
    def __init__(self, data_df):
        self.df = data_df
        self.columns = list(data_df.columns)

    def _get_valid_value(self, prompt, max_val):
        """[UPDATE] 支持输入索引或列名"""
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


    def run(self):
        print("\n" + "="*40)
        print(" BioData Interactive Wizard v1.0")
        print("="*40)
        config = {}
        step = 1
        
        # 初始化所有可能用到的变量，防止 UnboundLocalError
        xlabel = ylabel = model = title = legend_name = None
        legend = False
        graph_selected = "Box" 

        while step <= 4:
            # 1. 图表类型选择
            if step == 1:
                print("\n[Step 1/4] Select Graph Type:")
                print(" [1] Box Plot | [2] Scatter Plot | [3] Volcano Plot | [4] Heatmap")
                val = get_user_input("Choice (1-4)")
                
                if val == BACK_SIGNAL: return None
                graph_map = {"1":"Box","2":"Scatter","3":"Volcano","4":"Heatmap"}
                if val in graph_map:
                    graph_selected = graph_map[val]
                    config['graph'] = graph_selected
                    step += 1
                else:
                    print("(!) Invalid choice.")

            # 2. 变量映射
            elif step == 2:
                print(f"\n[Step 2/4] Variable Mapping ({graph_selected})")
                
                # [UX Upgrade] Smart Data Preview
                print(f"{'ID':<4} | {'Column Name':<25} | {'Type':<10} | {'Sample (First Value)':<20}")
                print("-" * 70)
                for i, col in enumerate(self.columns):
                    dtype = str(self.df[col].dtype)
                    sample = str(self.df[col].iloc[0])[:20] # Truncate long samples
                    print(f" {i:<3} | {col:<25} | {dtype:<10} | {sample:<20}")
                print("-" * 70)

                # Helper to check if column is likely numeric
                def is_numeric_col(col_name):
                    try:
                        # 1. Pure Numeric Check
                        if pd.api.types.is_numeric_dtype(self.df[col_name]): return True
                        
                        # 2. Strict String Conversion Check
                        if pd.to_numeric(self.df[col_name], errors='coerce').notna().mean() > 0.5: return True
                        
                        # 3. [NEW] Unit/Suffix Check (e.g. "10m", "20 ug/ml")
                        # Checks if >50% of non-empty values start with a number
                        valid_series = self.df[col_name].dropna().astype(str)
                        if len(valid_series) == 0: return False
                        
                        # Match start with number: optional +/- then digit or dot-digit
                        return valid_series.str.match(r'^\s*[-+]?\.?\d').mean() > 0.5
                    except:
                        return False

                # Select X (Independent Variable) - No Type Constraint
                x_idx = self._get_valid_value(f"Select X-axis (ID or Name): ", len(self.columns))
                if x_idx == BACK_SIGNAL: step -= 1; continue
                
                # Select Y (Dependent Variable) - [Type Guard] Must be Numeric
                while True:
                    y_idx = self._get_valid_value(f"Select Y-axis (ID or Name): ", len(self.columns))
                    if y_idx == BACK_SIGNAL: break
                    
                    col_name = self.columns[y_idx]
                    if is_numeric_col(col_name):
                        break
                    else:
                        print(f" [Error] Column '{col_name}' contains text data. Y-axis requires numeric data.")
                        print(f" Please select a numeric column (e.g. float, int).")

                if y_idx == BACK_SIGNAL: continue

                xlabel = self.columns[x_idx]
                ylabel = self.columns[y_idx]
                step += 1
            
            # 3. 数据转换 (Model Switching)
            elif step == 3:
                t_choice = None
                t_raw = None
                if graph_selected in ['Volcano','Heatmap']:
                    print(f"\n[Step 3/4] Data Transformation: Auto-skipped for {graph_selected}.")
                    model = 'linear'
                else:
                    print("\n[Step 3/4] Data Transformation (Model):")
                    print(" [1] Linear | [2] Log2 | [3] Log10 | [4] Natural Log (Ln)")
                    while True:
                        t_raw = get_user_input("Choice (1-4, Default Linear): ")
                        if t_raw == BACK_SIGNAL: 
                            step -= 1
                            break # 跳出 while True 
                        
                        t_choice = t_raw.strip() or "1"
                        transform_map = {"1":"linear","2":"log2","3":"log10","4":"ln"}
                        if t_choice in transform_map:
                            model = transform_map.get(t_choice, "linear")
                            break
                        print("(!) Invalid choice. Please select 1-4.")
                
                if t_raw == BACK_SIGNAL: continue # 跳到外层 step 循环
                step += 1
        
            # 4. 元数据
            elif step == 4:
                print("\n[Step 4/4] Metadata:")
                # Title: 默认不要，输入 y 开启
                title_raw = get_user_input(f"Show Title? (y/n, default: n): ")
                if title_raw == BACK_SIGNAL: step -= 1; continue
                
                title_q = title_raw.strip().lower() or 'n'
                title = None
                if title_q == 'y':
                    title_raw = get_user_input(f"Enter Title (default: {ylabel} Analysis)")
                    if title_raw == BACK_SIGNAL: continue # Re-ask "Show Title?"
                    title = title_raw.strip() or f"{ylabel} Analysis"

                # Legend: 默认不要，输入 y 开启
                legend_raw = get_user_input(f"Show Legend? (y/n, default: n): ")
                if legend_raw == BACK_SIGNAL: step -=1; continue # Go back to Title section (re-loop Step 4)
                
                legend_q = legend_raw.strip().lower() or 'n'
                legend = False
                legend_name = None
                if legend_q == 'y':
                    legend = True
                    legend_name_raw = get_user_input(f"Enter Legend Name (default: {ylabel})")
                    if legend_name_raw == BACK_SIGNAL: continue # Re-ask "Show Legend?"
                    legend_name = legend_name_raw.strip() or ylabel
                step += 1

        # 构造内部配置对象
        config = {
            "graph": graph_selected,
            "xlabel": xlabel,
            "ylabel": ylabel,
            "title": title,
            "legend": legend,
            "legend_name": legend_name,
            "model": model,

            "_mapping": {
                "independent_variable": xlabel,
                "dependent_variable": ylabel
            }
        }

        print("\n" + "="*40)
        print("Configuration captured! Ready to analyze.")
        print("-"*40 + "\n")

        return config