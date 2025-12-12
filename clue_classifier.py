import re
from typing import Tuple

class ClueClassifier:
    
    def __init__(self):

        #do not question thes black magic it works
        self.patterns = {
            'POSITION_ABSOLUTE': re.compile(r'(?:is\s+)?in\s+the\s+(\w+)\s+house', re.IGNORECASE),
            'POSITION_ABSOLUTE_NEGATIVE': re.compile(r'is\s+not\s+in\s+the\s+(\w+)\s+house', re.IGNORECASE),
            'NEXT_TO': re.compile(r'(?:and|are)\s+next\s+to\s+each\s+other', re.IGNORECASE),
            'DIRECT_LEFT': re.compile(r'(?:is\s+)?directly\s+(?:left|to\s+the\s+left)\s+of', re.IGNORECASE),
            'DIRECT_RIGHT': re.compile(r'(?:is\s+)?directly\s+(?:right|to\s+the\s+right)\s+of', re.IGNORECASE),
            'LEFT': re.compile(r'(?:is\s+)?(?:somewhere\s+)?to\s+the\s+left\s+of', re.IGNORECASE),
            'RIGHT': re.compile(r'(?:is\s+)?(?:somewhere\s+)?to\s+the\s+right\s+of', re.IGNORECASE),
            'DISTANCE': re.compile(r'(?:there\s+)?(?:is|are)\s+(?:\w+\s+)?house[s]?\s+between', re.IGNORECASE),
            'IDENTITY': re.compile(r'is\s+', re.IGNORECASE),
        }
    
    def classify(self, clue: str) -> Tuple[str, str]:
        clue = clue.strip()
        
        if self.patterns['POSITION_ABSOLUTE_NEGATIVE'].search(clue):
            return (clue, 'POSITION_ABSOLUTE_NEGATIVE')
        
        if self.patterns['DISTANCE'].search(clue):
            return (clue, 'DISTANCE')
        
        if self.patterns['NEXT_TO'].search(clue):
            return (clue, 'NEXT_TO')
        
        if self.patterns['DIRECT_LEFT'].search(clue):
            return (clue, 'DIRECT_LEFT')
        
        if self.patterns['DIRECT_RIGHT'].search(clue):
            return (clue, 'DIRECT_RIGHT')
        
        if self.patterns['LEFT'].search(clue):
            return (clue, 'LEFT')
        
        if self.patterns['RIGHT'].search(clue):
            return (clue, 'RIGHT')
        
        if self.patterns['POSITION_ABSOLUTE'].search(clue):
            return (clue, 'POSITION_ABSOLUTE')
        
        if self.patterns['IDENTITY'].search(clue):
            return (clue, 'IDENTITY')
        
        return (clue, 'UNKNOWN')
