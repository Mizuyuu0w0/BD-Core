import re
import pandas as pd
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class ForgivingParser:
    """
    Parses configuration with a forgiving strategy for formatting errors.
    Target Audience: Bio students who might make formatting errors.
    """
    
    def __init__(self, config_path):
        self.config_path = config_path
        self.config = {'_mapping': {}}
        self.unsafe_flags = []
    
    def parse(self):
        """
        Main parsing logic.
        """
        if not Path(self.config_path).exists():
            raise FileNotFoundError(f"Config file not found: {self.config_path}")

        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            for line in lines:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                # Check for UNSAFE flags
                if line.upper().startswith("UNSAFE:"):
                    self._extract_unsafe_flag(line)
                    continue
                
                # Parse Key-Value pairs
                # Example: "Graph: Box" or "graph = box"
                # Split by first valid delimiter (: or =)
                parts = re.split(r'[:=]', line, maxsplit=1)
                if len(parts) == 2:
                    key = self._normalize_key(parts[0])
                    value = parts[1].strip()
                    
                    # [DSL] Check for mapping syntax: {ColumnName}
                    if value.startswith('{') and value.endswith('}'):
                        real_col = value[1:-1].strip()
                        self.config['_mapping'][key] = real_col
                        # Also store raw value for reference
                        self.config[key] = real_col
                    else:
                        self.config[key] = value
                else:
                    logger.warning(f"Skipping unparseable line: {line}")
                    
            return self.config, self.unsafe_flags

        except Exception as e:
            logger.error(f"Parsing Error: {e}")
            raise

    def _normalize_key(self, key_str):
        """
        Normalize keys: Strip whitespace, lowercase, replace space with underscore.
        Example: " Graph: " -> "graph"
        Example: "Independent Variable" -> "independent_variable"
        """
        return key_str.strip().lower().replace(" ", "_")

    def _extract_unsafe_flag(self, line):
        """
        Store UNSAFE flags for liability transfer.
        """
        flag = line.split(":", 1)[1].strip()
        logger.warning(f"UNSAFE FLAG DETECTED: {flag}")
        self.unsafe_flags.append(flag)

    def smart_load_data(self, file_path, independent_var_name=None):
        """
        Smart-Load: Scan first 10 rows. 
        The row containing the Independent variable name is the Header.
        """
        # MVP Implementation: Just load normally for now, full logic to be implemented.
        # This is a placeholder for the logic described:
        # "Scan first 10 rows of data file. The row containing the Independent variable name is the Header."
        
        try:
            # Basic loading fallback
            if str(file_path).endswith('.csv'):
                df = pd.read_csv(file_path)
            else:
                df = pd.read_excel(file_path)
            return df
        except Exception as e:
            logger.error(f"Data Load Error: {e}")
            raise
