from typing import Dict, List, Tuple, Optional
from constraints import Constraint
import copy
import csv
import time



class ConstraintSolver:
    """
    Backtracking CSP solver with arc consistency (AC-3), forward checking, and MRV heuristic.
    """
    
    def __init__(self, attributes: Dict[str, List[str]], constraints: List[Constraint]):

        self.attributes = attributes
        self.constraints = constraints
        self.num_House = len(next(iter(attributes.values())))
        
        self.domains = self._initialize_domains()
        
        self.assignment = {}
        
        self.backtrack_count = 0
        self.propagation_calls = 0

        self.search_trace = []
        self.start_time = time.time()
        
    def _initialize_domains(self) -> Dict[int, Dict[str, set]]:
        """Initialize domains: all possible values for each position-attribute pair."""
        domains = {}
        for pos in range(1, self.num_House + 1):
            domains[pos] = {}
            for attr_key, attr_values in self.attributes.items():
                domains[pos][attr_key] = set(attr_values)
        return domains
    
    def solve(self) -> Optional[Dict[int, Dict[str, str]]]:
        """Apply AC-3 preprocessing, then solve via backtracking with forward checking."""
        if not self._ac3():
            return None
        
        if not self._propagate():
            return None
        
        return self._backtrack({})
    
    def _propagate(self) -> bool:
        """Forward checking: propagate constraints iteratively until fixpoint."""
        self.propagation_calls += 1
        
        changed = True
        while changed:
            changed = False
            
            # All-different: each value appears at most once per attribute
            for attr_key in sorted(self.attributes.keys()):
                for value in sorted(self.attributes[attr_key]):
                    positions_with_value = []
                    for houseNr in range(1, self.num_House + 1):
                        if value in self.domains[houseNr][attr_key]:
                            positions_with_value.append(houseNr)
                    
                    # If value can only go in one position, assign it
                    if len(positions_with_value) == 1:
                        houseNr = positions_with_value[0]
                        if len(self.domains[houseNr][attr_key]) > 1:
                            self.domains[houseNr][attr_key] = {value}
                            changed = True
                    
                    # If value has no valid position, conflict
                    elif len(positions_with_value) == 0:
                        return False
            
            # Unit propagation: remove assigned values from other positions
            for houseNr in range(1, self.num_House + 1):
                for attr_key in sorted(self.attributes.keys()):
                    if len(self.domains[houseNr][attr_key]) == 1:
                        value = list(self.domains[houseNr][attr_key])[0]
                        for other_houseNr in range(1, self.num_House + 1):
                            if other_houseNr != houseNr and value in self.domains[other_houseNr][attr_key]:
                                self.domains[other_houseNr][attr_key].discard(value)
                                changed = True
                                if len(self.domains[other_houseNr][attr_key]) == 0:
                                    return False
            
            # Apply unary constraints
            for houseNr in range(1, self.num_House + 1):
                for attr_key in sorted(self.attributes.keys()):
                    if len(self.domains[houseNr][attr_key]) == 0:
                        return False
                    
                    # Remove values violating position-specific constraints
                    values_to_remove = set()
                    for value in sorted(self.domains[houseNr][attr_key]):
                        test_solution = self._build_partial_solution()
                        test_solution[houseNr][attr_key] = value
                        
                        if not self._is_consistent(test_solution):
                            values_to_remove.add(value)
                    
                    if values_to_remove:
                        self.domains[houseNr][attr_key] -= values_to_remove
                        changed = True
                        if len(self.domains[houseNr][attr_key]) == 0:
                            return False
        
        return True
    
    def _ac3(self) -> bool:
        """AC-3 algorithm: enforce arc consistency on constraint graph."""
        # Build initial queue with only relevant arcs based on constraints
        queue = self._get_initial_arcs()
        queue_set = set(queue)  # For O(1) membership testing
        
        while queue:
            arc = queue.pop(0)
            queue_set.discard(arc)
            (houseNr_i, attr_key_i), (houseNr_j, attr_key_j) = arc
            
            # Revise the domain of variable Xi
            if self._revise(houseNr_i, attr_key_i, houseNr_j, attr_key_j):
                # If domain of Xi became empty, no solution exists
                if len(self.domains[houseNr_i][attr_key_i]) == 0:
                    return False
                
                # If the domain of Xi was reduced, re-add all arcs pointing to Xi
                for houseNr_k in range(1, self.num_House + 1):
                    for attr_key_k in self.attributes.keys():
                        if (houseNr_k, attr_key_k) != (houseNr_i, attr_key_i) and \
                           (houseNr_k, attr_key_k) != (houseNr_j, attr_key_j):
                            reverse_arc = ((houseNr_k, attr_key_k), (houseNr_i, attr_key_i))
                            if reverse_arc not in queue_set:
                                queue.append(reverse_arc)
                                queue_set.add(reverse_arc)
        
        return True
    
    def _get_initial_arcs(self) -> List[Tuple[Tuple[int, str], Tuple[int, str]]]:
        """Generate arcs for relevant attribute pairs based on constraints."""
        relevant_attr_pairs = set()
        
        # Extract relevant attribute pairs from constraints
        for constraint in self.constraints:
            attr_pair = self._get_constraint_attribute_pair(constraint)
            if attr_pair:
                attr_key1, attr_key2 = attr_pair
                # Add both directions as potential relevant pairs
                relevant_attr_pairs.add((attr_key1, attr_key2))
                if attr_key1 != attr_key2:
                    relevant_attr_pairs.add((attr_key2, attr_key1))
        
        # Also add all-different constraints between same attribute
        for attr_key in self.attributes.keys():
            relevant_attr_pairs.add((attr_key, attr_key))
        
        # Create arcs for relevant attribute pairs
        arcs = []
        for attr_key1, attr_key2 in sorted(relevant_attr_pairs):
            for houseNr1 in range(1, self.num_House + 1):
                for houseNr2 in range(1, self.num_House + 1):
                    if (houseNr1, attr_key1) != (houseNr2, attr_key2):
                        arcs.append(((houseNr1, attr_key1), (houseNr2, attr_key2)))
        
        return arcs
    
    def _get_constraint_attribute_pair(self, constraint: Constraint) -> Optional[Tuple[str, str]]:
        """Extract attribute pair from constraint, None if unary."""
        if hasattr(constraint, 'attr1') and hasattr(constraint, 'attr2'):
            if constraint.attr1 and constraint.attr2:
                _, attr_key1 = constraint.attr1
                _, attr_key2 = constraint.attr2
                return (attr_key1, attr_key2)
        
        return None
    
    def _revise(self, houseNr_i: int, attr_key_i: str, houseNr_j: int, attr_key_j: str) -> bool:
        """Remove values from (houseNr_i, attr_key_i) with no support in (houseNr_j, attr_key_j)."""
        revised = False
        values_to_remove = set()
        
        # Get only constraints that involve both attributes
        relevant_constraints = [
            c for c in self.constraints 
            if hasattr(c, 'attr1') and hasattr(c, 'attr2') 
            and c.attr1 and c.attr2
        ]
        
        for value_i in sorted(self.domains[houseNr_i][attr_key_i]):
            # Check if there exists a value in Xj's domain that supports value_i
            has_support = False
            
            for value_j in sorted(self.domains[houseNr_j][attr_key_j]):
                # Quick check: only test if attributes match constraint pattern
                is_valid = True
                
                for constraint in relevant_constraints:
                    _, attr1_key = constraint.attr1
                    _, attr2_key = constraint.attr2
                    
                    # Check if this constraint applies to our variables
                    if (attr_key_i == attr1_key and attr_key_j == attr2_key) or \
                       (attr_key_i == attr2_key and attr_key_j == attr1_key):
                        # Build minimal test solution
                        test_sol = {houseNr_i: {attr_key_i: value_i},
                                   houseNr_j: {attr_key_j: value_j}}
                        if not constraint.is_valid(test_sol):
                            is_valid = False
                            break
                
                if is_valid:
                    has_support = True
                    break
            
            # If no supporting value found, remove value_i from domain
            if not has_support:
                values_to_remove.add(value_i)
                revised = True
        
        self.domains[houseNr_i][attr_key_i] -= values_to_remove
        return revised
    
    def _backtrack(self, assignment: Dict[int, Dict[str, str]]) -> Optional[Dict[int, Dict[str, str]]]:
        """Depth-first search with backtracking, logging and forward checking."""
        if self._is_complete(assignment):
            return assignment
        
        self.backtrack_count += 1
        
        var = self._select_unassigned_variable(assignment)
        if var is None:
            return None
        
        houseNr, attr_key = var
        
        for value in sorted(self.domains[houseNr][attr_key]):

            current_features = self._get_feature_vector()

            log_row = [
                          len(self.search_trace) + 1,
                          houseNr,
                          attr_key,
                          value
                      ] + current_features

            self.search_trace.append(log_row)

            new_assignment = copy.deepcopy(assignment)
            if houseNr not in new_assignment:
                new_assignment[houseNr] = {}
            new_assignment[houseNr][attr_key] = value
            
            if self._is_consistent(new_assignment):
                saved_domains = copy.deepcopy(self.domains)
                
                self.domains[houseNr][attr_key] = {value}
                
                if self._propagate():
                    result = self._backtrack(new_assignment)
                    if result is not None:
                        return result
                
                self.domains = saved_domains
        
        return None
    
    def _is_complete(self, assignment: Dict[int, Dict[str, str]]) -> bool:
        """Check if all variables are assigned."""
        if len(assignment) != self.num_House:
            return False
        
        for houseNr in range(1, self.num_House + 1):
            if houseNr not in assignment:
                return False
            if len(assignment[houseNr]) != len(self.attributes):
                return False
        
        return True
    
    def _is_consistent(self, assignment: Dict[int, Dict[str, str]]) -> bool:
        """Check if assignment satisfies all-different and constraint checks."""
        for attr_key in sorted(self.attributes.keys()):
            used_values = []
            for houseNr in range(1, self.num_House + 1):
                if houseNr in assignment and attr_key in assignment[houseNr]:
                    value = assignment[houseNr][attr_key]
                    if value in used_values:
                        return False
                    used_values.append(value)
        
        for constraint in self.constraints:
            if not constraint.is_valid(assignment):
                return False
        
        return True
    
    def _select_unassigned_variable(self, assignment: Dict[int, Dict[str, str]]) -> Optional[Tuple[int, str]]:
        """Select unassigned variable with minimum remaining values (MRV heuristic)."""
        min_domain_size = float('inf')
        best_var = None
        
        for houseNr in range(1, self.num_House + 1):
            for attr_key in sorted(self.attributes.keys()):
                if houseNr in assignment and attr_key in assignment[houseNr]:
                    continue
                
                domain_size = len(self.domains[houseNr][attr_key])
                if domain_size == 0:
                    return (houseNr, attr_key)
                
                if domain_size < min_domain_size:
                    min_domain_size = domain_size
                    best_var = (houseNr, attr_key)
        
        return best_var
    
    def _build_partial_solution(self) -> Dict[int, Dict[str, str]]:
        """Extract determined values from domains to form partial solution."""
        solution = copy.deepcopy(self.assignment)
        
        for houseNr in range(1, self.num_House + 1):
            if houseNr not in solution:
                solution[houseNr] = {}
            
            for attr_key in self.attributes.keys():
                if len(self.domains[houseNr][attr_key]) == 1:
                    value = list(self.domains[houseNr][attr_key])[0]
                    if attr_key not in solution[houseNr]:
                        solution[houseNr][attr_key] = value
        
        return solution
    
    def print_solution(self, solution: Dict[int, Dict[str, str]]) -> None:
        if solution is None:
            print("No solution found.")
            return
        
        print("\n=== Solution ===")
        for pos in sorted(solution.keys()):
            print(f"\nHouse {pos}:")
            for attr_key, value in sorted(solution[pos].items()):
                print(f"  {attr_key}: {value}")
    
    def print_domains(self) -> None:
        """Print current domain state for debugging."""
        print("\n=== Current Domains ===")
        for pos in sorted(self.domains.keys()):
            print(f"\nPosition {pos}:")
            for attr_key, values in sorted(self.domains[pos].items()):
                print(f"  {attr_key}: {values}")

    def _get_feature_vector(self) -> List[int]:
        """
        Constructs a feature vector representing the current state of the search.

        Returns:
            List[int]: A flattened list of current domain sizes for all variables,
                       sorted by house number and attribute name to ensure consistency.
        """
        features = []
        sorted_attrs = sorted(self.attributes.keys())

        for house in range(1, self.num_House + 1):
            for attr in sorted_attrs:
                if house in self.domains and attr in self.domains[house]:
                    size = len(self.domains[house][attr])
                else:
                    size = 0
                features.append(size)

        return features

    def save_trace_to_csv(self, filename="solver_trace.csv") -> None:
        """
        Saves the recorded search trace to a CSV file.
        Generates dynamic headers to match the feature vector structure.
        """
        if not self.search_trace:
            print(f"Hinweis: Puzzle wurde ohne Backtracking gelöst (Trace ist leer). Erstelle leere CSV in {filename}.")

        header = ["step", "house_id", "attribute", "chosen_value"]

        sorted_attrs = sorted(self.attributes.keys())
        for h in range(1, self.num_House + 1):
            for attr in sorted_attrs:
                col_name = f"dom_size_H{h}_{attr}"
                header.append(col_name)

        try:
            with open(filename, mode='w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(header)
                writer.writerows(self.search_trace)
            print(f"Trace successfully saved to {filename} ({len(self.search_trace)} rows)")
        except Exception as e:
            print(f"Error saving trace: {e}")