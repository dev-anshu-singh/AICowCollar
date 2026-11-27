import os
import sys
import nbformat
from nbclient import NotebookClient

nb_path = os.path.join('cow_activity_experiments', 'cow_activity_classification.ipynb')
print(f"Loading notebook from: {nb_path}")

with open(nb_path, 'r', encoding='utf-8') as f:
    nb = nbformat.read(f, as_version=4)

client = NotebookClient(
    nb,
    timeout=1200,
    kernel_name='python3'
)

print("Executing all notebook cells in cow_activity_experiments environment...")
client.execute(cwd='cow_activity_experiments')

print("Saving executed notebook with all outputs embedded...")
with open(nb_path, 'w', encoding='utf-8') as f:
    nbformat.write(nb, f)

print("[SUCCESS] Notebook executed and updated successfully!")
