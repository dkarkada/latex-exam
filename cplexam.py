import sys
import re

class ExamModule:
	def __init__(self, mod_type, content):
		self.mod_type = mod_type;
		self.content = content;
	def get_content(self):
		return self.content;
	def get_type(self):
		return self.type;

class Exam:
	def __init__(self):
		self.sections = [];
		self.hasMatching = False;
		self.hasCover = False;
	def get_sections(self):
		return self.sections;
	def add_module(self, mod_type, mod_content):
		if mod_type == "cover":
			self.hasCover = True;
		self.sections.append(ExamModule(mod_type, mod_content));
	def verify_modules(self):
		if len(sections) == 0:
			return "Error: No sections found.";
		s_count = cover_count = 0;
		for section in sections:
			if section.get_type() = "section":
				s_count += 1;
			elif section.get_type() = "cover":
				cover_count += 1;
		if len(sections) - (s_count+cover_count) != 0:
			return "Internal error: Misidentified section."
		if cover_count > 1:
			return "Error: Only one cover allowed."
		if cover_count==1 and sections[0].get_type!="cover":
			return "Error: Cover must be first section."
		return None;

def generate_tex_string(filename, labelled_template):
	exam = Exam();
	with open(filename, 'r') as filein:
		lines = filein.readlines();
		ind = 0;
		header = r"(?i)\s*\[(cover|section)\]";
		while ind<len(lines) and not re.match(header, lines[ind]):
			ind += 1;
		if ind >= len(lines):
			print("Error: No sections found.");
			return None;
		mod_type = None;
		mod_content = None;
		while ind < len(lines):
			line = lines[ind];
			if re.match(header, lines[ind]):
				if mod_type:
					exam.add_module(mod_type, mod_content);
				splt = re.match(header, line).end();
				mod_type = line[:splt].strip()[1:-1].lower();
				mod_content = line[splt:];
				ind += 1;
			else:
				mod_content += line;
				ind += 1;
		exam.add_module(mod_type, mod_content);

	error = exam.verify_modules();
	if error:
		print(error);
		return None;

	tex_str = "";
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