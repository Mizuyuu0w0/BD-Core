import PyInstaller.__main__
import os
import shutil

# Mac 版应用名称
APP_NAME = "BioData_v1_2"

# 1. 清理环境
print("Cleaning previous Mac build artifacts...")
if os.path.exists('build'): shutil.rmtree('build')
if os.path.exists('dist'): shutil.rmtree('dist')
if os.path.exists(f"{APP_NAME}.spec"):
    os.remove(f'{APP_NAME}.spec')

print(f"Starting Mac build process for {APP_NAME}...")

# 2. 执行 PyInstaller 打包指令 (针对 Mac 优化)
PyInstaller.__main__.run([
    'main.py',
    f'--name={APP_NAME}',
    '--onefile',                     # 生成单执行文件
    '--console',                     # CLI Tool: Must rely on Terminal for input/output
    '--clean',
    '--noconfirm',
    
    # 隐藏依赖补丁
    '--hidden-import=scipy.special._ufuncs',
    '--hidden-import=scipy.special._cdflib',
    '--hidden-import=scipy.spatial.transform._rotation_groups',
    '--hidden-import=pandas._libs.tslibs.base',
    '--hidden-import=openpyxl',
    '--hidden-import=xlsxwriter',    # Excel Formatting dependency
    '--hidden-import=seaborn',
    '--hidden-import=matplotlib.backends.backend_tkagg',
    '--hidden-import=matplotlib.backends.backend_pdf',
    '--hidden-import=matplotlib.backends.backend_svg',
])

print("-" * 50)
print(f"Mac Build Success! Application is located at: dist/{APP_NAME}.app")
print("(Wait, if you used --onefile you might also see a Unix executable in dist/)")
print("-" * 50)
