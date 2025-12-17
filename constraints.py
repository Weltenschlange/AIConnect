import re

class Constraint():

    def get_info(self):
        raise NotImplementedError()

    def _replace_edgecases(self, text:str):
        if text.endswith("ing"):
            text = text[:-3]
        if text.endswith("s"):
            text = text[:-1]
        if text == "swede":
            text = text[:-1]
        if text == "ford f150":
            text = "ford f 150"
        return text


    def __init__(self, attributes: dict, clue: str):
        self.attributes = attributes
        self.clue = clue
        pass

    def _get_attribute_key_from_text(self, text):
        # Check for "mother's" first (before generic matching catches "name")
        if re.search(rf"\bmother's\b", text, re.IGNORECASE):
            return "mother"
        
        for key in self.attributes.keys():
            if key == "animals":
                if re.search(rf"\b{re.escape('keeps a pet')}\b", text, re.IGNORECASE):
                    return 'pet'
                if re.search(rf"\b{re.escape('keeps')}\b", text, re.IGNORECASE):
                    return key
                if re.search(rf"\b{re.escape('keeper')}\b", text, re.IGNORECASE):
                    return key
            if key == "month":
                if re.search(rf"\b{re.escape('birthday')}\b", text, re.IGNORECASE):
                    return key
            if key == "drink":
                if re.search(rf"\b{re.escape('drinker')}\b", text, re.IGNORECASE):
                    return key
            if key == "vacation":
                if re.search(rf"\b{re.escape('vacations')}\b", text, re.IGNORECASE):
                    return key
            if key == "colors":
                if re.search(rf"\b{re.escape('favorite color')}\b", text, re.IGNORECASE):
                    return key
            if key == "mother":
                if re.search(rf"\b{re.escape('the mother of')}\b", text, re.IGNORECASE):
                    return "child"
            if re.search(rf"\b{re.escape(key)}\b", text, re.IGNORECASE):
                return key
        return None

    def _extract_attribute_from_text(self, text):
        best_match = None
        best_length = 0
        
        for key in self.attributes.keys():
            k = self._extract_attribute_from_text_with_key(key, text)
            if k:
                value, _ = k
                value_modified = self._replace_edgecases(value)
                if len(value_modified) > best_length:
                    best_match = k
                    best_length = len(value_modified)
        
        return best_match
    
    def _extract_attribute_from_text_with_key(self, key, text):
        # Sort by length descending to match longer values first
        best_match = None
        best_length = 0
        
        # Special handling for months - map abbreviations to full names
        month_mapping = {
            'jan': 'january',
            'feb': 'february',
            'march': 'march',
            'april': 'april',
            'may': 'may',
            'june': 'june',
            'july': 'july',
            'aug': 'august',
            'sept': 'september',
            'oct': 'october',
            'nov': 'november',
            'dec': 'december'
        }
        
        for value in self.attributes[key]:
            value_modified = self._replace_edgecases(value)
            if value_modified in text and len(value_modified) > best_length:
                best_match = (value, key)
                best_length = len(value_modified)
            
            # For months, also check the full month name
            if key == "month" and value_modified in month_mapping:
                full_month = month_mapping[value_modified]
                if full_month in text and len(full_month) > best_length:
                    best_match = (value, key)
                    best_length = len(full_month)
        
        return best_match
    
    def is_valid(self, attributes):
        raise NotImplementedError()
    
    def get_wrong_attributes(self, attributes):
        raise NotImplementedError()
    
    def _get_position_by_attribute(self, attr_value, attr_key, currentSolution):
        for pos, attrs in currentSolution.items():
            if attrs.get(attr_key) == attr_value:
                return pos
        return None
    
class IdentityConstrain(Constraint):

    def get_info(self):
        return f"IdentityConstrain:  {self.clue}\nattr1:{self.attr1}\nattr2:{self.attr2}\nattributes:{self.attributes}\n"

    def is_valid(self, currentSolution):
        # Handle "house X is painted Y" pattern (position-based identity)
        if hasattr(self, 'house_num') and self.attr2:
            attr2_val, attr2_key = self.attr2
            # Check if position house_num has attr2_key = attr2_val
            if self.house_num in currentSolution:
                if attr2_key in currentSolution[self.house_num]:
                    return currentSolution[self.house_num][attr2_key] == attr2_val
            return True  # Not yet assigned
        
        if not self.attr1 or not self.attr2:
            return False
        
        attr1_val, attr1_key = self.attr1
        attr2_val, attr2_key = self.attr2
        
        pos1 = self._get_position_by_attribute(attr1_val, attr1_key, currentSolution)
        pos2 = self._get_position_by_attribute(attr2_val, attr2_key, currentSolution)
        
        # If one is assigned and the other is not, it's still potentially valid

        if pos1 is None or pos2 is None:
            return True
        
        return pos1 == pos2
    
    def get_wrong_attributes(self, currentSolution):
        if not self.attr1 or not self.attr2:
            return []
        
        attr1_val, attr1_key = self.attr1
        attr2_val, attr2_key = self.attr2
        
        pos1 = self._get_position_by_attribute(attr1_val, attr1_key, currentSolution)
        pos2 = self._get_position_by_attribute(attr2_val, attr2_key, currentSolution)
        
        # If both are assigned to different positions, both are wrong
        if pos1 is not None and pos2 is not None and pos1 != pos2:
            return [(attr1_val, attr1_key), (attr2_val, attr2_key)]
        
        return []

    def _parse_attributes(self):
        clue_lower = self.clue.lower()
        
        # Check for "X owns Y" pattern (e.g., "carol owns the hamster")
        owns_match = re.search(r'\b(\w+)\s+owns\s+(?:the\s+)?(\w+)', clue_lower)
        if owns_match:
            person_or_attr = owns_match.group(1)
            item_or_attr = owns_match.group(2)
            
            # Match person_or_attr as an attribute value
            for key1, values in self.attributes.items():
                if person_or_attr in [v.lower() for v in values]:
                    self.attr1 = (person_or_attr, key1)
                    break
            
            # Match item_or_attr as an attribute value
            for key2, values in self.attributes.items():
                if item_or_attr in [v.lower() for v in values]:
                    self.attr2 = (item_or_attr, key2)
                    break
            
            if self.attr1 and self.attr2:
                return
        
        # Check for "the [attr] house contains/has [value]" pattern
        house_pattern_match = re.search(r'the\s+(\w+)\s+house\s+(?:contains|has)\s+(?:the\s+)?(.+?)\.?$', clue_lower)
        if house_pattern_match:
            house_attr = house_pattern_match.group(1)
            pet_or_item = house_pattern_match.group(2).strip()
            
            # Match house_attr as an attribute value
            for key1, values in self.attributes.items():
                if house_attr in [v.lower() for v in values]:
                    self.attr1 = (house_attr, key1)
                    break
            
            # Match pet_or_item as an attribute value
            for key2, values in self.attributes.items():
                if pet_or_item in [v.lower() for v in values]:
                    self.attr2 = (pet_or_item, key2)
                    break
            
            if self.attr1 and self.attr2:
                return
        
        # Check for "house [num] is painted/is/contains/has [value]" pattern
        house_num_pattern = re.search(r'house\s+(\d+)\s+(?:is\s+painted|is|contains|has)\s+(.+?)\.?$', clue_lower)
        if house_num_pattern:
            house_num = house_num_pattern.group(1)
            value = house_num_pattern.group(2).strip()
            
            # Match value as an attribute
            self.attr2 = self._extract_attribute_from_text(value)
            if not self.attr2:
                # Try harder to extract
                for key, values in self.attributes.items():
                    if value in [v.lower() for v in values]:
                        self.attr2 = (value, key)
                        break
            
            if self.attr2:
                # Store position information in a way that is_valid can use
                self.house_num = int(house_num)
                return
        
        # Original "is" split pattern
        parts = self.clue.split(" is ")
        
        # Handle cases with 4+ parts (complex nested relationships)
        if len(parts) >= 4:
            # First, identify what attribute category is in parts[0]
            # e.g., "the person's child" → 'child' attribute
            key1 = self._get_attribute_key_from_text(parts[0])
            
            # Extract the value for that category from the surrounding parts
            if key1:
                # Try parts[1] first (usually has the value)
                self.attr1 = self._extract_attribute_from_text_with_key(key1, parts[1])
                # If not found, try parts[2]
                if not self.attr1:
                    self.attr1 = self._extract_attribute_from_text_with_key(key1, parts[2])
            
            # Fallback: extract any attribute from parts[1]
            if not self.attr1:
                self.attr1 = self._extract_attribute_from_text(parts[1])
            
            # For the second part, reconstruct remaining parts and extract
            # This handles cases where there are multiple "is" separators
            remaining = " is ".join(parts[2:])
            
            # Check if any attribute key appears in remaining part
            key = self._get_attribute_key_from_text(remaining)
            if key:
                self.attr2 = self._extract_attribute_from_text_with_key(key, remaining)
            if not self.attr2:
                self.attr2 = self._extract_attribute_from_text(remaining)
                
        elif len(parts) == 3:
            attr1_extracted_from = 0
            # Try to extract attr1 from parts[0]
            key = self._get_attribute_key_from_text(parts[0])
            if key:
                # First try to extract from parts[0]
                self.attr1 = self._extract_attribute_from_text_with_key(key, parts[0])
                # If not found, try parts[1] (the value might be in the next part)
                if not self.attr1:
                    self.attr1 = self._extract_attribute_from_text_with_key(key, parts[1])
                    attr1_extracted_from = 1
                    
            if not self.attr1:
                self.attr1 = self._extract_attribute_from_text(parts[0])
            if not self.attr1:
                self.attr1 = self._extract_attribute_from_text(parts[1])
                attr1_extracted_from = 1

            if attr1_extracted_from == 0:
                key = self._get_attribute_key_from_text(parts[1])
                if key:
                    self.attr2 = self._extract_attribute_from_text_with_key(key, parts[2])
                if not self.attr2:
                    self.attr2 = self._extract_attribute_from_text(parts[1])
                if not self.attr2:
                    self.attr2 = self._extract_attribute_from_text(parts[2])
            else:
                self.attr2 = self._extract_attribute_from_text(parts[2])
            
            # # Try to extract attr2 from parts[2], or parts[1] as fallback
            # for part_idx in [1, 2]:
            #     if not self.attr2:
            #         key = self._get_attribute_key_from_text(parts[part_idx])
            #         if key:
            #             self.attr2 = self._extract_attribute_from_text_with_key(key, parts[part_idx])
            #         if not self.attr2:
            #             self.attr2 = self._extract_attribute_from_text(parts[part_idx])
        elif len(parts) == 2:
            key = self._get_attribute_key_from_text(parts[0])
            if key:
                self.attr1 = self._extract_attribute_from_text_with_key(key, parts[0])
            if not self.attr1:
                self.attr1 = self._extract_attribute_from_text(parts[0])
            
            # Check for attribute keys first in parts[1] using _get_attribute_key_from_text
            key = self._get_attribute_key_from_text(parts[1])
            if key:
                self.attr2 = self._extract_attribute_from_text_with_key(key, parts[1])
            
            if not self.attr2:
                self.attr2 = self._extract_attribute_from_text(parts[1])
        else:
            pass
        

    def _try_fix_duplicate(self):
        if not self.attr1 or not self.attr2:
            return
        
        attr1_val, attr1_key = self.attr1
        attr2_val, attr2_key = self.attr2
        
        # Only attempt fix if both belong to same category
        if attr1_key != attr2_key:
            return
        
        # Try to find an alternative category for attr1
        for alt_key in self.attributes.keys():
            if alt_key == attr1_key:
                continue
            
            if attr1_val in self.attributes[alt_key]:
                self.attr1 = (attr1_val, alt_key)
                return
        
        # If no valid alternative found, try to reassign attr2 instead
        for alt_key in self.attributes.keys():
            if alt_key == attr2_key:
                continue
            
            if attr2_val in self.attributes[alt_key]:
                self.attr2 = (attr2_val, alt_key)
                return

    def __init__(self, attributes: dict, clue: str):
        super().__init__(attributes, clue)
        self.attr1:tuple = None
        self.attr2:tuple = None
        self.house_num = None  # For "house X is painted Y" pattern
        self._parse_attributes()
        self._try_fix_duplicate()

class NextToConstrain(Constraint):

    def get_info(self):
        return f"NextToConstrain: {self.clue}\nattr1:{self.attr1}\nattr2:{self.attr2}\nattributes:{self.attributes}\n"

    def is_valid(self, currentSolution):
        if not self.attr1 or not self.attr2:
            return False
        
        attr1_val, attr1_key = self.attr1
        attr2_val, attr2_key = self.attr2
        
        pos1 = self._get_position_by_attribute(attr1_val, attr1_key, currentSolution)
        pos2 = self._get_position_by_attribute(attr2_val, attr2_key, currentSolution)
        
        if pos1 is None or pos2 is None:
            return True
        
        return abs(pos1 - pos2) == 1
    
    def get_wrong_attributes(self, currentSolution):
        if not self.attr1 or not self.attr2:
            return []
        
        attr1_val, attr1_key = self.attr1
        attr2_val, attr2_key = self.attr2
        
        pos1 = self._get_position_by_attribute(attr1_val, attr1_key, currentSolution)
        pos2 = self._get_position_by_attribute(attr2_val, attr2_key, currentSolution)
        
        if pos1 is not None and pos2 is not None and abs(pos1 - pos2) != 1:
            return [(attr1_val, attr1_key), (attr2_val, attr2_key)]
        
        return []

    def _parse_attributes(self):
        parts = self.clue.split(" and ")
        
        if len(parts) >= 2:
            # Use _get_attribute_key_from_text to properly handle special cases
            key = self._get_attribute_key_from_text(parts[0])
            if key:
                self.attr1 = self._extract_attribute_from_text_with_key(key, parts[0])
                # If not found in parts[0], try parts[1]
                if not self.attr1:
                    self.attr1 = self._extract_attribute_from_text_with_key(key, parts[1])
            if not self.attr1:
                self.attr1 = self._extract_attribute_from_text(parts[0])
            
            second_part = parts[1]
            if " are next to each other" in second_part:
                second_part = second_part.replace(" are next to each other", "")
            
            key = self._get_attribute_key_from_text(second_part)
            if key:
                self.attr2 = self._extract_attribute_from_text_with_key(key, second_part)
            if not self.attr2:
                self.attr2 = self._extract_attribute_from_text(second_part)


    def __init__(self, attributes: dict, clue: str):
        super().__init__(attributes, clue)
        self.attr1:tuple = None
        self.attr2:tuple = None
        self._parse_attributes()

class DistanceConstrain(Constraint):
    def get_info(self):
        return f"DistanceConstrain: {self.clue}\ndistance:{self.distance}\nattr1:{self.attr1}\nattr2:{self.attr2}\nattributes:{self.attributes}\n"
    
    def is_valid(self, currentSolution):
        if not self.attr1 or not self.attr2:
            return False
        
        attr1_val, attr1_key = self.attr1
        attr2_val, attr2_key = self.attr2
        
        pos1 = self._get_position_by_attribute(attr1_val, attr1_key, currentSolution)
        pos2 = self._get_position_by_attribute(attr2_val, attr2_key, currentSolution)
        
        if pos1 is None or pos2 is None:
            return True
        
        return abs(pos1 - pos2) == self.distance + 1
    
    def get_wrong_attributes(self, currentSolution):
        if not self.attr1 or not self.attr2:
            return []
        
        attr1_val, attr1_key = self.attr1
        attr2_val, attr2_key = self.attr2
        
        pos1 = self._get_position_by_attribute(attr1_val, attr1_key, currentSolution)
        pos2 = self._get_position_by_attribute(attr2_val, attr2_key, currentSolution)
        
        if pos1 is not None and pos2 is not None and abs(pos1 - pos2) != self.distance + 1:
            return [(attr1_val, attr1_key), (attr2_val, attr2_key)]
        
        return []
    
    def _parse_attributes(self):
        distance_words = {
            "one": 1,
            "two": 2,
            "three": 3,
            "four": 4,
            "five": 5,
            "six": 6,
            "seven": 7,
            "eight": 8,
            "nine": 9,
            "ten": 10
        }
        
        self.distance = 1 
        
        clue = self.clue
        # Check if clue starts with "there are" and extract distance from next word
        if self.clue.startswith("there are"):
            # Extract the word after "there are"
            remaining = self.clue[9:].strip()  # Skip "there are"
            next_word = remaining.split()[0] if remaining.split() else None
            if next_word and next_word in distance_words:
                self.distance = distance_words[next_word]
        else:
            # Use regex word boundaries instead of substring matching
            for word, value in distance_words.items():
                if re.search(rf"\b{word}\b", self.clue):
                    self.distance = value
                    break

        if len(self.clue.split("between")) == 2:
            clue = self.clue.split("between")[1]
    
        if " and " in clue:
            parts = clue.split(" and ")

            if len(parts) >= 2:
                # Use _get_attribute_key_from_text to identify the semantic category first
                key1 = self._get_attribute_key_from_text(parts[0])
                if key1:
                    self.attr1 = self._extract_attribute_from_text_with_key(key1, parts[0])
                    # If not found in parts[0], try parts[1]
                    if not self.attr1:
                        self.attr1 = self._extract_attribute_from_text_with_key(key1, parts[1])
                if not self.attr1:
                    self.attr1 = self._extract_attribute_from_text(parts[0])
                
                second_part = parts[1].rstrip(".")
                key2 = self._get_attribute_key_from_text(second_part)
                if key2:
                    self.attr2 = self._extract_attribute_from_text_with_key(key2, second_part)
                if not self.attr2:
                    self.attr2 = self._extract_attribute_from_text(second_part)


    def __init__(self, attributes: dict, clue: str):
        super().__init__(attributes, clue)
        self.attr1:tuple = None
        self.attr2:tuple = None
        self.distance = 1
        self._parse_attributes()

class LeftConstrain(Constraint):

    def get_info(self):
        return f"LeftConstrain: {self.clue}\nattr1:{self.attr1}\nattr2:{self.attr2}\nattributes:{self.attributes}\n"
    
    def is_valid(self, currentSolution):
        if not self.attr1 or not self.attr2:
            return False
        
        attr1_val, attr1_key = self.attr1
        attr2_val, attr2_key = self.attr2
        
        pos1 = self._get_position_by_attribute(attr1_val, attr1_key, currentSolution)
        pos2 = self._get_position_by_attribute(attr2_val, attr2_key, currentSolution)
        
        if pos1 is None or pos2 is None:
            return True
        
        return pos1 < pos2
    
    def get_wrong_attributes(self, currentSolution):
        if not self.attr1 or not self.attr2:
            return []
        
        attr1_val, attr1_key = self.attr1
        attr2_val, attr2_key = self.attr2
        
        pos1 = self._get_position_by_attribute(attr1_val, attr1_key, currentSolution)
        pos2 = self._get_position_by_attribute(attr2_val, attr2_key, currentSolution)
        
        if pos1 is not None and pos2 is not None and pos1 >= pos2:
            return [(attr1_val, attr1_key), (attr2_val, attr2_key)]
        
        return []
    
    def _parse_attributes(self):
        if " is somewhere to the left of " in self.clue:
            parts = self.clue.split(" is somewhere to the left of ")
            
            if len(parts) == 2:
                key = self._get_attribute_key_from_text(parts[0])
                if key:
                    self.attr1 = self._extract_attribute_from_text_with_key(key, parts[0])
                    # If not found in parts[0], try parts[1]
                    if not self.attr1:
                        self.attr1 = self._extract_attribute_from_text_with_key(key, parts[1])
                if not self.attr1:
                    self.attr1 = self._extract_attribute_from_text(parts[0])
                
                second_part = parts[1].rstrip(".")
                key = self._get_attribute_key_from_text(second_part)
                if key:
                    self.attr2 = self._extract_attribute_from_text_with_key(key, second_part)
                    # If not found in the identified key, try case-insensitive matching first
                    if not self.attr2:
                        for value in self.attributes[key]:
                            if value.lower() in second_part.lower():
                                self.attr2 = (value, key)
                                break
                if not self.attr2:
                    self.attr2 = self._extract_attribute_from_text(second_part)


    def __init__(self, attributes: dict, clue: str):
        super().__init__(attributes, clue)
        self.attr1:tuple = None
        self.attr2:tuple = None
        self._parse_attributes()

class RightConstrain(Constraint):

    def get_info(self):
        return f"RightConstrain: {self.clue}\nattr1:{self.attr1}\nattr2:{self.attr2}\nattributes:{self.attributes}\n"
    
    def is_valid(self, currentSolution):
        if not self.attr1 or not self.attr2:
            return False
        
        attr1_val, attr1_key = self.attr1
        attr2_val, attr2_key = self.attr2
        
        pos1 = self._get_position_by_attribute(attr1_val, attr1_key, currentSolution)
        pos2 = self._get_position_by_attribute(attr2_val, attr2_key, currentSolution)
        
        if pos1 is None or pos2 is None:
            return True
        
        return pos1 > pos2
    
    def get_wrong_attributes(self, currentSolution):
        if not self.attr1 or not self.attr2:
            return []
        
        attr1_val, attr1_key = self.attr1
        attr2_val, attr2_key = self.attr2
        
        pos1 = self._get_position_by_attribute(attr1_val, attr1_key, currentSolution)
        pos2 = self._get_position_by_attribute(attr2_val, attr2_key, currentSolution)
        
        if pos1 is not None and pos2 is not None and pos1 <= pos2:
            return [(attr1_val, attr1_key), (attr2_val, attr2_key)]
        
        return []
    
    def _parse_attributes(self):
        if " is somewhere to the right of " in self.clue:
            parts = self.clue.split(" is somewhere to the right of ")
            
            if len(parts) != 2:
                return

            key = self._get_attribute_key_from_text(parts[0])
            if key:
                self.attr1 = self._extract_attribute_from_text_with_key(key, parts[0])
                # If not found in parts[0], try parts[1]
                if not self.attr1:
                    self.attr1 = self._extract_attribute_from_text_with_key(key, parts[1])
            if not self.attr1:
                self.attr1 = self._extract_attribute_from_text(parts[0])
                    
            second_part = parts[1].rstrip(".")
            key = self._get_attribute_key_from_text(second_part)
            if key:
                self.attr2 = self._extract_attribute_from_text_with_key(key, second_part)
                # If not found in the identified key, try case-insensitive matching first
                if not self.attr2:
                    for value in self.attributes[key]:
                        if value.lower() in second_part.lower():
                            self.attr2 = (value, key)
                            break
            if not self.attr2:
                self.attr2 = self._extract_attribute_from_text(second_part)


    def __init__(self, attributes: dict, clue: str):
        super().__init__(attributes, clue)
        self.attr1:tuple = None
        self.attr2:tuple = None
        self._parse_attributes()

class DirectLeftConstrain(Constraint):

    def get_info(self):
        return f"DirectLeftConstrain: {self.clue}\nattr1:{self.attr1}\nattr2:{self.attr2}\nattributes:{self.attributes}\n"
    
    def is_valid(self, currentSolution):
        if not self.attr1 or not self.attr2:
            return False
        
        attr1_val, attr1_key = self.attr1
        attr2_val, attr2_key = self.attr2
        
        pos1 = self._get_position_by_attribute(attr1_val, attr1_key, currentSolution)
        pos2 = self._get_position_by_attribute(attr2_val, attr2_key, currentSolution)
        
        if pos1 is None or pos2 is None:
            return True
        
        return pos2 - pos1 == 1
    
    def get_wrong_attributes(self, currentSolution):
        if not self.attr1 or not self.attr2:
            return []
        
        attr1_val, attr1_key = self.attr1
        attr2_val, attr2_key = self.attr2
        
        pos1 = self._get_position_by_attribute(attr1_val, attr1_key, currentSolution)
        pos2 = self._get_position_by_attribute(attr2_val, attr2_key, currentSolution)
        
        if pos1 is not None and pos2 is not None and pos2 - pos1 != 1:
            return [(attr1_val, attr1_key), (attr2_val, attr2_key)]
        
        return []
    
    def _parse_attributes(self):
        # Try multiple split patterns for "left of"
        parts = None
        clue_lower = self.clue.lower()
        
        if " is immediately to the left of " in clue_lower:
            parts = re.split(r'\s+is\s+immediately\s+to\s+the\s+left\s+of\s+', self.clue, flags=re.IGNORECASE)
        elif " is directly to the left of " in clue_lower:
            parts = re.split(r'\s+is\s+directly\s+to\s+the\s+left\s+of\s+', self.clue, flags=re.IGNORECASE)
        elif " is directly left of " in clue_lower:
            parts = self.clue.split(" is directly left of ")
        elif " directly to the left of " in clue_lower:
            parts = re.split(r'\s+directly\s+to\s+the\s+left\s+of\s+', self.clue, flags=re.IGNORECASE)
        
        if parts and len(parts) == 2:
            key = self._get_attribute_key_from_text(parts[0])
            if key:
                self.attr1 = self._extract_attribute_from_text_with_key(key, parts[0])
                # If not found in parts[0], try parts[1]
                if not self.attr1:
                    self.attr1 = self._extract_attribute_from_text_with_key(key, parts[1])
            if not self.attr1:
                self.attr1 = self._extract_attribute_from_text(parts[0])
            
            second_part = parts[1].rstrip(".")
            key = self._get_attribute_key_from_text(second_part)
            if key:
                self.attr2 = self._extract_attribute_from_text_with_key(key, second_part)
                # If not found in the identified key, try case-insensitive matching first
                if not self.attr2:
                    for value in self.attributes[key]:
                        if value.lower() in second_part.lower():
                            self.attr2 = (value, key)
                            break
            if not self.attr2:
                self.attr2 = self._extract_attribute_from_text(second_part)


    def __init__(self, attributes: dict, clue: str):
        super().__init__(attributes, clue)
        self.attr1:tuple = None
        self.attr2:tuple = None
        self._parse_attributes()

class DirectRightConstrain(Constraint):

    def get_info(self):
        return f"DirectRightConstrain: {self.clue}\nattr1:{self.attr1}\nattr2:{self.attr2}\nattributes:{self.attributes}\n"
    
    def is_valid(self, currentSolution):
        if not self.attr1 or not self.attr2:
            return False
        
        attr1_val, attr1_key = self.attr1
        attr2_val, attr2_key = self.attr2
        
        pos1 = self._get_position_by_attribute(attr1_val, attr1_key, currentSolution)
        pos2 = self._get_position_by_attribute(attr2_val, attr2_key, currentSolution)
        
        if pos1 is None or pos2 is None:
            return True
        
        return pos1 - pos2 == 1
    
    def get_wrong_attributes(self, currentSolution):
        if not self.attr1 or not self.attr2:
            return []
        
        attr1_val, attr1_key = self.attr1
        attr2_val, attr2_key = self.attr2
        
        pos1 = self._get_position_by_attribute(attr1_val, attr1_key, currentSolution)
        pos2 = self._get_position_by_attribute(attr2_val, attr2_key, currentSolution)
        
        if pos1 is not None and pos2 is not None and pos1 - pos2 != 1:
            return [(attr1_val, attr1_key), (attr2_val, attr2_key)]
        
        return []
    
    def _parse_attributes(self):
        # Try multiple split patterns for "right of"
        parts = None
        clue_lower = self.clue.lower()
        
        if " is immediately to the right of " in clue_lower:
            parts = re.split(r'\s+is\s+immediately\s+to\s+the\s+right\s+of\s+', self.clue, flags=re.IGNORECASE)
        elif " is directly to the right of " in clue_lower:
            parts = re.split(r'\s+is\s+directly\s+to\s+the\s+right\s+of\s+', self.clue, flags=re.IGNORECASE)
        elif " is directly right of " in clue_lower:
            parts = self.clue.split(" is directly right of ")
        elif " directly to the right of " in clue_lower:
            parts = re.split(r'\s+directly\s+to\s+the\s+right\s+of\s+', self.clue, flags=re.IGNORECASE)
        
        if parts and len(parts) == 2:
            key = self._get_attribute_key_from_text(parts[0])
            if key:
                self.attr1 = self._extract_attribute_from_text_with_key(key, parts[0])
                # If not found in parts[0], try parts[1]
                if not self.attr1:
                    self.attr1 = self._extract_attribute_from_text_with_key(key, parts[1])
            if not self.attr1:
                self.attr1 = self._extract_attribute_from_text(parts[0])
            
            second_part = parts[1].rstrip(".")
            key = self._get_attribute_key_from_text(second_part)
            if key:
                self.attr2 = self._extract_attribute_from_text_with_key(key, second_part)
                # If not found in the identified key, try case-insensitive matching first
                if not self.attr2:
                    for value in self.attributes[key]:
                        if value.lower() in second_part.lower():
                            self.attr2 = (value, key)
                            break
            if not self.attr2:
                self.attr2 = self._extract_attribute_from_text(second_part)


    def __init__(self, attributes: dict, clue: str):
        super().__init__(attributes, clue)
        self.attr1:tuple = None
        self.attr2:tuple = None
        self._parse_attributes()

class PositionAbsoluteConstrain(Constraint):

    def get_info(self):
        return f"PositionAbsoluteConstrain: {self.clue}\nPosition:{self.pos}\nattr1:{self.attr1}\nattributes:{self.attributes}\n"
    
    def is_valid(self, currentSolution):
        # Handle "person lives in the [color] house" - positive identity
        if hasattr(self, 'pos_attr') and self.attr1:
            attr1_val, attr1_key = self.attr1
            pos_attr_val, pos_attr_key = self.pos_attr
            
            pos1 = self._get_position_by_attribute(attr1_val, attr1_key, currentSolution)
            pos2 = self._get_position_by_attribute(pos_attr_val, pos_attr_key, currentSolution)
            
            if pos1 is None or pos2 is None:
                return True
            
            return pos1 == pos2
        
        if not self.attr1 or self.pos is None:
            return False
        
        attr_val, attr_key = self.attr1
        pos = self._get_position_by_attribute(attr_val, attr_key, currentSolution)
        
        if pos is None:
            return True
        
        return pos == self.pos
    
    def get_wrong_attributes(self, currentSolution):
        if not self.attr1 or self.pos is None:
            return []
        
        attr_val, attr_key = self.attr1
        pos = self._get_position_by_attribute(attr_val, attr_key, currentSolution)
        
        if pos is not None and pos != self.pos:
            return [(attr_val, attr_key)]
        
        return []
    
    def _parse_attributes(self):
        position_words = {
            "first": 1,
            "second": 2,
            "third": 3,
            "fourth": 4,
            "fifth": 5,
            "sixth": 6,
            "seventh": 7,
            "eighth": 8,
            "ninth": 9,
            "tenth": 10
        }
        
        self.pos = None
        clue_lower = self.clue.lower()
        
        # Check for "the person in house X owns Y" pattern
        person_house_owns = re.search(r'(?:the\s+)?person\s+in\s+house\s+(\d+)\s+owns\s+(?:the\s+)?(\w+)', clue_lower)
        if person_house_owns:
            self.pos = int(person_house_owns.group(1))
            item = person_house_owns.group(2)
            # Find which attribute this item belongs to
            for key, values in self.attributes.items():
                if item in [v.lower() for v in values]:
                    self.attr1 = (item, key)
                    return
        
        # Check for house number format: "lives in house 3" or "in house 2"
        house_num_match = re.search(r'(?:lives\s+in|in)\s+house\s+(\d+)', clue_lower)
        if house_num_match:
            self.pos = int(house_num_match.group(1))
            # Extract the person/attribute before "lives in house"
            parts = re.split(r'\s+(?:lives\s+in|in)\s+house\s+\d+', self.clue, maxsplit=1)
            if parts and parts[0]:
                self.attr1 = self._extract_attribute_from_text(parts[0])
            return
        
        # Check for position words
        for word, value in position_words.items():
            if word in clue_lower:
                self.pos = value
                break
        
        # Check for "lives in the [color] house" pattern
        if " lives in the " in clue_lower:
            parts = self.clue.split(" lives in the ")
            if len(parts) >= 2:
                # Extract person/attribute from first part
                self.attr1 = self._extract_attribute_from_text(parts[0])
                # Extract color/attribute from "[color] house" (note: "the" already consumed in split)
                match = re.search(r'(\w+)\s+house', parts[1].lower())
                if match:
                    color_or_pos = match.group(1)
                    # Try to match it as an attribute value
                    for key, values in self.attributes.items():
                        if color_or_pos in [v.lower() for v in values]:
                            # Found the color/attribute, now find its position
                            # We'll set pos in is_valid based on currentSolution
                            # For now, store it as an attr2-like reference
                            self.pos_attr = (color_or_pos, key)
                            return
        
        # Original pattern: "is in the"
        if " is in the " in clue_lower:
            parts = self.clue.split(" is in the ")
            
            if len(parts) >= 1:
                key = self._get_attribute_key_from_text(parts[0])
                if key:
                    self.attr1 = self._extract_attribute_from_text_with_key(key, parts[0])
                if not self.attr1:
                    self.attr1 = self._extract_attribute_from_text(parts[0])


    def __init__(self, attributes: dict, clue: str):
        super().__init__(attributes, clue)
        self.attr1:tuple = None
        self.pos = None
        self._parse_attributes()

class PositionAbsoluteNegativeConstrain(Constraint):

    def get_info(self):
        return f"PositionAbsoluteNegativeConstrain: {self.clue}\nPosition:{self.pos}\nattr1:{self.attr1}\nattributes:{self.attributes}\n"
    
    def is_valid(self, currentSolution):
        # Handle "person does not live in the [color] house" - negative identity
        if hasattr(self, 'pos_attr') and self.attr1:
            attr1_val, attr1_key = self.attr1
            pos_attr_val, pos_attr_key = self.pos_attr
            
            pos1 = self._get_position_by_attribute(attr1_val, attr1_key, currentSolution)
            pos2 = self._get_position_by_attribute(pos_attr_val, pos_attr_key, currentSolution)
            
            if pos1 is None or pos2 is None:
                return True
            
            return pos1 != pos2
        
        if not self.attr1 or self.pos is None:
            return False
        
        attr_val, attr_key = self.attr1
        pos = self._get_position_by_attribute(attr_val, attr_key, currentSolution)
        
        if pos is None:
            return True
        
        return pos != self.pos
    
    def get_wrong_attributes(self, currentSolution):
        if not self.attr1 or self.pos is None:
            return []
        
        attr_val, attr_key = self.attr1
        pos = self._get_position_by_attribute(attr_val, attr_key, currentSolution)
        
        if pos is not None and pos == self.pos:
            return [(attr_val, attr_key)]
        
        return []
    
    def _parse_attributes(self):
        position_words = {
            "first": 1,
            "second": 2,
            "third": 3,
            "fourth": 4,
            "fifth": 5,
            "sixth": 6,
            "seventh": 7,
            "eighth": 8,
            "ninth": 9,
            "tenth": 10
        }
        
        self.pos = None
        clue_lower = self.clue.lower()
        
        for word, value in position_words.items():
            if word in clue_lower:
                self.pos = value
                break
        
        # Check for "does not live in the [color] house" pattern
        if " does not live in the " in clue_lower:
            parts = self.clue.split(" does not live in the ")
            if len(parts) >= 2:
                # Extract person/attribute from first part
                self.attr1 = self._extract_attribute_from_text(parts[0])
                # Extract color/attribute from "the [color] house"
                match = re.search(r'(\w+)\s+house', parts[1].lower())
                if match:
                    color_or_pos = match.group(1)
                    # This is really an identity constraint: person != color
                    # But we're treating it as position constraint
                    # We need to store the color reference
                    for key, values in self.attributes.items():
                        if color_or_pos in [v.lower() for v in values]:
                            # Found the color/attribute
                            # We'll need to handle this in is_valid
                            self.pos_attr = (color_or_pos, key)
                            return
        
        # Original pattern: "is not in the"
        if " is not in the " in clue_lower:
            parts = self.clue.split(" is not in the ")
            
            if len(parts) >= 1:
                key = self._get_attribute_key_from_text(parts[0])
                if key:
                    self.attr1 = self._extract_attribute_from_text_with_key(key, parts[0])
                if not self.attr1:
                    self.attr1 = self._extract_attribute_from_text(parts[0])

    def __init__(self, attributes: dict, clue: str):
        super().__init__(attributes, clue)
        self.attr1:tuple = None
        self.pos = None
        self._parse_attributes()