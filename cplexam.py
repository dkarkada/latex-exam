import sys
import re

class ExamModule:
	def __init__(self, mod_type, content):
		self.mod_type = mod_type;
		self.content = content;
	def to_string(self):
		content = "";
		for line in self.content:
			content += line;
		return content.strip();

class ExamSection:
	def __init__(self, sec_type, content):
		self.sec_type = sec_type;
		self.content = [];
		self.hasMatching = False;
		self.modules = [];
		self.to_modules(content);
	def get_type(self):
		return self.sec_type;
	def to_modules(self,content):
		ind = 0;
		header_tag = r"(?i)\s*\[(title|subtitle|author|contact|studentid|info|instructions|mc|frq|match|text)\]";
		while ind<len(content) and not re.match(header_tag, content[ind]):
			self.content.append(content[ind]);
			ind += 1;
		mod_type = None;
		mod_content = [];
		while ind < len(content):
			line = content[ind];
			if re.match(header_tag, content[ind]):
				if mod_type:
					self.add_module(mod_type, mod_content);
				splt = re.match(header_tag, line).end();
				mod_type = line[:splt].strip()[1:-1].lower();
				mod_content = [line[splt:]];
				ind += 1;
			else:
				mod_content.append(line);
				ind += 1;
		self.add_module(mod_type, mod_content);
	def add_module(self, mod_type, content):
		if mod_type == "match":
			self.hasMatching = True;
		self.modules.append(ExamModule(mod_type, content));
	def to_tex(self, cnt):
		if self.sec_type == "cover":
			return self.cover_to_tex();
		else:
			return self.section_to_tex();
	def get_cover_info(self):
		if self.sec_type != "cover":
			return None, None, None;
		title = subtitle = identifier = None;
		for module in self.modules:
			if module.mod_type == "title":
				title = module.to_string();
			if module.mod_type == "subtitle":
				subtitle = module.to_string();
			if module.mod_type == "studentid":
				identifier = module.to_string();
		return title, subtitle, identifier;
	def cover_to_tex(self):
		return "";
	def section_to_tex(self):
		return "";

class Exam:
	def __init__(self):
		self.sections = [];
		self.hasMatching = False;
		self.hasCover = False;
	def get_sections(self):
		return self.sections;
	def add_section(self, sec_type, content):
		if sec_type == "cover":
			self.hasCover = True;
		self.sections.append(ExamSection(sec_type, content));
		self.hasMatching = self.hasMatching or self.sections[-1].hasMatching;
	def verify_sections(self):
		sections = self.sections;
		if len(sections) == 0:
			return "Error: No sections found.";
		s_count = cover_count = 0;
		for section in sections:
			if section.get_type() == "section":
				s_count += 1;
			elif section.get_type() == "cover":
				cover_count += 1;
		if len(sections) - (s_count+cover_count) != 0:
			return "Internal error: Misidentified section."
		if cover_count > 1:
			return "Error: Only one cover allowed."
		if cover_count==1 and sections[0].get_type()!="cover":
			return "Error: Cover must be first section."
		return None;
	def preamble(self, template):
		tex_str = template["preamble"] + "\n";
		if self.hasMatching:
			tex_str += template["wordbank"] + "\n";
		if self.hasCover:
			cover = self.sections[0];
			title, subtitle, identifier = cover.get_cover_info();
			tex_header = "";
			if title:
				tex_str += "\\newcommand{{\\examtitle}}{{{}}}\n".format(title);
				tex_header += "{\\examtitle\\ - Page \\thepage}";
			if subtitle:
				tex_str += "\\newcommand{{\\examsubtitle}}{{{}}}\n".format(subtitle);
				tex_header = "{\\examsubtitle}" + tex_header;
			if identifier:
				tex_str += "\\newcommand{{\\identifier}}{{{}}}\n".format(identifier);
				tex_header += "{\\identifier:\\kern .5 in}";
			tex_str += "\\pagestyle{head}\n" + tex_header + "\n\\headrule";
			print(tex_str);


def generate_tex_string(filename, labelled_template):
	exam = Exam();
	with open(filename, 'r') as filein:
		lines = filein.readlines();
		ind = 0;
		header_tag = r"(?i)\s*\[(cover|section)\]";
		while ind<len(lines) and not re.match(header_tag, lines[ind]):
			ind += 1;
		if ind >= len(lines):
			print("Error: No sections found.");
			return None;
		sec_type = None;
		sec_content = [];
		while ind < len(lines):
			line = lines[ind];
			if re.match(header_tag, lines[ind]):
				if sec_type:
					exam.add_section(sec_type, sec_content);
				splt = re.match(header_tag, line).end();
				sec_type = line[:splt].strip()[1:-1].lower();
				sec_content = [line[splt:]];
				ind += 1;
			else:
				sec_content.append(line);
				ind += 1;
		exam.add_section(sec_type, sec_content);

	error = exam.verify_sections();
	if error:
		print(error);
		return None;

	tex_str = exam.preamble(labelled_template);
	cnt = 0;
	for section in exam.get_sections():
		tex_str += section.to_tex(cnt);
		cnt += 1;
	print(cnt);

	return tex_str;

def read_template():
	with open("template.tex", 'r') as filein:
		labels = {};
		label = "";
		for line in filein:
			if not re.match(r"\s*$", line):
				if re.match(r"\s*%", line):
					splt = re.search("%", line).end();
					label = line[splt:].strip();

				elif label != "":
					if label in labels:
						labels[label] += line;
					else:
						labels[label] = line;
	return labels;

def main():
	# existence of argument is checked in bash script
	filename = sys.argv[1];
	# read template file
	labelled_template = read_template();	
	tex_str = generate_tex_string(filename, labelled_template)




if __name__ == "__main__":
	main();