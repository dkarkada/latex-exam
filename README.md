# latex-exam
Transpile an exam in .exam format into LaTeX.

## Why I made this
Making exams in LaTeX can be painful and tedious. I wrote this tool to expedite the formatting process. It reads your input `.exam` file, and produces a pdf of the exam and answer key in LaTeX.

## Installation
### On Ubuntu
Clone the repo into a directory of your choice. Create a symbolic link in `~/bin/` to examtex:

```
ln -s file/to/repo/examtex ~/bin/examtex
chmod +x ~/bin/examtex
source ~/.bashrc
```

and that should be that.

### On anything else
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

### Sublime 

If you're writing your exams in Sublime (a popular [text editor](https://www.sublimetext.com/)), you can get some sweet syntax highlighting by putting `Exam.sublime-syntax` in the appropriate directory (on Ubuntu: `~/.config/sublime-text-3/Packages/User/`). You can get a build system by putting `Exam.sublime-build` in the same directory; then using ctrl-b will automatically run

```
examtex -c $file
```
for the current file.

### VS Code

In VS Code (another popular [editor](https://code.visualstudio.com/)), you can get syntax highlighting by installing the `exam` folder in the appropriate directory (on Ubuntu: `~/.vscode/extensions/`). Unfortunately, setting up the build system was too tricky and I didn't figure out how to make it work so you'll have to use the terminal :( 

## Making `.exam` files
A sample exam is provided in `tutorial/sample.exam`.  Exams are organized into sections, each containing modules. Sections and modules are headed by a tag: `[Section]` represents the start of a new section, and `[FRQ]` represents the start of a module for free-response questions.

A full tour of the expected `.exam` file format can be found in the documentation and tutorial.

