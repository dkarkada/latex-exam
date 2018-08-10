import sys
import re
import math
from random import shuffle

def compile_error(err):
	print(err)
	sys.exit(0)

def make_latex_safe(line):
	line = line.replace("%", "\\%")
	match = re.search("\"[^\"]*\"", line)
	while match:
		repl = "``{}''".format(match.group(0)[1:-1])
		line = line[:match.start()] + repl + line[match.end():]
		match = re.match("\"[^\"]*\"", line)
	return line

def bang_args(line):
	match_0 = re.search("{", line)
	match_1 = re.search("}", line)
	if match_0 and match_1 and match_0.end() < match_1.start():
		args = line[match_0.end():match_1.start()]
		args = args.split(",")
		args = [arg.strip() for arg in args if arg.strip()!=""]
		return args
	return None

def bang_to_tex(line, context):
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
	return tex_str

def update_options(line, options):
	args = bang_args(line)
	if re.match(r"\s*!options", line):		
		if not args:
			compile_error("Expected args for options.")
		for arg in args:
			match = re.search("=", arg)
			if match:
				options[arg[:match.start()]] = arg[match.end():]
			else:
				options[arg] = ''

class MCQuestion:
	def __init__(self, question, choices, correct_choice):
		self.question = question
		self.choices = choices
		if not correct_choice:
			self.correct_choice = self.choices[0]
			shuffle(self.choices)
		else:
			self.correct_choice = correct_choice
	def to_tex(self):
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
	def calc_height(self, qwidth, choicewidth):
		height = 11*math.ceil(len(self.question)/qwidth)+10
		for choice in self.choices:
			height += 11*math.ceil(len(choice)/choicewidth)+5
		return height
	def get_answer(self):
		ind = self.choices.index(self.correct_choice)
		return chr(65 + ind)

class ExamModule:
	def __init__(self, mod_type, content):
		self.mod_type = mod_type
		self.content = [line.rstrip() for line in content if not re.match(r"\s*$", line)]
		bang_pattern = r"\s*!(newpage|options|gap|img)"
		self.bangs = [line for line in self.content if re.match(bang_pattern, line)]
		self.options = {}	
		for line in self.bangs:
			update_options(line, options=self.options)
		self.ans_str = ""
	def get_type(self):
		return self.mod_type
	def get_content(self):
		return self.content
	def get_bangs(self):
		return self.bangs
	def to_string(self):
		content = ""
		for line in self.content:
			content += line
		return content.strip()
	def to_tex(self, qcount):
		tex_str = ""
		tex_generator = getattr(self, self.mod_type+"_tex", None)
		if not tex_generator:
			compile_error("Illegal module: {}", self.mod_type)
		tex_str += tex_generator(qcount)
		return tex_str
	def title_tex(self, qcount):
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
	def mc_tex(self, qcount):
		content = self.content
		bangs = self.bangs
		options = self.options
		initial_qcount = qcount[0]
		questions = []
		solutions = []
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
					match = re.search("{C}", line)
					if match:
						line = line[:match.start()].strip()
						correct_choice = line
						choices.append(line)
					else:
						choices.append(line.strip())
				else:
					if len(choices) == 0:
						compile_error("No answer choices found: {}", question_str)
					questions.append(MCQuestion(question_str, choices, correct_choice))
					solutions.append(questions[-1].get_answer())
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
		questions.append(MCQuestion(question_str, choices, correct_choice))
		solutions.append(questions[-1].get_answer())

		# generate tex
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
		if "intro-height" in options:
			page_height_pt = 672 - int(options["intro-height"])
		else:
			page_height_pt = 500
		for question in questions:
			if type(question) == MCQuestion:
				qwidth, choicewidth = (50, 43) if "twocolumn" in options else (100, 80)
				qheight = question.calc_height(qwidth, choicewidth)
				page_height_pt = 672 if col_num>2 else page_height_pt
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
			else: # "question" is actually bang tex
				tex_str += question
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
		content = self.content
		bangs = self.bangs
		options = self.options
		hierarchy = [qcount[0], 0, 0]
		solutions = []
		prev_indent_count = indent_count = 0
		tex_str = "\\begin{questions}\n"
		tex_str += "\\setcounter{{question}}{{{}}}\n".format(qcount[0])
		for line in content:
			if line not in bangs:
				line = make_latex_safe(line)
				if not re.match(r"\s*//", line):
					indent_count = len(line) - len(line.lstrip("\t"))
					indent_change = indent_count - prev_indent_count
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

					match = re.match(r"{\s*\d+\s*}", line)
					point_str = ""
					if match:
						point_str = match.group(0)[1:-1]
						point_str = "[{}]".format(point_str)
						line = line[match.end():]
					if indent_count == 0:
						tex_str += "\\question{} {}\n".format(point_str, line)
						qcount[0] += 1
					elif indent_count == 1:
						tex_str += "\t\\part{} {}\n".format(point_str, line)
					else:
						tex_str += "\t\t\\subpart{} {}\n".format(point_str, line)
					prev_indent_count = indent_count
				else:
					line = line.strip()[2:].strip()
					match = re.match(r"{\s*\d+\s*}", line)
					if match:
						height = int(line[match.start()+1:match.end()-1])*20
						height_str = "[{} pt]".format(height)
						line = line[match.end():]
					else:
						height_str = "[{} pt]".format(20*math.ceil(len(line)/75))
					tab_str = "\t"*(indent_count+1)
					tex_str += "{}\\begin{{solution}}{}\n".format(tab_str,
						height_str if "ans" not in options or options["ans"]=="here" else "")
					tex_str += "{}{}\n".format(tab_str, line)
					solutions.append((hierarchy.copy(), height_str, line))
					tex_str += tab_str + "\\end{solution}\n"
			else:
				tex_str += bang_to_tex(line, context=[])
		indent_change = 0 - prev_indent_count
		line = line.strip()
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
	def match_tex(self, qcount):
		content = self.content
		bangs = self.bangs
		options = self.options
		question_data = []
		solutions = []
		initial_qcount = qcount[0]
		for line in content:
			if line not in bangs:
				line = make_latex_safe(line)
				if len(line.split("::")) != 2:
					compile_error("Invalid syntax in match: {}", line)
				line = line.split("::")
				question_data.append(line)
		if "noshuffle" not in options:
			shuffle(question_data)
		ans_list = sorted(list(set([line[0] for line in question_data])))
		if len(ans_list) > 26:
			compile_error("Too many choices in word bank.")
		tex_str = ""
		tex_str += "\\begin{wordbank}{3}\n"
		for ans in ans_list:
			tex_str += "\t\\wbelem{{{}}}\n".format(ans)
		tex_str += "\\end{wordbank}\n"
		tex_str += "\\begin{questions}\n"
		tex_str += "\\setcounter{{question}}{{{}}}\n".format(qcount[0])
		if not "showpoints" in options:
			tex_str += "\t\\hidepoints\n"
		for line in question_data:
			question, ans = line[1], line[0]
			ans_letter = chr(65 + ans_list.index(ans))
			solutions.append(ans_letter)
			tex_str += "\t\\question\\match{{{}}}{{{}}}\n".format(ans_letter, question)
			qcount[0] += 1
		if not "showpoints" in options:
			tex_str += "\t\\showpoints\n"	
		tex_str += "\\end{questions}\n"

		# generate answers
		if self.has_ans_sheet():
			self.ans_str = self.gen_ans(initial_qcount, solutions)
		else:
			self.ans_str = tex_str 
		return tex_str
	def text_tex(self, qcount):
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
	def has_ans_sheet(self):
		return "ans" in self.options and self.options["ans"]=="sheet"
	def gen_ans(self, initial_qcount, solutions):
		ans_str = ""
		if self.mod_type in ["match", "mc"]:
			ans_str += "\t\\raggedcolumns\n"
			ans_str += "\t\\begin{multicols}{5}\n"
			ans_str += "\t\\begin{enumerate}\n"
			ans_str += "\t\\setcounter{{enumi}}{{{}}}\n".format(initial_qcount)
			for sol in solutions:
				ans_str += "\t\\item \\choiceblank{{{}}}\n".format(sol)
			ans_str += "\t\\end{enumerate}\n"
			if len(solutions) % 5 != 0:
				ans_str += "\t\\fixcolspacing\n"
			ans_str += "\t\\end{multicols}\n"
		elif self.mod_type == "frq":
			for (hierarchy, height_str, sol) in solutions:
				qnum = "{}.".format(hierarchy[0])
				qpart = chr(hierarchy[1]+96)+"." if hierarchy[1]!=0 else ""
				qsubpart = ""
				# convert to roman
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
		self.to_modules(content)
	def get_type(self):
		return self.sec_type
	def to_modules(self, content):
		ind = 0
		tag_pattern = r"(?i)\s*\[(title|subtitle|author|header|info|instructions|mc|frq|match|text)\]"
		while ind<len(content) and not re.match(tag_pattern, content[ind]):
			self.content.append(content[ind])
			ind += 1
		mod_type = None
		mod_content = []
		while ind < len(content):
			line = content[ind]
			if re.match(tag_pattern, line):
				if mod_type:
					self.modules.append(ExamModule(mod_type, mod_content))
				splt = re.match(tag_pattern, line).end()
				mod_type = line[:splt].strip()[1:-1].lower()
				mod_content = [line[splt:]]
				ind += 1
			else:
				mod_content.append(line)
				ind += 1
		self.modules.append(ExamModule(mod_type, mod_content))
	def to_tex(self, qcount):
		if self.sec_type == "cover":
			return self.cover_to_tex()
		else:
			return self.section_to_tex(qcount)
	def cover_to_tex(self):
		mod_names = [mod.get_type() for mod in self.modules]
		tex_str = "\\begin{coverpages}\n"
		centered = False
		spacings = {"title": "0.10", "subtitle": "0.05", "author": "0.05",\
					"info": "0.15", "instructions": "0.15", "header": "0.00"}
		for mod in self.modules:
			content = mod.get_content()
			mt = mod.get_type()
			bangs = mod.get_bangs()
			if len(content) == 0:
				compile_error("Empty module in Cover: {}".format(mt))
			if mt not in spacings:
				compile_error("Invalid module type in Cover: {}".format(mt))
			spacing = spacings[mt]
			if mt in ["title", "subtitle", "author", "info"] and not centered:
				tex_str += "\t\\begin{center}\n"
				centered = True
			elif mt not in ["title", "subtitle", "author", "info"] and centered:
				tex_str += "\t\\end{center}\n"
				centered = False
			tex_str += "\t\t\\vspace{{{} in}}\n".format(spacing)
			if mt == "info":
				tex_str += "\t\t\\def\\arraystretch{2}\\tabcolsep=3pt\n\t\t\\begin{tabular}{l r}\n"
			for line in content:
				if line not in bangs:
					line = make_latex_safe(line)
					if mt == "title":
						tex_str += "\t\t\\par\\noindent\\textbf{{\\Huge  {}}}\n".format(line) 
					if mt == "subtitle":
						tex_str += "\t\t\\par\\noindent\\textbf{{\\large {}}}\n".format(line)
					if mt == "author":
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
		if centered:
			tex_str += "\t\\end{center}\n"
			centered = False
		tex_str += "\\end{coverpages}\n"
		return tex_str
	def section_to_tex(self, qcount):
		tex_str = "\n\\newpage\n"
		for module in self.modules:
			tex_str += module.to_tex(qcount)
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
		self.template = self.read_template()
	def read_template():
		"""
		Returns a dict which labels the tex snippets.

		Reads template.tex, contains tex snippets for use in the preamble.
		"""
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
		return labels
	def verify_sections(self):
		"""Make sure nothing is wonky about the exam"""
		sections = self.sections
		if len(sections) == 0:
			compile_error("No sections found.")
		s_count = cover_count = header_count = 0
		for section in sections:
			if section.get_type() == "section":
				s_count += 1
			elif section.get_type() == "cover":
				cover_count += 1
			elif section.get_type() == "header":
				header_count += 1
		assert len(sections) == s_count + cover_count + header_count, "Misidentified section."
		if cover_count > 1:
			compile_error("Only one cover allowed.")
		if header_count > 1:
			compile_error("Only one header allowed.")	
	def get_header_info(self):
		"""Returns a 3-element list of header items, if a header is defined."""
		header = None
		for section in self.section:
			if section.sec_type == "header":
				header = section
		if not header:
			return None
		content = header.content
		if len(content) != 3:
			compile_error("Header must have 3 elements.")
		# Commented lines are filler for empty header item
		return [item if not re.match(r"\s*//", item) else "" for item in content]
	def exam_preamble(self):
		"""Returns tex for exam preamble."""
		tex_str = self.template["preamble"] + "\n"
		tex_str += self.template["answerkey"] + "\n"
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
		tag_pattern = r"(?i)\s*\[(cover|section)\]"
		while ind<len(lines) and not re.match(tag_pattern, lines[ind]):
			ind += 1
		if ind >= len(lines):
			compile_error("No sections found.")
			return None
		# putting together exam
		sec_type = None
		sec_content = []
		while ind < len(lines):
			line = lines[ind]
			match = re.match(tag_pattern, line)
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
	# read template file
	labelled_template = read_template()	
	tex_str, ans_str = generate_tex(filename, labelled_template)
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
