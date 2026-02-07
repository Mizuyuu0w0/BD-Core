import PyInstaller.__main__
import os
import shutil

APP_NAME = "BioData v1.0"

# 1. 清理旧的构建环境 (防止缓存导致的怪异 bug)
print("Cleaning previous build artifacts...")
if os.path.exists('build'):
    shutil.rmtree('build')
if os.path.exists('dist'):
    shutil.rmtree('dist')
if os.path.exists(f"{APP_NAME}.spec"):
    os.remove(f'{APP_NAME}.spec')

print(f"Starting build process for {APP_NAME}...")

# 2. 执行 PyInstaller 打包指令
# 等同于在终端运行: pyinstaller main.py --onefile ...
PyInstaller.__main__.run ([
    'main.py',
    f'--name={APP_NAME}',
    '--onefile',
    '--console',
    '--clean',
    '--noconfirm',
    '--distpath=.', # Output to root directory

    # [关键] 强制包含科学计算库的隐藏依赖
    #这是 PyInstaller 打包 Pandas/Scipy/Matplotlib 时最容易缺少的模块
    '--hidden-import=scipy.special._ufuncs',
    '--hidden-import=scipy.special._cdflib',
    '--hidden-import=scipy.spatial.transform._rotation_groups',
    '--hidden-import=pandas._libs.tslibs.base',
    '--hidden-import=openpyxl',       # Excel 读写依赖
    '--hidden-import=xlsxwriter',     # Excel 格式化依赖
    '--hidden-import=seaborn',
    '--hidden-import=matplotlib.backends.backend_tkagg', 
    '--hidden-import=matplotlib.backends.backend_pdf',
    '--hidden-import=matplotlib.backends.backend_svg',
])

print("-" * 50)
print(f"Build Success! Executable is located at: ./{APP_NAME}.exe (Project Root)")
print("-" * 50)