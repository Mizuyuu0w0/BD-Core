import sys
import argparse
import logging
import json
from pathlib import Path
import uuid
import matplotlib.pyplot as plt

from core.parser import ForgivingParser
from core.cleaner import DataCleaner
from core.artifact_manager import ArtifactManager
from core.dispatcher import PluginDispatcher
from core.wizard import AnalysisWizard
from core.style import NatureStyler
from core.utils import get_user_input, BACK_SIGNAL

# Configure Basic Logging
# Log to stderr to keep stdout clean for JSON pipe (Machine Mode constraint)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stderr)]
)

logger = logging.getLogger(__name__)

def setup_args():
    """定义 CLI 参数"""
    parser = argparse.ArgumentParser(description="BD-Core: Data Visualization Engine for Biological Science")
    parser.add_argument('--mode', choices=['human', 'api'], default='human')
    parser.add_argument('--config',type=str,help="Path to configuration file (.bd)")
    parser.add_argument('--input',type=str,help="Path to input data file (xlsx/csv)")
    return parser.parse_args()

def main():
    args = setup_args()
    NatureStyler.apply()
    
    if args.mode == 'api':
        # API 模式保持线性，不需要循环
        return

    try:
        while True:
            # --- 自动发现数据 (Data Discovery) ---
            data_path = args.input
            is_interactive_selection = False # Flag to track if user was prompted for file selection
            
            if not data_path:
                # [Smart Discovery] Scan for .xlsx/.csv, ignoring temp files (~$)
                candidates = list(Path('.').glob('*.xlsx')) + list(Path('.').glob('*.csv'))
                candidates = [f for f in candidates if not f.name.startswith('~$')]

                # [Smart Fallback] If no data in root, check 'test' folder
                if not candidates:
                    candidates = list(Path('test').glob('*.xlsx')) + list(Path('test').glob('*.csv'))
                    candidates = [f for f in candidates if not f.name.startswith('~$')]

                if not candidates:
                    logger.error("No data file (.xlsl/.csv) found in current directory")
                    break # Exit loop to trigger finally
                if len(candidates) > 1:
                    is_interactive_selection = True
                    print("\nMultiple data files detected:")
                    for i, f in enumerate(candidates):
                        print(f" [{i}] {f.name}")
                    try:
                        choice = int(get_user_input(f"Select data file (0-{len(candidates)-1}):", allow_back=False))
                        data_path = candidates[choice]
                    except (ValueError, IndexError):
                        logger.error("Invalid selection. Exiting.")
                        break # Exit loop to trigger finally
                else:
                    data_path = candidates[0]
                
                logger.info(f"Auto-detected data: {data_path}")

            # 预加载数据
            dummy_parser = ForgivingParser(None)
            raw_df = dummy_parser.smart_load_data(data_path)

            # --- 3. 配置发现或启动向导 (Config / Wizard) ---
            config_path = args.config
            config = {}
            if config_path:
                # [Explicit] 用户明确指定了配置文件
                logger.info(f"Loading config from: {config_path}")
                parser = ForgivingParser(config_path)
                config, _ = parser.parse()
            else:
                # 尝试自动寻找 .bd 文件 (测试后门)
                bd_files = list(Path('.').glob('*.bd'))
                if bd_files:
                    config_path = bd_files[0]
                    parser = ForgivingParser(config_path)
                    config, _ = parser.parse()
                else:
                    # [Default] 默认启动交互式向导 (不再自动寻找 .bd 文件)
                    logger.info("No config provided. Launching Interactive Wizard...")
                    wizard = AnalysisWizard(raw_df)
                    config = wizard.run()

                    if config is None:
                        print("\n[System] Wizard cancelled.")
                        # [Fix Infinite Loop] If we didn't ask for file selection, we MUST ask if they want to restart
                        # otherwise it loops infinitely on the same file.
                        if not is_interactive_selection:
                            retry = get_user_input("Restart wizard? (y/n, default: n)", allow_back=False)
                            if retry.lower() != 'y':
                                break # Exit main loop
                        
                        print("\n[System] Returning to file selection...")
                        continue # 返回到文件选择起点
                '''
                # 批注: [UNSAFE 协议实现]
                # 将解析出的 "UNSAFE: ALLOW_SMALL_SAMPLE" 等标记注入到 config 字典。
                # 这样下游的 Plugin 看到这个标记，就会放宽校验标准。
                if unsafe_flags:
                    config['_unsafe_flags'] = unsafe_flags
                    logger.warning(f"Unsafe Flags Injected: {unsafe_flags}")
                '''
             # [UX Fix] 自动修正 Y轴 标签以反映转换
            model = config.get('model','linear')
            if model != 'linear' and config.get('ylabel'):
                config['ylabel'] = f'{config['ylabel']} ({model})'

            # --- 4. 清洗与转换 pipeline ---
            cleaner = DataCleaner(raw_df, config)
            clean_df = cleaner.run()
    
            # --- 5. 环境初始化 (Initialization) ---
            # 生成唯一的 RunID，创建沙箱文件夹
            # 计算输入数据的 SHA256 指纹，确保实验可复现 (Reproducibility)
            run_id = str(uuid.uuid4())[:8]
            am = ArtifactManager(run_id, config)
            am.calculate_input_hash(config, clean_df)

            # --- 6. 分发 (Dispatching) ---
            # 将清洗后的数据交给 Dispatcher，由它唤醒对应的 Plugin (如 Boxplot)
            logger.info("Generating Result...")
            dispatcher = PluginDispatcher(am)
            dispatcher.dispatch(config, clean_df)

            # --- 7. 预览 (Reviewing) ---
            # [Single Run Mode] No blocking preview.
            # print("\n" + "-"*30)
            # print("Close the plot window to finish.")
            # print("-" * 30 + "\n")
            
            # --- 8. 收尾 (Closing) ---
            # 保存审计日志，关闭会话
            am.close()
            logger.info(f"Process Complete. RunID: {run_id}")

            # [UX Upgrade] Loop on same file
            # Ask user if they want to analyze the SAME file again
            print("\n" + "="*40)
            break
        
    except Exception as e:
        # 批注: 错误处理策略 (Error Handling Strategy)
        # Human Mode: 打印完整的堆栈跟踪 (traceback)，方便开发者调试。
        logger.exception("Critical Error during execution")

        # API Mode: 只能返回一行 JSON 错误信息。
        # 绝对不能打印堆栈，否则前端解析器会因为收到非 JSON 数据而报错。
        if args.mode == 'api':
            print(json.dumps({"status":"error","message":str(e)}))
    
    finally:
        # [EXE UX] Prevent terminal from closing immediately on error or exit
        if getattr(sys, 'frozen', False):
            print("\n" + "="*40)
            input("[Program Finished] Press Enter to exit...")
            print("="*40)

if __name__ == '__main__':
    main()