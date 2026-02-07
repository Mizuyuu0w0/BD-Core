import pandas as pd 
import numpy as np 
import re 
import logging

# 获取 logger，遵循 logging 本地化原则
logger = logging.getLogger(__name__)

class DataCleaner:
    """
    BioDiagnosis 核心清洗器 (Opinionated Sanitizer)
    
    Philosophy: 
    "Dirty in, Clean out." 
    不询问用户，直接执行最严格的清洗标准。
    """

    def __init__(self, df: pd.DataFrame, config: dict = None):
        # 永远不要修改原始数据引用，创建深拷贝
        self.df = df.copy()
        self.config = config or {}
    
    def run(self) -> pd.DataFrame:
        """
        执行完整的清洗流水线。
        Order: Headers -> Values -> Shape (Melt) -> Types
        """
        logger.info("Starting Data Sanitization Pipeline...")

        # 1. [NEW] 模型转换 (Log2, Log10, etc.)
        self._apply_transformation()

        # 1. 清洗表头 (标准化)
        self._sanitize_headers()
        # 2. 清洗数值 (正则提取 & ND处理)
        self._sanitize_values()
        # 3. 自动融合 (重塑形状) - 必须在数值清洗后进行，以准确判断列类型
        self._auto_melt_strategy()
        # 4. 类型强制 (最后防线)
        self._final_type_enforcement()

        return self.df

    def _apply_transformation(self):
        """[NEW] 实现模型切换逻辑 (安全版: 仅转换 Y 轴)"""
        model = self.config.get('model','linear').lower()
        if model == "linear": return

        logger.info(f"Applying {model} transformation to data.")

        # 尝试获取 Y 轴列名 (Wizard 模式下一定有)
        target_col = self.config.get('_mapping', {}).get('dependent_variable')

        # 核心逻辑：如果是数值，则应用数学转换
        def math_op(x):
            try:
                val = float(x)
                if val <= 0: return np.nan
                if model == 'log2': return np.log2(val)
                if model == 'log10': return np.log10(val)
                if model == 'ln': return np.log(val)
            except:
                return x
            return x

        if target_col and target_col in self.df.columns:
            logger.info(f'Targeting specifice column for transformation: {target_col}')
            self.df[target_col] = self.df[target_col].map(math_op)
        else:
            logger.warning('Global transformation applied (Risky).')
            # 对整个 DataFrame 应用转换（此时表头还没清洗，所以用 map）
            self.df = self.df.map(math_op)
    
    def _sanitize_headers(self):
        """
        Header 清洗逻辑 - 强制小写、去空格、下划线连接
        Example: "Conc. (mg/ml)" -> "conc._(mg/ml)"
        """
        logger.debug("Sanitizing Headers...")

        # 转换为字符串 -> 去除首尾空格 -> 转小写 -> 把中间的空白变成下划线
        self.df.columns = (self.df.columns
                           .astype(str)
                           .str.strip()
                           .str.lower()
                           .str.replace(r'\s+','_',regex=True))

    def _sanitize_values(self):
        """
        数值清洗逻辑 (最关键部分)
        涵盖: 单位剥离, ND处理, 科学记数法支持
        """
        logger.debug("Sanitizing Values (Regax Deep Clean)...")

        # 预编译正则以提升性能 (Scientific Notation Supported)
        # ^ : Start
        # [-+]? : Optional Sign
        # \d*\.?\d+ : Numbers (supports 10, 10.5, .5)
        # ([eE][-+]?\d+)? : Optional Exponent (e-5, E+10)
        num_pattern = re.compile(r'^([-+]?\d*\.?\d+([eE][-+]?\d+)?)')

        def clean_cell(x):
            if pd.isna(x):
                return x
            
            s = str(x).strip()

            # [Opinionated] 处理生物学常见的 "Not Detected"
            # 匹配 ND, N.D., nd, n.d.
            if re.match(r'(?i)^n\.?d\.?$', s):
                return np.nan

            # [Fast Path] 尝试直接转换
            try:
                return float(s)
            except ValueError:
                pass
                
            # [Unsafe Extraction] 尝试提取混杂文本中的数字
            # Example: "1.5 mg/mL" -> 1.5
            # Example: "1.2e-3 A.U." -> 0.0012
            match = num_pattern.search(s)
            if match:
                try:
                    return float(match.group(1))
                except ValueError:
                    return np.nan # 提取出的字符串仍无法转float (极罕见)
            
            # 如果都失败了，说明它是真正的文本 (如分组标签 "Control")
            return s
        
        # Apply map (Performance Warning: 在大数据集上较慢，但为保证质量必须如此)
        self.df = self.df.map(clean_cell)

    def _auto_melt_strategy(self):
        """
        Auto-Melt (自动融合策略)
        判定是否为 Excel 宽表 (Wide Format)，如果是，强制转换为 Tidy Data (Long Format)。
        """
        # [Heuristic Update 2.0] "Numeric Leaning" Strategy
        # 即使被 Pandas 认为是 Object 列，只要其中大部分 (>50%) 是数字，就视为数值列。
        def is_numeric_leaning(col):
            if pd.api.types.is_numeric_dtype(col):
                return True
            # 尝试强制转换，计算有效数字比例
            num_counts = pd.to_numeric(col, errors='coerce').notna().sum()
            total_counts = len(col)
            return (num_counts / total_counts) > 0.5 if total_counts > 0 else False

        numeric_cols = [c for c in self.df.columns if is_numeric_leaning(self.df[c])]
        object_cols = [c for c in self.df.columns if c not in numeric_cols]

        # [Scatter SKIP] 如果是散点图，通常需要 X vs Y 的宽表格式，跳过 Auto-Melt
        graph_type = self.config.get('graph', '').lower()
        if 'scatter' in graph_type or 'heatmap' in graph_type:
            logger.info(f"Skipping Auto-Melt for {graph_type} graph (requires Wide Data).")
            return

        # 只有当疑似数字列的数量是文本列的2倍以上，且没有明确的 'group' 列时，才认为是宽表。
        is_wide = (len(numeric_cols) > len(object_cols) * 2) and ('group' not in object_cols)

        if is_wide:
            logger.info(f"Detecting Wide Data Format ({len(numeric_cols)} num vs {len(object_cols)} obj).") 
            logger.info("Initiating Auto-Melt...")

            # 假设所有非数字列都是 ID 变量
            id_vars = list(object_cols)
            if not id_vars:
                # 极端情况：全是数字 (如矩阵)，生成索引列作为 ID
                self.df['index'] = self.df.index
                id_vars = ['index']

            # 执行 Melt
            self.df = self.df.melt( id_vars=id_vars,
                                    var_name='variable',
                                    value_name='value')

            # 清洗 Melt 后的 variable 列 (防止奇怪的列名残留)
            self.df['variable']= self.df['variable'].astype(str).str.strip()

            logger.info(f"Data Melted. New Shape: {self.df.shape}")

    def _final_type_enforcement(self):
        """
        类型强制 (Type Enforcement)
        确保核心列的类型正确，为 Plugin 做好准备。
        """
        # 1. Value 列必须是数字
        if 'value' in self.df.columns:
            self.df['value'] = pd.to_numeric(self.df['value'],errors='coerce')
        
        # [Fix] 强制 Config 中指定的因变量 (Dependent Variable) 为数字
        # 防止 Boxplot 收到字符串导致的 crash
        target_y = self.config.get('_mapping', {}).get('dependent_variable')
        if target_y:
            # 必须应用与 _sanitize_headers 相同的变换逻辑，才能找到列
            # Lowercase + Spaces to Underscores
            target_y_clean = str(target_y).strip().lower()
            target_y_clean = re.sub(r'\s+', '_', target_y_clean)

            if target_y_clean in self.df.columns:
                 # [Safety Fix] 只有当列看起来像数字时，才进行强制转换
                 # 否则，如果用户把 "Group" 选成了 Y 轴，原来的逻辑会把整列变成 NaN -> 0 Rows
                 # 除非用户明确指定了数学模型 (Log/Ln)，此时必须强制转换
                 is_transform = self.config.get('model', 'linear') != 'linear'
                 
                 # 复用之前的 is_numeric_leaning 逻辑 (Wrapper for local scope)
                 def check_numeric(col):
                     try: 
                        # 1. Strict conversion
                        if pd.to_numeric(col, errors='coerce').notna().mean() > 0.5: return True
                        
                        # 2. [Unit Support] Check if values start with numbers (e.g. 10kg)
                        valid_series = col.dropna().astype(str)
                        if len(valid_series) == 0: return False
                        return valid_series.str.match(r'^\s*[-+]?\.?\d').mean() > 0.5
                     except: return False

                 if is_transform or check_numeric(self.df[target_y_clean]):
                     # [CRITICAL] 这里必须用 _sanitize_values 里的强力清洗逻辑
                     # 简单的 pd.to_numeric 会把 "10kg" 变成 NaN
                     # 所以我们需要手动提取数字，再转换
                     
                     # 定义临时提取函数 (复用 _sanitize_values 逻辑)
                     num_pattern = re.compile(r'^([-+]?\d*\.?\d+([eE][-+]?\d+)?)')
                     def extract_num(x):
                         s = str(x).strip()
                         # 尝试直接转
                         try: return float(s)
                         except: pass
                         # 尝试正则提取
                         match = num_pattern.search(s)
                         if match:
                             try: return float(match.group(1))
                             except: pass
                         return np.nan

                     self.df[target_y_clean] = self.df[target_y_clean].map(extract_num)
                 else:
                     logger.warning(f"Target Y '{target_y_clean}' appears to be categorical. Skipping numeric enforcement.")
                     
                 # 更新 Config 中的映射
                 target_y = target_y_clean

        # 2. 确保存在 'group' 列 (Plugin 依赖此名)
        if 'group' not in self.df.columns:
            # [Scatter SKIP] 散点图不需要强制 group 列，且改名会破坏 x 轴
            if 'scatter' in self.config.get('graph', '').lower():
                logger.info("Skipping Group Assignment for Scatter plot.")
                return

            # [Priority 1] 如果 Melt 产生了 'variable' 列，直接用它作为 group
            if 'variable' in self.df.columns:
                logger.info("Using 'variable' column as 'group'")
                self.df.rename(columns={'variable':'group'}, inplace=True)
            
            # [Priority 2] 寻找其他文本列
            else:
                obj_cols = self.df.select_dtypes(include=['object','category']).columns
                if len(obj_cols) > 0:
                    target_col = obj_cols[0]
                    # [Safety Check] 防止把 Y 轴误认为是 Group
                    if target_col != target_y:
                        logger.info(f"Auto-assigning column '{target_col}' as a 'group'")
                        self.df.rename(columns={target_col: 'group'}, inplace=True)
