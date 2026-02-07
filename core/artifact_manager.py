import os
import json
import hashlib
import time
import logging
import pandas as pd 
import matplotlib.pyplot as plt 
from pathlib import Path

logger = logging.getLogger(__name__)

class ArtifactManager:
    """
    负责管理所有文件的输出、沙箱创建和审计日志。
    支持自定义输出路径 (Output data) 和 智能命名。
    """
    def __init__(self, run_id, config=None):
        self.run_id = run_id
        self.config = config or {}
        
        # --- 统一命名策略 (Consistent Naming Strategy) ---
        # 1. 无论用户是否指定路径，文件夹本身的名字必须是描述性的
        self.timestamp = time.strftime("%d%m%Y_%H%M%S")
        
        # 提取命名元数据
        g_type = self.config.get('graph', 'Graph').capitalize()
        map_cfg = self.config.get('_mapping', {})
        ylabel = self.config.get('ylabel', map_cfg.get('dependent_variable', 'Y'))
        xlabel = self.config.get('xlabel', map_cfg.get('independent_variable', 'X'))
        
        # User Request: No underscores, use spaces
        # 仅仅移除非法字符，保留空格
        def clean(s): return str(s).replace('/', '_').replace(':', '')
        
        # 生成基于内容的文件夹名 (Space-separated with brackets for time)
        if 'box' in g_type.lower():
             folder_name = f"{g_type} Graph ({clean(ylabel)}) [{self.timestamp}]"
        elif 'scatter' in g_type.lower():
             folder_name = f"{g_type} Graph ({clean(ylabel)} against {clean(xlabel)}) [{self.timestamp}]"
        elif 'volcano' in g_type.lower():
             # Volcano uses Log2FC(x) and P-Value(y)
             folder_name = f"{g_type} Graph ({clean(ylabel)} vs {clean(xlabel)}) [{self.timestamp}]"
        elif 'heatmap' in g_type.lower():
             # Heatmap uses correlation or generic title
             folder_name = f"{g_type} Graph (Correlation Matrix) [{self.timestamp}]"
        else:
             folder_name = f"BD Result [{self.timestamp}] {self.run_id}"

        # --- 路径决策逻辑 (Path Decision Logic) ---
        # 2. 如果用户指定了 Output data，则将其作为父目录
        custom_parent = self.config.get('output_data')
        
        if custom_parent:
            # 用户指定: "MyExperiment/Day1" -> "MyExperiment/Day1/Box_Graph..."
            # 注意：用户输入可能包含引号
            clean_parent = custom_parent.strip().strip('"').strip("'")
            self.sandbox_dir = Path(clean_parent) / folder_name
            self.mode = f"Custom Nested Path ({clean_parent})"
        else:
            # 默认: 当前目录 -> "./Box Graph..."
            self.sandbox_dir = Path(folder_name)
            self.mode = "Default Descriptive Sandbox"

        # 创建目录
        self._create_sandbox()

        # 审计日志字典
        self.audit_log = {
            "RunID": self.run_id,
            "Timestamp": time.strftime("%d%m%Y_%H%M%S"),
            "OutputMode": self.mode,
            "Environment": "CLI", 
            "Operations": []
        }

    def _create_sandbox(self):
        try:
            self.sandbox_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Sandbox Created ({self.mode}): {self.sandbox_dir.absolute()}")
        except Exception as e :
            logger.error(f"Failed to create sandbox: {e}")
            raise
    
    def log_audit(self, message):
        """记录关键操作到审计日志"""
        entry = f"{time.strftime('%H:%M:%S')} - {message}"
        self.audit_log["Operations"].append(entry)
        logger.info(message)
    
    def calculate_input_hash(self, config, df):
        """计算输入数据的指纹 (Config + Data)"""
        try:
            config_str = json.dumps(config, sort_keys=True)
            data_hash = pd.util.hash_pandas_object(df).sum()
            raw_signature = f"{config_str}|{data_hash}"
            signature = hashlib.sha256(raw_signature.encode()).hexdigest()[:16]
            self.audit_log["InputHash"] = signature
            return signature
        except Exception as e:
            logger.warning(f"Hash calculation failed: {e}")
            return "HASH_FAILED"

    def save_figure(self, fig, name):
        """同时保存 PDF (Vector) 和 PNG (Preview)"""
        try:
            pdf_path = self.sandbox_dir / f"{name}.pdf"
            fig.savefig(pdf_path, format='pdf', bbox_inches='tight')
            
            png_path = self.sandbox_dir / f"{name}.png"
            fig.savefig(png_path, format='png', dpi=300, bbox_inches='tight')

            self.log_audit(f"Artifact Saved: {name} (PDF+PNG)")
            return str(pdf_path)
        except Exception as e:
            logger.error(f"Failed to save figure: {e}")
            raise
    
    def save_data(self, data_content, name):
        """
        [Upgrade] 保存多 Sheet 且带边框的 Excel (需要安装 xlsxwriter)
        Args:
            data_content: pd.DataFrame OR dict { 'SheetName': df, ... }
        """
        try:
            xlsx_path = self.sandbox_dir / f"{name}.xlsx"
            
            # 统一转为字典格式
            if isinstance(data_content, pd.DataFrame):
                data_dict = {'Data': data_content}
            else:
                data_dict = data_content

            # 使用 xlsxwriter 引擎
            with pd.ExcelWriter(xlsx_path, engine='xlsxwriter') as writer:
                for sheet_name, df in data_dict.items():
                    df.to_excel(writer, sheet_name=sheet_name, index=False)
                    
                    # 获取 formatted objects
                    workbook  = writer.book
                    worksheet = writer.sheets[sheet_name]
                    
                    # 定义黑色边框
                    border_fmt = workbook.add_format({'border': 1})
                    
                    # 给有数据的区域画格子 (conditional_format)
                    if len(df) > 0:
                        worksheet.conditional_format(0, 0, len(df), len(df.columns)-1,
                                                    {'type': 'no_errors', 'format': border_fmt})

            self.log_audit(f"Data Saved: {name}.xlsx (Sheets: {list(data_dict.keys())})")
            
        except Exception as e:
            logger.error(f"Failed to save data: {e}. Ensure xlsxwriter is installed.")

    def close(self):
        """收尾：写入最终的 audit.json"""
        audit_path = self.sandbox_dir / "audit_log.json"
        with open(audit_path, 'w', encoding="utf-8") as f:
            json.dump(self.audit_log, f, indent=2, ensure_ascii=False)
        logger.info("Session Closed. Audit Log sealed")