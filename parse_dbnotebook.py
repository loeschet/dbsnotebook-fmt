#!/usr/bin/env python3

import argparse
import sys
import re
import jupytext
from typing import List


def add_linebreak_after_percent_words(text: str) -> str:
    """
    Add an extra line break after words starting with '%' in the given text.

    This function finds all occurrences of words starting with '%' followed by
    any content up to the next newline or end of the string. It then adds an
    extra line break after each such occurrence.

    Parameters
    ----------
    text : str
        The input text to process.

    Returns
    -------
    str
        The processed text with extra line breaks added after words
        starting with '%'.
    """
    pattern = r"(%[a-zA-Z]+.*?)(\n|$)"

    def add_newline(match: re.Match) -> str:
        return match.group(1) + "\n\n"

    return re.sub(pattern, add_newline, text, flags=re.DOTALL)


def parse_dbnotebook(file_str: List[str]) -> str:
    """
    Parse a Databricks notebook file and convert it to a Jupyter-like format.

    This function takes a Databricks notebook file content as a list of strings
    and converts it to a format similar to Jupyter notebooks. It processes
    each block of the file, handling markdown and code cells differently.

    Parameters
    ----------
    file_str : List[str]
        A list of strings, where each string represents a block in the
        Databricks notebook file.

    Returns
    -------
    str
        A single string representing the converted notebook content in a
        Jupyter-like format.
    """
    full_str = ""

    for idx, blck in enumerate(file_str):
        if idx == 0:  # special handling of first line
            blck = "\n" + "\n".join(blck.split("\n", 3)[1:])

        if "# MAGIC" in blck:
            tmp_str = "# %% [markdown]" + blck + "\n"
            tmp_str = tmp_str.replace("# MAGIC %md\n", "")
            tmp_str = tmp_str.replace("# MAGIC ", "# ")
            tmp_str = add_linebreak_after_percent_words(tmp_str)
            full_str += tmp_str

        else:
            full_str += "# %%" + blck + "\n"

    return full_str


def process_magic_commands(text: str) -> str:
    """
    Process magic commands in Databricks notebook text.

    This function takes a string containing Databricks notebook content and
    processes magic commands, specifically handling markdown cells indicated
    by "# MAGIC %md". It ensures that all lines within a markdown cell are
    properly prefixed with "# MAGIC".

    Parameters
    ----------
    text : str
        A string containing the content of a Databricks notebook.

    Returns
    -------
    str
        A string with the processed content, where all lines within markdown
        cells are correctly prefixed with "# MAGIC".
    """
    lines = text.split("\n")
    result = []
    i = 0
    while i < len(lines):
        if lines[i].strip() == "# MAGIC %md":
            result.append(lines[i])
            i += 1
            while i < len(lines) and not lines[i].startswith(
                "# COMMAND ----------"
            ):
                if lines[i].startswith("#"):
                    result.append("# MAGIC" + lines[i][1:])
                else:
                    result.append(lines[i])
                i += 1
        else:
            result.append(lines[i])
            i += 1

    return "\n".join(result)


def split_script(file_content: str) -> List[str]:
    """
    Split a Databricks notebook script into blocks.

    This function takes the content of a Databricks notebook as a single string
    and splits it into blocks. Each block is separated by the Databricks
    command separator "# COMMAND ----------".

    Parameters
    ----------
    file_content : str
        A string containing the entire content of a Databricks notebook script.

    Returns
    -------
    List[str]
        A list of strings, where each string represents a block of code or
        markdown from the original script, excluding the command separators.
    """
    lines = file_content.split("\n")
    result = []
    current_block = []

    for line in lines:
        if line.strip() == "# COMMAND ----------":
            if current_block:
                result.append("\n".join(current_block))
                current_block = []
        else:
            current_block.append(line)

    if current_block:
        result.append("\n".join(current_block))

    return result


def parse_jupyter_notebook(file_content: str) -> str:
    """
    Convert a Jupyter notebook content to Databricks notebook format.

    This function takes the content of a Jupyter notebook as a string and
    converts it to the Databricks notebook format. It processes markdown
    and code cell delimiters, handles magic commands, and adjusts the
    overall structure to match Databricks notebook conventions.

    Parameters
    ----------
    file_content : str
        A string containing the content of a Jupyter notebook.

    Returns
    -------
    str
        A string representing the converted content in Databricks notebook
        format.
    """
    file_content = "# Databricks notebook source\n" + file_content
    file_content = file_content.replace(
        "# %% [markdown]\n", "# COMMAND ----------\n\n# MAGIC %md\n"
    )
    file_content = file_content.replace("# %%\n", "# COMMAND ----------\n\n")
    file_content = file_content.replace("#\n", "")
    file_content = process_magic_commands(file_content)
    file_content = file_content.replace("\n\n\n", "\n\n")
    file_content = file_content.replace(
        "# Databricks notebook source\n# COMMAND ----------\n\n",
        "# Databricks notebook source\n",
    )
    return file_content


def main():
    parser = argparse.ArgumentParser(
        description=("Split a Python script based on "
                     "'# COMMAND ----------' delimiters.")
    )
    parser.add_argument("file", help="Path to the Python file to be split")
    parser.add_argument("--output", "-o", default=None, help="Path to the output file")

    args = parser.parse_args()

    try:
        with open(args.file, "r") as file:
            file_content = file.read()
    except FileNotFoundError:
        print(f"Error: File '{args.file}' not found.", file=sys.stderr)
        sys.exit(1)
    except IOError:
        print(f"Error: Could not read file '{args.file}'.", file=sys.stderr)
        sys.exit(1)

    if args.file.endswith(".py"):
        print("Parsing Databricks notebook to Jupyter notebook")
        assert (
            "# Databricks notebook source" in file_content
        ), "This script does not appear to be a Databricks notebook."
        if args.output is not None:
            output_file = args.output
        else:
            output_file = args.file.replace(".py", ".ipynb")
        split_blocks = split_script(file_content)
        parsed_nb = parse_dbnotebook(split_blocks)
        nb = jupytext.reads(parsed_nb, fmt="py:percent")
        jupytext.write(nb, output_file)
    elif args.file.endswith(".ipynb"):
        print("Parsing Jupyter notebook to Databricks notebook")
        if args.output is not None:
            output_file = args.output
        else:
            output_file = args.file.replace(".ipynb", ".py")
        nb = jupytext.read(args.file)
        nb_str = jupytext.writes(nb, fmt="py:percent")
        with open(output_file, "w") as file:
            file.write(parse_jupyter_notebook(nb_str))
    else:
        raise ValueError("File must be a Python script or Jupyter notebook.")


if __name__ == "__main__":
    main()
