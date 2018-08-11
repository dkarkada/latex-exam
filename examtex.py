import sys
import re
import math
from random import shuffle

bang_pattern = r"\s*!(newpage|options|gap|img|pkg)"
mod_pattern = r"(?i)\s*\[(title|subtitle|author|info|instructions|match|mc|frq|text|latex)\]"
sec_pattern = r"(?i)\s*\[(header|cover|section)\]"

def compile_error(err):
	"""Does this really need a docstring."""
	print(err)
	sys.exit(0)

def make_latex_safe(line):
	"""Replace LaTeX-sensitive characters with LaTeX counterparts. Returns modified line."""
	line = line.replace("%", "\\%")
	# search for quoted substrings, replace with ``''
	match = re.search("\"[^\"]*\"", line)
	while match:
		repl = "``{}''".format(match.group(0)[1:-1])
		line = line[:match.start()] + repl + line[match.end():]
		match = re.match("\"[^\"]*\"", line)
	return line

def bang_args(line):
	"""Parses and returns a bang's arguments"""
	match_0 = re.search("{", line)
	match_1 = re.search("}", line)
	if match_0 and match_1 and match_0.end() < match_1.start():
		args = line[match_0.end():match_1.start()]
		args = args.split(",")
		args = [arg.strip() for arg in args if arg.strip()!=""]
		return args
	return None

def bang_to_tex(line, context):
	"""Parses a bang and returns the corresponding tex"""
	args = bang_args(line)
	tex_str = ""
	if re.match(r"\s*!img", line):
		if not args:
			compile_error("Expected args for img.")
		tex_str += "\t\t\\vspace{0.05 in}\n"
		if len(args) == 1:
			img_str = "\t\t\\includegraphics{{{}}}\n".format(args[0])
		else:
			img_str = "\t\t\\includegraphics[width={}]{{{}}}\n".format(args[1], args[0])
		# check if bang is already centered
		if (context is None) or ("centered" not in context) or (context["centered"]==False):
			tex_str += "\t\\begin{center}\n"
			tex_str += img_str
			tex_str += "\t\\end{center}\n"
		else:
			tex_str += "\t\t\\par\\noindent\n"
			tex_str += "\t\t" + img_str							
		tex_str += "\t\t\\vspace{0.05 in}\n"
	if re.match(r"\s*!newpage", line):
		tex_str += "\t\t\\newpage\n"
	if re.match(r"\s*!gap", line):
		if args:
			tex_str += "\t\t\\vspace{{{}}}\n".format(args[0])
		else:
			tex_str += "\t\t\\vspace{0.10 in}\n"
	if re.match(r"\s*!pkg", line):
		if not args:
			compile_error("Expected args for pkg.")
		for arg in args:
			tex_str += "\\usepackage{{{}}}\n".format(arg)
	return tex_str

def update_options(bang, options):
	"""Parses an options bang and updates the options dict."""
	args = bang_args(bang)
	if re.match(r"\s*!options", bang):		
		if not args:
			compile_error("Expected args for options.")
		for arg in args:
			# check if option has a value vs. is a flag
			match = re.search("=", arg)
			if match:
				options[arg[:match.start()]] = arg[match.end():]
			else:
				options[arg] = ''

class MCQuestion:

	def __init__(self, question, points, choices, correct_choice):
		self.question = question
		self.points = points
		self.choices = choices
		# if correct choice not specified, by default first given answer is correct
		if not correct_choice:
			self.correct_choice = self.choices[0]
			# randomize choices
			shuffle(self.choices)
		else:
			self.correct_choice = correct_choice

	def to_tex(self):
		"""Generates tex for MC question"""
		tex_str = ""		
		tex_str += "\t\\question{} {}\n".format(self.points, self.question)
		tex_str += "\t\\begin{choices}\n"
		for choice in self.choices:
			if choice == self.correct_choice:
				tex_str += "\t\t\\CorrectChoice {}\n".format(choice)
			else:
				tex_str += "\t\t\\choice {}\n".format(choice)
		tex_str += "\t\\end{choices}\n"
		return tex_str

	def calc_height(self, qwidth, choicewidth, point_len):
		"""Returns estimate of height (in pt) required to display question and choices."""
		qlength = len(self.question)+point_len
		height = 11*math.ceil(qlength/qwidth)+10
		for choice in self.choices:
			height += 11*math.ceil(len(choice)/choicewidth)+5
		return height

	def get_answer(self):
		"""Returns capital-letter character of correct answer choice."""
		ind = self.choices.index(self.correct_choice)
		return chr(65 + ind)

class ExamModule:

	def __init__(self, mod_type, content):
		self.mod_type = mod_type
		# eliminate blank lines
		self.content = [line.rstrip() for line in content if not re.match(r"\s*$", line)]
		# filter content for bangs		
		self.bangs = [line for line in self.content if re.match(bang_pattern, line)]
		# set up module options
		self.options = {}
		for line in self.bangs:
			update_options(line, options=self.options)
		self.ans_str = ""

	def to_tex(self, qcount):
		"""Generates tex for module."""
		tex_str = ""
		# picks appropriate method for this module
		tex_generator = getattr(self, self.mod_type+"_tex", None)
		if not tex_generator:
			compile_error("Illegal module: " + self.mod_type)
		tex_str += tex_generator(qcount)
		return tex_str

	def title_tex(self, qcount):
		"""Client should use to_tex()."""
		content = self.content
		bangs = self.bangs
		tex_str = ""
		for line in content:
			if line not in bangs:				
				line = make_latex_safe(line)
				tex_str += "\\par\\noindent \\textbf{{\\large {}}}\n".format(line)
			else:
				tex_str += bang_to_tex(line, context=None)
		return tex_str

	def instructions_tex(self, qcount):
		"""Client should use to_tex()."""
		content = self.content
		bangs = self.bangs
		tex_str = ""
		for line in self.content:
			if line not in bangs:
				line = make_latex_safe(line)
				tex_str += "\\par\\noindent {}\n".format(line)
			else:
				tex_str += bang_to_tex(line, context=None)
		return tex_str

	def match_tex(self, qcount):
		"""Client should use to_tex()."""
		content = self.content
		bangs = self.bangs
		options = self.options
		# keeps question-answer pairs together while shuffling
		question_data = []
		# keep track of the first question number
		initial_qcount = qcount[0]
		# generate point-value tex
		if "qworth" in options:
			point_str = "[{}]".format(options["qworth"])
		else:
			point_str = ""
		# build question_data
		for line in content:
			if line not in bangs:
				line = make_latex_safe(line)
				if len(line.split("::")) != 2:
					compile_error("Invalid syntax in match: " + line)
				line = line.split("::")
				question_data.append(line)
		if "noshuffle" not in options:
			shuffle(question_data)
		# remove duplicate answers and sort alphebetically
		ans_list = sorted(list(set([line[0] for line in question_data])))
		# make word bank
		if len(ans_list) > 26:
			compile_error("Too many choices in word bank.")
		tex_str = "\\begin{wordbank}{3}\n"
		for ans in ans_list:
			tex_str += "\t\\wbelem{{{}}}\n".format(ans)
		tex_str += "\\end{wordbank}\n"
		tex_str += "\\begin{questions}\n"
		tex_str += "\\setcounter{{question}}{{{}}}\n".format(qcount[0])
		# generate questions and solution letters
		solutions = []
		for line in question_data:
			question, ans = line[1].strip(), line[0].strip()
			ans_letter = chr(65 + ans_list.index(ans))
			solutions.append(ans_letter)
			tex_str += "\t\\question{}\\match{{{}}}{{{}}}\n".format(point_str, ans_letter, question)
			qcount[0] += 1
		tex_str += "\\end{questions}\n"
		# generate answers
		if self.has_ans_sheet():
			self.ans_str = self.gen_ans(initial_qcount, solutions)
		else:
			self.ans_str = tex_str 
		return tex_str

	def mc_tex(self, qcount):
		"""Client should use to_tex()."""
		content = self.content
		bangs = self.bangs
		options = self.options
		# keep track of the first question number
		initial_qcount = qcount[0]
		questions = []
		solutions = []
		# generate point-value tex
		if "qworth" in options:
			point_str = "[{}]".format(options["qworth"])
			# length of string to display points (i.e. "(2 points) "). Need for qheight
			point_len = 11
		else:
			point_str = ""
			point_len = 0 
		# keep track of bang-generated tex to preserve order
		bang_tex = []
		# generate questions and solutions
		question_str = None
		choices = []
		correct_choice = None
		for line in content:
			if line not in bangs:
				line = make_latex_safe(line)
				if not question_str:
					question_str = line
				elif re.match("\t+", line):
					# check if correct answer specified; by default first choice is correct
					match = re.search("{C}", line)
					if match:
						line = line[:match.start()]
						correct_choice = line.strip()
					choices.append(line.strip())
				else:
					if len(choices) == 0:
						compile_error("No answer choices found: " + question_str)
					mcq = MCQuestion(question_str, point_str, choices, correct_choice)
					questions.append(mcq)
					solutions.append(mcq.get_answer())
					# add accumulated bang tex after this question
					if bang_tex:
						questions.append("".join(bang_tex))
						bang_tex = []
					question_str = line
					choices = []
					correct_choice = None
			else:
				twocolumn = "twocolumn" in options
				bang_line = bang_to_tex(line, context={"twocolumn":twocolumn})
				if bang_line != "":
					bang_tex.append(bang_line)
		# append last question
		mcq = MCQuestion(question_str, point_str, choices, correct_choice)
		questions.append(mcq)
		solutions.append(mcq.get_answer())
		# generate question tex
		tex_str = ""
		if "twocolumn" in options:
			tex_str += "\\setlength{\\columnsep}{0.40 in}\n"
			tex_str += "\\begin{multicols*}{2}\n"
			tex_str += "\\renewcommand{\\choiceshook}{\\setlength{\\leftmargin}{0.40 in}}\n"
			tex_str += "\\renewcommand{\\questionshook}{\\setlength{\\leftmargin}{0.0 in}}\n"
		tex_str += "\\begin{questions}\n"
		tex_str += "\\setcounter{{question}}{{{}}}\n".format(qcount[0])
		cur_line = 0
		col_num = 1
		# make first page MC columns shorter due to title and instructions
		if "intro-height" in options:
			try:
				page_height_pt = 672 - int(options["intro-height"])
			except ValueError:
				compile_error("Option intro-height in MC module must have numeric value.")
		else:
			page_height_pt = 500
		for question in questions:
			if type(question) == MCQuestion:
				qwidth, choicewidth = (50, 43) if "twocolumn" in options else (100, 80)
				qheight = question.calc_height(qwidth, choicewidth, point_len)
				firstpage = col_num<=2 if "twocolumn" in options else col_num<=1
				if not firstpage:
					page_height_pt = 672
				# decide whether to insert column break
				if cur_line + qheight > page_height_pt:
					if "twocolumn" in options:
						tex_str += "\t\\vfill\\null\\columnbreak\n"
					else:
						tex_str += "\t\\newpage\n"
					col_num += 1
					cur_line = qheight
				else:
					cur_line += qheight
				tex_str += question.to_tex()
				qcount[0] += 1
			else:
				# "question" is actually bang tex
				tex_str += question
				# new column since bang tex could screw with spacing
				if "!img" or "!gap" in question:
					cur_line = 0
					if "twocolumn" in options:
						tex_str += "\t\\vfill\\null\\columnbreak\n"
					else:
						tex_str += "\t\\newpage\n"
					col_num += 1
		tex_str += "\\end{questions}\n"
		if "twocolumn" in options:
			tex_str += "\\end{multicols*}\n"
			tex_str += "\\renewcommand{\\choiceshook}{}\n"
			tex_str += "\\renewcommand{\\questionshook}{}\n"
		# generate answers
		if self.has_ans_sheet():
			self.ans_str = self.gen_ans(initial_qcount, solutions)
		else:
			self.ans_str = tex_str
		return tex_str

	def frq_tex(self, qcount):
		"""Client should use to_tex()."""
		content = self.content
		bangs = self.bangs
		options = self.options
		solutions = []
		# 3-item list for question number, part number, subpart number
		hierarchy = [qcount[0], 0, 0]
		# indents indicate question hierarchy
		prev_indent_count = indent_count = 0
		tex_str = "\\begin{questions}\n"
		tex_str += "\\setcounter{{question}}{{{}}}\n".format(qcount[0])
		for line in content:
			if line not in bangs:
				line = make_latex_safe(line)
				# check that line is not a solution
				if not re.match(r"\s*//", line):
					# current line indentation
					indent_count = len(line) - len(line.lstrip("\t"))
					# change from previous indentation
					indent_change = indent_count - prev_indent_count
					# switch on indent_change to determine whether starting/ending parts/subparts
					line = line.strip()
					if indent_change == -2:
						tex_str += "\t\t\\end{subparts}\n"
						tex_str += "\t\\end{parts}\n"
						hierarchy = [hierarchy[0]+1, 0, 0]
					elif indent_change == -1:
						if indent_count == 0:
							tex_str += "\t\\end{parts}\n"
							hierarchy = [hierarchy[0]+1, 0, 0]
						else:
							tex_str += "\t\t\\end{subparts}\n"
							hierarchy = [hierarchy[0], hierarchy[1]+1, 0]
					elif indent_change == 0:
						hierarchy[indent_count] += 1
					elif indent_change == 1:
						if indent_count == 1:
							tex_str += "\t\\begin{parts}\n"
							hierarchy[1] += 1
						elif indent_count == 2:
							tex_str += "\t\t\\begin{subparts}\n"
							hierarchy[2] += 1
						else:
							compile_error("Too many indents: " + line)
					else:
						compile_error("Too many indents: " + line)
					# show point values if defined
					match = re.match(r"{\s*\d+\s*}", line)
					point_str = ""
					if match:
						point_str = match.group(0)[1:-1]
						point_str = "[{}]".format(point_str)
						line = line[match.end():]
					# question tex
					if indent_count == 0:
						tex_str += "\\question{} {}\n".format(point_str, line)
						qcount[0] += 1
					elif indent_count == 1:
						tex_str += "\t\\part{} {}\n".format(point_str, line)
					else:
						tex_str += "\t\t\\subpart{} {}\n".format(point_str, line)
					prev_indent_count = indent_count
				else:
					# remove // and strip
					line = line.strip()[2:].strip()
					# solution height
					match = re.match(r"{\s*\d+\s*}", line)
					if match:
						height = int(line[match.start()+1:match.end()-1])*20
						height_str = "[{} pt]".format(height)
						line = line[match.end():]
					else:
						height_str = "[{} pt]".format(20*math.ceil(len(line)/75))
					# solution tex
					tab_str = "\t"*(indent_count+1)
					tex_str += "{}\\begin{{solution}}{}\n".format(tab_str,
						height_str if not self.has_ans_sheet() else "")
					tex_str += "{}{}\n".format(tab_str, line)
					solutions.append((hierarchy.copy(), height_str, line))
					tex_str += tab_str + "\\end{solution}\n"
			else:
				tex_str += bang_to_tex(line, context=None)
		# close any remaining subparts or parts environments
		indent_change = 0 - prev_indent_count
		if indent_change == -2:
			tex_str += "\t\t\\end{subparts}\n"
			tex_str += "\t\\end{parts}\n"
		elif indent_change == -1:
			tex_str += "\t\\end{parts}\n"
		tex_str += "\\end{questions}\n"
		# generate answers
		if self.has_ans_sheet():
			self.ans_str = self.gen_ans(None, solutions)
		else:
			self.ans_str = tex_str.replace("!newpage", "")
		return tex_str

	def text_tex(self, qcount):
		"""Client should use to_tex()."""
		content = self.content
		bangs = self.bangs
		tex_str = ""
		for line in content:
			if line not in bangs:
				line = make_latex_safe(line)
				line = re.sub(r"\\i\s*{", r"\\textit{", line)
				line = re.sub(r"\\b\s*{", r"\\textbf{", line)
				tex_str += "\t\\par {}\n".format(line)
			else:
				tex_str += bang_to_tex(line, context=None)				
		return tex_str

	def latex_tex(self, qcount):
		"""Client should use to_tex()."""
		return "\n".join(self.content) + "\n"

	def has_ans_sheet(self):
		"""Returns true if this module has option ans=sheet"""
		return "ans" in self.options and self.options["ans"]=="sheet"

	def gen_ans(self, initial_qcount, solutions):
		"""
		Returns tex for answer sheet.

		initial_qcount (int): the question number the previous module ended with.
		solutions (list): contains solutions for this module. FRQ solutions are 3-tupled as
			(hierarchy, hieght_str, solution_str).
		"""
		ans_str = ""
		if self.mod_type in ["match", "mc"]:
			ans_str += "\t\\raggedcolumns\n"
			ans_str += "\t\\begin{multicols}{5}\n"
			ans_str += "\t\\begin{enumerate}\n"
			ans_str += "\t\\setcounter{{enumi}}{{{}}}\n".format(initial_qcount)
			for sol in solutions:
				ans_str += "\t\\item \\choiceblank{{{}}}\n".format(sol)
			ans_str += "\t\\end{enumerate}\n"
			# spacing needs fixing iff the columns are uneven in length.
			if len(solutions) % 5 != 0:
				ans_str += "\t\\fixcolspacing\n"
			ans_str += "\t\\end{multicols}\n"
		elif self.mod_type == "frq":
			for (hierarchy, height_str, sol) in solutions:
				qnum = "{}.".format(hierarchy[0])
				qpart = chr(hierarchy[1]+96)+"." if hierarchy[1]!=0 else ""
				# convert to roman
				qsubpart = ""
				if hierarchy[2]!=0:
					romans = [('x',  10), ('ix', 9), ('v',  5), ('iv', 4), ('i',  1)]
					subpart_num = hierarchy[2]
					for numeral, integer in romans:
						while subpart_num >= integer:
							qsubpart += numeral
							subpart_num -= integer
					qsubpart += "."
				qnum += qpart + qsubpart
				ans_str += "\t\\\\[5 pt]\n"
				ans_str += "\t\\begin{minipage}{\\linewidth}\n"
				ans_str += "\t\t\\par\\noindent {}\n".format(qnum)
				ans_str += "\t\t\\begin{{solution}}{}\n".format(height_str)
				ans_str += "\t\t\t{}\n".format(sol)
				ans_str += "\t\t\\end{solution}\n"
				ans_str += "\t\t\\par\\noindent\\hrulefill\n"
				ans_str += "\t\\end{minipage}\n"
			ans_str += "\t\\\\[10 pt]\n"
		return ans_str


class ExamSection:

	def __init__(self, sec_type, content):
		self.sec_type = sec_type
		self.content = []
		self.modules = []
		# parse content into modules
		ind = 0
		# content for this section. Should be only bangs
		while ind<len(content) and not re.match(mod_pattern, content[ind]):
			self.content.append(content[ind])
			ind += 1
		# module parsing
		mod_type = None
		mod_content = []
		while ind < len(content):
			line = content[ind]
			# look for module tag
			match = re.match(mod_pattern, line)
			if match:
				if mod_type:
					# we are not in first module; can append previous module and start new one
					self.modules.append(ExamModule(mod_type, mod_content))
				splt = match.end()
				mod_type = line[:splt].strip()[1:-1].lower()
				mod_content = [line[splt:]]
				ind += 1
			else:
				mod_content.append(line)
				ind += 1
		# add last module
		self.modules.append(ExamModule(mod_type, mod_content))

	def to_tex(self, qcount):
		"""
		Returns tex for this section.

		qcount (list): A singleton list containing the current question number.
		"""
		if self.sec_type == "cover":
			return self.cover_to_tex()
		elif self.sec_type == "section":
			return self.section_to_tex(qcount)
		elif self.sec_type == "header":
			return ""
		assert False, "Unexpected section type."

	def cover_to_tex(self):
		"""Client should use to_tex()."""
		# prevent nesting of center environments
		centered = False
		# top/bottom margins for each module
		spacings = {"title": "0.10", "subtitle": "0.05", "author": "0.05",\
					"info": "0.15", "instructions": "0.15"}
		tex_str = "\\begin{coverpages}\n"
		# section bangs
		for line in self.content:
			if re.match(bang_pattern, line):
				tex_str += bang_to_tex(line, context=None)
		# module tex
		for mod in self.modules:
			content = mod.content
			mt = mod.mod_type
			bangs = mod.bangs
			if mt not in spacings:
				compile_error("Invalid module type in Cover: " + mt)
			# centering
			if mt in ["title", "subtitle", "author", "info"] and not centered:
				tex_str += "\t\\begin{center}\n"
				centered = True
			elif mt not in ["title", "subtitle", "author", "info"] and centered:
				tex_str += "\t\\end{center}\n"
				centered = False
			# spacing
			spacing = spacings[mt]
			tex_str += "\t\t\\vspace{{{} in}}\n".format(spacing)
			# module content
			if mt == "info":
				tex_str += "\t\t\\par\n"
				tex_str += "\t\t\\def\\arraystretch{2}\\tabcolsep=3pt\n\t\t\\begin{tabular}{r r}\n"
			for line in content:
				if line not in bangs:
					line = make_latex_safe(line)
					if mt == "title":
						tex_str += "\t\t\\par\\noindent\\textbf{{\\Huge  {}}}\n".format(line) 
					if mt == "subtitle":
						tex_str += "\t\t\\par\\noindent\\textbf{{\\large {}}}\n".format(line)
					if mt == "author":
						# Bold author's name, italicize author contact info
						match = re.search(",", line)
						if match:
							splt = match.end()
							author = line[:splt-1]
							author_info = line[splt:]
							tex_str += "\t\t\\par\\noindent\\textbf{{Written by: {}}}, \\textit{{{}}}\n".format(
								author, author_info)
						else:
							tex_str += "\t\t\\textbf{{Written by: {}}}\n".format(content[0])
					if mt == "info":
						tex_str += "\t\t\t\\textbf{{{}:}} & \\makebox[4in]{{\\hrulefill}} \\\\\n".format(
							line.strip())
					if mt == "instructions":
						tex_str += "\t\\par {}\n".format(line.strip())
				else:
					tex_str += bang_to_tex(line, context={"centered": centered})
			if mt == "info":
				tex_str += "\t\t\\end{tabular}\n"
			tex_str += "\t\t\\vspace{{{} in}}\n".format(spacing)
		# close centering after last module
		if centered:
			tex_str += "\t\\end{center}\n"
			centered = False
		tex_str += "\\end{coverpages}\n"
		return tex_str

	def section_to_tex(self, qcount):
		"""
		Client should use to_tex().
		"""
		tex_str = "\n\\newpage\n"
		# section bangs
		for line in self.content:
			if re.match(bang_pattern, line):
				tex_str += bang_to_tex(line, context=None)
		# module tex
		for module in self.modules:
			tex_str += module.to_tex(qcount)
		return tex_str

	def get_packages(self):
		tex_str = ""
		for line in self.content:
			if re.match(r"\s*!pkg", line):
				tex_str += bang_to_tex(line, context=None)
		return tex_str

	def ans_tex(self, ans_key):
		"""
		Returns tex for the answer key or answer sheet.

		ans_key (bool): True if we're generating the answer key (as opposed to sheet).
		"""
		ans_str = ""
		title_tex = ""
		# prevent duplicate titles in a separated question set
		untitled = True
		for module in self.modules:
			if module.mod_type == "title":
				title_tex = module.title_tex(qcount=None)
			elif module.mod_type in ["match", "frq", "mc"]:
				if ans_key or module.has_ans_sheet():
					if untitled:
						# newpage if copying section straight from exam
						if not module.has_ans_sheet():
							ans_str += "\\newpage\n"
						untitled = False
						ans_str += title_tex
					ans_str += module.ans_str
		return ans_str


class Exam:

	def __init__(self):
		self.sections = []
		# is in list so that updates elsewhere will stick around (pass by reference hack)
		self.question_counter = [0]
		# make template containing labelled tex snippets
		with open("template.tex", 'r') as filein:
			labels = {}
			label = ""
			for line in filein:
				if not re.match(r"\s*$", line):
					match = re.match(r"\s*%", line)
					if match:
						splt = match.end()
						label = line[splt:].strip()
					elif label != "":
						if label in labels:
							labels[label] += line
						else:
							labels[label] = line
		self.template = labels

	def verify_sections(self):
		"""Make sure nothing is wonky about the exam"""
		sections = self.sections
		if len(sections) == 0:
			compile_error("No sections found.")
		s_count = cover_count = header_count = 0
		for section in sections:
			if section.sec_type == "section":
				s_count += 1
			elif section.sec_type == "cover":
				cover_count += 1
			elif section.sec_type == "header":
				header_count += 1
		assert len(sections) == s_count + cover_count + header_count, "Misidentified section."
		if cover_count > 1:
			compile_error("Only one cover allowed.")
		if header_count > 1:
			compile_error("Only one header allowed.")	

	def get_header_info(self):
		"""Returns a 3-element list of header items, if a header is defined."""
		header = None
		for section in self.sections:
			if section.sec_type == "header":
				header = section
		if not header:
			return None
		content = [item.strip() for item in header.content if item.strip()!=""]
		# remove pkg bangs
		content = [item for item in content if not re.match(bang_pattern, item)]
		if len(content) != 3:
			compile_error("Header must have 3 elements.")
		# Commented lines are filler for empty header item
		return [item if not re.match(r"\s*//", item) else "" for item in content]

	def get_packages(self):
		"""Gets package imports from header as tex commands."""
		header = None
		for section in self.sections:
			if section.sec_type == "header":
				header = section
		if not header:
			return ""
		return header.get_packages()

	def exam_preamble(self):
		"""Returns tex for exam preamble."""
		tex_str = self.template["preamble"] + "\n"
		tex_str += self.template["answerkey"] + "\n"
		for pkg in self.get_packages():
			tex_str += pkg
		header_elems = self.get_header_info()
		if header_elems:
			e0 = header_elems[0] if header_elems[0]!="" else ""
			e1 = header_elems[1] + " - Page \\thepage" if header_elems[1]!="" else ""
			e2 = header_elems[2] + ":\\kern .5 in" if header_elems[2]!="" else ""
			tex_header = "\\header{{{}}}{{{}}}{{{}}}\n".format(e0, e1, e2)
			tex_str += "\n\\pagestyle{head}\n" + tex_header + "\\headrule\n"
		return tex_str

	def to_tex(self):
		"""Returns exam tex."""	
		tex_str = self.exam_preamble()
		tex_str += "\n\\begin{document}\n"
		# generate question tex
		for section in self.sections:
			tex_str += section.to_tex(self.question_counter)
		# generate answer sheet
		ans_sheet = ""
		for section in self.sections:
			ans_sheet += section.ans_tex(False)
		if ans_sheet != "":
			tex_str += "\\newpage\n"
			tex_str += "\\section*{Answer Sheet}\n"
			tex_str += ans_sheet
		tex_str += "\\end{document}"
		return tex_str

	def ans_tex(self):
		"""Returns answer key tex."""
		ans_str = self.template["preamble"] + "\n"
		ans_str += self.template["answerkey"] + "\n"
		ans_str += "\\printanswers" + "\n"
		ans_str += "\n\\begin{document}\n"
		for section in self.sections:
			ans_str += section.ans_tex(True)
		ans_str += "\\end{document}"
		return ans_str


def generate_tex(filename):
	"""
	Returns a tuple containing tex for the exam and answer key.

	filename (str): filename of .exam file
	"""
	exam = Exam()
	with open(filename, 'r') as filein:
		lines = filein.readlines()
		ind = 0
		# any lines above the first section are comments and are ignored
		while ind<len(lines) and not re.match(sec_pattern, lines[ind]):
			ind += 1
		if ind >= len(lines):
			compile_error("No sections found.")
			return None
		# putting together exam
		sec_type = None
		sec_content = []
		while ind < len(lines):
			line = lines[ind]
			match = re.match(sec_pattern, line)
			if match:
				if sec_type:
					exam.sections.append(ExamSection(sec_type, sec_content))
				splt = match.end()
				sec_type = line[:splt].strip()[1:-1].lower()
				sec_content = [line[splt:]]
				ind += 1
			else: # should only be bangs
				sec_content.append(line)
				ind += 1
		# since last section still needs to be added
		exam.sections.append(ExamSection(sec_type, sec_content))
	# make sure everything is set up correctly
	exam.verify_sections()

	return exam.to_tex(), exam.ans_tex()

def main():
	# existence of argument is checked in bash script
	filename = sys.argv[1]
	tex_str, ans_str = generate_tex(filename)
	# write to tex files
	match = re.search("\\.", filename)
	if match:
		filename = filename[:match.start()]
	with open(filename+"-EXAM.tex", 'w+') as fileout:
		fileout.write(tex_str)
	with open(filename+"-KEY.tex", 'w+') as fileout:
		fileout.write(ans_str)

if __name__ == "__main__":
	main()
