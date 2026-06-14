import PyInstaller.__main__
import os
import sys

# Define base path
base_path = os.path.abspath(".")

# Define assets to include (format: 'source;destination')
# On Windows, separator is ';'
assets = [
    ('templates', 'templates'),
    ('static', 'static'),
    ('moodie_model.pkl', '.'),
    ('moodie_labels.pkl', '.'),
]

# Construct add-data arguments
data_args = []
for src, dst in assets:
    if os.path.exists(os.path.join(base_path, src)):
        data_args.extend(['--add-data', f'{src}{os.pathsep}{dst}'])

# PyInstaller command
params = [
    'app.py',
    '--name=Moodie_Foodie_Final',
    '--onefile',
    '--windowed',
    '--noconfirm',
    '--clean',
    '--hidden-import=food_data',
    '--hidden-import=sklearn.ensemble',
    '--hidden-import=sklearn.preprocessing',
    '--hidden-import=sklearn.compose',
    '--hidden-import=sklearn.pipeline',
    '--hidden-import=sklearn.utils._typedefs',
    '--hidden-import=sklearn.utils._cython_blas',
    '--hidden-import=sklearn.neighbors._typedefs',
    '--hidden-import=sklearn.neighbors._partition_nodes',
    '--hidden-import=sklearn.tree._utils',
    *data_args
]

print(f"Starting build with params: {params}")
PyInstaller.__main__.run(params)
print("Build complete! Check the 'dist' folder for Moodie_Foodie_Final.exe")
