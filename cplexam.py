import sys
import re

def compile_error(err):
	print(err)
	sys.exit(0)

class ExamModule:
	def __init__(self, mod_type, content):
		self.mod_type = mod_type
		content = [line.strip() for line in content if not re.match(r"\s*$", line)]
		bang_pattern = r"\s*!(newpage|options|gap|img)"
		self.bangs = [line for line in content if re.match(bang_pattern, line)]
		self.content = [line for line in content if line not in self.bangs]
	def get_type(self):
		return self.mod_type
	def get_content(self):
		return self.content
	def to_string(self):
		content = ""
		for line in self.content:
			content += line
		return content.strip()
	def to_tex(self):
		tex_str = ""
		if self.mod_type == "title":
			tex_str += "\\par\\noindent \\textbf{{\\large {}}}\n".format(self.content[0])
		elif self.mod_type == "instructions":
			for line in self.content:
				tex_str += "\\par\\noindent {}".format(line)
		elif self.mod_type == "mc":
			tex_str += self.mc_tex()
		elif self.mod_type == "frq":
			tex_str += self.frq_tex()
		elif self.mod_type == "match":
			tex_str += self.match_tex()
		elif self.mod_type == "text":
			tex_str += self.text_tex()
		else:
			compile_error("Illegal module: {}", self.mod_type)
		return tex_str
	def mc_tex(self):
		return ""
	def frq_tex(self):
		return ""
	def match_tex(self):
		return ""
	def text_tex(self):
		return ""


class ExamSection:
	def __init__(self, sec_type, content):
		self.sec_type = sec_type
		self.content = []
		self.hasMatching = False
		self.modules = []
		self.to_modules(content)
	def get_type(self):
		return self.sec_type
	def to_modules(self,content):
		ind = 0
		tag_pattern = r"(?i)\s*\[(title|subtitle|author|header|info|instructions|mc|frq|match|text)\]"
		while ind<len(content) and not re.match(tag_pattern, content[ind]):
			self.content.append(content[ind])
			ind += 1
		mod_type = None
		mod_content = []
		while ind < len(content):
			line = content[ind]
			if re.match(tag_pattern, content[ind]):
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
	def to_tex(self):
		if self.sec_type == "cover":
			return self.cover_to_tex()
		else:
			return self.section_to_tex()
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
		for mod in self.modules:
			content = mod.get_content()
			mt = mod.get_type()
			if mt in ["title", "subtitle", "author", "info"] and not centered:
				tex_str += "\t\\begin{center}\n"
				centered = True
			elif mt not in ["title", "subtitle", "author", "info"] and centered:
				tex_str += "\t\\end{center}\n"
				centered = False
			if mt == "title":
				tex_str += "\t\t\\vspace{0.10 in}\n"
				tex_str += "\t\t\\par\\noindent\\textbf{{\\Huge  {}}}\n".format(content[0]) 
				tex_str += "\t\t\\vspace{0.10 in}\n"
			if mt == "subtitle":
				tex_str += "\t\t\\vspace{0.05 in}\n"
				tex_str += "\t\t\\par\\noindent\\textbf{{\\large {}}}\n".format(content[0])
				tex_str += "\t\t\\vspace{0.05 in}\n"
			if mt == "author":
				tex_str += "\t\t\\vspace{0.05 in}\n"
				if len(content) == 2:
					tex_str += "\t\t\\par\\noindent\\textbf{{Written by: {}}}, \\textit{{{}}}\n".format(
						content[0], content[1])
				else:
					tex_str += "\t\t\\textbf{{Written by: {}}}\n".format(mod.to_string())
				tex_str += "\t\t\\vspace{0.05 in}\n"
			if mt == "info":
				if len(content) == 0:
					compile_error("Empty Info module (cover).")
				tex_str += "\t\t\\vspace{0.15 in}\n"
				tex_str += "\t\t\\def\\arraystretch{2}\\tabcolsep=3pt\n\t\t\\begin{tabular}{l r}\n"
				for line in content:
					tex_str += "\t\t\t\\textbf{{{}:}} & \\makebox[4in]{{\\hrulefill}} \\\\\n"\
									.format(line.strip())
				tex_str += "\t\t\\end{tabular}\n"
				tex_str += "\t\t\\vspace{0.15 in}\n"
			if mt == "instructions":
				if len(content) == 0:
					compile_error("Empty Instructions module (cover).")
				tex_str += "\t\\vspace{0.15 in}\n"
				for line in content:
					tex_str += "\t\\par {}\n".format(line.strip())
				tex_str += "\t\\vspace{0.15 in}\n"
		if centered:
			tex_str += "\t\\end{center}\n"
			centered = False
		tex_str += "\\end{coverpages}\n"
		return tex_str
	def section_to_tex(self):
		tex_str = "\n\\newpage\n"
		for module in self.modules:
			tex_str += module.to_tex()
		return tex_str

class Exam:
	def __init__(self):
		self.sections = []
		self.hasMatching = False
		self.hasCover = False
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
			if re.match(tag_pattern, lines[ind]):
				if sec_type:
					exam.add_section(sec_type, sec_content)
				splt = re.match(tag_pattern, line).end()
				sec_type = line[:splt].strip()[1:-1].lower()
				sec_content = [line[splt:]]
				ind += 1
			else:
				sec_content.append(line)
				ind += 1
		exam.add_section(sec_type, sec_content)

	exam.verify_sections()

	tex_str = exam.preamble(labelled_template)
	for section in exam.get_sections():
		tex_str += section.to_tex()
	tex_str += "\\end{document}"
	# print(tex_str)

	return tex_str

def read_template():
	with open("template.tex", 'r') as filein:
		labels = {}
		label = ""
		for line in filein:
			if not re.match(r"\s*$", line):
				if re.match(r"\s*%", line):
					splt = re.search("%", line).end()
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
	filename = filename[:re.search("\\.", filename).end()] + "tex"
	with open(filename, 'w+') as fileout:
		fileout.write(tex_str)

if __name__ == "__main__":
	main()