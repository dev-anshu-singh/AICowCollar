with open('cow_activity_experiments/build_notebook.py', 'r', encoding='utf-8') as f:
    c = f.read()

c = c.replace('code("""', 'code(r"""')
c = c.replace('md("""', 'md(r"""')

with open('cow_activity_experiments/build_notebook.py', 'w', encoding='utf-8') as f:
    f.write(c)

print('Updated build_notebook.py successfully!')
