# dbsnotebook-fmt
A simple formatting script for databricks notebooks to jupyter notebooks and back using the [`jupytext` package](https://github.com/mwouts/jupytext).


## Software requirements

The following `python` packages should be installed to use the script:

- `argparse`
- `jupytext`

The code was implemented and tested using python version 3.12

## Usage

The script converts python files (must end in `.py` to work) which are formatted as databricks notebooks to jupyter notebooks and vice-versa. The script is simply a wrapper around [`jupytext`](https://github.com/mwouts/jupytext) which makes it work for databricks notebooks. The file to format can simply be added as a positional argument:

```bash
python parse_dbnotebook.py your_databricks_notebook.py
```

This will create a corresponding jupyter notebook with the filename `your_databricks_notebook.ipynb` in the current working directory. Alternatively, an output filepath can be provided using the `--output` or `-o` option. The same command works with passing an `.ipynb` file as argument, which results in a corresponding `.py` file to be stored in the current working directory.