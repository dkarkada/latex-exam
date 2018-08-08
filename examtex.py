import sys
import re
import math
from random import shuffle

def compile_error(err):
	print(err)
	sys.exit(0)

def make_latex_safe(line):
	line = re.sub("%", "\\%", line)
	match = re.search("\"[^\"]*\"", line)
	while match:
		repl = "``{}''".format(match.group(0)[1:-1])
		line = line[:match.start()] + repl + line[match.end():]
		match = re.match("\"[^\"]*\"", line)
	return line

def handle_bang(line, context, options):
	tex_str = ""
	match_0 = re.search("{", line)
	match_1 = re.search("}", line)
	args = None
	if match_0 and match_1 and match_0.end() < match_1.start():
		args = line[match_0.end():match_1.start()]
		args = args.split(",")
		args = [arg.strip() for arg in args if arg.strip()!=""]
	if re.match(r"\s*!img", line):
		if not args:
			compile_error("Expected args for img in cover.")
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
	if re.match(r"\s*!options", line):
		for arg in args:
			match = re.search("=", arg)
			if match:
				options[arg[:match.start()]] = arg[match.end():]
			else:
				options[arg] = ''
	return tex_str

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
		self.ans_tex = ""
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
				tex_str += handle_bang(line, context=None, options={})
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
				tex_str += handle_bang(line, context=None, options={})
		return tex_str
	def mc_tex(self, qcount):
		content = self.content
		bangs = self.bangs
		options = self.options
		questions = []
		solutions = []
		question_str = None
		choices = []
		correct_choice = None
		bang_tex = []
		initial_qcount = qcount[0]+1
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
				bang_line = handle_bang(line, context={"twocolumn":twocolumn}, options=options)
				if bang_line != "":
					bang_tex.append(bang_line)
		questions.append(MCQuestion(question_str, choices, correct_choice))
		solutions.append(questions[-1].get_answer())
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
		if "ans" in options and options["ans"]=="sheet":
			self.ans_tex = self.gen_ans(initial_qcount, solutions)
		else:
			self.ans_tex = tex_str
		return tex_str
	def frq_tex(self, qcount):
		content = self.content
		bangs = self.bangs
		options = self.options
		# we actually want to start at qcount+1, but since prev=count=0, we naturally increment on first pass
		hierarchy_counter = qcount[0]
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
						hierarchy_counter = math.floor(hierarchy_counter+1)
					elif indent_change == -1:
						if indent_count == 0:
							tex_str += "\t\\end{parts}\n"
							hierarchy_counter = math.floor(hierarchy_counter+1)
						else:
							tex_str += "\t\t\\end{subparts}\n"
							hierarchy_counter = math.floor(hierarchy_counter*100+1) / 100
					elif indent_change == 0:
						hierarchy_counter += 10**(-2*(indent_count))
					elif indent_change == 1:
						if indent_count == 1:
							tex_str += "\t\\begin{parts}\n"
							hierarchy_counter += 0.01
						elif indent_count == 2:
							tex_str += "\t\t\\begin{subparts}\n"
							hierarchy_counter += 0.0001
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
					match = re.match(r"{\s*\d+[^}]*}", line)
					if match:
						height_str = line[match.start()+1:match.end()-1]
						height_str = "[{}]".format(height_str)
						line = line[match.end():]
					else:
						height_str = "[{} pt]".format(20*math.ceil(len(line)/75))
					tab_str = "\t"*(indent_count+1)
					tex_str += "{}\\begin{{solution}}{}\n".format(tab_str,
						height_str if "ans" not in options or options["ans"]=="here" else "")
					tex_str += "{}{}\n".format(tab_str, line)
					solutions.append((round(hierarchy_counter, 4), line))
					tex_str += tab_str + "\\end{solution}\n"
			else:
				tex_str += handle_bang(line, context=[], options=options)
		indent_change = 0 - prev_indent_count
		line = line.strip()
		if indent_change == -2:
			tex_str += "\t\t\\end{subparts}\n"
			tex_str += "\t\\end{parts}\n"
		elif indent_change == -1:
			tex_str += "\t\\end{parts}\n"
		tex_str += "\\end{questions}\n"
		if "ans" in options and options["ans"]=="sheet":
			self.ans_tex = self.gen_ans(None, solutions)
		else:
			self.ans_tex = tex_str 
		return tex_str
	def match_tex(self, qcount):
		content = self.content
		bangs = self.bangs
		options = self.options
		question_data = []
		solutions = []
		initial_qcount = qcount[0]+1
		for line in content:
			if line not in bangs:
				line = make_latex_safe(line)
				if len(line.split("::")) != 2:
					compile_error("Invalid syntax in match: {}", line)
				line = line.split("::")
				question_data.append(line)
			else:
				handle_bang(line, context=None, options=options)
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
		if "ans" in options and options["ans"]=="sheet":
			self.ans_tex = self.gen_ans(initial_qcount, solutions)
		else:
			self.ans_tex = tex_str 
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
				tex_str += handle_bang(line, context=None, options={})				
		return tex_str
	def gen_ans(self, initial_qcount, solutions):
		print("AAE")

class ExamSection:
	def __init__(self, sec_type, content):
		self.sec_type = sec_type
		self.content = []
		self.hasMatching = False
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
					self.add_module(mod_type, mod_content)
				splt = re.match(tag_pattern, line).end()
				mod_type = line[:splt].strip()[1:-1].lower()
				mod_content = [line[splt:]]
				ind += 1
			else:
				mod_content.append(line)
				ind += 1
		self.add_module(mod_type, mod_content)
	def add_module(self, mod_type, content):
		if mod_type == "match":
			self.hasMatching = True
		self.modules.append(ExamModule(mod_type, content))
	def to_tex(self, qcount):
		if self.sec_type == "cover":
			return self.cover_to_tex()
		else:
			return self.section_to_tex(qcount)
	def get_header_info(self):
		assert self.sec_type == "cover", "Cannot get header info: not a cover."
		header = None
		for module in self.modules:
			if module.mod_type == "header":
				header = module
		if not header:
			return ["", "", ""]
		content = header.content
		if len(content) != 3:
			compile_error("Header must have 3 elements.")
		return content
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
					tex_str += handle_bang(line, context={"centered": centered}, options={})
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

class Exam:
	def __init__(self):
		self.sections = []
		self.hasMatching = False
		self.hasCover = False
		self.question_counter = [0]
	def get_sections(self):
		return self.sections
	def add_section(self, sec_type, content):
		if sec_type == "cover":
			self.hasCover = True
		self.sections.append(ExamSection(sec_type, content))
		self.hasMatching = self.hasMatching or self.sections[-1].hasMatching
	def verify_sections(self):
		sections = self.sections
		if len(sections) == 0:
			compile_error("No sections found.")
		s_count = cover_count = 0
		for section in sections:
			if section.get_type() == "section":
				s_count += 1
			elif section.get_type() == "cover":
				cover_count += 1
		assert len(sections) == s_count+cover_count, "Misidentified section."
		if cover_count > 1:
			compile_error("Only one cover allowed.")
		if cover_count==1 and sections[0].get_type()!="cover":
			compile_error("Cover must be first section.")
		return None
	def preamble(self, template):
		tex_str = template["preamble"] + "\n"
		if self.hasMatching:
			tex_str += template["wordbank"] + "\n"
		if self.hasCover:
			cover = self.sections[0]
			header_elems = cover.get_header_info()
			header_elems = [item if not re.match("//", item) else "" for item in header_elems]
			if not (header_elems[0] == header_elems[1] == header_elems[2] == ""):
				e0 = header_elems[0] if header_elems[0]!="" else ""
				e1 = header_elems[1] + " - Page \\thepage" if header_elems[1]!="" else ""
				e2 = header_elems[2] + ":\\kern .5 in" if header_elems[2]!="" else ""
				tex_header = "\\header{{{}}}{{{}}}{{{}}}\n"\
									.format(e0, e1, e2)
				tex_str += "\n\\pagestyle{head}\n" + tex_header + "\\headrule\n"
		tex_str += "\n\\begin{document}\n"
		return tex_str
	def to_tex(self, labelled_template):		
		tex_str = self.preamble(labelled_template)
		for section in self.get_sections():
			tex_str += section.to_tex(self.question_counter)
		tex_str += "\\end{document}"
		return tex_str

def generate_tex_string(filename, labelled_template):
	exam = Exam()
	with open(filename, 'r') as filein:
		lines = filein.readlines()
		ind = 0
		tag_pattern = r"(?i)\s*\[(cover|section)\]"
		while ind<len(lines) and not re.match(tag_pattern, lines[ind]):
			ind += 1
		if ind >= len(lines):
			compile_error("No sections found.")
			return None
		sec_type = None
		sec_content = []
		while ind < len(lines):
			line = lines[ind]
			match = re.match(tag_pattern, line)
			if match:
				if sec_type:
					exam.add_section(sec_type, sec_content)
				splt = match.end()
				sec_type = line[:splt].strip()[1:-1].lower()
				sec_content = [line[splt:]]
				ind += 1
			else:
				sec_content.append(line)
				ind += 1
		exam.add_section(sec_type, sec_content)

	exam.verify_sections()
	return exam.to_tex(labelled_template)

def read_template():
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

def main():
	# existence of argument is checked in bash script
	filename = sys.argv[1]
	# read template file
	labelled_template = read_template()	
	tex_str = generate_tex_string(filename, labelled_template)
	# write to tex file
	match = re.search("\\.", filename)
	if match:
		filename = filename[:match.start()]
	filename = filename + ".tex"
	with open(filename, 'w+') as fileout:
		fileout.write(tex_str)

if __name__ == "__main__":
	main()