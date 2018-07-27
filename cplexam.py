import sys
import re

class ExamModule:
	def __init__(self, mod_type):
		self.mod_type = mod_type;
	def set_content(self, content):
		self.content = content;
	def get_content(self):
		return self.content;

def generate_tex_string(filename, labelled_template):
	with open(filename, 'r') as file:
		for line in file:




def read_template():
	with open("template.tex", 'r') as file:
		labels = {};
		label = "";
		for line in file:
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
	generate_tex_string(filename, labelled_template)




if __name__ == "__main__":
	main();