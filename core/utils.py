import sys

BACK_SIGNAL = "__BACK__"

def get_user_input(prompt, allow_back=True):
    """
    全局输入处理器：
    - 输入 'q'/'quit'/'exit' -> 直接退出程序
    - 输入 'b'/'back' -> 返回 BACK_SIGNAL
    - 其他 -> 返回原始输入字符串
    """
    suffix = " (or 'b' to back, 'q' to quit): " if allow_back else " (or 'q' to quit):"

    while True:
        try:
            val = input(f"{prompt}{suffix}").strip()
            if val.lower() in ['q','exit','quit']:
                print("\n[System] Exiting BioData... Goodbye!")
                sys.exit(0)
        
            if allow_back and val.lower() in ['b','back']:
                return BACK_SIGNAL

            return val
        except EOFError:
            sys.exit(0)