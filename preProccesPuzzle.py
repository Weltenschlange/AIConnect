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
            # Try without ## for Test_100 format
            parts = re.split(r'\nClues:', puzzle_text, flags=re.IGNORECASE)
        
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

                # Extract values with backticks (Gridmode format)
                values = re.findall(r'`([^`]+)`', values_str)
                
                if values:
                    attributes[attr_name] = values
            
            # Test_100 format: "Colors: orange, blue, green."
            elif ':' in line and line.strip():
                parts_simple = line.split(':', 1)
                if len(parts_simple) == 2:
                    attr_name = parts_simple[0].strip().lower()
                    values_str = parts_simple[1].strip()
                    
                    # Skip lines with backticks (already handled above)
                    if '`' in values_str:
                        continue
                    
                    # Extract comma-separated values
                    values = [v.strip().rstrip('.') for v in values_str.split(',')]
                    values = [v for v in values if v]
                    
                    if values and attr_name:
                        # Normalize attribute name (Colors -> color, Pets -> pet)
                        if attr_name.endswith('s') and attr_name not in ['class']:
                            attr_name = attr_name[:-1]
                        attributes[attr_name] = values
            
        return attributes
    
    def proccess(self, puzzle_text):
        characteristics_text, clues = self.preprocess_puzzle(puzzle_text)

        attrs = self.extract_attributes(characteristics_text)
        
        # For Test_100 format: extract names from clues if not in attributes
        if 'name' not in attrs and attrs and clues:
            names = set()
            exclude_words = {'House', 'Colors', 'Pets', 'Clues', 'The', 'Each', 'There', 'This', 'And', 'Or'}
            for clue in clues:
                # Extract capitalized words (likely names)
                potential_names = re.findall(r'\b([A-Z][a-z]+)\b', clue)
                for name in potential_names:
                    if name not in exclude_words:
                        names.add(name)
            
            if names:
                attrs['name'] = sorted(list(names))
        
        # Balance attribute lengths - add dummy values if needed
        if attrs:
            max_len = max(len(vals) for vals in attrs.values())
            for key, vals in attrs.items():
                if len(vals) < max_len:
                    # Add dummy values
                    dummy_count = max_len - len(vals)
                    for i in range(dummy_count):
                        # Generate unique dummy names
                        if key == 'name':
                            dummy_val = f'Person{i+1}'
                        else:
                            dummy_val = f'{key}{i+1}'
                        vals.append(dummy_val)

        return attrs, clues

