import numpy as np
import re
import sys
import os
import random
import math


def compile_error(err, traceback=None):
    """Does this really need a docstring."""
    print(err, file=sys.stderr)
    if traceback:
        print("\t", traceback)
    sys.exit(1)


def latexify(line):
    """Replace LaTeX-sensitive characters with LaTeX counterparts.
    Returns modified line."""
    line = line.replace("%", "\\%")
    # search for double quoted substrings, replace with ``''
    match = re.search("\"[^\"]*\"", line)
    while match:
        repl = "``{}''".format(match.group(0)[1:-1])
        line = line[:match.start()] + repl + line[match.end():]
        match = re.search("\"[^\"]*\"", line)
    # search for single quoted substrings, replace with `'. Capture
    # surrounding whitespace
    match = re.search("\\s'[^']+'\\s", line)
    while match:
        repl = "`{}'".format(match.group(0)[2:-2])
        line = line[:match.start()+1] + repl + line[match.end()-1:]
        match = re.search("\\s'[^']+'\\s", line)
    # custom bold and italics syntax
    line = re.sub(r"\\i\s*{", r"\\textit{", line)
    line = re.sub(r"\\b\s*{", r"\\textbf{", line)
    return line


def process_options(content):
    options = {}
    for line in content:
        try:
            key, val = line.split("::")
        except ValueError:
            compile_error("Options must have 'key:: value' structure.", line)
        key = key.strip().lower()
        val = [x.strip() for x in val.strip().split(";;")]
        options[key] = val
    return options


class Section:

    def __init__(self, lines):
        sep = np.flatnonzero([re.match("-----", l) for l in lines])
        if sep.size != 0:
            sep = sep[0]
            self.options = process_options(lines[:sep])
            self.lines = lines[sep+1:]
        else:
            self.options = {}
            self.lines = lines
        self.content = []

    def gobble(lines):
        module_ptrn = r"(?i){(image|text|latex)}\s*$"
        bang_ptrn = r"(?i)\s*!(newpage|gap|newcol|hrule)"
        cont = lines[0]
        if re.match(module_ptrn, cont):
            module_type = cont.strip().lower()[1:-1]
            end = 1
            while end < len(lines) and re.match(r"\s", lines[end]):
                end += 1
            if end == 1:
                compile_error("Empty module.", cont)
            cont = lines[1:end]
            if module_type == "image":
                return Image(cont), lines[end:]
            elif module_type == "text":
                return Text(cont), lines[end:]
            elif module_type == "latex":
                return Latex(cont), lines[end:]
        elif re.match(bang_ptrn, cont):
            return Bang(cont), lines[1:]
        return None, lines

    def to_tex(self):
        return ""

    def ans_sheet_tex(self):
        return ""


class Cover(Section):

    def __init__(self, lines):
        Section.__init__(self, lines)
        lines = self.lines
        while lines:
            cont, lines = Cover.gobble(lines)
            self.content.append(cont)

    def gobble(lines):
        cont, lines = Section.gobble(lines)
        if cont:
            return cont, lines
        try:
            key, val = lines[0].split('::')
        except ValueError:
            compile_error("Error in Cover. Each line must have exactly\
                one double colon.", lines[0])
        val = [v.strip() for v in val.split(";;")]
        cont = (key.strip().lower(), val)
        return cont, lines[1:]

    def to_tex(self):
        tex = []
        for cont in self.content:
            if type(cont) == tuple:
                key, val = cont
                if key == "title":
                    title = latexify(val[0])
                    tex.append("\\begin{center}")
                    tex.append("\t\\par\\noindent\\textbf{{\\Huge {}}}"
                               .format(title))
                    tex.append("\\end{center}")
                if key == "subtitle":
                    subtitle = latexify(val[0])
                    tex.append("\\begin{center}")
                    tex.append("\t\\par\\noindent\\textbf{{\\large {}}}"
                               .format(subtitle))
                    tex.append("\\end{center}")
                if key == "id":
                    tex.append("\\begin{center}")
                    tex.append("\t\\par")
                    tex.append("\t\\def\\arraystretch{2}\\tabcolsep=3pt")
                    tex.append("\t\\begin{tabular}{r r}")
                    for v in val:
                        v = latexify(v)
                        tex.append("\t\t\\textbf{{{}:}}".format(v)
                                   + "& \\makebox[4in]{\\hrulefill} \\\\")
                    tex.append("\t\\end{tabular}")
                    tex.append("\\end{center}")
                if key == "author":
                    tex.append("\\begin{center}")
                    tex.append("\t\\par")
                    tex.append("\t\\def\\arraystretch{1}\\tabcolsep=3pt")
                    tex.append("\t\\begin{tabular}{r l}")
                    for i in range(len(val)):
                        v = latexify(val[i])
                        firstcol = "\\textbf{{Written by:}}" if i == 0 else ""
                        tex.append("\t\t {} & {} \\\\".format(firstcol, v))
                    tex.append("\t\\end{tabular}")
                    tex.append("\\end{center}")
            else:
                tex.append(cont.to_tex())
        return "\n".join(tex)


class Match(Section):

    def __init__(self, lines):
        Section.__init__(self, lines)
        lines = self.lines
        while lines:
            cont, lines = Match.gobble(lines)
            self.content.append(cont)

    def gobble(lines):
        cont, lines = Section.gobble(lines)
        if cont:
            return cont, lines
        try:
            ans, ques = lines[0].split('::')
        except ValueError:
            compile_error("Error in Match/TF. Each line must have exactly\
                one double colon.", lines[0])
        cont = (ques.strip().lower(), ans.strip().lower())
        return cont, lines[1:]

    def to_tex(self):
        for cont in self.content:
            if isinstance(cont, tuple):
                q, a = cont
                pass
            else:
                pass
        return ""


class TF(Section):

    def __init__(self, lines):
        Section.__init__(self, lines)
        lines = self.lines
        while lines:
            cont, lines = Match.gobble(lines)
            self.content.append(cont)

    def to_tex(self):
        for cont in self.content:
            pass
        return ""


class MC(Section):

    def __init__(self, lines):
        Section.__init__(self, lines)
        self.format_options()
        lines = self.lines
        while lines:
            cont, lines = MC.gobble(lines)
            self.content.append(cont)

    def format_options(self):
        options = self.options
        if "twocolumn" in options:
            twocol = options["twocolumn"][0].lower()
            if twocol not in ["true", "false"]:
                compile_error("Twocolumn option must be boolean.")
            options["twocolumn"] = (twocol == "true")
        else:
            options["twocolumn"] = False
        if "name" in options:
            options["name"] = options["name"][0]
        else:
            options["name"] = None
        if "condense" in options:
            condense = options["condense"][0].lower()
            if condense not in ["true", "false"]:
                compile_error("Condense option must be boolean.")
            options["condense"] = (condense == "true")
        else:
            options["condense"] = False

    def gobble(lines):
        cont, lines = Section.gobble(lines)
        if cont:
            return cont, lines
        question = lines[0].strip()
        lines = lines[1:]
        end = 0
        while end < len(lines) and re.match(r"\s", lines[end]):
            end += 1
        choices = [l.strip() for l in lines[:end]]
        MCQ = MC.MCQuestion(question, choices)
        return MCQ, lines[end:]

    def to_tex(self):
        global qcount
        initial_qcount = qcount
        tex = ["\\newpage"]
        if self.options["name"]:
            tex.append("\\section*{{{}}}".format(self.options["name"]))
        twocol = self.options["twocolumn"]
        if twocol:
            tex.append("\\setlength{\\columnsep}{0.40 in}")
            tex.append("\\begin{multicols*}{2}")
            tex.append("\\renewcommand{\\choiceshook}{\\setlength" +
                       "{\\leftmargin}{0.40 in}}")
            tex.append("\\renewcommand{\\questionshook}{\\setlength" +
                       "{\\leftmargin}{0.0 in}}")
        in_questions = False
        for cont in self.content:
            if type(cont) == MC.MCQuestion:
                if not in_questions:
                    in_questions = True
                    tex.append("\\begin{questions}")
                    tex.append("\\setcounter{{question}}{{{}}}".format(qcount))
                qcount += 1
            else:
                if in_questions:
                    in_questions = False
                    tex.append("\\end{questions}")
            tex.append(cont.to_tex())
        if in_questions:
            tex.append("\\end{questions}")
        if twocol:
            tex.append("\\end{multicols*}")
            tex.append("\\renewcommand{\\choiceshook}{}")
            tex.append("\\renewcommand{\\questionshook}{}")
        if self.options["condense"]:
            qcount = initial_qcount
            tex.append(self.ans_sheet_tex())
        return "\n".join(tex)

    def ans_sheet_tex(self):
        global qcount
        tex = []
        solutions = []
        for cont in self.content:
            if type(cont) == MC.MCQuestion:
                solutions.append(cont.get_answer())
        tex.append("\\raggedcolumns")
        tex.append("\\begin{multicols}{5}")
        tex.append("\\begin{enumerate}")
        tex.append("\t\\setcounter{{enumi}}{{{}}}".format(qcount))
        for sol in solutions:
            tex.append("\t\\item \\choiceblank{{{}}}".format(sol))
            qcount += 1
        tex.append("\\end{enumerate}")
        # spacing needs fixing iff the columns are uneven in length.
        if len(solutions) % 5 != 0:
            tex.append("\\fixcolspacing")
        tex.append("\\end{multicols}")
        return "\n".join(tex)

    class MCQuestion:

        def __init__(self, question, choices):
            self.question = question
            self.choices = []
            self.correct_choice = None
            for choice in choices:
                match = re.search("{C}", choice)
                if match:
                    choice = choice[:match.start()]
                    self.correct_choice = choice
                self.choices.append(choice)
            # if correct choice not specified, first given answer is correct
            if not self.correct_choice:
                self.correct_choice = self.choices[0]
                # randomize choices
                random.shuffle(self.choices)

        def to_tex(self):
            """Generates tex for MC question"""
            tex_str = ""
            tex_str += "\t\\question {}\n".format(self.question)
            tex_str += "\t\\begin{choices}\n"
            for choice in self.choices:
                if choice == self.correct_choice:
                    tex_str += "\t\t\\CorrectChoice {}\n".format(choice)
                else:
                    tex_str += "\t\t\\choice {}\n".format(choice)
            tex_str += "\t\\end{choices}\n"
            return tex_str

        def get_answer(self):
            """Returns capital-letter character of correct answer choice."""
            ind = self.choices.index(self.correct_choice)
            return chr(65 + ind)

        def to_tex(self):
            tex = ["\\question {}".format(latexify(self.question))]
            tex.append("\t\\begin{choices}")
            for choice in self.choices:
                correct = choice == self.correct_choice
                choice_str = "CorrectChoice" if correct else "choice"
                tex.append("\t\\{} {}".format(choice_str,
                                              latexify(choice)))
            tex.append("\t\\end{choices}")
            return "\n".join(tex)


class FRQ(Section):

    def __init__(self, lines):
        Section.__init__(self, lines)
        self.format_options()
        lines = self.lines
        while lines:
            cont, lines = FRQ.gobble(lines)
            self.content.append(cont)

    def format_options(self):
        options = self.options
        if "name" in options:
            options["name"] = options["name"][0]
        else:
            options["name"] = None

    def gobble(lines):
        cont, lines = Section.gobble(lines)
        if cont:
            return cont, lines
        end = 1
        while end < len(lines) and re.match(r"\s", lines[end]):
            end += 1
        frq = FRQ.FRQuestion(lines[:end], 0)
        return frq, lines[end:]

    def to_tex(self):
        global qcount
        tex = ["\\newpage"]
        if self.options["name"]:
            tex.append("\\section*{{{}}}".format(self.options["name"]))
        in_questions = False
        for cont in self.content:
            if type(cont) == FRQ.FRQuestion:
                if not in_questions:
                    in_questions = True
                    tex.append("\\begin{questions}")
                    tex.append("\\setcounter{{question}}{{{}}}".format(qcount))
                qcount += 1
            else:
                if in_questions:
                    in_questions = False
                    tex.append("\\end{questions}")
            tex.append(cont.to_tex())
        if in_questions:
            tex.append("\\end{questions}")
        return "\n".join(tex)

    def ans_sheet_tex(self):
        global qcount
        tex = []
        tex.append("\\begin{questions}")
        tex.append("\\setcounter{{question}}{{{}}}".format(qcount))
        for cont in self.content:
            if type(cont) == FRQ.FRQuestion:
                tex.append(cont.ans_sheet_tex())
                qcount += 1
        tex.append("\\end{questions}")
        return "\n".join(tex)

    class FRQuestion:
        partlabels = ['question', 'part', 'subpart', 'subsubpart']

        def __init__(self, lines, level):
            self.content = []
            self.level = level
            self.point_val = ""
            question = lines[0].strip()
            match = re.match(r"{\s*[\d\.]+\s*}", question)
            if match:
                self.point_val = "[{}]".format(match.group(0)[1:-1])
                question = question[match.end():].strip()
            self.question = question if question != "*" else ""
            lines = FRQ.FRQuestion.unindent(lines[1:])
            if len(lines) == 0:
                compile_error("FRQ question missing answer.", self.question)
            if len(lines) == 1 and re.match(r"\s*//", lines[0]):
                line = lines[0].strip()[2:].strip()
                # solution height
                match = re.match(r"{\s*[\d\.]+\s*}", line)
                if match:
                    self.ans_height = int(float(match.group(0)[1:-1])*18)
                    line = line[match.end():]
                else:
                    self.ans_height = 18*math.ceil(len(line)/75)
                self.answer = line.strip()
            else:
                while lines:
                    frq, lines = FRQ.FRQuestion.gobble(lines, level)
                    self.content.append(frq)

        def unindent(lines):
            unindented = []
            for line in lines:
                line = re.sub("\t", "    ", line)
                if line[:4] != "    ":
                    compile_error("Bad indent.", line)
                unindented.append(line[4:])
            return unindented

        def gobble(lines, level):
            if re.match(r"\s", lines[0]):
                compile_error("Question overindented.", lines[0])
            end = 1
            while end < len(lines) and re.match(r"\s", lines[end]):
                end += 1
            frq = FRQ.FRQuestion(lines[:end], level+1)
            return frq, lines[end:]

        def to_tex(self):
            indent = "\t" * self.level
            qlabel = FRQ.FRQuestion.partlabels[self.level]
            tex = ["{}\\{}{} {}".format(indent, qlabel, self.point_val,
                   latexify(self.question))]
            if self.content:
                if self.level+1 >= len(FRQ.FRQuestion.partlabels):
                    compile_error("FRQ too nested (subsubsubparts not \
                        allowed.)", self.question)
                indent1 = "\t" * (self.level+1)
                qlabel1 = FRQ.FRQuestion.partlabels[self.level+1] + "s"
                tex.append("{}\\begin{{{}}}".format(indent1, qlabel1))
                for cont in self.content:
                    tex.append(cont.to_tex())
                tex.append("{}\\end{{{}}}".format(indent1, qlabel1))
            elif not exam.meta["answer sheet"]:
                indent1 = "\t" * (self.level+1)
                tex.append(indent1 + "\\par")
                tex.append("{}\\begin{{solution}}[{}pt]"
                           .format(indent1, self.ans_height))
                tex.append(indent1 + latexify(self.answer))
                tex.append(indent1 + "\\end{solution}")
            return "\n".join(tex)

        def ans_sheet_tex(self):
            indent = "\t" * self.level
            qlabel = FRQ.FRQuestion.partlabels[self.level]
            tex = []
            if self.content:
                tex.append("{}\\{}".format(indent, qlabel))
                if self.level+1 >= len(FRQ.FRQuestion.partlabels):
                    compile_error("FRQ too nested (subsubsubparts not \
                        allowed.)", self.question)
                indent1 = "\t" * (self.level+1)
                qlabel1 = FRQ.FRQuestion.partlabels[self.level+1] + "s"
                tex.append("{}\\begin{{{}}}".format(indent1, qlabel1))
                for cont in self.content:
                    if type(cont) == FRQ.FRQuestion:
                        tex.append(cont.ans_sheet_tex())
                tex.append("{}\\end{{{}}}".format(indent1, qlabel1))
            else:
                tex.append("{}\\{}\\ifprintanswers\\else\\vphantom{{0}}\\fi"
                           .format(indent, qlabel))
                indent1 = "\t" * (self.level+1)
                tex.append(indent1 + "\\par")
                tex.append("{}\\begin{{solution}}[{}pt]"
                           .format(indent1, self.ans_height))
                tex.append(indent1 + latexify(self.answer))
                tex.append(indent1 + "\\end{solution}")
            return "\n".join(tex)


class Module:

    def __init__(self, lines):
        sep = np.flatnonzero([re.match(r"\s*-----", l) for l in lines])
        if sep.size != 0:
            sep = sep[0]
            self.options = process_options(lines[:sep])
            self.lines = lines[sep+1:]
        else:
            self.options = {}
            self.lines = lines
        self.content = []


class Image(Module):

    def __init__(self, lines):
        Module.__init__(self, lines)
        self.format_options()
        if len(self.lines) == 0:
            compile_error("Image missing filepath.")
        self.img_path = self.lines[0].strip()

    def format_options(self):
        options = self.options
        if "width" in options:
            width = options["width"][0]
            if width[-1] == "%":
                width = ".{}\\textwidth".format(width[:-1])
            options["width"] = width
        else:
            options["width"] = "\\textwidth"

    def to_tex(self):
        img_str = "\t\\includegraphics[width={}]{{{}}}".format(
                self.options["width"], self.img_path)
        tex = ["\\begin{center}"]
        tex.append(img_str)
        tex.append("\\end{center}")
        return "\n".join(tex)


class Text(Module):

    def __init__(self, lines):
        Module.__init__(self, lines)

    def to_tex(self):
        tex = ["\\par\\noindent"]
        for l in self.lines:
            tex.append(latexify(l.strip()))
            tex.append("\\par")
        tex = tex[:-1]
        return "\n".join(tex)


class Latex(Module):

    def __init__(self, lines):
        Module.__init__(self, lines)

    def to_tex(self):
        lines = FRQ.FRQuestion.unindent(self.lines)
        return "".join(lines)


class Bang:

    def __init__(self, line):
        line = line.strip().split()
        self.bang = line[0].lower()
        self.options = line[1:]

    def to_tex(self):
        if self.bang == "!newpage":
            return "\\newpage"
        if self.bang == "!newcol":
            return "\\vfill\\null\\columnbreak"
        if self.bang == "!hrule":
            return "\\par\\hrulefill"
        if self.bang == "!gap":
            if self.options:
                return "\\vspace{{{}}}".format(self.options[0])
            return "\\vspace{0.10in}"


class Exam:

    def __init__(self, examdata):
        self.sections = []
        self.meta = {}
        sec_pattern = r"(?i)\s*\[(meta|cover|match|tf|mc|frq)\]\s*$"
        section_inds = [re.match(sec_pattern, line) for line in examdata]
        section_inds = np.flatnonzero(section_inds)
        if len(section_inds) == 0:
            compile_error("No sections found.")
        section_inds = list(section_inds)
        section_inds.append(len(examdata))
        for i in range(len(section_inds)-1):
            ind = section_inds[i]
            section_type = examdata[ind].strip()[1:-1].lower()
            start = ind + 1
            end = section_inds[i+1]
            if start >= end:
                compile_error("Empty section found.", examdata[ind])
            content = examdata[start:end]
            if section_type == "meta":
                meta = process_options(content)
                self.meta.update(meta)
            elif section_type == "cover":
                self.sections.append(Cover(content))
            elif section_type == "match":
                self.sections.append(Match(content))
            elif section_type == "tf":
                self.sections.append(TF(content))
            elif section_type == "mc":
                self.sections.append(MC(content))
            elif section_type == "frq":
                self.sections.append(FRQ(content))
        self.format_meta()

    def format_meta(self):
        meta = self.meta
        if "answer sheet" in meta:
            sheet = meta["answer sheet"][0].lower()
            if sheet not in ["true", "false"]:
                compile_error("Answer sheet option must be boolean.")
            meta["answer sheet"] = (sheet == "true")
        else:
            meta["answer sheet"] = False
        if "image sheet" in meta:
            sheet = meta["image sheet"][0].lower()
            if sheet not in ["true", "false"]:
                compile_error("Image sheet option must be boolean.")
            meta["image sheet"] = (sheet == "true")
        else:
            meta["image sheet"] = False

    def meta_tex(self):
        tex = [template]
        if "packages" in self.meta:
            for pkg in self.meta["packages"]:
                tex.append("\\usepackage{{{}}}\n".format(pkg))
        if "header" in self.meta:
            header = self.meta["header"]
            if len(header) != 3:
                compile_error("Header must have three parts.", header)
            l, c, r = map(latexify, header)
            c = c + (" - Page \\thepage" if c != "" else "")
            r = r + (":\\kern .5 in" if r != "" else "")
            header_tex = "\\header{{{}}}{{{}}}{{{}}}\n".format(l, c, r)
            tex.append("\\pagestyle{head}\n" + header_tex + "\\headrule")
        return "\n".join(tex)

    def to_tex(self):
        tex = [self.meta_tex()]
        tex.append("\n\\begin{document}")
        for section in self.sections:
            tex.append(section.to_tex())
        tex.append("\\end{document}\n")
        return "\n".join(tex)

    def ans_sheet_tex(self):
        if not self.meta["answer sheet"]:
            return None
        tex = [self.meta_tex()]
        tex.append("\n\\begin{document}")
        tex.append("\\section*{Answer Sheet}")
        for section in self.sections:
            ans = section.ans_sheet_tex()
            tex.append(ans)
            if ans != "":
                tex.append("\\vspace{0.25in}")
        tex.append("\\end{document}\n")
        return "\n".join(tex)

    def ans_key_tex(self):
        if self.meta["answer sheet"]:
            tex = self.to_tex()
        else:
            tex = self.ans_sheet_tex()
        tex = re.sub("%\\printanswers", "\\printanswers", tex)
        return tex


def main():
    random.seed(5)
    global exam
    global qcount
    global template
    template_dir = os.path.join(os.path.dirname(sys.argv[0]), "template.tex")
    with open(template_dir, 'r') as filein:
        template = "".join(filein.readlines())
    # existence of argument is checked in executable script
    filename = sys.argv[1]
    with open(filename, 'r') as filein:
        lines = filein.readlines()
    lines = [l for l in lines if l.strip() != ""]
    exam = Exam(lines)
    # write to tex files
    match = re.search("\\.", filename)
    if match:
        filename = filename[:match.start()]
    qcount = 0
    exam_tex = exam.to_tex()
    with open(filename+"-EXAM.tex", 'w+') as fileout:
        fileout.write(exam_tex)
    key_tex = exam_tex
    if exam.meta["answer sheet"]:
        qcount = 0
        sheet_tex = exam.ans_sheet_tex()
        with open(filename+"-ANS_SHEET.tex", 'w+') as fileout:
            fileout.write(sheet_tex)
        key_tex = sheet_tex
    key_tex = re.sub("%\\printanswers", "\\printanswers", key_tex)
    with open(filename+"-KEY.tex", 'w+') as fileout:
        fileout.write(key_tex)


qcount = 0
exam = None
template = ""
main()
