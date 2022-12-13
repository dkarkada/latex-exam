# latex-exam
Transpile an exam in .exam format into LaTeX.

## Why I made this
Making exams in LaTeX can be painful and tedious. I wrote this tool to expedite the formatting process. It reads your input `.exam` file, and produces a pdf of the exam and answer key in LaTeX.

## Installation
### Linux
Clone the repo into a directory of your choice. Make `~/bin/` and ensure it is in your PATH (e.g. add `export PATH="$PATH:~/bin"` to your `.bashrc` or `.profile`). Then create a symbolic link in `~/bin/` to examtex:

```
ln -s file/to/repo/examtex ~/bin/examtex
chmod +x ~/bin/examtex
source ~/.bashrc
```

and that should be that. 

### Windows
I use WSL and follow the steps above.

### macOS
Idk how/if it works on any other operating systems.

## How to use it
This tool requires python 3 to produce the .tex files, and latexmk (which should come with most TeX distributions) to then produce the pdf.

`examtex` is an executable python script which takes arguments

```
examtex -option filepath/filename.exam
```

and produces `filename-EXAM.tex` and `filename-KEY.tex` in the same directory. The available options are:

* -p: will create `filename-EXAM.pdf` and `filename-KEY.pdf`
* -c: will create `filename-EXAM.pdf` and `filename-KEY.pdf` and clean up the auxiliary files.

## Syntax Highlighting

In VS Code (a popular [editor](https://code.visualstudio.com/)), you can get syntax highlighting by installing the `exam` extension from the [marketplace](https://marketplace.visualstudio.com/items?itemName=dkarkada.exam).

## Making `.exam` files
A tutorial exam is provided in `docs/tutorial/tutorial.exam`. A full example is in `docs/example/`. Exams are organized into sections, each containing modules. A full tour of the expected `.exam` file format can be found in the documentation and tutorial.

