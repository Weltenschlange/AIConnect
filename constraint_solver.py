from typing import Dict, List, Tuple, Optional
from constraints import Constraint
import copy


class ConstraintSolver:
    """
    Smart Constraint Satisfaction Problem (CSP) solver for logic puzzles.
    
    Uses:
    - Constraint propagation (AC-3 like) for domain pruning
    - Backtracking search with Minimum Remaining Values (MRV) heuristic
    - Forward checking to reduce search space
    """
    
    def __init__(self, attributes: Dict[str, List[str]], constraints: List[Constraint]):

        self.attributes = attributes
        self.constraints = constraints
        self.num_House = len(next(iter(attributes.values())))
        
        self.domains = self._initialize_domains()
        
        self.assignment = {}
        
        self.backtrack_count = 0
        self.propagation_calls = 0
        
    def _initialize_domains(self) -> Dict[int, Dict[str, set]]:
        domains = {}
        for pos in range(1, self.num_House + 1):
            domains[pos] = {}
            for attr_key, attr_values in self.attributes.items():
                domains[pos][attr_key] = set(attr_values)
        return domains
    
    def solve(self) -> Optional[Dict[int, Dict[str, str]]]:
        if not self._propagate():
            return None
        
        result = self._backtrack({})
        
        return result
    
    def _propagate(self) -> bool:
        self.propagation_calls += 1
        
        changed = True
        while changed:
            changed = False
            
            # Apply all-different constraint: each value can only appear once per attribute
            for attr_key in self.attributes.keys():
                for value in self.attributes[attr_key]:
                    positions_with_value = []
                    for houseNr in range(1, self.num_House + 1):
                        if value in self.domains[houseNr][attr_key]:
                            positions_with_value.append(houseNr)
                    
                    # If value can only go in one position, assign it there
                    if len(positions_with_value) == 1:
                        houseNr = positions_with_value[0]
                        if len(self.domains[houseNr][attr_key]) > 1:
                            self.domains[houseNr][attr_key] = {value}
                            changed = True
                    
                    # If value has nowhere to go, inconsistency
                    elif len(positions_with_value) == 0:
                        return False
            
            # If position has only one value for an attribute, remove it from other positions
            for houseNr in range(1, self.num_House + 1):
                for attr_key in self.attributes.keys():
                    if len(self.domains[houseNr][attr_key]) == 1:
                        value = list(self.domains[houseNr][attr_key])[0]
                        for other_houseNr in range(1, self.num_House + 1):
                            if other_houseNr != houseNr and value in self.domains[other_houseNr][attr_key]:
                                self.domains[other_houseNr][attr_key].discard(value)
                                changed = True
                                if len(self.domains[other_houseNr][attr_key]) == 0:
                                    return False
            
            # Apply unary constraints (constraints with single attributes)
            for houseNr in range(1, self.num_House + 1):
                for attr_key in self.attributes.keys():
                    if len(self.domains[houseNr][attr_key]) == 0:
                        return False  # Empty domain = inconsistency
                    
                    # Remove values that would violate position-specific constraints
                    values_to_remove = set()
                    for value in self.domains[houseNr][attr_key]:
                        test_solution = self._build_partial_solution()
                        test_solution[houseNr][attr_key] = value
                        
                        if not self._is_consistent(test_solution):
                            values_to_remove.add(value)
                    
                    if values_to_remove:
                        self.domains[houseNr][attr_key] -= values_to_remove
                        changed = True
                        if len(self.domains[houseNr][attr_key]) == 0:
                            return False
            
            # Apply AC-3 arc consistency
            if not self._ac3():
                return False
        
        return True
    
    def _ac3(self) -> bool:
        """
        Optimized AC-3 Algorithm with Lazy Arc Creation.
        
        Instead of creating all arcs upfront (6 * num_attributes * 6 * num_attributes = expensive),
        only create arcs for attribute pairs that interact based on constraints.
        
        An arc from variable Xi to variable Xj is consistent if for every value in Xi's domain,
        there exists a value in Xj's domain that satisfies the constraint between them.
        """
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
                # (except the arc we just processed)
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
        """
        Generate only relevant arcs based on constraints.
        
        For each constraint, extract the attribute types involved and create arcs
        between all positions for those attribute types.
        """
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
        for attr_key1, attr_key2 in relevant_attr_pairs:
            for houseNr1 in range(1, self.num_House + 1):
                for houseNr2 in range(1, self.num_House + 1):
                    if (houseNr1, attr_key1) != (houseNr2, attr_key2):
                        arcs.append(((houseNr1, attr_key1), (houseNr2, attr_key2)))
        
        return arcs
    
    def _get_constraint_attribute_pair(self, constraint: Constraint) -> Optional[Tuple[str, str]]:
        """
        Extract the attribute types involved in a constraint.
        
        Returns a tuple of (attr_key1, attr_key2) if the constraint involves two attributes,
        or None if it's a unary constraint.
        """
        if hasattr(constraint, 'attr1') and hasattr(constraint, 'attr2'):
            if constraint.attr1 and constraint.attr2:
                _, attr_key1 = constraint.attr1
                _, attr_key2 = constraint.attr2
                return (attr_key1, attr_key2)
        
        # Unary constraints (PositionAbsolute, etc.) don't contribute to arc generation
        return None
    
    def _revise(self, houseNr_i: int, attr_key_i: str, houseNr_j: int, attr_key_j: str) -> bool:
        """
        Revise the domain of variable Xi by removing values that have no support in Xj.
        
        Returns True if the domain of Xi was modified, False otherwise.
        """
        revised = False
        values_to_remove = set()
        
        for value_i in self.domains[houseNr_i][attr_key_i]:
            # Check if there exists a value in Xj's domain that supports value_i
            has_support = False
            
            for value_j in self.domains[houseNr_j][attr_key_j]:
                # Create a test assignment
                test_solution = self._build_partial_solution()
                test_solution[houseNr_i][attr_key_i] = value_i
                test_solution[houseNr_j][attr_key_j] = value_j
                
                # Check if this pairing is consistent with constraints
                if self._is_consistent(test_solution):
                    has_support = True
                    break
            
            # If no supporting value found, remove value_i from domain
            if not has_support:
                values_to_remove.add(value_i)
                revised = True
        
        self.domains[houseNr_i][attr_key_i] -= values_to_remove
        return revised
    
    def _backtrack(self, assignment: Dict[int, Dict[str, str]]) -> Optional[Dict[int, Dict[str, str]]]:

        if self._is_complete(assignment):
            return assignment
        
        self.backtrack_count += 1
        
        var = self._select_unassigned_variable(assignment)
        if var is None:
            return None
        
        houseNr, attr_key = var
        
        for value in list(self.domains[houseNr][attr_key]):
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
        if len(assignment) != self.num_House:
            return False
        
        for houseNr in range(1, self.num_House + 1):
            if houseNr not in assignment:
                return False
            if len(assignment[houseNr]) != len(self.attributes):
                return False
        
        return True
    
    def _is_consistent(self, assignment: Dict[int, Dict[str, str]]) -> bool:

        for attr_key in self.attributes.keys():
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
        min_domain_size = float('inf')
        best_var = None
        
        for houseNr in range(1, self.num_House + 1):
            for attr_key in self.attributes.keys():
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
        """Print current domains for debugging."""
        print("\n=== Current Domains ===")
        for pos in sorted(self.domains.keys()):
            print(f"\nPosition {pos}:")
            for attr_key, values in sorted(self.domains[pos].items()):
                print(f"  {attr_key}: {values}")
