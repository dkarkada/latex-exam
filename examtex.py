import sys
import os.path
import re
import math
from random import shuffle

bang_pattern = r"\s*!(newpage|options|ans-options|gap|img|pkg)"
mc_bang_pattern = r"\s*!(newcol|txt|hrule)"
mod_pattern = r"(?i)\s*\[(title|subtitle|author|info|match|tf|mc|frq|text|latex|table)\]"
sec_pattern = r"(?i)\s*\[(header|cover|section)\]"

tex_template = ""

def compile_error(err):
	"""Does this really need a docstring."""
	print(err, file=sys.stderr)
	sys.exit(1)

def make_latex_safe(line):
	"""Replace LaTeX-sensitive characters with LaTeX counterparts. Returns modified line."""
	line = line.replace("%", "\\%")
	# search for double quoted substrings, replace with ``''
	match = re.search("\"[^\"]*\"", line)
	while match:
		repl = "``{}''".format(match.group(0)[1:-1])
		line = line[:match.start()] + repl + line[match.end():]
		match = re.search("\"[^\"]*\"", line)
	# search for single quoted substrings, replace with `'. Capture surrounding whitespace
	match = re.search("\\s'[^']+'\\s", line)
	while match:
		repl = "`{}'".format(match.group(0)[2:-2])
		line = line[:match.start()+1] + repl + line[match.end()-1:]
		match = re.search("\\s'[^']+'\\s", line)
	# custom bold and italics syntax
	line = re.sub(r"\\i\s*{", r"\\textit{", line)
	line = re.sub(r"\\b\s*{", r"\\textbf{", line)
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

def bang_to_tex(line, centered=False):
	"""Parses a bang and returns the corresponding tex"""
	args = bang_args(line)
	tex_str = ""
	if re.match(r"\s*!img", line):
		if not args:
			compile_error("Expected args for img.")
		tex_str += "\t\t\\par\\noindent\n"
		if len(args) == 1:
			img_str = "\t\t\\includegraphics{{{}}}\n".format(args[0])
		else:
			img_str = "\t\t\\includegraphics[width={}]{{{}}}\n".format(args[1], args[0])
		# check if bang is already centered
		if not centered:
			tex_str += "\t\\begin{center}\n"
			tex_str += img_str
			tex_str += "\t\\end{center}\n"
		else:
			tex_str += "\t\t\\vspace{0.05 in}\n"
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
	if re.match(r"\s*!hrule", line):
		tex_str += "\t\t\\par\n"
		tex_str += "\t\t\\hrulefill\n"
		tex_str += "\t\t\\vspace{0.05 in}\n"
	if re.match(r"\s*!txt", line):
		if not args:
			compile_error("Expected args for txt.")
		tex_str += "\t\\begin{flushleft}\n"
		snippet = ", ".join(args)
		tex_str += "\t\\par {}\n".format(snippet)
		tex_str += "\t\\end{flushleft}\n"
	if re.match(r"\s*!newcol", line):
		tex_str += "" # do nothing
	return tex_str

def update_options(bang, options, ans_options):
	"""Parses an options bang and updates the options dict."""
	args = bang_args(bang)
	opt = None
	if re.match(r"\s*!options", bang):
		if not args:
			compile_error("Expected args for options.")
		opt = options
	elif re.match(r"\s*!ans-options", bang):		
		if not args:
			compile_error("Expected args for ans-options.")
		opt = ans_options
	else:
		return
	for arg in args:
		# check if option has a value vs. is a flag
		match = re.search("=", arg)
		if match:
			opt[arg[:match.start()]] = arg[match.end():]
		else:
			opt[arg] = ''

def num_indents(line):
	""" Returns the number of indents in a line, using either tabs or 4 spaces."""
	match = re.match(r"\s+", line)
	if not match:
		return 0
	match = re.match(r"\t+", line)
	if match:
		return len(match.group(0))
	match = re.match(r" +", line)
	if match:
		return len(match.group(0)) // 4
	return 0

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
		if mod_type == "mc":
			self.bangs += [line for line in self.content if re.match(mc_bang_pattern, line)]
		# set up module options
		self.options = {}
		self.ans_options = {}
		for line in self.bangs:
			update_options(line, options=self.options, ans_options=self.ans_options)
		self.ans_sheet_str = ""
		self.ans_key_str = ""

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
				tex_str += bang_to_tex(line)
		return tex_str

	def match_tex(self, qcount):
		return self.match_tf_tex(qcount, is_tf=False)		

	def tf_tex(self, qcount):
		return self.match_tf_tex(qcount, is_tf=True)

	def match_tf_tex(self, qcount, is_tf):
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
		if is_tf:			
			if len(ans_list) != 2:
				compile_error("Can only have 2 answers for true/false.")
			tex_str = ""
		else:
			if len(ans_list) > 26:
				compile_error("Too many choices in word bank.")
			tex_str = "\\begin{wordbank}{3}\n"
			for ans in ans_list:
				tex_str += "\t\\wbelem{{{}}}\n".format(ans)
			tex_str += "\\end{wordbank}\n"
		# generate questions and solution letters
		tex_str += "\\begin{questions}\n"
		tex_str += "\\setcounter{{question}}{{{}}}\n".format(qcount[0])
		solutions = []
		for line in question_data:
			question, ans = line[1].strip(), line[0].strip()
			if is_tf:
				ans_letter = 'T' if ans.lower() in ["t","true"] else 'F'
			else:
				ans_letter = chr(65 + ans_list.index(ans))
			solutions.append(ans_letter)
			if not re.match(r"\s*//", question):
				tex_str += "\t\\question{}\\match{{{}}}{{{}}}\n".format(point_str, ans_letter, question)
			qcount[0] += 1
		tex_str += "\\end{questions}\n"
		# generate answers
		self.gen_ans(initial_qcount, solutions)
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
		current_bangs = []
		# generate questions and solutions
		question_str = None
		choices = []
		correct_choice = None
		for line in content:
			if line not in bangs:
				line = make_latex_safe(line)
				if not question_str:
					# add accumulated bang tex before first question
					if current_bangs:
						questions += current_bangs
						current_bangs = []
					question_str = line
				# check if indented
				elif num_indents(line) != 0:
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
					# add accumulated bang tex before next question
					if current_bangs:
						questions += current_bangs
						current_bangs = []
					# start next question
					question_str = line
					choices = []
					correct_choice = None
			else:
				current_bangs.append(line)
		# append last question
		mcq = MCQuestion(question_str, point_str, choices, correct_choice)
		questions.append(mcq)
		solutions.append(mcq.get_answer())
		# add accumulated bang tex at the end
		if current_bangs:
			questions += current_bangs
			current_bangs = []
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
				# "question" is actually bang
				bang = question
				bang_tex = bang_to_tex(bang)
				tex_str += bang_tex
				# new column since bang tex could screw with spacing
				if "!newcol" in bang:
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
		self.gen_ans(initial_qcount, solutions)
		return tex_str

	def frq_tex(self, qcount):
		"""Client should use to_tex()."""
		content = self.content
		bangs = self.bangs
		solutions = []
		initial_qcount = qcount[0]
		# 3-item list for question number, part number, subpart number
		hierarchy = [qcount[0], 0, 0]
		# indents indicate question hierarchy
		prev_indent_count = indent_count = 0
		tex_str = "\\begin{questions}\n"
		tex_str += "\t\\setcounter{{question}}{{{}}}\n".format(qcount[0])
		for line in content:
			if line not in bangs:
				line = make_latex_safe(line)
				# check that line is not a solution
				if not re.match(r"\s*//", line):
					# current line indentation
					indent_count = num_indents(line)
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
					# empty question (subparts without question)
					if line == "*":
						line = ""
					if indent_count == 0:
						tex_str += "\t\\question{} {}\n".format(point_str, line)
						qcount[0] += 1
					elif indent_count == 1:
						tex_str += "\t\t\\part{} {}\n".format(point_str, line)
					else:
						tex_str += "\t\t\t\\subpart{} {}\n".format(point_str, line)
					prev_indent_count = indent_count
				else:
					# remove // and strip
					line = line.strip()[2:].strip()
					# solution height
					match = re.match(r"{\s*[\d\.]+\s*}", line)
					if match:
						height = int(float(line[match.start()+1:match.end()-1])*16)-12
						height_str = "{} pt".format(height)
						line = line[match.end():]
					else:
						height_str = "{} pt".format(16*math.ceil(len(line)/75))
					# solution tex
					solutions.append((hierarchy.copy(), height_str, line))
					if "sheet" not in self.ans_options:
						tab_str = "\t"*(indent_count+2)
						tex_str += "{}\\begin{{solution}}[{}]\n".format(tab_str, height_str) \
								+ "{}{}\n".format(tab_str, line) \
								+ tab_str + "\\end{solution}\n"
			else:
				tex_str += bang_to_tex(line)
		# close any remaining subparts or parts environments
		indent_change = 0 - prev_indent_count
		if indent_change == -2:
			tex_str += "\t\t\\end{subparts}\n"
			tex_str += "\t\\end{parts}\n"
		elif indent_change == -1:
			tex_str += "\t\\end{parts}\n"
		tex_str += "\\end{questions}\n"
		# generate answers
		self.gen_ans(initial_qcount, solutions)
		return tex_str

	def text_tex(self, qcount):
		"""Client should use to_tex()."""
		content = self.content
		bangs = self.bangs
		tex_str = ""
		noindent = "\\noindent"
		for line in content:
			if line not in bangs:
				line = make_latex_safe(line)
				tex_str += "\t\\par{} {}\n".format(noindent, line)
				noindent = ""
			else:
				tex_str += bang_to_tex(line)				
		return tex_str

	def latex_tex(self, qcount):
		"""Client should use to_tex()."""
		return "\n".join(self.content) + "\n"

	def table_tex(self, qcount):
		"""Client should use to_tex()."""
		content = self.content
		bangs = self.bangs
		options = self.options
		if "pattern" not in options:
			compile_error("Expected pattern option in table module.")
		pattern = options["pattern"]
		if "boxed" in options:
			pattern = "|{}|".format(pattern)
		tex_str = "\\begin{center}\n"
		if "linespace" in options:
			tex_str += "\\def\\arraystretch{{{}}}\n".format(options["linespace"])
		tex_str += "\\begin{{tabular}}{{{}}}\n".format(pattern)
		if "boxed" in options:
			tex_str += "\\hline\n"
		for line in content:
			if line not in bangs:
				if re.match(r"\s*-*\s*$", line):
					tex_str += "\t\\hline\n"
				else:
					line = make_latex_safe(line)
					# split on both tabs and on multi-space
					line = re.split(r'\t+| {2,}', line)
					print(line)
					line = [tdata for tdata in line if tdata != ""]
					line = " & ".join(line) + "\\\\"
					tex_str += "\t{}\n".format(line)
			else:
				tex_str += bang_to_tex(line, centered=True)
		if "boxed" in options:
			tex_str += "\\hline\n"
		tex_str += "\\end{tabular}\n"
		tex_str += "\\end{center}\n"
		return tex_str

	def gen_ans(self, initial_qcount, solutions):
		"""
		Generates module tex for answer sheet and module tex for answer key.

		initial_qcount (int): the question number the previous module ended with.
		solutions (list): contains solutions for this module. FRQ solutions are 3-tupled as
			(hierarchy, hieght_str, solution_str).
		"""
		if self.mod_type in ["match", "tf", "mc"]:
			ans_str = "\t\\raggedcolumns\n" \
					+ "\t\\begin{multicols}{5}\n" \
					+ "\t\\begin{enumerate}\n" \
					+ "\t\\setcounter{{enumi}}{{{}}}\n".format(initial_qcount)
			for sol in solutions:
				ans_str += "\t\\item \\choiceblank{{{}}}\n".format(sol)
			ans_str += "\t\\end{enumerate}\n"
			# spacing needs fixing iff the columns are uneven in length.
			if len(solutions) % 5 != 0:
				ans_str += "\t\\fixcolspacing\n"
			ans_str += "\t\\end{multicols}\n"
			# newpage option
			if "break" in self.ans_options:
				ans_str += "\t\\newpage\n"
			# assign result
			self.ans_key_str = ans_str
			if "sheet" in self.ans_options:
				self.ans_sheet_str = ans_str
		elif self.mod_type == "frq":
			self.ans_key_str = self.gen_frq_ans(initial_qcount, solutions, sheet=False)
			if "sheet" in self.ans_options:
				self.ans_sheet_str = self.gen_frq_ans(initial_qcount, solutions, sheet=True)

	def gen_frq_ans(self, initial_qcount, solutions, sheet):		
		ans_str = ""
		if "twocolumn" in self.ans_options:
			ans_str += "\\setlength{\\columnsep}{0.40 in}\n" \
					+ "\\setlength{\\columnseprule}{0.2 pt}\n" \
					+ "\\begin{multicols*}{2}\n" \
					+ "\\renewcommand{\\questionshook}{\\setlength{\\leftmargin}{0.15 in}}\n"
		ans_str += "\t\\begin{questions}\n" \
				+ "\t\\setcounter{{question}}{{{}}}\n".format(initial_qcount)
		prev = [initial_qcount, 0, 0]
		level = 0
		ans_stubs = ["\\question", "\\part", "\\subpart"]
		tab_stubs = ["\t", "\t\t", "\t\t\t"]
		for (hierarchy, height_str, sol) in solutions:
			# figure out how the hierarchy changed from previous q
			diff = [hierarchy[i] - prev[i] for i in range(len(hierarchy))]
			# highest level of hierarchy change
			topmost_change_ind = 0 if diff[0]!=0 else (1 if diff[1]!=0 else 2)
			# adding another question/part/subpart to an existing list
			if topmost_change_ind == level:
				# add the qps
				ans_str += "{}{}\n".format(tab_stubs[level], ans_stubs[level])
				# in the case that the new qps has subparts, need to start env and put in dummy qps
				i = level + 1
				while i<3 and hierarchy[i]!=0:
					level = i
					ans_str += "{}\\begin{{{}s}}\n".format(tab_stubs[i], ans_stubs[i][1:])
					ans_str += "{}{}\n".format(tab_stubs[i], ans_stubs[i])
					i += 1
			# ending a sublist, adding a new higher-level qps
			elif topmost_change_ind < level:
				# need to close existing environments, up to the necessary level
				i = level
				while i>topmost_change_ind:
					ans_str += "{}\\end{{{}s}}\n".format(tab_stubs[i], ans_stubs[i][1:])
					i -= 1
				# need to close existing environments, up to the necessary level
				level = i
				ans_str += "{}{}\n".format(tab_stubs[i], ans_stubs[i])
				i += 1
				while i<3 and hierarchy[i]!=0:
					level = i
					ans_str += "{}\\begin{{{}s}}\n".format(tab_stubs[i], ans_stubs[i][1:])
					ans_str += "{}{}\n".format(tab_stubs[i], ans_stubs[i])
					i += 1
			# putting in the answer
			if (sheet):
				ans_str += "\t{}\\ \\vspace{{{}}}\n".format(tab_stubs[level], height_str)
			else:
				ans_str += "\t{}{}\n".format(tab_stubs[level], sol)
			prev = hierarchy
		# cleanup: close existing environments
		while level>=0:
			ans_str += "{}\\end{{{}s}}\n".format(tab_stubs[level], ans_stubs[level][1:])
			level -= 1
		if "twocolumn" in self.ans_options:
			ans_str += "\t\\end{multicols*}\n" \
					+ "\\renewcommand{\\questionshook}{}\n"
		# newpage option
		if "break" in self.ans_options:
			ans_str += "\t\\newpage\n"
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
		# top/bottom margins for each module, inches
		spacings = {"title": "0.10", "subtitle": "0.05", "author": "0.05",\
					"info": "0.15", "text":"0.10", "latex":"0.00", "table":"0.05"}
		tex_str = "\\begin{coverpages}\n"
		# section bangs
		for line in self.content:
			if re.match(bang_pattern, line):
				tex_str += bang_to_tex(line)
		# module tex
		for mod in self.modules:
			content = mod.content
			mt = mod.mod_type
			bangs = mod.bangs
			if mt not in spacings:
				compile_error("Invalid module type in Cover: " + mt)
			# centering
			centered_modules = ["title", "subtitle", "author", "info"]
			if mt in centered_modules and not centered:
				tex_str += "\t\\begin{center}\n"
				centered = True
			elif mt not in centered_modules and centered:
				tex_str += "\t\\end{center}\n"
				centered = False
			# spacing
			spacing = spacings[mt]
			tex_str += "\t\t\\vspace{{{} in}}\n".format(spacing)
			# module content
			if mt in ["text", "latex", "table"]:
				tex_str += mod.to_tex(qcount=None)
			else:
				if mt in ["info", "author"]:
					tex_str += "\t\t\\par\n"
					tex_str += "\t\t\\def\\arraystretch{2}\\tabcolsep=3pt\n\t\t\\begin{tabular}{r r}\n"
				if mt == "author":
					tex_str += "\t\t\t\\textbf{{Written by:}}\n"
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
								tex_str += "\t\t\t & \\textbf{{{}}}, \\textit{{{}}} \\\\\n".format(
									author, author_info)
							else:
								tex_str += "\t\t\t & \\textbf{{{}}} \\\\\n".format(content[0])
						if mt == "info":
							tex_str += "\t\t\t\\textbf{{{}:}} & \\makebox[4in]{{\\hrulefill}} \\\\\n".format(
								line.strip())
					else:
						tex_str += bang_to_tex(line, centered=True)
				if mt in ["info", "author"]:
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
				tex_str += bang_to_tex(line)
		# module tex
		for module in self.modules:
			tex_str += module.to_tex(qcount)
		return tex_str

	def get_packages(self):
		tex_str = ""
		for line in self.content:
			if re.match(r"\s*!pkg", line):
				tex_str += bang_to_tex(line)
		return tex_str

	def ans_tex(self, ans_key):
		"""
		Returns tex for the answer key or answer sheet.

		ans_key (bool): True if we're generating the answer key (as opposed to sheet).
		"""
		# don't want to generate answer key for header or cover
		if self.sec_type != "section":
			return ""
		ans_str = ""
		for module in self.modules:
			if module.mod_type in ["match", "tf", "frq", "mc"]:
				if ans_key:
					ans_str += module.ans_key_str
				elif "sheet" in module.ans_options:
					ans_str += module.ans_sheet_str
				ans_str += "\\par\\vspace{.05in}\n"
		return ans_str


class Exam:

	def __init__(self):
		self.sections = []
		# is in list so that updates elsewhere will stick around (pass by reference hack)
		self.question_counter = [0]

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
		tex_str = tex_template + "\n"
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
		tex_str += "\\end{document}\n"
		return tex_str

	def ans_key_tex(self):
		"""Returns answer key tex."""
		ans_str = self.exam_preamble()
		ans_str += "\\printanswers" + "\n"
		ans_str += "\n\\begin{document}\n"
		ans_str += "\\section*{Answer Key}\n"
		for section in self.sections:
			ans_str += section.ans_tex(True)
		ans_str += "\\end{document}\n"
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

	return exam.to_tex(), exam.ans_key_tex()

def read_template(dir):
	"""
	Reads the template tex file for the preamble.

	dir (str): The directory containing the template file.
	"""
	with open(os.path.join(dir, "template.tex"), 'r') as filein:
		global tex_template
		for line in filein:
			# update global variable
			tex_template += line

def main():
	read_template(os.path.dirname(sys.argv[0]))
	# existence of argument is checked in executable script
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
