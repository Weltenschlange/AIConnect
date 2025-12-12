import re

class PreProcess:
    PATTERNS = {
        "not_at_position": re.compile(r"(.+)\s+is\s+not\s+in\s+the\s+(\w+)\s+house"),
        "at_position": re.compile(r"(.+)\s+(?:is\s+)?in\s+the\s+(\w+)\s+house"),
        "next_to": re.compile(r"(.+)\s+and\s+(.+)\s+are\s+next\s+to\s+each\s+other"),
        "direct_left": re.compile(r"(.+)\s+is\s+directly\s+(?:left|to\s+the\s+left)\s+of\s+(.+)"),
        "left_of": re.compile(r"(.+)\s+is\s+(?:somewhere\s+)?to\s+the\s+left\s+of\s+(.+)"),
        "distance": re.compile(r"there\s+(?:is|are)\s+(\w+)\s+house[s]?\s+between\s+(.+?)\s+and\s+(.+)"),
        "same": re.compile(r"(.+)\s+is\s+(.+)")
    }

    def preprocess_puzzle(self, puzzle_text):

        parts = re.split(r'##\s*clues:', puzzle_text, flags=re.IGNORECASE)
        
        if len(parts) < 2:
            return "", []
        
        characteristics_text = parts[0]
        clues_text = parts[1]
        
        clues = []
        for line in clues_text.split('\n'):
            line = line.strip()
            if line:
                clue = re.sub(r'^\d+\.\s+', '', line)
                if clue:
                    #replace "-"" with " " so that worlds like hip-hop are now hip hop wich are found in attributes
                    clue = clue.replace("-"," ")
                    clues.append(clue)
        
        return characteristics_text, clues

    def extract_attributes(self, characteristics_text):
        attributes = {}
        
        lines = characteristics_text.split('\n')
        
        for line in lines:
            match = re.match(r'\s*-\s*(.+?):\s*(.+)', line)
            if match:
                description = match.group(1).strip()
                values_str = match.group(2)

                words = description.split()
                attr_name = words[-1] if words else "unknown"

                #this are edge cases when we get genres or models as names use the word before that like music/film or phone/car
                if attr_name == "genres" or attr_name == "models":
                    attr_name = words[-2]

                #the only attribute that is not easely understandeble with my extraction method is the mother attribute
                #thats why i rename it
                if attr_name == "unique":
                    attr_name = "mother"
                if attr_name == "colors":
                    attr_name = words[-2]

                values = re.findall(r'`([^`]+)`', values_str)
                
                if values:
                    attributes[attr_name] = values
            
        return attributes
    
    def proccess(self, puzzle_text):
        characteristics_text, clues = self.preprocess_puzzle(puzzle_text)

        attrs = self.extract_attributes(characteristics_text)

        return attrs, clues

