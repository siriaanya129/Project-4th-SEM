# EL_Sem4/backend/app/question_engine.py
import json
import random
import math
import re 
import os
from scipy import stats
from typing import List, Dict, Any, Callable, Tuple, Union
from collections import Counter # For mode calculation
from scipy.stats import norm, binom, poisson, t # For p-values, critical values, etc.

# --- Utility for Pluralization ---
_plural_forms = { # Add more as needed for your item_plural choices
    "bulb": "bulbs", "board": "boards", "widget": "widgets", "sensor": "sensors",
    "apple": "apples", "stone": "stones", "component": "components",
    "battery": "batteries", "call": "calls", "hit": "hits", "breakdown": "breakdowns",
    "voter":"voters", "resident":"residents", "employee":"employees", "student":"students",
    "item": "items", "observation":"observations", "day":"days", "hour":"hours", "minute":"minutes",
    "city":"cities", "company":"companies", "method":"methods", "score":"scores", "trial":"trials",
    "participant":"participants", "male":"males", "app":"apps", "blend":"blends", "bar":"bars",
    "quiz": "quizzes", "wolf": "wolves", "leaf": "leaves", "shelf": "shelves",
    "life": "lives", "knife": "knives", "potato": "potatoes", "tomato": "tomatoes",
    "hero": "heroes", "echo": "echoes", "bus": "buses", "box": "boxes",
    "watch": "watches", "church": "churches", "story": "stories", "baby": "babies",
    "man": "men", "woman": "women", "child": "children", "foot": "feet",
    "tooth": "teeth", "goose": "geese", "mouse": "mice", "person": "people",
    "sheep": "sheep", "fish": "fish", "deer": "deer", "series": "series",
    "species": "species", "crisis": "crises", "analysis": "analyses",
    "basis": "bases", "diagnosis": "diagnoses", "ellipsis": "ellipses",
    "hypothesis": "hypotheses", "oasis": "oases", "parenthesis": "parentheses",
    "synthesis": "syntheses", "thesis": "theses", "cactus": "cacti",
    "focus": "foci", "fungus": "fungi", "nucleus": "nuclei",
    "radius": "radii", "stimulus": "stimuli", "syllabus": "syllabi",
    "alumnus": "alumni", "bacillus": "bacilli", "criterion": "criteria",
    "curriculum": "curricula", "datum": "data", "erratum": "errata", "medium": "media",
    "memorandum": "memoranda", "phenomenon": "phenomena", "stratum": "strata",
    "spectrum": "spectra"
}
def get_plural(singular_noun: str) -> str:
    singular_noun_lower = singular_noun.lower()
    if singular_noun_lower in _plural_forms:
        if singular_noun and singular_noun[0].isupper():
            plural_base = _plural_forms[singular_noun_lower]
            return plural_base[0].upper() + plural_base[1:]
        return _plural_forms[singular_noun_lower]
    if singular_noun_lower.endswith('y') and len(singular_noun_lower) > 1 and singular_noun_lower[-2].lower() not in 'aeiou':
        return singular_noun[:-1] + 'ies'
    elif singular_noun_lower.endswith(('s', 'sh', 'ch', 'x', 'z')):
        return singular_noun + 'es'
    return singular_noun + 's'

# --- Helper for Z-values ---
Z_TABLE_COMMON = {
    90: 1.645,
    95: 1.96,
    99: 2.576
}

# --- Variable Generator Functions ---
# Each function takes `details` (from template's var_gen section) and `current_vars`
# (already generated vars for the current question instance)

def _vg_random_choice(details: Dict, current_vars: Dict) -> Any:
    return random.choice(details["choices"])

def _vg_random_int_range(details: Dict, current_vars: Dict) -> int:
    return random.randint(details["min"], details["max"])

def _vg_lookup_from_options(details: Dict, current_vars: Dict) -> str:
    idx_var_name = details["source_var"] 
    options_list_key_in_vars = details["options_list_var"] 
    key_to_lookup_in_dict = details["lookup_key"]

    if idx_var_name not in current_vars:
        print(f"ERROR (_vg_lookup_from_options): Index variable '{idx_var_name}' not found in current_vars. Details: {details}")
        return f"LOOKUP_ERROR_IDX_VAR_MISSING_{idx_var_name}"
    
    idx = int(current_vars[idx_var_name])
    
    if options_list_key_in_vars not in current_vars:
        print(f"ERROR (_vg_lookup_from_options): Options list key '{options_list_key_in_vars}' not found in current_vars. Details: {details}")
        return f"LOOKUP_ERROR_LIST_KEY_MISSING_{options_list_key_in_vars}"

    options_list_of_dicts = current_vars[options_list_key_in_vars]

    if not isinstance(options_list_of_dicts, list):
        print(f"ERROR (_vg_lookup_from_options): Variable '{options_list_key_in_vars}' is not a list. Found type: {type(options_list_of_dicts)}. Details: {details}")
        return "LOOKUP_ERROR_NOT_A_LIST"
    
    # This check assumes the list should contain dictionaries for this specific lookup type
    if not all(isinstance(d, dict) for d in options_list_of_dicts):
        # Adding a specific check if the list is simple strings and the lookup key is implicitly 'value'
        if all(isinstance(d, str) for d in options_list_of_dicts) and key_to_lookup_in_dict == "value": # A convention for list of strings
             if 0 <= idx < len(options_list_of_dicts):
                 return options_list_of_dicts[idx]
             else:
                print(f"ERROR (_vg_lookup_from_options): Index {idx} out of bounds for simple options_list '{options_list_key_in_vars}' of length {len(options_list_of_dicts)}.")
                return "LOOKUP_ERROR_INDEX_SIMPLE_LIST"
        
        print(f"ERROR (_vg_lookup_from_options): Variable '{options_list_key_in_vars}' is not a list of dictionaries. Details: {details}")
        return "LOOKUP_ERROR_NOT_LIST_OF_DICTS"
    
    if not (0 <= idx < len(options_list_of_dicts)):
        print(f"ERROR (_vg_lookup_from_options): Index {idx} out of bounds for options_list '{options_list_key_in_vars}' of length {len(options_list_of_dicts)}. Details: {details}")
        return "LOOKUP_ERROR_INDEX_OUT_OF_BOUNDS"
        
    dict_for_lookup = options_list_of_dicts[idx]
    
    if not isinstance(dict_for_lookup, dict):
        print(f"ERROR (_vg_lookup_from_options): Item at index {idx} in '{options_list_key_in_vars}' is not a dictionary. Item: {dict_for_lookup}")
        return "LOOKUP_ERROR_ITEM_NOT_DICT"

    if key_to_lookup_in_dict not in dict_for_lookup:
        print(f"ERROR (_vg_lookup_from_options): Lookup key '{key_to_lookup_in_dict}' not found in selected dictionary from '{options_list_key_in_vars}'. Dict: {dict_for_lookup}. Details: {details}")
        return f"LOOKUP_ERROR_KEY_NOT_IN_DICT_{key_to_lookup_in_dict}"
        
    return str(dict_for_lookup[key_to_lookup_in_dict])


def _vg_square_value(details: Dict, current_vars: Dict) -> Union[int, float]:
    base_val = current_vars[details["source_var"]]
    return base_val * base_val

def _vg_random_float_range(details: Dict, current_vars: Dict) -> float:
    val = random.uniform(details["min"], details["max"])
    return round(val, details.get("decimals", 2))

def _vg_sum_vars(details: Dict, current_vars: Dict) -> Union[int, float]:
    total = 0
    for var_name in details["vars_to_sum"]:
        total += current_vars[var_name]
    return total

def _vg_calculate_mean_with_missing(details: Dict, current_vars: Dict) -> float:
    known_values = current_vars[details["known_values_var"]]
    missing_value = current_vars[details["missing_value_var"]]
    all_values = known_values + [missing_value]
    return sum(all_values) / len(all_values)

def _vg_generate_int_array(details: Dict, current_vars: Dict) -> List[int]:
    size = current_vars.get(details.get("size_var")) if details.get("size_var") else details["size"]
    return [random.randint(details["min_val"], details["max_val"]) for _ in range(size)]

def _vg_array_to_string(details: Dict, current_vars: Dict) -> str:
    arr = current_vars[details["source_var"]]
    return ", ".join(map(str, arr))

def _vg_calculate_successes_from_prop(details: Dict, current_vars: Dict) -> int:
    sample_size = current_vars[details["sample_size_var"]]
    proportion = current_vars[details["proportion_var"]]
    return int(round(sample_size * proportion))

def _vg_generate_p_value_relative_to_alpha(details: Dict, current_vars: Dict) -> float:
    alpha = current_vars[details["alpha_var"]]
    scenario = current_vars[details["scenario_var"]]
    if scenario == "less_than_alpha":
        return round(random.uniform(0.0001, alpha * 0.9), 4)
    else: # greater_than_alpha
        return round(random.uniform(alpha * 1.1, alpha + 0.2), 4)

def _vg_calculate_x_from_z(details: Dict, current_vars: Dict) -> Union[int, float]:
    mean = current_vars[details["mean_var"]]
    std_dev = current_vars[details["std_dev_var"]]
    z_score = current_vars[details["z_score_var"]]
    x = mean + (z_score * std_dev)
    return int(round(x)) if isinstance(mean, int) and isinstance(std_dev, int) else round(x, 2)


def _vg_fixed_value(details: Dict, current_vars: Dict) -> Any:
    return details["value"]

def _vg_random_int_range_dependent_max(details: Dict, current_vars: Dict) -> int:
    max_val = current_vars[details["max_var"]]
    min_val = details.get("min", 0)
    if min_val > max_val : min_val = max_val # ensure min <= max
    return random.randint(min_val, max_val)

def _vg_generate_perfect_square(details: Dict, current_vars: Dict) -> int: # Added
    base = random.randint(details["min_base"], details["max_base"])
    return base * base

def _vg_generate_int_array_with_mode(details: Dict, current_vars: Dict) -> List[int]:
    size = details["size"]
    mode_val = current_vars.get(details.get("mode_val_var"), random.randint(details["min_val"],details["max_val"]))
    mode_freq = current_vars.get(details.get("mode_freq_var"), random.randint(details.get("mode_freq_min",2), size // 2 if size > 2 else 2))
    mode_freq = min(mode_freq, size -1 if size > 1 else 1) # Ensure mode_freq < size

    arr = [mode_val] * mode_freq
    remaining_size = size - mode_freq
    for _ in range(remaining_size):
        val = random.randint(details["min_val"], details["max_val"])
        # Avoid making another value equally or more frequent than the intended mode
        # This is a simplification; true guarantee is harder.
        temp_counts = Counter(arr + [val])
        while temp_counts[val] > mode_freq or (val != mode_val and temp_counts[val] == mode_freq and len(set(arr + [val])) == len(set(arr))): # Avoid creating multiple modes unintentionally
             val = random.randint(details["min_val"], details["max_val"])
             temp_counts = Counter(arr + [val])
        arr.append(val)
    random.shuffle(arr)
    return arr[:size]


def _vg_shuffle_array(details: Dict, current_vars: Dict) -> List[any]:
    arr = list(current_vars[details["source_var"]])
    random.shuffle(arr)
    return arr

def _vg_singular_form(details: Dict, current_vars: Dict) -> str: # Simple version
    plural = current_vars[details["source_var"]]
    if plural.lower().endswith("ies") and len(plural) > 3 : return plural[:-3] + "y"
    if plural.lower().endswith("s") and len(plural) > 1: return plural[:-1]
    return plural # Fallback

def _vg_calculate_n_from_N_ratio_int(details: Dict, current_vars: Dict) -> int:
    N = int(current_vars[details["N_var"]])
    ratio = float(current_vars[details["ratio_var"]])
    return max(1, int(round(N * ratio)))

def _vg_random_int_range_step(details: Dict, current_vars: Dict) -> int:
    step = details.get("step", 1)
    return random.randrange(details["min"], details["max"] + step, step)


def _vg_multiply_vars_float(details: Dict, current_vars: Dict) -> float:
    product = 1.0
    vars_to_multiply = details.get("vars_to_multiply", [details.get("var1"), details.get("var2")])
    for var_name in vars_to_multiply:
        if var_name: product *= float(current_vars[var_name])
    return round(product, details.get("decimals", 4))

def _vg_percent_to_decimal(details: Dict, current_vars: Dict) -> float:
    return current_vars[details["source_var"]] / 100.0

def _vg_decimal_to_percent(details: Dict, current_vars: Dict) -> float:
    return current_vars[details["source_var"]] * 100.0

def _vg_decimal_to_percent_str(details: Dict, current_vars: Dict) -> str:
    val = current_vars[details["source_var"]] * 100.0
    return f"{val:.{details.get('decimals', 0)}f}"


def _vg_identity(details: Dict, current_vars: Dict) -> Any:
    return current_vars[details["source_var"]]

def _vg_conditional_value(details: Dict, current_vars: Dict) -> Any:
    condition_val_actual = current_vars[details["condition_var"]]
    for case in details["conditions_values"]:
        if case["if_val"] == condition_val_actual:
            return case["then_val"]
    return details.get("default_val", None)

def _vg_random_int_range_dependent_max_strict(details: Dict, current_vars: Dict) -> int:
    max_val = current_vars[details["max_var"]] + details.get("max_plus", 0)
    min_val = details.get("min",0)
    if min_val > max_val : # if min becomes greater after max_plus adjustment
        #This can happen if max_var is small and max_plus is negative.
        #Default to min_val or raise an error, or swap
        return min_val 
    if min_val == max_val: return min_val
    return random.randint(min_val, max_val)

def _vg_random_int_near_lambda(details: Dict, current_vars: Dict) -> int:
    lambda_val = float(current_vars[details["lambda_var"]])
    range_around = int(details.get("range_around", 2))
    min_k = max(0, int(round(lambda_val - range_around)))
    max_k = int(round(lambda_val + range_around))
    if min_k > max_k : min_k = max_k  # Prevent errors in random.randint
    return random.randint(min_k, max_k)


def _vg_plural_form(details: Dict, current_vars: Dict) -> str:
    singular = str(current_vars[details["source_var"]])
    return get_plural(singular)

def _vg_random_float_range_plus(details: Dict, current_vars: Dict) -> float:
    base = float(current_vars[details["base_var"]])
    add_val = random.uniform(details["min_add"], details["max_add"])
    return round(base + add_val, details.get("decimals", 2))

def _vg_conditional_text(details: Dict, current_vars: Dict) -> str:
    idx = int(current_vars[details["source_var"]])
    return details["choices"][idx]

def _vg_calculate_one_minus_var(details: Dict, current_vars: Dict) -> float:
    val = float(current_vars[details["source_var"]])
    return round(1.0 - val, details.get("decimals", 4))

def _vg_calculate_cov_from_vars_corr(details: Dict, current_vars: Dict) -> float:
    var1 = float(current_vars[details["var1"]])
    var2 = float(current_vars[details["var2"]])
    corr = float(current_vars[details["corr_var"]])
    return round(corr * math.sqrt(var1) * math.sqrt(var2), details.get("decimals", 4))

def _vg_calculate_cov_from_target_corr(details: Dict, current_vars: Dict) -> float:
    target_corr = float(current_vars[details["target_corr_var"]])
    std_dev_x = float(current_vars[details["std_dev_x_var"]])
    std_dev_y = float(current_vars[details["std_dev_y_var"]])
    return round(target_corr * std_dev_x * std_dev_y, details.get("decimals", 4))


def _vg_sort_array(details: Dict, current_vars: Dict) -> List[Any]:
    arr = list(current_vars[details["source_var"]])
    arr.sort()
    return arr

def _vg_lookup_z_for_confidence(details: Dict, current_vars: Dict) -> float:
    conf_level = int(current_vars[details["conf_level_var"]])
    return Z_TABLE_COMMON.get(conf_level, 1.96) # Default to 95%

def _vg_generate_p2_for_diff_prop_scenario(details: Dict, current_vars: Dict) -> int:
    p1_base_percent = int(current_vars[details["p1_var"]])
    scenario = current_vars[details["scenario_var"]]
    if scenario == "increase":
        return random.randint(min(99, p1_base_percent + 3), min(100,p1_base_percent + 10))
    elif scenario == "decrease":
        return random.randint(max(1, p1_base_percent - 10), max(0, p1_base_percent - 3))
    else: # no_change
        return random.randint(max(1, p1_base_percent - 2), min(99,p1_base_percent + 2))

def _vg_generate_ci_diff_prop_lower(details: Dict, current_vars: Dict) -> str:
    p1 = current_vars[details["p1_perc_var"]] / 100.0
    p2 = current_vars[details["p2_perc_var"]] / 100.0
    # This is a simplified placeholder for actual CI calculation, needs n1, n2.
    # The real CI calculation will happen in the answer_logic.
    # Here, we just generate something plausible for the *template text filling*.
    diff = p2 - p1
    return f"{diff - 0.08:.3f}" 

def _vg_generate_ci_diff_prop_upper(details: Dict, current_vars: Dict) -> str:
    p1 = current_vars[details["p1_perc_var"]] / 100.0
    p2 = current_vars[details["p2_perc_var"]] / 100.0
    diff = p2 - p1
    return f"{diff + 0.08:.3f}"

def _vg_city_name_based_on_higher_prop(details: Dict, current_vars: Dict) -> str:
    prop_A = float(current_vars[details["prop_A_var"]]) # These are actual proportions
    prop_B = float(current_vars[details["prop_B_var"]])
    return details["name_A"] if prop_A > prop_B else details["name_B"]

def _vg_calculate_systematic_interval(details: Dict, current_vars: Dict) -> int:
    N = int(current_vars[details["N_var"]])
    n = int(current_vars[details["n_var"]])
    return max(1, int(round(N/n))) if n > 0 else N # Avoid division by zero

def _vg_multiply_vars(details: Dict, current_vars: Dict) -> Union[int, float]: # Added
    product = 1
    for var_name in details.get("vars_to_multiply", [details.get("var1"), details.get("var2")]):
        if var_name: product *= current_vars[var_name]
    return product

def _vg_generate_mu_null_for_ci_test(details: Dict, current_vars: Dict) -> float:
    scenario = current_vars[details["scenario_var"]]
    lower = float(current_vars[details["lower_var"]])
    upper = float(current_vars[details["upper_var"]])
    center = float(current_vars[details["center_var"]])
    if scenario == "inside_ci":
        return round(random.uniform(lower + 0.1*(upper-lower), upper - 0.1*(upper-lower)), 2)
    else: # outside_ci
        return round(center + random.choice([-1,1]) * (upper-lower), 2) # Outside by about the width of CI

def _vg_conditional_prop_scenario(details: Dict, current_vars: Dict) -> float:
    scenario = current_vars[details["scenario_var"]] # e.g. "A_higher"
    base_prop = float(current_vars[details["base_var"]])
    diff_prop = float(current_vars[details["other_base_var"]])
    condition = details["condition_for_base"] # e.g. "A_higher"
    
    if scenario == condition: # This variable should be the higher one
        return round(max(base_prop, base_prop + diff_prop if base_prop + diff_prop < 1 else base_prop - diff_prop ), 2)
    else: # This variable should be the lower one
        return round(min(base_prop, base_prop - diff_prop if base_prop - diff_prop > 0 else base_prop + diff_prop), 2)

def _vg_square_float_value(details: Dict, current_vars: Dict) -> Any:
    base_val = current_vars[details["source_var"]]
    return round(base_val * base_val, details.get("decimals", 4)) 

def _vg_calculate_x_bar_for_test_stat(details: Dict, current_vars: Dict) -> float:
    mu0 = float(current_vars[details["mu0_var"]])
    s = float(current_vars[details["s_var"]])
    n = int(current_vars[details["n_var"]])
    target_t_or_z_details = details["target_t_or_z"]
    
    if isinstance(target_t_or_z_details, dict) and "type" in target_t_or_z_details:
        gen_type = target_t_or_z_details["type"]
        # IMPORTANT: Accessing VARIABLE_GENERATOR_FUNCTIONS here creates a circular dependency
        # if this function is defined before the dictionary.
        # This needs careful handling or refactoring.
        # For now, let's assume a simpler case or that it uses a pre-defined value.
        # A better way for nested generators: pass the engine or generator_map itself.
        if gen_type == "multiply_vars_float": # Hardcoding for this specific case
             target_t_or_z = _vg_multiply_vars_float(target_t_or_z_details.get("params", target_t_or_z_details), current_vars)
        else:
            print(f"Warning: Nested generator type '{gen_type}' for target_t_or_z not fully supported in this simplified _vg_calculate_x_bar_for_test_stat.")
            target_t_or_z = float(target_t_or_z_details.get("value", random.uniform(-2.5, 2.5)))
    else:
        target_t_or_z = float(target_t_or_z_details)

    if n <= 0: return mu0
    x_bar = mu0 + (target_t_or_z * (s / math.sqrt(n)))
    return round(x_bar, details.get("decimals", 2))

def _vg_calculate_cov_from_vars_corr(details, current_vars):
    var1 = float(current_vars[details["var1"]])
    var2 = float(current_vars[details["var2"]])
    corr = float(current_vars[details["corr_var"]])
    return round(corr * (var1 ** 0.5) * (var2 ** 0.5), details.get("decimals", 4))

def _vg_generate_p_value_for_scenario(details, current_vars):
    scenario = current_vars[details["scenario_var"]]
    if scenario == "significant":
        return round(random.uniform(0.001, 0.04), 3)
    return round(random.uniform(0.06, 0.2), 3)

def _vg_generate_sorted_int_array(details, current_vars):
    size = details["size"]
    min_val = details["min_val"]
    max_val = details["max_val"]
    arr = [random.randint(min_val, max_val) for _ in range(size)]
    arr.sort()
    return arr

def _vg_square_float_value(details, current_vars):
    base = float(current_vars[details["source_var"]])
    return round(base * base, details.get("decimals", 4))

def _vg_subtract_vars(details, current_vars):
    minuend = float(current_vars[details["var1"]])
    subtrahend = float(current_vars[details["var2"]])
    return round(minuend - subtrahend, details.get("decimals", 2))

def _vg_multiply_vars(details, current_vars):
    result = 1
    for var in details["vars"]:
        result *= current_vars[var]
    return result

def _vg_random_int_range_dependent(details, current_vars):
    min_val = details.get("min", 0)
    max_val = current_vars[details["max_var"]]
    return random.randint(min_val, max_val)

def _vg_generate_ci_diff_lower(details, current_vars):
    scenario = current_vars[details["scenario_var"]]
    if scenario == "mu1_greater":
        return round(random.uniform(0.1, 2.0), 2)
    elif scenario == "mu2_greater":
        return round(random.uniform(-5.0, -1.0), 2)
    else:
        return round(random.uniform(-2.0, -0.1), 2)

def _vg_generate_ci_diff_upper(details, current_vars):
    scenario = current_vars[details["scenario_var"]]
    lower = float(current_vars[details["lower_bound_var"]])
    if scenario == "mu1_greater":
        return round(lower + random.uniform(1.0, 4.0), 2)
    elif scenario == "mu2_greater":
        return round(lower + random.uniform(1.0, 4.0), 2)
    else:
        return round(random.uniform(0.1, 2.0), 2)

def _vg_generate_dataset_for_percentile(details: Dict, current_vars: Dict) -> List[int]:
    size = details.get("size", 10)
    min_val = details.get("min", 1)
    max_val = details.get("max", 100)
    return sorted(random.choices(range(min_val, max_val + 1), k=size))

def _vg_generate_array_with_mode_val(details: Dict, current_vars: Dict) -> List[Union[int, float]]:
    size = int(details.get("size", 10))
    min_val = details.get("min_val", 1)
    max_val = details.get("max_val", 10)
    
    # Get mode_val: either from current_vars (if generated by another step) or generate it now
    if "mode_val_var" in details and details["mode_val_var"] in current_vars:
        mode_val = current_vars[details["mode_val_var"]]
    else:
        mode_val = random.randint(min_val, max_val)
    
    # Get mode_freq: either from current_vars or generate/use default
    if "mode_freq_var" in details and details["mode_freq_var"] in current_vars:
        mode_freq = int(current_vars[details["mode_freq_var"]])
    else:
        # Ensure mode_freq is at least 2, and less than size to allow other numbers
        # And not more than half the size to make it a clear mode usually
        min_freq = details.get("mode_freq_min", 2)
        max_freq_possible = max(min_freq, size // 2 if size > 3 else size -1) # Ensure mode is not everything
        max_freq_possible = min(max_freq_possible, size -1 if size > 1 else 1) # Cannot be full size unless size is 1
        if min_freq > max_freq_possible : min_freq = max_freq_possible # Adjust if min_freq is too high for current size

        mode_freq = random.randint(min_freq, max_freq_possible) if min_freq <= max_freq_possible else min_freq


    arr = [mode_val] * mode_freq
    
    # For explanation template later, store these in current_vars so _al_find_mode_simple can access them
    current_vars["generated_mode_value_for_explanation"] = mode_val 
    current_vars["generated_mode_frequency_for_explanation"] = mode_freq

    remaining_size = size - mode_freq
    if remaining_size < 0: # Should not happen with corrected mode_freq logic
        print(f"Warning: mode_freq {mode_freq} > size {size} in _vg_generate_array_with_mode_val. Truncating.")
        return arr[:size]

    for _ in range(remaining_size):
        # Generate other values that are not the mode_val
        # and try to avoid creating a new mode or matching mode_freq
        attempts = 0
        while attempts < 50: # Safety break
            val = random.randint(min_val, max_val)
            temp_arr_check = arr + [val]
            counts = Counter(temp_arr_check)
            
            is_safe_to_add = True
            if val == mode_val and len(arr) < size: # Only add mode_val if we are still under mode_freq (shouldn't happen here)
                pass # This path should not be taken if remaining_size > 0
            
            # Check if adding 'val' makes it a new mode or equally frequent
            for v_count, freq_count in counts.items():
                if v_count != mode_val and freq_count >= mode_freq:
                    is_safe_to_add = False
                    break
            
            if is_safe_to_add:
                arr.append(val)
                break
            attempts += 1
        if attempts == 50: # Could not find a suitable non-mode value easily
            # Fallback: just add a random value (might create multi-modal, less ideal)
            arr.append(random.randint(min_val, max_val) if val == mode_val else val)


    random.shuffle(arr)
    return arr[:size]


def _vg_subtract_from_constant(details: Dict, current_vars: Dict) -> Union[int, float]:
    constant = details["constant"]
    subtract_val_key = details["subtract_var"]
    
    if subtract_val_key not in current_vars:
        print(f"ERROR in _vg_subtract_from_constant: Prerequisite var '{subtract_val_key}' not found in current_vars. Details: {details}")
        # Return a value that signals an error or can be caught, or raise an exception
        # For now, returning 0 might hide issues if 0 is a plausible calculation result.
        # Consider returning a specific error marker or raising an exception.
        return f"ERROR_VAR_NOT_FOUND_{subtract_val_key}" 
        
    subtract_val = current_vars[subtract_val_key]
    
    try:
        # Ensure both are numbers before subtraction
        num_constant = float(constant)
        num_subtract_val = float(subtract_val)
        return num_constant - num_subtract_val
    except (ValueError, TypeError):
        print(f"ERROR in _vg_subtract_from_constant: Cannot subtract. Constant='{constant}', SubtractVal='{subtract_val}'. Not both numbers.")
        return f"ERROR_TYPE_SUBTRACT"
    

def _vg_abs_z_value(details: Dict, current_vars: Dict) -> float:
    z_val = float(current_vars[details["z_var"]])
    return abs(z_val)

def _vg_alpha_bp_test(details: Dict, current_vars: Dict) -> float:
    alpha_percent = current_vars.get(details.get("alpha_var", "alpha_pref"), 5)
    return float(alpha_percent) / 100.0

def _vg_alpha_pref(details: Dict, current_vars: Dict) -> int:
    return random.choice([1, 5, 10])

def _vg_dataset_arr_mode_unshuffled(details: Dict, current_vars: Dict) -> int:
    arr = current_vars[details["source_var"]]
    counts = Counter(arr)
    mode_val = max(counts, key=counts.get)
    return mode_val

def _vg_dataset_arr_percentile_unsorted(details: Dict, current_vars: Dict) -> float:
    arr = list(current_vars[details["source_var"]])
    k = float(current_vars[details["percentile_var"]])
    sorted_arr = sorted(arr)
    index = int((k / 100) * (len(sorted_arr) - 1))
    return sorted_arr[index]


def _vg_power_decimal(details: Dict, current_vars: Dict) -> float:
    power_percent = current_vars.get(details.get("source_var", "power_percent"), 80)
    return float(power_percent) / 100.0

def _vg_dataset_arr_range(details: Dict, current_vars: Dict) -> int:
    arr = current_vars[details["source_var"]]
    return max(arr) - min(arr)

def _vg_claim_description(details: Dict, current_vars: Dict) -> str:
    return random.choice([
        "The new method is faster", "The new treatment is more effective",
        "The new curriculum improves scores", "The device is more energy efficient"
    ])

def _vg_claim_type_idx(details: Dict, current_vars: Dict) -> int:
    return random.randint(0, details.get("num_types", 3))


def _vg_ci_half_width(details: Dict, current_vars: Dict) -> float:
    upper = float(current_vars[details["upper_var"]])
    lower = float(current_vars[details["lower_var"]])
    return round((upper - lower) / 2.0, 3)

def _vg_ci_mean_center(details: Dict, current_vars: Dict) -> float:
    upper = float(current_vars[details["upper_var"]])
    lower = float(current_vars[details["lower_var"]])
    return round((upper + lower) / 2.0, 3)

def _vg_category_frequency(details: Dict, current_vars: Dict) -> int:
    arr = current_vars[details["source_var"]]
    target = current_vars[details["target_val_var"]]
    return arr.count(target)

def _vg_company_a(details: Dict, current_vars: Dict) -> str:
    return random.choice(["Alpha Inc.", "Beta Corp.", "Gamma LLC", "Delta Ltd."])

def _vg_company_b(details: Dict, current_vars: Dict) -> str:
    options = ["Omega Inc.", "Zeta Corp.", "Theta LLC", "Lambda Ltd."]
    a = current_vars.get("company_a", "")
    return random.choice([c for c in options if c != a]) if a else random.choice(options)

def _vg_competition_type(details: Dict, current_vars: Dict) -> str:
    return random.choice(["tournament", "open contest", "ranked challenge", "team event"])

def _vg_conf_level_ci_find_mean(details: Dict, current_vars: Dict) -> int:
    return random.choice([90, 95, 99])

def _vg_conf_level_prop_ci(details: Dict, current_vars: Dict) -> int:
    return random.choice([90, 95, 99])

def _vg_confidence_level_percent(details: Dict, current_vars: Dict) -> int:
    return random.choice([80, 85, 90, 95, 99])

def _vg_corr_AB_temp(details: Dict, current_vars: Dict) -> float:
    return round(random.uniform(-1.0, 1.0), 2)


def _vg_corr_coeff(details: Dict, current_vars: Dict) -> float:
    return round(random.uniform(-1.0, 1.0), 2)

def _vg_corr_coeff_target(details: Dict, current_vars: Dict) -> float:
    return round(random.uniform(-0.9, 0.9), 2)

def _vg_cov_AB(details: Dict, current_vars: Dict) -> float:
    return round(random.uniform(-50, 50), 2)

def _vg_cov_xy(details: Dict, current_vars: Dict) -> float:
    return round(random.uniform(-100, 100), 2)

def _vg_covariance_value(details: Dict, current_vars: Dict) -> float:
    return round(random.uniform(1, 30), 2)

def _vg_critical_mean_val(details: Dict, current_vars: Dict) -> float:
    mean = float(current_vars[details["mean_var"]])
    margin = float(current_vars[details["margin_var"]])
    return round(mean + margin, 2)

def _vg_random_int_range_between(details: Dict, current_vars: Dict) -> int:
    min_val = int(current_vars[details["min_var"]])
    max_val = int(current_vars[details["max_var"]])
    offset = details.get("offset", 0)

    # Apply offset to min and max
    min_val += offset
    max_val -= offset

    # Swap if needed
    if min_val > max_val:
        min_val, max_val = max_val, min_val

    return random.randint(min_val, max_val)


def _vg_dataset_arr(details: Dict, current_vars: Dict) -> List[int]:
    size = details.get("size", 10)
    return [random.randint(10, 100) for _ in range(size)]

def _vg_dataset_arr_mean(details: Dict, current_vars: Dict) -> float:
    arr = current_vars[details["arr_var"]]
    return round(sum(arr) / len(arr), 2) if arr else 0.0


def _vg_dataset_base(details: Dict, current_vars: Dict) -> List[int]:
    base = details.get("base", 10)
    step = details.get("step", 5)
    size = details.get("size", 10)
    return [base + step * i for i in range(size)]

def _vg_dataset_known_values_arr(details: Dict, current_vars: Dict) -> List[int]:
    values = details["values"]
    count = details.get("count", len(values))
    return random.sample(values * ((count // len(values)) + 1), count)

def _vg_dataset_known_values_str(details: Dict, current_vars: Dict) -> str:
    arr = current_vars[details["arr_var"]]
    return ", ".join(str(x) for x in arr)

def _vg_dataset_size(details: Dict, current_vars: Dict) -> int:
    return random.randint(details.get("min", 5), details.get("max", 50))

def _vg_dataset_size_mean(details: Dict, current_vars: Dict) -> float:
    size = current_vars[details["size_var"]]
    mean = current_vars[details["mean_var"]]
    return round(size * mean, 2)

def _vg_dataset_size_p(details: Dict, current_vars: Dict) -> int:
    total = current_vars[details["N_var"]]
    ratio = current_vars[details["ratio_var"]]
    return math.ceil(total * ratio)

def _vg_dataset_size_range(details: Dict, current_vars: Dict) -> Tuple[int, int]:
    min_size = details.get("min", 10)
    max_size = details.get("max", 100)
    return (min_size, max_size)

def _vg_dataset_str(details: Dict, current_vars: Dict) -> List[str]:
    size = details.get("size", 10)
    pool = details.get("pool", ["A", "B", "C", "D", "E"])
    return [random.choice(pool) for _ in range(size)]

def _vg_dataset_str_mean(details: Dict, current_vars: Dict) -> float:
    arr = current_vars[details["arr_var"]]
    num_arr = [float(x) for x in arr if str(x).replace(".", "").isdigit()]
    return round(sum(num_arr) / len(num_arr), 2) if num_arr else 0.0 #######


def _vg_dataset_str_percentile(details: Dict, current_vars: Dict) -> float:
    arr = current_vars[details["arr_var"]]
    k = current_vars[details["k_var"]]
    sorted_arr = sorted(float(x) for x in arr if str(x).replace(".", "").isdigit())
    if not sorted_arr: return 0.0
    if k <= 0: return sorted_arr[0]
    if k >= 100: return sorted_arr[-1]
    index = k * (len(sorted_arr) - 1) / 100
    lower = int(index)
    upper = math.ceil(index)
    if lower == upper:
        return round(sorted_arr[int(index)], 2)
    return round(sorted_arr[lower] + (sorted_arr[upper] - sorted_arr[lower]) * (index - lower), 2)

def _vg_dataset_str_range(details: Dict, current_vars: Dict) -> float:
    arr = [float(x) for x in current_vars[details["arr_var"]] if str(x).replace(".", "").isdigit()]
    return max(arr) - min(arr) if arr else 0.0

def _vg_defect_rate_decimal(details: Dict, current_vars: Dict) -> float:
    return round(random.uniform(0.01, 0.10), 4)

def _vg_defect_rate_percent(details: Dict, current_vars: Dict) -> float:
    return round(current_vars[details["decimal_var"]] * 100, 2)

def _vg_diff_scenario(details: Dict, current_vars: Dict) -> str:
    return random.choice(["A", "B"])

def _vg_effect_direction(details: Dict, current_vars: Dict) -> str:
    return random.choice(["increase", "decrease"])

def _vg_effect_size_bp(details: Dict, current_vars: Dict) -> float:
    return round(random.uniform(0.2, 0.8), 2)

def _vg_effect_size_brew(details: Dict, current_vars: Dict) -> float:
    return round(abs(current_vars[details["mean1"]] - current_vars[details["mean2"]]), 2)

def _vg_event_correlated(details: Dict, current_vars: Dict) -> str:
    return random.choice(["sunshine", "rainfall", "temperature"])

def _vg_event_correlated_plural(details: Dict, current_vars: Dict) -> str:
    singular = current_vars[details["singular_var"]]
    return get_plural(singular)

def _vg_event_type_poisson(details: Dict, current_vars: Dict) -> str:
    return random.choice(["call", "accident", "hit", "breakdown"])

def _vg_event_type_poisson_plural(details: Dict, current_vars: Dict) -> str:
    return get_plural(current_vars[details["singular_var"]])

def _vg_example_scores_arr(details: Dict, current_vars: Dict) -> List[int]:
    return [random.randint(60, 100) for _ in range(details.get("size", 10))]

def _vg_example_scores_str(details: Dict, current_vars: Dict) -> str:
    return ", ".join(str(score) for score in current_vars[details["source_var"]])

def _vg_ey_val(details: Dict, current_vars: Dict) -> float:
    return round(current_vars[details["mu"]] + current_vars[details["cov"]], 2)

def _vg_group1_desc(details: Dict, current_vars: Dict) -> str:
    return random.choice(["Group A", "Control Group", "Treatment A"])

def _vg_group2_desc(details: Dict, current_vars: Dict) -> str:
    return random.choice(["Group B", "Placebo", "Treatment B"])

def _vg_income_range_high(details: Dict, current_vars: Dict) -> int:
    return current_vars[details["low"]] + random.randint(10000, 50000)

def _vg_income_range_low(details: Dict, current_vars: Dict) -> int:
    return random.randint(10000, 30000)


def _vg_k_successes_binomial(details: Dict, current_vars: Dict) -> int:
    return random.randint(0, current_vars[details["n_var"]])

def _vg_k_val_poisson(details: Dict, current_vars: Dict) -> int:
    return random.randint(1, 20)

def _vg_lambda_approx_check(details: Dict, current_vars: Dict) -> float:
    return round(current_vars[details["mean"]], 2)

def _vg_lambda_calculated(details: Dict, current_vars: Dict) -> float:
    return round(current_vars[details["total"]] / current_vars[details["time"]], 2)

def _vg_lambda_poisson_var(details: Dict, current_vars: Dict) -> float:
    return round(current_vars[details["lambda_var"]], 2)

def _vg_lambda_poisson_var_sq(details: Dict, current_vars: Dict) -> float:
    val = current_vars[details["lambda_var"]]
    return round(val * val, 2)

def _vg_lambda_val_poisson(details: Dict, current_vars: Dict) -> float:
    return round(random.uniform(1.5, 10.0), 2)

def _vg_last_year_avg_score(details: Dict, current_vars: Dict) -> float:
    return round(random.uniform(60.0, 95.0), 2)

def _vg_location_poisson(details: Dict, current_vars: Dict) -> str:
    return random.choice(["factory", "intersection", "hospital", "office"])

def _vg_lower_bound_ci_find_mean(details: Dict, current_vars: Dict) -> float:
    mean_key = details.get("mean", "mean_val")
    margin_key = details.get("margin", "margin_error")

    mean = current_vars.get(mean_key)
    margin = current_vars.get(margin_key)

    if mean is None or margin is None:
        print(f"ERROR (_vg_lower_bound_ci_find_mean): Missing required keys '{mean_key}' or '{margin_key}' in current_vars.")
        return -9999.99

    try:
        return round(float(mean) - float(margin), 2)
    except Exception as e:
        print(f"ERROR (_vg_lower_bound_ci_find_mean): Failed calculation due to invalid data types. Mean: {mean}, Margin: {margin}, Error: {e}")
        return -9999.99

def _vg_sum_vars_int(details: Dict, current_vars: Dict) -> int:
    total = 0
    for val in details["vars_to_sum"]:
        if isinstance(val, int):
            total += val
        elif val in current_vars:
            total += int(current_vars[val])
        else:
            print(f"ERROR (_vg_sum_vars_int): Variable '{val}' not found in current_vars.")
            return "ERROR_SUM_VAR_MISSING"
    return total


def _vg_lower_bound_diff(details: Dict, current_vars: Dict) -> float:
    return round(current_vars[details["diff"]] - current_vars[details["margin"]], 2)

def _vg_lower_diff_prop(details: Dict, current_vars: Dict) -> float:
    return round(current_vars[details["p1"]] - current_vars[details["p2"]], 3)

def _vg_margin_error(details: Dict, current_vars: Dict) -> float:
    return round(current_vars[details["z"]] * current_vars[details["std"]] / (current_vars[details["n"]]**0.5), 2)

def _vg_margin_error_fm(details: Dict, current_vars: Dict) -> float:
    return round(current_vars[details["critical"]] * current_vars[details["sd"]] / (current_vars[details["n"]]**0.5), 2)

def _vg_max_defects(details: Dict, current_vars: Dict) -> int:
    return random.randint(1, 10)

def _vg_mean_score_test(details: Dict, current_vars: Dict) -> float:
    return round(sum(current_vars[details["scores"]]) / len(current_vars[details["scores"]]), 2)

def _vg_mean_val(details: Dict, current_vars: Dict) -> float:
    arr = current_vars[details["arr"]]
    return round(sum(arr) / len(arr), 2) if arr else 0.0

def _vg_missing_value_x(details: Dict, current_vars: Dict) -> float:
    known_sum = sum(current_vars[details["arr"]])
    expected_mean = current_vars[details["mean"]]
    total_elements = current_vars[details["size"]]
    return round((expected_mean * total_elements) - known_sum, 2)

def _vg_mode_val(details: Dict, current_vars: Dict) -> Any:
    return max(set(current_vars[details["arr"]]), key=current_vars[details["arr"]].count)

def _vg_mu0_brew_time(details: Dict, current_vars: Dict) -> float:
    return round(random.uniform(2.5, 5.0), 2)

def _vg_mu_alt(details: Dict, current_vars: Dict) -> float:
    return round(current_vars[details["mu_null"]] + random.uniform(1, 5), 2)

def _vg_mu_alt_diff(details: Dict, current_vars: Dict) -> float:
    return round(current_vars[details["mu_alt"]] - current_vars[details["mu_null"]], 2)

def _vg_mu_null(details: Dict, current_vars: Dict) -> float:
    return round(random.uniform(20, 100), 2)

def _vg_mu_null_val(details: Dict, current_vars: Dict) -> float:
    return current_vars[details["source_var"]]

def _vg_multiplier(details: Dict, current_vars: Dict) -> float:
    return round(random.uniform(0.5, 2.0), 2)

def _vg_n_binomial_test(details: Dict, current_vars: Dict) -> int:
    return random.randint(30, 200)

def _vg_n_brew_sample(details: Dict, current_vars: Dict) -> int:
    return random.randint(5, 25)

def _vg_n_prop_ci(details: Dict, current_vars: Dict) -> int:
    return random.randint(30, 500)

def _vg_n_sample_fpc(details: Dict, current_vars: Dict) -> int:
    return random.randint(50, 200)

def _vg_n_sample_fpc_ratio(details: Dict, current_vars: Dict) -> float:
    return round(current_vars[details["n_sample"]] / current_vars[details["pop_size"]], 2)

def _vg_n_sys_sample(details: Dict, current_vars: Dict) -> int:
    return current_vars[details["pop_size"]] // current_vars[details["interval"]]

def _vg_n_town_sample(details: Dict, current_vars: Dict) -> int:
    return random.randint(10, 100)

def _vg_n_town_sample_ratio(details: Dict, current_vars: Dict) -> float:
    return round(current_vars[details["n_sample"]] / current_vars[details["pop_total"]], 2)

def _vg_n_trials_binom_mean(details: Dict, current_vars: Dict) -> int:
    return int(current_vars[details["mean"]] / current_vars[details["p"]])

def _vg_n_trials_binom_var(details: Dict, current_vars: Dict) -> int:
    return int(current_vars[details["variance"]] / (current_vars[details["p"]] * (1 - current_vars[details["p"]])))

def _vg_num_attempts_ft(details: Dict, current_vars: Dict) -> int:
    return random.randint(3, 10)

def _vg_num_known_values(details: Dict, current_vars: Dict) -> int:
    return len([x for x in current_vars[details["arr_var"]] if isinstance(x, (int, float))])

def _vg_num_mode_val(details: Dict, current_vars: Dict) -> int:
    return Counter(current_vars[details["arr_var"]])[current_vars[details["mode_val"]]]

def _vg_num_students_sd(details: Dict, current_vars: Dict) -> int:
    return random.randint(25, 100)

def _vg_num_successes(details: Dict, current_vars: Dict) -> int:
    return int(current_vars[details["n"]] * current_vars[details["p"]])

def _vg_num_trials(details: Dict, current_vars: Dict) -> int:
    return random.randint(10, 100)

def _vg_original_mean(details: Dict, current_vars: Dict) -> float:
    return round(sum(current_vars[details["arr_var"]]) / len(current_vars[details["arr_var"]]), 2)

def _vg_outlier_score(details: Dict, current_vars: Dict) -> float:
    return random.uniform(100, 150)

def _vg_p1_percent(details: Dict, current_vars: Dict) -> float:
    return round(random.uniform(40, 60), 1)

def _vg_p1_percent_base(details: Dict, current_vars: Dict) -> float:
    return round(current_vars[details["p1_percent"]] / 100, 4)

def _vg_p1_true_scenario(details: Dict, current_vars: Dict) -> str:
    return random.choice(["A", "B"])

def _vg_p2_percent(details: Dict, current_vars: Dict) -> float:
    return round(random.uniform(40, 60), 1)

def _vg_p2_true_scenario(details: Dict, current_vars: Dict) -> str:
    return random.choice(["A", "B"])

def _vg_p_binom_mean(details: Dict, current_vars: Dict) -> float:
    return round(current_vars[details["n_var"]] * current_vars[details["p_var"]], 2)

def _vg_p_binom_var(details: Dict, current_vars: Dict) -> float:
    p = current_vars[details["p_var"]]
    n = current_vars[details["n_var"]]
    return round(n * p * (1 - p), 2)

def _vg_p_hat_target(details: Dict, current_vars: Dict) -> float:
    return round(random.uniform(0.3, 0.7), 2)

def _vg_p_value_argument(details: Dict, current_vars: Dict) -> str:
    return random.choice(["greater", "less", "not equal"])

def _vg_p_value_gen(details: Dict, current_vars: Dict) -> float:
    return round(random.uniform(0.001, 0.099), 4)

def _vg_p_value_scenario(details: Dict, current_vars: Dict) -> str:
    return random.choice(["more effective", "less effective", "no difference"])

def _vg_p_value_scenario_arg(details: Dict, current_vars: Dict) -> str:
    return random.choice(["increased", "decreased", "unchanged"])

def _vg_percentile_k(details: Dict, current_vars: Dict) -> float:
    return round(random.uniform(10, 90), 1)

def _vg_points_added(details: Dict, current_vars: Dict) -> int:
    return random.randint(1, 10)

def _vg_pop_mean_clt(details: Dict, current_vars: Dict) -> float:
    return round(random.uniform(60, 100), 2)

def _vg_pop_std_clt(details: Dict, current_vars: Dict) -> float:
    return round(random.uniform(10, 20), 2)

def _vg_pop_std_dev(details: Dict, current_vars: Dict) -> float:
    return round(random.uniform(5, 15), 2)

def _vg_positive_outcome_description(details: Dict, current_vars: Dict) -> str:
    return random.choice(["passed", "approved", "completed successfully", "achieved target"])

def _vg_power_percent(details: Dict, current_vars: Dict) -> float:
    return round(current_vars[details["decimal_var"]] * 100, 2)

def _vg_prob_success(details: Dict, current_vars: Dict) -> float:
    return round(random.uniform(0.1, 0.9), 2)

def _vg_prob_success_ft(details: Dict, current_vars: Dict) -> float:
    return round(random.uniform(0.2, 0.6), 2)

def _vg_product_cat(details: Dict, current_vars: Dict) -> str:
    return random.choice(["Gadget", "Tool", "Appliance", "Device"])

def _vg_product_ci_find_mean(details: Dict, current_vars: Dict) -> str:
    return random.choice(["smartphone", "refrigerator", "vacuum cleaner", "laptop"])

def _vg_product_name(details: Dict, current_vars: Dict) -> str:
    return random.choice(["iWidget", "GizmoPro", "TechMate", "UltraClean"])

def _vg_product_type(details: Dict, current_vars: Dict) -> str:
    return random.choice(["electronic", "mechanical", "hybrid"])

def _vg_prop_A_actual(details: Dict, current_vars: Dict) -> float:
    return round(random.uniform(0.4, 0.7), 2)

def _vg_prop_A_percent(details: Dict, current_vars: Dict) -> float:
    return round(current_vars[details["actual_var"]] * 100, 2)

def _vg_prop_B_actual(details: Dict, current_vars: Dict) -> float:
    return round(random.uniform(0.3, 0.6), 2)

def _vg_prop_B_percent(details: Dict, current_vars: Dict) -> float:
    return round(current_vars[details["actual_var"]] * 100, 2)

def _vg_proportion_true(details: Dict, current_vars: Dict) -> float:
    return round(random.uniform(0.2, 0.8), 2)

def _vg_q1_val(details: Dict, current_vars: Dict) -> float:
    arr = sorted(current_vars[details["source_array"]])
    return arr[len(arr)//4]

def _vg_q3_val(details: Dict, current_vars: Dict) -> float:
    arr = sorted(current_vars[details["source_array"]])
    return arr[(3*len(arr))//4]

def _vg_sample_mean(details: Dict, current_vars: Dict) -> float:
    return round(sum(current_vars[details["array_var"]]) / len(current_vars[details["array_var"]]), 2)

def _vg_sample_size(details: Dict, current_vars: Dict) -> int:
    return random.randint(30, 300)

def _vg_sample_size_base(details: Dict, current_vars: Dict) -> int:
    return random.randint(40, 200)

def _vg_sample_size_clt(details: Dict, current_vars: Dict) -> int:
    return random.choice([30, 50, 100, 200])

def _vg_sample_size_items(details: Dict, current_vars: Dict) -> int:
    return random.randint(30, 200)

def _vg_sample_size_prop(details: Dict, current_vars: Dict) -> int:
    return random.randint(50, 300)

def _vg_scenario_higher(details: Dict, current_vars: Dict) -> str:
    return random.choice(["A", "B"])

def _vg_scenario_type(details: Dict, current_vars: Dict) -> str:
    return random.choice(["one-tailed", "two-tailed"])

def _vg_score1(details: Dict, current_vars: Dict) -> float:
    return round(random.uniform(60, 95), 1)

def _vg_score2(details: Dict, current_vars: Dict) -> float:
    return round(random.uniform(60, 95), 1)

def _vg_score_high(details: Dict, current_vars: Dict) -> int:
    return random.randint(90, 100)

def _vg_score_low(details: Dict, current_vars: Dict) -> int:
    return random.randint(50, 70)

def _vg_service_place(details: Dict, current_vars: Dict) -> str:
    return random.choice(["online", "in-store", "phone"])

def _vg_sorted_dataset_arr_median(details: Dict, current_vars: Dict) -> float:
    arr = sorted(current_vars[details["arr_var"]])
    n = len(arr)
    if n == 0:
        return 0.0
    mid = n // 2
    if n % 2 == 0:
        return (arr[mid - 1] + arr[mid]) / 2
    else:
        return arr[mid]

def _vg_sorted_dataset_str_median(details: Dict, current_vars: Dict) -> float:
    arr = sorted(float(x) for x in current_vars[details["arr_var"]])
    n = len(arr)
    if n == 0:
        return 0.0
    mid = n // 2
    if n % 2 == 0:
        return (arr[mid - 1] + arr[mid]) / 2
    else:
        return arr[mid]

def _vg_std_dev1(details: Dict, current_vars: Dict) -> float:
    return round(random.uniform(5.0, 15.0), 2)

def _vg_std_dev2(details: Dict, current_vars: Dict) -> float:
    return round(random.uniform(5.0, 15.0), 2)

def _vg_std_dev_a(details: Dict, current_vars: Dict) -> float:
    return round(random.uniform(1.0, 10.0), 2)

def _vg_std_dev_b(details: Dict, current_vars: Dict) -> float:
    return round(random.uniform(1.0, 10.0), 2)

def _vg_std_dev_b_factor(details: Dict, current_vars: Dict) -> float:
    return round(current_vars[details["std_dev_a"]] * random.uniform(1.1, 2.0), 2)

def _vg_std_dev_base(details: Dict, current_vars: Dict) -> float:
    return round(random.uniform(1.0, 5.0), 2)

def _vg_std_dev_bp(details: Dict, current_vars: Dict) -> float:
    return round(random.uniform(0.5, 2.0), 2)

def _vg_std_dev_test(details: Dict, current_vars: Dict) -> float:
    return round(random.uniform(2.0, 8.0), 2)

def _vg_std_dev_val(details: Dict, current_vars: Dict) -> float:
    return round(random.uniform(1.0, 10.0), 2)

def _vg_std_dev_x_base(details: Dict, current_vars: Dict) -> float:
    return round(random.uniform(2.0, 5.0), 2)

def _vg_std_dev_x_c(details: Dict, current_vars: Dict) -> float:
    return round(current_vars[details["base_var"]] * random.uniform(1.1, 1.5), 2)

def _vg_std_dev_y_base(details: Dict, current_vars: Dict) -> float:
    return round(random.uniform(2.0, 5.0), 2)

def _vg_std_dev_y_c(details: Dict, current_vars: Dict) -> float:
    return round(current_vars[details["base_var"]] * random.uniform(1.1, 1.5), 2)

def _vg_success_rate_percent(details: Dict, current_vars: Dict) -> float:
    return round(random.uniform(60.0, 99.0), 2)

def _vg_target_mean(details: Dict, current_vars: Dict) -> float:
    return round(random.uniform(30.0, 70.0), 2)

def _vg_target_proportion_percent(details: Dict, current_vars: Dict) -> float:
    return round(random.uniform(40.0, 90.0), 2)

def _vg_time_unit_poisson(details: Dict, current_vars: Dict) -> str:
    return random.choice(["minute", "hour", "day"])

def _vg_total1_pref(details: Dict, current_vars: Dict) -> str:
    return random.choice(["total number of", "number of", "all"])

def _vg_total2_pref(details: Dict, current_vars: Dict) -> str:
    return random.choice(["total number of", "number of", "all"])

def _vg_total_observations(details: Dict, current_vars: Dict) -> int:
    return random.randint(30, 300)

def _vg_upper_bound_ci_find_mean(details: Dict, current_vars: Dict) -> float:
    return round(current_vars[details["mean"]] + current_vars[details["margin"]], 2)

def _vg_upper_bound_diff(details: Dict, current_vars: Dict) -> float:
    return round(random.uniform(2.0, 5.0), 2)

def _vg_upper_diff_prop(details: Dict, current_vars: Dict) -> float:
    return round(random.uniform(0.01, 0.1), 3)

def _vg_upper_height_ci(details: Dict, current_vars: Dict) -> float:
    return round(current_vars[details["mean"]] + current_vars[details["ci_half"]], 2)

def _vg_var1(details: Dict, current_vars: Dict) -> float:
    return round(random.uniform(3.0, 7.0), 2)

def _vg_var1_name(details: Dict, current_vars: Dict) -> str:
    return random.choice(["height", "weight", "score"])

def _vg_var2(details: Dict, current_vars: Dict) -> float:
    return round(random.uniform(3.0, 7.0), 2)

def _vg_var2_name(details: Dict, current_vars: Dict) -> str:
    return random.choice(["height", "weight", "score"])

def _vg_random_choice_different(details: Dict, current_vars: Dict) -> str:
    choices = details["choices"]
    avoid = current_vars[details["different_from_var"]]
    filtered = [choice for choice in choices if choice != avoid]
    return random.choice(filtered) if filtered else avoid


def _vg_var_A(details: Dict, current_vars: Dict) -> float:
    return round(random.uniform(5.0, 10.0), 2)

def _vg_var_B(details: Dict, current_vars: Dict) -> float:
    return round(random.uniform(2.0, 6.0), 2)

def _vg_var_x(details: Dict, current_vars: Dict) -> float:
    return round(random.uniform(1.0, 5.0), 2)

def _vg_var_x_corr(details: Dict, current_vars: Dict) -> float:
    return round(random.uniform(-1.0, 1.0), 2)

def _vg_var_x_val(details: Dict, current_vars: Dict) -> float:
    return round(current_vars[details["var"]] + random.uniform(-1.0, 1.0), 2)

def _vg_var_y(details: Dict, current_vars: Dict) -> float:
    return round(random.uniform(1.0, 5.0), 2)

def _vg_var_y_corr(details: Dict, current_vars: Dict) -> float:
    return round(random.uniform(-1.0, 1.0), 2)

def _vg_var_y_val(details: Dict, current_vars: Dict) -> float:
    return round(current_vars[details["var"]] + random.uniform(-1.0, 1.0), 2)

def _vg_variance(details: Dict, current_vars: Dict) -> float:
    return round(random.uniform(1.0, 25.0), 2)

def _vg_variance_base(details: Dict, current_vars: Dict) -> float:
    return round(random.uniform(1.0, 10.0), 2)

def _vg_variance_val(details: Dict, current_vars: Dict) -> float:
    return round(current_vars[details["std_dev"]] ** 2, 2)

def _vg_weight1_decimal(details: Dict, current_vars: Dict) -> float:
    return round(random.uniform(0.1, 0.5), 2)

def _vg_weight1_percent(details: Dict, current_vars: Dict) -> float:
    return round(current_vars[details["decimal_var"]] * 100, 2)

def _vg_weight2_decimal(details: Dict, current_vars: Dict) -> float:
    return round(random.uniform(0.1, 0.5), 2)

def _vg_weight2_percent(details: Dict, current_vars: Dict) -> float:
    return round(current_vars[details["decimal_var"]] * 100, 2)

def _vg_weight2_percent_calc(details: Dict, current_vars: Dict) -> float:
    return round(random.uniform(0.1, 0.5) * 100, 2)

def _vg_weight_A_decimal(details: Dict, current_vars: Dict) -> float:
    return round(random.uniform(0.1, 0.5), 2)

def _vg_weight_A_percent(details: Dict, current_vars: Dict) -> float:
    return round(current_vars[details["decimal_var"]] * 100, 2)

def _vg_weight_B_decimal(details: Dict, current_vars: Dict) -> float:
    return round(random.uniform(0.1, 0.5), 2)

def _vg_weight_B_percent(details: Dict, current_vars: Dict) -> float:
    return round(current_vars[details["decimal_var"]] * 100, 2)

def _vg_x_bar_brew_time(details: Dict, current_vars: Dict) -> float:
    return round(random.uniform(2.0, 5.0), 2)

def _vg_x_success_prop_ci(details: Dict, current_vars: Dict) -> int:
    return int(round(current_vars[details["sample_size_var"]] * current_vars[details["p_hat_var"]]))

def _vg_x_val(details: Dict, current_vars: Dict) -> float:
    return round(float(current_vars[details["value_var"]]), 2)

def _vg_z_score_target(details: Dict, current_vars: Dict) -> float:
    return round(random.uniform(1.0, 3.0), 2)

def _vg_z_score_val(details: Dict, current_vars: Dict) -> float:
    mean = float(current_vars[details["mean_var"]])
    std_dev = float(current_vars[details["std_var"]])
    x = float(current_vars[details["x_var"]])
    return round((x - mean) / std_dev, 3) if std_dev != 0 else 0.0

def _vg_z_val_prop_ci(details: Dict, current_vars: Dict) -> float:
    conf_level = int(current_vars[details["conf_level_var"]])
    return Z_TABLE_COMMON.get(conf_level, 1.96)

def _vg_z_value_prop(details: Dict, current_vars: Dict) -> float:
    p1 = float(current_vars[details["p1_var"]])
    p2 = float(current_vars[details["p2_var"]])
    n1 = int(current_vars[details["n1_var"]])
    n2 = int(current_vars[details["n2_var"]])
    numerator = p1 - p2
    denominator = math.sqrt((p1 * (1 - p1)) / n1 + (p2 * (1 - p2)) / n2)
    return round(numerator / denominator, 3) if denominator != 0 else 0.0

def _vg_person2_name(details: Dict, current_vars: Dict) -> str:
    return random.choice(["John", "Nick", "Aanya", "Sara"])

def _vg_score_type(details: Dict, current_vars: Dict) -> str:
    return random.choice(["test score", "math score", "reading score", "performance rating"])

def _vg_score_type_plural(details: Dict, current_vars: Dict) -> str:
    singular = current_vars[details["singular_var"]]
    return get_plural(singular)

def _vg_group_type(details: Dict, current_vars: Dict) -> str:
    return random.choice(["Control Group", "Treatment Group", "Experimental Group", "Placebo Group"])

def _vg_service_type(details: Dict, current_vars: Dict) -> str:
    return random.choice(["internet service", "mobile service", "subscription service", "cloud storage"])

def _vg_test_stat_scenario(details: Dict, current_vars: Dict) -> str:
    return random.choice(["z-test", "t-test", "chi-square test", "ANOVA"])

def _vg_statistical_test(details: Dict, current_vars: Dict) -> str:
    return random.choice(["z-test", "t-test", "chi-squared test", "F-test"])

def _vg_outlier_description(details: Dict, current_vars: Dict) -> str:
    return random.choice(["exceptionally high score", "very low result", "unusual reading", "anomalous value"])

def _vg_conf_level_text(details: Dict, current_vars: Dict) -> str:
    level = current_vars[details["conf_level_var"]]
    return f"{level}% confidence level"

def _vg_item_qc_property(details: Dict, current_vars: Dict) -> str:
    condition_var = details["condition_var"]
    condition_val = current_vars.get(condition_var)

    condition_map = {c["if_val"]: c["then_val"] for c in details["conditions_values"]}

    if condition_val not in condition_map:
        raise ValueError(f"[CRITICAL] condition_val '{condition_val}' from '{condition_var}' not in condition map: {list(condition_map.keys())}")
    
    return condition_map[condition_val]







    
# Global temporary store for variable_generators of the current template being processed.
# This is a workaround for _vg_lookup_from_options needing access to the original list of choices.
# A cleaner way would be to pass the template's variable_generators dict into each _vg function.
template_variable_generators_store = {}


VARIABLE_GENERATOR_FUNCTIONS: Dict[str, Callable] = {
    "random_choice": _vg_random_choice,
    "random_int_range": _vg_random_int_range,
    "lookup_from_options": _vg_lookup_from_options,
    "square_value": _vg_square_value,
    "random_float_range": _vg_random_float_range,
    "sum_vars": _vg_sum_vars,
    "calculate_mean_with_missing": _vg_calculate_mean_with_missing,
    "generate_int_array": _vg_generate_int_array,
    "array_to_string": _vg_array_to_string,
    "calculate_successes_from_prop": _vg_calculate_successes_from_prop,
    "generate_p_value_relative_to_alpha": _vg_generate_p_value_relative_to_alpha,
    "calculate_x_from_z": _vg_calculate_x_from_z,
    "fixed_value": _vg_fixed_value,
    "random_int_range_dependent_max": _vg_random_int_range_dependent_max,
    "generate_perfect_square": _vg_generate_perfect_square,
    "generate_int_array_with_mode": _vg_generate_int_array_with_mode,
    "shuffle_array": _vg_shuffle_array,
    "singular_form": _vg_singular_form,
    "calculate_n_from_N_ratio_int": _vg_calculate_n_from_N_ratio_int,
    "calculate_n_from_N_ratio": _vg_calculate_n_from_N_ratio_int, 
    "random_int_range_step": _vg_random_int_range_step,
    "multiply_vars_float": _vg_multiply_vars_float,
    "percent_to_decimal": _vg_percent_to_decimal,
    "decimal_to_percent": _vg_decimal_to_percent,
    "decimal_to_percent_str": _vg_decimal_to_percent_str,
    "identity": _vg_identity,
    "conditional_value": _vg_conditional_value,
    "random_int_range_dependent_max_strict": _vg_random_int_range_dependent_max_strict,
    "random_int_near_lambda": _vg_random_int_near_lambda,
    "plural_form": _vg_plural_form,
    "random_float_range_plus": _vg_random_float_range_plus,
    "conditional_text": _vg_conditional_text,
    "calculate_one_minus_var": _vg_calculate_one_minus_var,
    "calculate_cov_from_vars_corr": _vg_calculate_cov_from_vars_corr,
    "calculate_cov_from_target_corr": _vg_calculate_cov_from_target_corr,
    "sort_array": _vg_sort_array,
    "lookup_z_for_confidence": _vg_lookup_z_for_confidence,
    "generate_p2_for_diff_prop_scenario": _vg_generate_p2_for_diff_prop_scenario,
    "generate_ci_diff_prop_lower": _vg_generate_ci_diff_prop_lower,
    "generate_ci_diff_prop_upper": _vg_generate_ci_diff_prop_upper,
    "city_name_based_on_higher_prop": _vg_city_name_based_on_higher_prop,
    "calculate_systematic_interval": _vg_calculate_systematic_interval,
    "multiply_vars": _vg_multiply_vars,
    "generate_mu_null_for_ci_test": _vg_generate_mu_null_for_ci_test,
    "conditional_prop_scenario": _vg_conditional_prop_scenario,
    "square_float_value": _vg_square_float_value,
    "random_int_range_between": _vg_random_int_range_between,
    "calculate_x_bar_for_test_stat": _vg_calculate_x_bar_for_test_stat, 
    "calculate_cov_from_vars_corr": _vg_calculate_cov_from_vars_corr,
    "generate_p_value_for_scenario": _vg_generate_p_value_for_scenario,
    "generate_sorted_int_array": _vg_generate_sorted_int_array,
    "random_choice_different": _vg_random_choice_different,
    "square_float_value": _vg_square_float_value,
    "subtract_vars": _vg_subtract_vars,
    "sum_vars_int": _vg_sum_vars_int,
    "multiply_vars": _vg_multiply_vars,
    "random_int_range_dependent": _vg_random_int_range_dependent,
    "generate_ci_diff_lower": _vg_generate_ci_diff_lower,
    "generate_ci_diff_upper": _vg_generate_ci_diff_upper,
    "generate_dataset_for_percentile": _vg_generate_dataset_for_percentile,
    "generate_array_with_mode_val": _vg_generate_array_with_mode_val, 
    "subtract_from_constant": _vg_subtract_from_constant,
    "abs_z_value": _vg_abs_z_value,
    "alpha_bp_test": _vg_alpha_bp_test,
    "alpha_pref": _vg_alpha_pref,
    "dataset_arr_mode_unshuffled": _vg_dataset_arr_mode_unshuffled,
    "dataset_arr_percentile_unsorted": _vg_dataset_arr_percentile_unsorted,
    "power_decimal": _vg_power_decimal,
    "dataset_arr_range": _vg_dataset_arr_range,
    "claim_description": _vg_claim_description,
    "claim_type_idx": _vg_claim_type_idx,
    "ci_half_width": _vg_ci_half_width,
    "ci_mean_center": _vg_ci_mean_center,
    "category_frequency": _vg_category_frequency,
    "company_a": _vg_company_a,
    "company_b": _vg_company_b,
    "competition_type": _vg_competition_type,
    "conf_level_ci_find_mean": _vg_conf_level_ci_find_mean,
    "conf_level_prop_ci": _vg_conf_level_prop_ci,
    "confidence_level_percent": _vg_confidence_level_percent,
    "corr_AB_temp": _vg_corr_AB_temp,
    "corr_coeff": _vg_corr_coeff,
    "corr_coeff_target": _vg_corr_coeff_target,
    "cov_AB": _vg_cov_AB,
    "cov_xy": _vg_cov_xy,
    "covariance_value": _vg_covariance_value,
    "critical_mean_val": _vg_critical_mean_val,
    "dataset_arr": _vg_dataset_arr,
    "dataset_arr_mean": _vg_dataset_arr_mean,
    "dataset_base": _vg_dataset_base,
    "dataset_known_values_arr": _vg_dataset_known_values_arr,
    "dataset_known_values_str": _vg_dataset_known_values_str,
    "dataset_size": _vg_dataset_size,
    "dataset_size_mean": _vg_dataset_size_mean,
    "dataset_size_p": _vg_dataset_size_p,
    "dataset_size_range": _vg_dataset_size_range,
    "dataset_str": _vg_dataset_str,
    "dataset_str_mean": _vg_dataset_str_mean,
    "dataset_str_percentile": _vg_dataset_str_percentile,
    "dataset_str_range": _vg_dataset_str_range,
    "defect_rate_decimal": _vg_defect_rate_decimal,
    "defect_rate_percent": _vg_defect_rate_percent,
    "diff_scenario": _vg_diff_scenario,
    "effect_direction": _vg_effect_direction,
    "effect_size_bp": _vg_effect_size_bp,
    "effect_size_brew": _vg_effect_size_brew,
    "event_correlated": _vg_event_correlated,
    "event_correlated_plural": _vg_event_correlated_plural,
    "event_type_poisson": _vg_event_type_poisson,
    "event_type_poisson_plural": _vg_event_type_poisson_plural,
    "example_scores_arr": _vg_example_scores_arr,
    "example_scores_str": _vg_example_scores_str,
    "ey_val": _vg_ey_val,
    "group1_desc": _vg_group1_desc,
    "group2_desc": _vg_group2_desc,
    "income_range_high": _vg_income_range_high,
    "income_range_low": _vg_income_range_low,
    "k_successes_binomial": _vg_k_successes_binomial,
    "k_val_poisson": _vg_k_val_poisson,
    "lambda_approx_check": _vg_lambda_approx_check,
    "lambda_calculated": _vg_lambda_calculated,
    "lambda_poisson_var": _vg_lambda_poisson_var,
    "lambda_poisson_var_sq": _vg_lambda_poisson_var_sq,
    "lambda_val_poisson": _vg_lambda_val_poisson,
    "last_year_avg_score": _vg_last_year_avg_score,
    "location_poisson": _vg_location_poisson,
    "lower_bound_ci_find_mean": _vg_lower_bound_ci_find_mean,
    "lower_bound_diff": _vg_lower_bound_diff,
    "lower_diff_prop": _vg_lower_diff_prop,
    "margin_error": _vg_margin_error,
    "margin_error_fm": _vg_margin_error_fm,
    "max_defects": _vg_max_defects,
    "mean_score_test": _vg_mean_score_test,
    "mean_val": _vg_mean_val,
    "missing_value_x": _vg_missing_value_x,
    "mode_val": _vg_mode_val,
    "mu0_brew_time": _vg_mu0_brew_time,
    "mu_alt": _vg_mu_alt,
    "mu_alt_diff": _vg_mu_alt_diff,
    "mu_null": _vg_mu_null,
    "mu_null_val": _vg_mu_null_val,
    "multiplier": _vg_multiplier,
    "n_binomial_test": _vg_n_binomial_test,
    "n_brew_sample": _vg_n_brew_sample,
    "n_prop_ci": _vg_n_prop_ci,
    "n_sample_fpc": _vg_n_sample_fpc,
    "n_sample_fpc_ratio": _vg_n_sample_fpc_ratio,
    "n_sys_sample": _vg_n_sys_sample,
    "n_town_sample": _vg_n_town_sample,
    "n_town_sample_ratio": _vg_n_town_sample_ratio,
    "n_trials_binom_mean": _vg_n_trials_binom_mean,
    "n_trials_binom_var": _vg_n_trials_binom_var,
    "num_attempts_ft": _vg_num_attempts_ft,
    "num_known_values": _vg_num_known_values,
    "num_mode_val": _vg_num_mode_val,
    "num_students_sd": _vg_num_students_sd,
    "num_successes": _vg_num_successes,
    "num_trials": _vg_num_trials,
    "original_mean": _vg_original_mean,
    "outlier_score": _vg_outlier_score,
    "p1_percent": _vg_p1_percent,
    "p1_percent_base": _vg_p1_percent_base,
    "p1_true_scenario": _vg_p1_true_scenario,
    "p2_percent": _vg_p2_percent,
    "p2_true_scenario": _vg_p2_true_scenario,
    "p_binom_mean": _vg_p_binom_mean,
    "p_binom_var": _vg_p_binom_var,
    "p_hat_target": _vg_p_hat_target,
    "p_value_argument": _vg_p_value_argument,
    "p_value_gen": _vg_p_value_gen,
    "p_value_scenario": _vg_p_value_scenario,
    "p_value_scenario_arg": _vg_p_value_scenario_arg,
    "percentile_k": _vg_percentile_k,
    "points_added": _vg_points_added,
    "pop_mean_clt": _vg_pop_mean_clt,
    "pop_std_clt": _vg_pop_std_clt,
    "pop_std_dev": _vg_pop_std_dev,
    "positive_outcome_description": _vg_positive_outcome_description,
    "power_percent": _vg_power_percent,
    "prob_success": _vg_prob_success,
    "prob_success_ft": _vg_prob_success_ft,
    "product_cat": _vg_product_cat,
    "product_ci_find_mean": _vg_product_ci_find_mean,
    "product_name": _vg_product_name,
    "product_type": _vg_product_type,
    "prop_A_actual": _vg_prop_A_actual,
    "prop_A_percent": _vg_prop_A_percent,
    "prop_B_actual": _vg_prop_B_actual,
    "prop_B_percent": _vg_prop_B_percent,
    "proportion_true": _vg_proportion_true,
    "q1_val": _vg_q1_val,
    "q3_val": _vg_q3_val,
    "sample_mean": _vg_sample_mean,
    "sample_size": _vg_sample_size,
    "sample_size_base": _vg_sample_size_base,
    "sample_size_clt": _vg_sample_size_clt,
    "sample_size_items": _vg_sample_size_items,
    "sample_size_prop": _vg_sample_size_prop,
    "scenario_higher": _vg_scenario_higher,
    "scenario_type": _vg_scenario_type,
    "score1": _vg_score1,
    "score2": _vg_score2,
    "score_high": _vg_score_high,
    "score_low": _vg_score_low,
    "service_place": _vg_service_place,
    "sorted_dataset_arr_median": _vg_sorted_dataset_arr_median,
    "sorted_dataset_str_median": _vg_sorted_dataset_str_median,
    "std_dev1": _vg_std_dev1,
    "std_dev2": _vg_std_dev2,
    "std_dev_a": _vg_std_dev_a,
    "std_dev_b": _vg_std_dev_b,
    "std_dev_b_factor": _vg_std_dev_b_factor,
    "std_dev_base": _vg_std_dev_base,
    "std_dev_bp": _vg_std_dev_bp,
    "std_dev_test": _vg_std_dev_test,
    "std_dev_val": _vg_std_dev_val,
    "std_dev_x_base": _vg_std_dev_x_base,
    "std_dev_x_c": _vg_std_dev_x_c,
    "std_dev_y_base": _vg_std_dev_y_base,
    "std_dev_y_c": _vg_std_dev_y_c,
    "success_rate_percent": _vg_success_rate_percent,
    "target_mean": _vg_target_mean,
    "target_proportion_percent": _vg_target_proportion_percent,
    "time_unit_poisson": _vg_time_unit_poisson,
    "total1_pref": _vg_total1_pref,
    "total2_pref": _vg_total2_pref,
    "total_observations": _vg_total_observations,
    "upper_bound_ci_find_mean": _vg_upper_bound_ci_find_mean,
    "upper_bound_diff": _vg_upper_bound_diff,
    "upper_diff_prop": _vg_upper_diff_prop,
    "upper_height_ci": _vg_upper_height_ci,
    "var1": _vg_var1,
    "var1_name": _vg_var1_name,
    "var2": _vg_var2,
    "var2_name": _vg_var2_name,
    "var_A": _vg_var_A,
    "var_B": _vg_var_B,
    "var_x": _vg_var_x,
    "var_x_corr": _vg_var_x_corr,
    "var_x_val": _vg_var_x_val,
    "var_y": _vg_var_y,
    "var_y_corr": _vg_var_y_corr,
    "var_y_val": _vg_var_y_val,
    "variance": _vg_variance,
    "variance_base": _vg_variance_base,
    "variance_val": _vg_variance_val,
    "weight1_decimal": _vg_weight1_decimal,
    "weight1_percent": _vg_weight1_percent,
    "weight2_decimal": _vg_weight2_decimal,
    "weight2_percent": _vg_weight2_percent,
    "weight2_percent_calc": _vg_weight2_percent_calc,
    "weight_A_decimal": _vg_weight_A_decimal,
    "weight_A_percent": _vg_weight_A_percent,
    "weight_B_decimal": _vg_weight_B_decimal,
    "weight_B_percent": _vg_weight_B_percent,
    "x_bar_brew_time": _vg_x_bar_brew_time,
    "x_success_prop_ci": _vg_x_success_prop_ci,
    "x_val": _vg_x_val,
    "z_score_target": _vg_z_score_target,
    "z_score_val": _vg_z_score_val,
    "z_val_prop_ci": _vg_z_val_prop_ci,
    "z_value_prop": _vg_z_value_prop,
    "person2_name": _vg_person2_name,
    "score_type": _vg_score_type,
    "score_type_plural": _vg_score_type_plural,
    "group_type": _vg_group_type,
    "service_type": _vg_service_type,
    "test_stat_scenario": _vg_test_stat_scenario,
    "statistical_test": _vg_statistical_test,
    "outlier_description": _vg_outlier_description,
    "conf_level_text": _vg_conf_level_text,
    "item_qc_property": _vg_item_qc_property,


}



# --- Answer Logic Helper: Generate Distractors ---
def _generate_numerical_distractors(
    correct_ans: float, 
    num_distractors: int = 3, 
    typical_range_factor: float = 0.3, # Adjusted default
    min_diff: float = 0.1, 
    decimals: int = 2  # <<< ADDED THIS PARAMETER (and its default value)
) -> List[float]:
    """Generates plausible numerical distractors, rounded to specified decimals."""
    distractors = set()
    # Ensure correct_ans is float for calculations
    try:
        correct_ans_float = float(correct_ans)
    except (ValueError, TypeError):
        return [round(random.uniform(1, 100), decimals) for _ in range(num_distractors)] # Fallback non-numeric correct_ans

    if correct_ans_float == 0: 
        typical_offset = 1.0 * (10**(-decimals)) # Scale offset based on decimals
    else: 
        typical_offset = abs(correct_ans_float * typical_range_factor)
    
    # Ensure min_diff is sensible relative to typical_offset and decimals
    effective_min_diff = max(min_diff, (0.1 * (10**(-decimals))))
    if typical_offset < effective_min_diff : typical_offset = effective_min_diff 
    
    attempts = 0
    while len(distractors) < num_distractors and attempts < num_distractors * 15: # Increased attempts for better variety
        attempts += 1
        
        strategy_choice = random.random()
        distractor_val: float

        if strategy_choice < 0.4: 
            offset_factor = random.uniform(0.5, 2.0) 
            distractor_val = correct_ans_float + random.choice([-1, 1]) * offset_factor * typical_offset
        elif strategy_choice < 0.7: 
            distractor_val = correct_ans_float + random.choice([-1, 1]) * random.uniform(effective_min_diff, effective_min_diff * 5)
        else: 
            if correct_ans_float != 0:
                factor = random.choice([0.5, 0.75, 1.25, 1.5, 1.75, 0.25])
                distractor_val = correct_ans_float * factor
            else: 
                distractor_val = random.choice([-1, 1]) * random.uniform(effective_min_diff, effective_min_diff * 5)
        
        # Round the potential distractor to the specified number of decimals *before* checking uniqueness
        rounded_distractor = round(distractor_val, decimals)
        rounded_correct_ans = round(correct_ans_float, decimals)

        if abs(rounded_distractor - rounded_correct_ans) >= (effective_min_diff / 2): # Ensure it's not effectively the same as correct after rounding
            distractors.add(rounded_distractor)
            
    # Fill remaining slots if needed
    list_dist = list(distractors)
    current_distractor_idx = 1
    while len(list_dist) < num_distractors:
        fallback_offset = (abs(correct_ans_float * 0.1) + effective_min_diff) * (current_distractor_idx + random.random())
        new_d_val = correct_ans_float + (fallback_offset if current_distractor_idx % 2 == 0 else -fallback_offset)
        rounded_new_d = round(new_d_val, decimals)
        
        is_new_distractor = True
        for existing_d in list_dist: # Check against already rounded distractors
            if abs(rounded_new_d - existing_d) < (10**(-decimals-1)): # Check if effectively same
                is_new_distractor = False; break
        if abs(rounded_new_d - round(correct_ans_float, decimals)) < (10**(-decimals-1)): # Check against correct
            is_new_distractor = False

        if is_new_distractor:
            list_dist.append(rounded_new_d)
        
        current_distractor_idx += 1
        if current_distractor_idx > num_distractors * 5 : break 

    return [float(d) for d in list_dist[:num_distractors]]


def _format_options(
    correct_answer_raw_value: Any, 
    distractors: List[Any],
    is_string_based: bool = False,
    decimals: int = 2 # Default decimals if not specified otherwise
) -> Tuple[Any, List[str], int]:
    """
    Formats numerical options, combines correct answer with distractors,
    shuffles them, and returns the raw correct answer, the list of option strings, 
    and the index of the correct option string.
    """
    correct_option_str: str
    
    # 1. Format the correct answer into its string representation for options
    if is_string_based or isinstance(correct_answer_raw_value, str):
        correct_option_str = str(correct_answer_raw_value)
    elif isinstance(correct_answer_raw_value, (int, float)):
        if isinstance(correct_answer_raw_value, int) or (isinstance(correct_answer_raw_value, float) and correct_answer_raw_value == int(correct_answer_raw_value) and decimals == 0):
            correct_option_str = str(int(correct_answer_raw_value))
        else:
            correct_option_str = f"{float(correct_answer_raw_value):.{decimals}f}"
    else: # Fallback for other types
        correct_option_str = str(correct_answer_raw_value)

    # 2. Format distractors and ensure they are strings
    formatted_distractors = []
    for d_val in distractors:
        if is_string_based or isinstance(d_val, str):
            formatted_distractors.append(str(d_val))
        elif isinstance(d_val, (int, float)):
            if isinstance(d_val, int) or (isinstance(d_val, float) and d_val == int(d_val) and decimals == 0):
                formatted_distractors.append(str(int(d_val)))
            else:
                formatted_distractors.append(f"{float(d_val):.{decimals}f}")
        else:
            formatted_distractors.append(str(d_val))

    # 3. Combine and ensure uniqueness
    # Start with the correct answer, then add unique distractors
    options_display_strings = [correct_option_str]
    for d_str in formatted_distractors:
        if d_str not in options_display_strings and len(options_display_strings) < 4:
            options_display_strings.append(d_str)
            
    # 4. Pad if not enough options
    idx_pad = 1
    while len(options_display_strings) < 4:
        # Generate a fallback distractor that is unlikely to match others
        # This logic for fallback can be improved to be more context-aware
        fallback_val_num = random.uniform(100, 200) + idx_pad
        fallback_str = f"{fallback_val_num:.{decimals}f}" if not is_string_based and isinstance(correct_answer_raw_value, float) else str(int(fallback_val_num))
        if is_string_based: fallback_str = f"AltOpt_{idx_pad}"
        
        if fallback_str not in options_display_strings:
            options_display_strings.append(fallback_str)
        else: # if somehow it still clashes, just make it very unique
             options_display_strings.append(f"Fallback_Unique_{random.randint(1000,9999)}")
        idx_pad += 1
        if idx_pad > 10 : break # safety break

    final_shuffled_options = options_display_strings[:4] # Ensure exactly 4
    random.shuffle(final_shuffled_options)
    
    correct_idx_in_shuffled_list = 0 # Default
    try:
        correct_idx_in_shuffled_list = final_shuffled_options.index(correct_option_str)
    except ValueError:
        # This is a critical issue if the known correct answer string isn't in the final list.
        # It implies an issue with how options/distractors were formed or if correct_option_str was altered.
        # For robustness in testing, ensure it's added and re-shuffle or log error.
        print(f"CRITICAL WARNING in _format_options: Correct answer string '{correct_option_str}' was not found in final options: {final_shuffled_options}. This indicates a problem with distractor generation or formatting. Forcing correct answer into options.")
        if correct_option_str not in final_shuffled_options: # If truly missing
            if len(final_shuffled_options) == 4: final_shuffled_options[random.randint(0,3)] = correct_option_str # Replace one
            else: final_shuffled_options.append(correct_option_str) # Add if less than 4
            random.shuffle(final_shuffled_options) # Re-shuffle
            final_shuffled_options = final_shuffled_options[:4] # Ensure 4
            try:
                correct_idx_in_shuffled_list = final_shuffled_options.index(correct_option_str)
            except ValueError: # Should absolutely not happen now
                 correct_idx_in_shuffled_list = 0 


    return correct_answer_raw_value, final_shuffled_options, correct_idx_in_shuffled_list

# --- Answer Logic Functions ---
# Each returns: (correct_answer_value, list_of_shuffled_option_strings, index_of_correct_answer_in_list)

def _al_fixed_choice(generated_vars: Dict, details: Dict, options_template: List[str]) -> Tuple[str, List[str], int]:
    correct_idx = details["correct_option_index"]
    # Substitute placeholders in options if any.
    processed_options = [substitute_placeholders(opt, generated_vars) for opt in options_template]
    correct_answer_text = processed_options[correct_idx]
    # For fixed choice, we don't shuffle options from template; their order is fixed.
    return correct_answer_text, processed_options, correct_idx

def _al_fixed_choice_conditional(generated_vars: Dict, details: Dict, options_template: List[str]) -> Tuple[str, List[str], int]:
    condition_val_actual = generated_vars[details["condition_var"]]
    condition_val_target = details["condition_val"]
    
    if condition_val_actual == condition_val_target:
        correct_idx = details["correct_option_index_if_true"]
    else:
        correct_idx = details["correct_option_index_if_false"]
    
    processed_options = [substitute_placeholders(opt, generated_vars) for opt in options_template]
    correct_answer_text = processed_options[correct_idx]
    return correct_answer_text, processed_options, correct_idx

def _al_calculate_standard_error_mean(generated_vars: Dict, details: Dict, options_template: List[str]) -> Tuple[float, List[str], int]:
    variance = float(generated_vars["variance"])
    sample_size = int(generated_vars["sample_size"])
    if sample_size <= 0: return 0.0, ["Error: n<=0"]*4,0
    correct_ans = math.sqrt(variance / sample_size)
    distractors = _generate_numerical_distractors(correct_ans, typical_range_factor=0.5, min_diff=0.1)
    # Common error: forgetting sqrt, or using n instead of sqrt(n)
    distractors.append(variance / sample_size) 
    distractors.append(math.sqrt(variance) / sample_size)
    return _format_options(correct_ans, distractors, decimals=3)


def _al_calculate_covariance_from_corr(generated_vars: Dict, details: Dict, options_template: List[str]) -> Tuple[float, List[str], int]:
    var_x = float(generated_vars["var_x"])
    var_y = float(generated_vars["var_y"])
    corr_coeff = float(generated_vars["corr_coeff"])
    std_dev_x = math.sqrt(var_x)
    std_dev_y = math.sqrt(var_y)
    correct_ans = corr_coeff * std_dev_x * std_dev_y
    distractors = _generate_numerical_distractors(correct_ans, typical_range_factor=0.3)
    # Common error: forgetting sqrt, or using variances directly
    distractors.append(corr_coeff * var_x * var_y) 
    return _format_options(correct_ans, distractors, decimals=2)

def _al_calculate_iqr(generated_vars: Dict, details: Dict, options_template: List[str]) -> Tuple[int, List[str], int]:
    q1 = int(generated_vars["q1_val"])
    q3 = int(generated_vars["q3_val"])
    correct_ans = q3 - q1
    distractors = _generate_numerical_distractors(correct_ans, typical_range_factor=0.5, min_diff=1)
    distractors.append(q1 + q3) # Common error: sum instead of difference
    distractors.append(q1)
    distractors.append(q3)
    return _format_options(correct_ans, distractors, is_string_based=False, decimals=0)

def _al_calculate_point_estimate_proportion(generated_vars: Dict, details: Dict, options_template: List[str]) -> Tuple[float, List[str], int]:
    num_successes = int(generated_vars["num_successes"])
    sample_size = int(generated_vars["sample_size_prop"])

    if sample_size == 0:
        return 0.0, ["Error: N=0"]*4, 0
    
    correct_ans = num_successes / sample_size
    
    distractors = _generate_numerical_distractors(correct_ans, typical_range_factor=0.3, min_diff=0.01, decimals=3)
    distractors.append(num_successes / (sample_size + 1) if sample_size > 0 else 0) # n+1 error
    distractors.append((num_successes + 1) / sample_size if sample_size > 0 else 0) # x+1 error

    return _format_options(correct_ans, distractors, decimals=3)

def _al_calculate_binomial_probability(vars: Dict[str, Any], params: List[str]) -> float:
    from math import comb
    n, k, p = vars[params[0]], vars[params[1]], vars[params[2]]
    return round(comb(n, k) * (p ** k) * ((1 - p) ** (n - k)), 5)

def _al_calculate_std_dev_from_variance(vars: Dict[str, Any], params: List[str]) -> float:
    import math
    return round(math.sqrt(vars[params[0]]), 3)

def _al_interpret_ci_difference_means(generated_vars: Dict, details: Dict, options_template: List[str]) -> Tuple[str, List[str], int]:
    lower = float(generated_vars[details["params"][0]])
    upper = float(generated_vars[details["params"][1]])

    if lower > 0:
        correct_ans = "μ1 is significantly greater than μ2"
    elif upper < 0:
        correct_ans = "μ2 is significantly greater than μ1"
    elif lower <= 0 <= upper:
        correct_ans = "There is no significant difference between μ1 and μ2"
    else:
        correct_ans = "The sample sizes were too small"  # Should never hit unless values are invalid

    # Filter distractors from template
    distractors = [opt for opt in options_template if opt != correct_ans]

    return _format_options(correct_ans, distractors, is_string_based=True)


def _al_calculate_ci_mean_known_sigma(vars: Dict[str, Any], details: Dict, options_template: List[str]) -> Tuple[str, List[str], int]:
    import math
    sample_mean = float(vars["sample_mean"])
    pop_std_dev = float(vars["pop_std_dev"])
    sample_size = int(vars["sample_size"])
    z_value = float(details.get("z_value_fixed", 1.96))

    se = pop_std_dev / math.sqrt(sample_size)
    margin = z_value * se
    lower = round(sample_mean - margin, 2)
    upper = round(sample_mean + margin, 2)
    correct_ans = f"({lower}, {upper})"

    # Create distractors using nearby values
    distractors = _generate_numerical_distractors(lower + upper, num_distractors=3, decimals=2)
    distractors_strs = [f"({round(d - margin, 2)}, {round(d + margin, 2)})" for d in distractors]

    return _format_options(correct_ans, distractors_strs, is_string_based=True)


def _al_p_value_decision(generated_vars: Dict, details: Dict, options_template: List[str]) -> Tuple[str, List[str], int]:
    # Get the generated p-value and alpha level
    p_val = float(generated_vars.get("p_value_gen", 1.0))
    alpha = float(generated_vars.get("alpha_level_gen", 0.05))

    # The options_template from JSON is ["Reject...", "Fail to reject...", "Accept...", "Inconclusive"]
    # Determine the correct answer based on the rule: p <= alpha -> Reject
    if p_val <= alpha:
        correct_answer_text = options_template[0]  # "Reject the null hypothesis (H₀)"
    else:
        correct_answer_text = options_template[1]  # "Fail to reject the null hypothesis (H₀)"

    # The options are fixed strings, so we don't need to generate distractors.
    # We just need to shuffle them.
    final_shuffled_options = list(options_template)
    random.shuffle(final_shuffled_options)
    
    # Find the new index of our correct answer after the shuffle
    try:
        final_correct_index = final_shuffled_options.index(correct_answer_text)
    except ValueError:
        # This is a safety fallback, should not happen.
        final_correct_index = 0

    # Return the three items the engine expects: (value, [options], index)
    return (correct_answer_text, final_shuffled_options, final_correct_index)

def _al_calculate_z_score(generated_vars: Dict, details: Dict, options_template: List[str]) -> Tuple[float, List[str], int]:
    x_val = float(generated_vars["x_val"])
    mean_val = float(generated_vars["mean_val"])
    std_dev_val = float(generated_vars["std_dev_val"])

    if std_dev_val == 0:
        return 0.0, ["Error: SD=0"]*4, 0
        
    correct_ans = (x_val - mean_val) / std_dev_val
    
    distractors = _generate_numerical_distractors(correct_ans, typical_range_factor=0.5, min_diff=0.1, decimals=2)
    distractors.append((mean_val - x_val) / std_dev_val) # Numerator flipped
    distractors.append((x_val - mean_val) * std_dev_val) # Multiplied instead of divided

    return _format_options(correct_ans, distractors, decimals=2)

def _al_calculate_range(generated_vars: Dict, details: Dict, options_template: List[str]) -> Tuple[Union[int, float], List[str], int]:
    dataset = generated_vars.get("dataset_arr_range", generated_vars.get("dataset_arr"))
    if not dataset:
        return 0, ["Error: No data"] * 4, 0
    
    min_val = min(dataset)
    max_val = max(dataset)
    correct_ans = max_val - min_val

    # For explanation template
    generated_vars["min_val_range"] = min_val
    generated_vars["max_val_range"] = max_val

    distractors = _generate_numerical_distractors(float(correct_ans), decimals=0 if isinstance(correct_ans, int) else 2)
    distractors.append(max_val) # Common error: just max
    distractors.append(min_val) # Common error: just min
    
    return _format_options(correct_ans, distractors, decimals=0 if isinstance(correct_ans, int) else 2)

def _al_calculate_relative_frequency(generated_vars: Dict, details: Dict, options_template: List[str]) -> Tuple[float, List[str], int]:
    category_frequency = float(generated_vars["category_frequency"])
    total_observations = float(generated_vars["total_observations"])

    if total_observations == 0:
        return 0.0, ["Error: Total is 0"] * 4, 0
    
    correct_ans = category_frequency / total_observations
    
    distractors = _generate_numerical_distractors(correct_ans, typical_range_factor=0.5, min_diff=0.01, decimals=3)
    distractors.append(total_observations / category_frequency if category_frequency != 0 else 0.0) # Inverted
    distractors.append(category_frequency) # Just frequency
    
    return _format_options(correct_ans, distractors, decimals=3)

def _al_find_median_sorted_odd(generated_vars: Dict, details: Dict, options_template: List[str]) -> Tuple[Union[int, float], List[str], int]:
    # Assumes 'sorted_dataset_arr_median' is already sorted and has odd length from _vg_generate_sorted_int_array
    dataset = generated_vars["sorted_dataset_arr_median"]
    if not dataset:
        return 0, ["Error: No data"] * 4, 0
    
    n = len(dataset)
    correct_ans = dataset[n // 2] # Works for odd n because index is (n-1)/2

    distractors = _generate_numerical_distractors(float(correct_ans), decimals=0 if isinstance(correct_ans, int) else 1)
    if n > 1 : distractors.append(dataset[n//2 -1]) # Value before
    if n > 2 : distractors.append(dataset[n//2 +1]) # Value after

    return _format_options(correct_ans, distractors, is_string_based=False, decimals=0 if isinstance(correct_ans, int) else 1)

def _al_find_mode_simple(generated_vars: Dict, details: Dict, options_template: List[str]) -> Tuple[Union[str, int, float], List[str], int]:
    # Try to get the dataset using common keys, or a key specified in answer_logic params
    dataset_key = details.get("dataset_variable_name", "dataset_arr_mode") # Allow override from template
    dataset = generated_vars.get(dataset_key)
    
    if dataset is None: # If primary key not found, try a common fallback
        dataset = generated_vars.get("dataset_arr") 

    if not dataset or not isinstance(dataset, list):
        print(f"Warning: Dataset for mode calculation is missing or not a list. Key tried: '{dataset_key}', Fallback tried: 'dataset_arr'. Vars: {list(generated_vars.keys())}")
        return "N/A", ["Error: No data"] * 4, 0

    counts = Counter(dataset)
    max_freq = 0
    modes = []
    
    # Check if all elements are unique (no mode if max_freq is 1 and all are unique)
    all_unique_and_freq_one = True
    for value, freq in counts.items():
        if freq > 1:
            all_unique_and_freq_one = False
        if freq > max_freq:
            max_freq = freq
            modes = [value]
        elif freq == max_freq:
            modes.append(value)
    
    if not modes or (max_freq == 1 and all_unique_and_freq_one):
        correct_ans_display = "No mode"
        correct_ans_val = "No mode" 
        
        distractors = []
        if dataset: distractors.append(str(random.choice(dataset)))
        else: distractors.append("5") # Fallback if dataset was truly empty
        if dataset: distractors.append(str(round(sum(dataset)/len(dataset),1) if len(dataset)>0 else "10"))
        else: distractors.append("10")
        distractors.append("Multiple modes")
        
        options, correct_idx = _format_options(correct_ans_display, distractors, is_string_based=True)
        return correct_ans_val, options, correct_idx # correct_idx might be different after shuffle

    # If there's a mode
    correct_ans = modes[0] # Take the first mode if multiple
    correct_ans_display = str(correct_ans)
    
    if len(modes) > 1:
        generated_vars["is_multimodal"] = True 
        correct_ans_display = f"{correct_ans} (one of multiple modes)" # Clarify if multimodal
    else:
        generated_vars["is_multimodal"] = False

    # For explanation template 
    generated_vars["correct_ans_val"] = correct_ans # The actual mode value
    generated_vars["mode_frequency_val"] = max_freq

    distractors_vals = []
    # Add a non-mode value from the dataset if possible
    non_modes = [val for val in dataset if val not in modes]
    if non_modes:
        distractors_vals.append(random.choice(non_modes))
    
    # Generate some numerical distractors if the mode is numerical
    if isinstance(correct_ans, (int, float)):
        distractors_vals.extend(
    _generate_numerical_distractors(
        float(correct_ans) if isinstance(correct_ans, (int,float)) else 10.0, 
        num_distractors=max(0, 3-len(distractors_vals)), # Use num_distractors, ensure non-negative
        decimals=0 if isinstance(correct_ans,int) else 2
    )
)
    else: # If mode is string, add some other distinct values from dataset or generic strings
        for val in dataset:
            if len(distractors_vals) < 3 and str(val) != correct_ans_display and str(val) not in distractors_vals:
                distractors_vals.append(str(val))
        while len(distractors_vals) < 3:
            distractors_vals.append(f"Option {random.randint(100,200)}") # Generic string distractors

    return _format_options(correct_ans_display, distractors_vals, is_string_based=True)

def _al_calculate_std_dev_from_variance(generated_vars: Dict, details: Dict, options_template: List[str]) -> Tuple[float, List[str], int]:
    variance = float(generated_vars["variance_val"])
    if variance < 0: return 0.0, ["Invalid Variance"]*4, 0
    correct_ans = math.sqrt(variance)
    
    distractors = _generate_numerical_distractors(correct_ans, typical_range_factor=0.5, min_diff=0.1)
    distractors.append(variance) # Common error: forgetting sqrt
    distractors.append(correct_ans**2 / 2) # Another plausible error
    
    return _format_options(correct_ans, distractors, decimals=2)

def _al_mean_multiplication_effect(generated_vars: Dict, details: Dict, options_template: List[str]) -> Tuple[Union[int, float], List[str], int]:
    original_mean = generated_vars["original_mean"]
    multiplier = generated_vars["multiplier"]
    correct_ans = original_mean * multiplier

    distractors = _generate_numerical_distractors(float(correct_ans), decimals=1)
    distractors.append(original_mean + multiplier) # Add instead of multiply
    distractors.append(original_mean / multiplier if multiplier != 0 else original_mean) # Divide

    return _format_options(correct_ans, distractors, decimals=1 if isinstance(correct_ans, float) else 0)

def _al_calculate_binomial_probability(generated_vars: Dict, details: Dict, options_template: List[str]) -> Tuple[float, List[str], int]:
    n = int(generated_vars["num_trials"])
    k = int(generated_vars["num_successes"])
    p = float(generated_vars["prob_success"])

    if not (0 <= k <= n and 0 <= p <= 1):
        return 0.0, ["Invalid params"]*4, 0
        
    correct_ans = binom.pmf(k, n, p)
    
    distractors = _generate_numerical_distractors(correct_ans, typical_range_factor=0.8, min_diff=0.001, decimals=4)
    # Common error: P(X<k) or P(X>k) or using k/n
    if k > 0: distractors.append(binom.pmf(k-1, n, p))
    distractors.append(k/n if n > 0 else 0.0)
        
    return _format_options(correct_ans, distractors, decimals=4)

def _al_calculate_binomial_cumulative_probability_le(generated_vars: Dict, details: Dict, options_template: List[str]) -> Tuple[float, List[str], int]:
    # P(X <= k)
    n = int(generated_vars["sample_size_items"])
    k_le = int(generated_vars["max_defects"])
    p = float(generated_vars["defect_rate_decimal"])

    if not (0 <= k_le <= n and 0 <= p <= 1):
        return 0.0, ["Invalid params"]*4, 0

    correct_ans = binom.cdf(k_le, n, p)
    
    distractors = _generate_numerical_distractors(correct_ans, typical_range_factor=0.5, min_diff=0.01, decimals=4)
    distractors.append(binom.pmf(k_le, n, p)) # P(X=k) instead of P(X<=k)
    if k_le < n : distractors.append(1 - binom.cdf(k_le, n, p)) # P(X > k)

    return _format_options(correct_ans, distractors, decimals=4)


def _al_calculate_poisson_probability(generated_vars: Dict, details: Dict, options_template: List[str]) -> Tuple[float, List[str], int]:
    lambda_val = float(generated_vars.get("lambda_calculated", 0)) # Ensure lambda_calculated is generated
    k_target = int(generated_vars.get("exact_calls_target", 0))

    if lambda_val <= 0 : # Lambda must be positive
        print(f"Warning: Invalid lambda ({lambda_val}) for Poisson probability. Template: {details.get('id')}")
        return 0.0, ["Invalid Params"]*4, 0
    
    correct_ans = poisson.pmf(k_target, lambda_val)
    
    distractors = _generate_numerical_distractors(correct_ans, typical_range_factor=0.8, min_diff=0.0001, decimals=4)
    if k_target > 0 : distractors.append(poisson.pmf(k_target -1, lambda_val))
    distractors.append(poisson.cdf(k_target, lambda_val))

    return _format_options(correct_ans, distractors, decimals=4)

def _al_calculate_binomial_at_least_one(generated_vars: Dict, details: Dict, options_template: List[str]) -> Tuple[float, List[str], int]:
    n = int(generated_vars["num_attempts_ft"])
    p = float(generated_vars["prob_success_ft"])

    if not (n > 0 and 0 <= p <= 1):
         return 0.0, ["Invalid params"]*4, 0

    prob_zero_successes = binom.pmf(0, n, p)
    correct_ans = 1.0 - prob_zero_successes
    generated_vars["prob_zero_successes"] = round(prob_zero_successes, 4) # For explanation

    distractors = _generate_numerical_distractors(correct_ans, typical_range_factor=0.4, min_diff=0.01, decimals=4)
    distractors.append(prob_zero_successes) # P(X=0)
    distractors.append(binom.pmf(1,n,p)) # P(X=1)

    return _format_options(correct_ans, distractors, decimals=4)

def _al_normal_approx_poisson_gt(generated_vars: Dict, details: Dict, options_template: List[str]) -> Tuple[float, List[str], int]:
    # P(X > k) = 1 - P(X <= k). Using continuity correction, P(X <= k) approx by P(Normal <= k+0.5)
    lambda_val = float(generated_vars["lambda_val_poisson"])
    k_val = int(generated_vars["k_val_poisson"])

    if lambda_val <= 0: return 0.0, ["Invalid lambda"]*4, 0
    
    mu = lambda_val
    sigma = math.sqrt(lambda_val)
    z_score = (k_val + 0.5 - mu) / sigma
    correct_ans = 1 - norm.cdf(z_score) # This is P(Z > z_score)

    generated_vars["z_score_calc"] = round(z_score, 3) # For explanation

    distractors = _generate_numerical_distractors(correct_ans, typical_range_factor=0.6, min_diff=0.001, decimals=4)
    distractors.append(norm.cdf(z_score)) # P(Z <= z_score) common error
    # Without continuity correction
    z_no_cc = (k_val - mu) / sigma
    distractors.append(1 - norm.cdf(z_no_cc))

    return _format_options(correct_ans, distractors, decimals=4)

def _al_calculate_sample_variance(generated_vars: Dict, details: Dict, options_template: List[str]) -> Tuple[float, List[str], int]:
    # This was provided in the previous response, ensure it's correctly implemented.
    # If it was 'pass' before, replace it with the full implementation.
    dataset = generated_vars.get("dataset_arr", generated_vars.get("dataset_arr_variance")) # Allow flexible key
    if not dataset or len(dataset) < 2:
        return 0.0, ["Invalid Data"] * 4, 0
    
    n = len(dataset)
    mean = sum(dataset) / n
    generated_vars["sample_mean_calc"] = round(mean, 3) # For explanation
    
    squared_deviations = sum([(x - mean)**2 for x in dataset])
    generated_vars["sum_sq_dev_calc"] = round(squared_deviations, 3) # For explanation
    generated_vars["n_minus_1"] = n - 1 # For explanation

    correct_ans = squared_deviations / (n - 1)
    
    distractors = _generate_numerical_distractors(correct_ans, decimals=3)
    if n > 0: distractors.append(squared_deviations / n) # Div by n error
    if n > 1: distractors.append(math.sqrt(correct_ans)) # Std dev instead of variance

    return _format_options(correct_ans, distractors, decimals=3)

def _al_find_missing_value_for_mean(generated_vars: Dict, details: Dict, options_template: List[str]) -> Tuple[Union[int, float], List[str], int]:
    known_values = generated_vars["dataset_known_values_arr"]
    target_mean = float(generated_vars["target_mean"])
    num_total_values = len(known_values) + 1
    
    sum_known = sum(known_values)
    generated_vars["sum_known_values"] = sum_known # For explanation
    # target_mean = (sum_known + x) / num_total_values
    # x = (target_mean * num_total_values) - sum_known
    correct_ans = (target_mean * num_total_values) - sum_known
    
    # Determine if result should be int or float based on target_mean or known_values
    is_int_result = all(isinstance(v, int) for v in known_values) and (target_mean == int(target_mean))
    if is_int_result:
        correct_ans = int(round(correct_ans))
        decimals = 0
    else:
        correct_ans = round(correct_ans, 2)
        decimals = 2

    distractors = _generate_numerical_distractors(float(correct_ans), decimals=decimals)
    # Common error: (target_mean * len(known_values)) - sum_known
    distractors.append((target_mean * len(known_values)) - sum_known)
    distractors.append(target_mean - (sum_known / len(known_values)) if known_values else target_mean)

    return _format_options(correct_ans, distractors, decimals=decimals)

def _al_calculate_correlation_coefficient(generated_vars: Dict, details: Dict, options_template: List[str]) -> Tuple[float, List[str], int]:
    cov_xy = float(generated_vars["cov_xy"])
    var_x = float(generated_vars["var_x_corr"])
    var_y = float(generated_vars["var_y_corr"])

    if var_x <= 0 or var_y <= 0: # Variances must be positive
        return 0.0, ["Error: Var<=0"]*4, 0
        
    std_dev_x = math.sqrt(var_x)
    std_dev_y = math.sqrt(var_y)

    if std_dev_x * std_dev_y == 0:
         return 0.0, ["Error: SD_prod=0"]*4, 0

    correct_ans = cov_xy / (std_dev_x * std_dev_y)
    # Clamp result between -1 and 1 due to potential float inaccuracies
    correct_ans = max(-1.0, min(1.0, correct_ans))

    distractors = _generate_numerical_distractors(correct_ans, typical_range_factor=0.4, min_diff=0.05, decimals=2)
    distractors.append(cov_xy / (var_x * var_y) if (var_x * var_y !=0) else 0) # Used variances directly
    distractors.append(cov_xy * std_dev_x * std_dev_y) # Multiplied instead

    return _format_options(correct_ans, distractors, decimals=2)

def _al_expected_value_product_independent(generated_vars: Dict, details: Dict, options_template: List[str]) -> Tuple[Union[int, float], List[str], int]:
    ex = generated_vars["ex_val"]
    ey = generated_vars["ey_val"]
    correct_ans = ex * ey

    distractors = _generate_numerical_distractors(float(correct_ans), decimals=0 if isinstance(correct_ans, int) else 1)
    distractors.append(ex + ey) # Sum instead of product
    distractors.append(ex - ey)

    return _format_options(correct_ans, distractors, decimals=0 if isinstance(correct_ans, int) else 1)

def _al_calculate_kth_percentile(generated_vars: Dict, details: Dict, options_template: List[str]) -> Tuple[Union[int,float], List[str], int]:
    dataset = generated_vars["dataset_arr_percentile"]
    k = int(generated_vars["percentile_k"])

    if not dataset:
        return 0, ["Error: No data"] * 4, 0
    if not (0 < k < 100):
        return 0, ["Error: Invalid k"] * 4, 0

    n = len(dataset)

    rank = (k / 100) * (n - 1)

    if rank.is_integer():
        idx1 = int(rank) - 1 
        idx2 = int(rank) # This is rank, so index is rank
        if idx1 >= 0 and idx2 < n : # Check bounds after 0-indexing
            correct_ans = (dataset[idx1] + dataset[idx2]) / 2.0
        elif idx1 >=0 and idx1 < n: # Only first index is valid (e.g. P100 on small set)
            correct_ans = dataset[idx1]
        else: # Should not happen with k < 100
            correct_ans = dataset[n-1]
    else:
        idx = int(math.ceil(rank)) - 1
        idx = max(0, min(idx, n - 1)) # Clamp index to valid range
        correct_ans = dataset[idx]

    # If the dataset elements are integers, and the result is .0, convert to int
    if all(isinstance(x, int) for x in dataset) and correct_ans == int(correct_ans):
        correct_ans = int(correct_ans)
        decimals = 0
    else:
        correct_ans = round(correct_ans, 1) # Percentiles often shown with 1 decimal
        decimals = 1

    distractors = _generate_numerical_distractors(float(correct_ans), decimals=decimals)
    # Distractor using (k/100)*N index without proper handling
    wrong_idx_rank = (k/100)*n
    wrong_idx = int(round(wrong_idx_rank))-1
    wrong_idx = max(0, min(wrong_idx, n - 1))
    if dataset[wrong_idx] != correct_ans : distractors.append(dataset[wrong_idx])
    if k == 50 and n > 0: distractors.append(sum(dataset)/len(dataset)) # Mean as distractor for median

    return _format_options(correct_ans, distractors, decimals=decimals)

def _al_calculate_mode(generated_vars: Dict, details: Dict, options_template: List[str]) -> Tuple[Union[str, int, float], List[str], int]:
    # This is an alias for _al_find_mode_simple if the logic is identical
    # Or it can have a slightly different implementation if "calculate_mode" is for more complex cases
    return _al_find_mode_simple(generated_vars, details, options_template)

def _al_calculate_mean(generated_vars: Dict, details: Dict, options_template: List[str]) -> Tuple[Union[float, int], List[str], int]:
    dataset_key = "dataset_arr_mean" # Default key from your STAT_U1_T3_S1_E_D_002 template
    if dataset_key not in generated_vars: # Fallback if another key was used for the dataset
        dataset_key = generated_vars.get("dataset_source_var", "dataset_arr") # Or a generic one
    
    dataset = generated_vars.get(dataset_key)

    if not dataset or not isinstance(dataset, list) or len(dataset) == 0:
        print(f"Warning: Dataset for mean calculation is missing or empty for template. Vars: {generated_vars.keys()}")
        return 0.0, ["Error: No data"] * 4, 0
    
    correct_ans_float = sum(dataset) / len(dataset)
    
    # Determine if the answer should be displayed as an integer or float
    # If all dataset items are integers and the mean is a whole number, display as int.
    all_integers_in_data = all(isinstance(x, int) for x in dataset)
    if all_integers_in_data and correct_ans_float == int(correct_ans_float):
        correct_ans_display_val = int(correct_ans_float)
        option_decimals = 0
    else:
        correct_ans_display_val = round(correct_ans_float, 2) # Default to 2 decimals for float means
        option_decimals = 2

    # For explanation template placeholders
    generated_vars["sum_of_values"] = sum(dataset)
    generated_vars["count_of_values"] = len(dataset) # Use 'count_of_values' to avoid conflict if 'n' is used elsewhere

    # Generate distractors
    distractors = _generate_numerical_distractors(
        correct_ans_float, # Use the float value for generating numerical distractors
        num_distractors=3, # We need 3
        decimals=option_decimals
    )
    
    # Add a common error: dividing by (n-1) if dataset is large enough for it to be distinct
    if len(dataset) > 1 and (sum(dataset) / (len(dataset) - 1)) != correct_ans_float:
        common_error_distractor = sum(dataset) / (len(dataset) - 1)
        # Ensure it's added if space, or replaces one
        if len(distractors) < 3:
            distractors.append(common_error_distractor)
        else:
            distractors[random.randint(0,2)] = common_error_distractor 
            # Be careful this doesn't make it same as correct_ans if correct_ans was also an error

    # Ensure distractors are unique and different from correct_ans after formatting
    temp_formatted_distractors = []
    correct_ans_str_formatted = f"{correct_ans_display_val:.{option_decimals}f}" if option_decimals > 0 else str(correct_ans_display_val)

    for d_val in distractors:
        if isinstance(d_val, (int, float)):
            formatted_d = f"{d_val:.{option_decimals}f}" if option_decimals > 0 else str(int(round(d_val)))
            if formatted_d != correct_ans_str_formatted and formatted_d not in temp_formatted_distractors:
                temp_formatted_distractors.append(formatted_d)
        elif str(d_val) != correct_ans_str_formatted and str(d_val) not in temp_formatted_distractors: # If a distractor was already a string
            temp_formatted_distractors.append(str(d_val))
    
    distractors = temp_formatted_distractors[:3] # Take up to 3 unique formatted distractors

    return _format_options(correct_ans_display_val, distractors, decimals=option_decimals)

def _al_variance_sum_independent_vars(generated_vars: Dict, details: Dict, options_template: List[str]) -> Tuple:
    var_x = generated_vars["var_x_val"]
    var_y = generated_vars["var_y_val"]
    correct_ans = var_x + var_y
    distractors = _generate_numerical_distractors(correct_ans, decimals=0)
    return _format_options(correct_ans, distractors, decimals=0)

def _al_sample_size_proportion_no_prior(generated_vars: Dict, details: Dict, options_template: List[str]) -> Tuple:
    margin_error = generated_vars["margin_error"]
    z = generated_vars["z_value_prop"]
    p = 0.5  # max variance assumption
    n = (z ** 2 * p * (1 - p)) / (margin_error ** 2)
    correct_ans = int(math.ceil(n))
    distractors = _generate_numerical_distractors(correct_ans)
    return _format_options(correct_ans, distractors, decimals=0)

def _al_mean_addition_effect(generated_vars: Dict, details: Dict, options_template: List[str]) -> Tuple:
    original_mean = generated_vars["original_mean"]
    addend = generated_vars["addend"]
    correct_ans = original_mean + addend
    distractors = _generate_numerical_distractors(correct_ans, decimals=0)
    return _format_options(correct_ans, distractors, decimals=0)

def _al_find_median_sorted_even(generated_vars: Dict, details: Dict, options_template: List[str]) -> Tuple:
    arr = sorted(generated_vars["dataset_arr"])
    n = len(arr)
    if n % 2 != 0 or n < 2:
        return 0, ["Invalid input"] * 4, 0
    mid = n // 2
    correct_ans = (arr[mid - 1] + arr[mid]) / 2
    decimals = 1 if isinstance(correct_ans, float) else 0
    distractors = _generate_numerical_distractors(correct_ans, decimals=decimals)
    return _format_options(correct_ans, distractors, decimals=decimals)

def _al_calculate_z_score_population_mean_diff(generated_vars: Dict, details: Dict, options_template: List[str]) -> Tuple:
    sample_mean = generated_vars["sample_mean"]
    pop_mean = generated_vars["population_mean"]
    pop_std_dev = generated_vars["population_std_dev"]
    sample_size = generated_vars["sample_size"]
    se = pop_std_dev / math.sqrt(sample_size)
    correct_ans = round((sample_mean - pop_mean) / se, 2)
    distractors = _generate_numerical_distractors(correct_ans, decimals=2)
    return _format_options(correct_ans, distractors, decimals=2)

def _al_calculate_margin_of_error(generated_vars: Dict, details: Dict, options_template: List[str]) -> Tuple:
    z = generated_vars["z_value"]
    std_dev = generated_vars["std_dev"]
    n = generated_vars["sample_size"]
    margin_error = z * (std_dev / math.sqrt(n))
    correct_ans = round(margin_error, 2)
    distractors = _generate_numerical_distractors(correct_ans, decimals=2)
    return _format_options(correct_ans, distractors, decimals=2)

def _al_calculate_p_value_z_test(generated_vars: Dict, details: Dict, options_template: List[str]) -> Tuple:
    from scipy.stats import norm
    z = generated_vars["z_stat"]
    p_value = 2 * (1 - norm.cdf(abs(z)))  # two-tailed
    correct_ans = round(p_value, 3)
    distractors = _generate_numerical_distractors(correct_ans, decimals=3)
    return _format_options(correct_ans, distractors, decimals=3)

def _al_calculate_effect_size(generated_vars: Dict, details: Dict, options_template: List[str]) -> Tuple:
    mean_diff = generated_vars["mean_diff"]
    pooled_std_dev = generated_vars["pooled_std_dev"]
    effect_size = mean_diff / pooled_std_dev
    correct_ans = round(effect_size, 2)
    distractors = _generate_numerical_distractors(correct_ans, decimals=2)
    return _format_options(correct_ans, distractors, decimals=2)

def _al_calculate_mean_squared_error(generated_vars: Dict, details: Dict, options_template: List[str]) -> Tuple:
    errors = generated_vars["errors_arr"]
    squared_errors = [(e ** 2) for e in errors]
    mse = sum(squared_errors) / len(squared_errors)
    correct_ans = round(mse, 2)
    distractors = _generate_numerical_distractors(correct_ans, decimals=2)
    return _format_options(correct_ans, distractors, decimals=2)

def _al_calculate_binomial_mean(generated_vars: Dict, details: Dict, options_template: List[str]) -> Tuple[float, List[str], int]:
    n = float(generated_vars["n_trials_binom_mean"])
    p = float(generated_vars["p_binom_mean"])
    correct_ans = n * p
    
    distractors = _generate_numerical_distractors(correct_ans, decimals=2)
    distractors.append(n * p * (1-p)) # Variance
    distractors.append(n * (1-p))     # Expected failures
    
    return _format_options(correct_ans, distractors, decimals=2)

def _al_fixed_choice_dynamic_option(generated_vars: Dict, details: Dict, options_template: List[str]) -> Tuple[str, List[str], int]:
    correct_idx = details["correct_option_template_index"] # The index of the option that contains the correct answer variable
    
    # Options are already processed by substitute_placeholders if they contain {vars}
    # The options_template here would be the raw list of strings from the JSON.
    processed_options = [substitute_placeholders(opt, generated_vars) for opt in options_template]
    
    correct_answer_text = processed_options[correct_idx]
    # The actual value of the correct answer might be one of the generated_vars
    # For simplicity, we treat the formatted string as the 'value' here for fixed_choice.
    correct_answer_raw_value = correct_answer_text 

    return correct_answer_raw_value, processed_options, correct_idx


def _al_calculate_x_from_z_word_problem(generated_vars: Dict, details: Dict, options_template: List[str]) -> Tuple[Union[float, int], List[str], int]:
    mean_val = float(generated_vars["mean_score_test"])
    std_dev_val = float(generated_vars["std_dev_test"])
    z_score_val = float(generated_vars["z_score_val"])
    
    correct_ans = mean_val + (z_score_val * std_dev_val)
    
    # Determine if output should be int or float
    is_int_result = isinstance(mean_val, int) and isinstance(std_dev_val, int) and (z_score_val * std_dev_val == int(z_score_val * std_dev_val))
    decimals = 0 if is_int_result else 2
    if is_int_result:
        correct_ans = int(round(correct_ans))

    distractors = _generate_numerical_distractors(correct_ans, decimals=decimals)
    distractors.append(mean_val - (z_score_val * std_dev_val)) # Wrong sign for z-score effect
    distractors.append((correct_ans - mean_val) / std_dev_val if std_dev_val != 0 else 0) # This would be the z-score

    return _format_options(correct_ans, distractors, decimals=decimals)


def _al_mean_sum_vars(generated_vars: Dict, details: Dict, options_template: List[str]) -> Tuple[Union[int, float], List[str], int]:
    mean_x = generated_vars["mean_x_sum"]
    mean_y = generated_vars["mean_y_sum"]
    correct_ans = mean_x + mean_y

    is_int_result = isinstance(mean_x, int) and isinstance(mean_y, int)
    decimals = 0 if is_int_result else 1

    distractors = _generate_numerical_distractors(float(correct_ans), decimals=decimals)
    distractors.append(mean_x * mean_y) # Product
    distractors.append(abs(mean_x - mean_y)) # Difference

    return _format_options(correct_ans, distractors, decimals=decimals)

def _al_calculate_weighted_mean_two_values(generated_vars: Dict, details: Dict, options_template: List[str]) -> Tuple[float, List[str], int]:
    score1 = float(generated_vars["score1"])
    weight1 = float(generated_vars["weight1_decimal"]) # Assuming this is 0.xx form
    score2 = float(generated_vars["score2"])
    weight2 = float(generated_vars["weight2_decimal"]) # Assuming this is 0.xx form

    if (weight1 + weight2) == 0: # Avoid division by zero
        correct_ans = 0.0
    else:
        correct_ans = (score1 * weight1) + (score2 * weight2) # if weights sum to 1
        # If weights don't sum to 1, but are relative weights:
        # correct_ans = (score1 * weight1 + score2 * weight2) / (weight1 + weight2)


    # Determine decimals based on input scores
    decimals = 1 if isinstance(score1, float) or isinstance(score2, float) else 0
    correct_ans_val = round(correct_ans, decimals if decimals > 0 else 2) # ensure some rounding for floats

    distractors = _generate_numerical_distractors(correct_ans_val, decimals=decimals)
    # Simple average
    distractors.append((score1 + score2) / 2)
    
    return _format_options(correct_ans_val, distractors, decimals=decimals)


def _al_calculate_binomial_variance(generated_vars: Dict, details: Dict, options_template: List[str]) -> Tuple[float, List[str], int]:
    n = float(generated_vars["n_trials_binom_var"])
    p = float(generated_vars["p_binom_var"])
    
    if not (n > 0 and 0 <= p <= 1):
         return 0.0, ["Invalid params"]*4, 0

    correct_ans = n * p * (1 - p)
    
    distractors = _generate_numerical_distractors(correct_ans, decimals=3)
    distractors.append(n * p) # Mean
    distractors.append(math.sqrt(n * p * (1-p)) if n * p * (1-p) >=0 else 0) # Standard deviation

    return _format_options(correct_ans, distractors, decimals=3)

def _al_variance_linear_combination_two_vars(generated_vars: Dict, details: Dict, options_template: List[str]) -> Tuple[float, List[str], int]:
    w1 = float(generated_vars["weight_A_decimal"])
    w2 = float(generated_vars["weight_B_decimal"])
    var_A = float(generated_vars["var_A"])
    var_B = float(generated_vars["var_B"])
    cov_AB = float(generated_vars["cov_AB"])

    correct_ans = (w1**2 * var_A) + (w2**2 * var_B) + (2 * w1 * w2 * cov_AB)
    
    distractors = _generate_numerical_distractors(correct_ans, decimals=4)
    # Common error: forgetting the 2 in 2w1w2Cov(A,B)
    distractors.append((w1**2 * var_A) + (w2**2 * var_B) + (w1 * w2 * cov_AB))
    # Common error: Var(w1A + w2B) = w1*Var(A) + w2*Var(B)
    distractors.append((w1 * var_A) + (w2 * var_B))

    return _format_options(correct_ans, distractors, decimals=4)

def _al_sample_size_two_means(generated_vars: Dict, details: Dict, options_template: List[str]) -> Tuple[int, List[str], int]:
    effect_size = float(generated_vars["effect_size_bp"])
    std_dev = float(generated_vars["std_dev_bp"])
    alpha = float(generated_vars["alpha_bp_test"]) # e.g., 0.05
    power = float(generated_vars["power_decimal"]) # e.g., 0.80 for 80%
    
    beta = 1 - power

    # Z-values (two-tailed for alpha, one-tailed for beta)
    z_alpha_div_2 = norm.ppf(1 - (alpha / 2))
    z_beta = norm.ppf(1 - beta) # or norm.ppf(power)

    if effect_size == 0: return 9999, ["Error: Effect=0"]*4,0 # Avoid division by zero
    
    # Formula: n = 2 * ( (Z_alpha/2 + Z_beta) * sigma / Delta )^2
    n_float = 2 * (((z_alpha_div_2 + z_beta) * std_dev) / effect_size)**2
    correct_ans = math.ceil(n_float) # Sample size must be integer, rounded up

    generated_vars["z_alpha_div_2_val"] = round(z_alpha_div_2,3) # For explanation
    generated_vars["z_beta_val"] = round(z_beta,3) # For explanation

    distractors = _generate_numerical_distractors(float(correct_ans), num_distractors=3, decimals=0)
    # Error: using Z_alpha instead of Z_alpha/2
    z_alpha_one_sided = norm.ppf(1 - alpha)
    distractors.append(math.ceil(2 * (((z_alpha_one_sided + z_beta) * std_dev) / effect_size)**2))
    # Error: Forgetting the '2 *' at the beginning
    distractors.append(math.ceil((((z_alpha_div_2 + z_beta) * std_dev) / effect_size)**2))
    
    return _format_options(correct_ans, distractors, is_string_based=False, decimals=0)

def _al_calculate_ci_proportion(generated_vars: Dict, details: Dict, options_template: List[str]) -> Tuple[str, List[str], int]:
    x_successes = int(generated_vars["x_success_prop_ci"])
    n_sample = int(generated_vars["n_prop_ci"])
    z_value = float(generated_vars["z_val_prop_ci"])

    if n_sample == 0:
        return "(Error, N=0)", ["Error"]*4, 0
    
    p_hat = x_successes / n_sample
    generated_vars["p_hat_calc"] = round(p_hat, 4) # For explanation

    # Check conditions for normal approximation (though large N usually assumed for this type)
    if n_sample * p_hat < 5 or n_sample * (1 - p_hat) < 5:
        print(f"Warning: Sample size too small for normal approx in CI proportion. Template: {details.get('id')}")
        # Could return an error or proceed with caution

    standard_error = math.sqrt((p_hat * (1 - p_hat)) / n_sample)
    margin_of_error = z_value * standard_error
    
    lower_bound = p_hat - margin_of_error
    upper_bound = p_hat + margin_of_error

    # For explanation template
    generated_vars["correct_lower_bound"] = f"{lower_bound:.3f}"
    generated_vars["correct_upper_bound"] = f"{upper_bound:.3f}"
    
    correct_ans_str = f"({lower_bound:.3f}, {upper_bound:.3f})"
    correct_ans_val_tuple = (round(lower_bound,3), round(upper_bound,3)) # Actual value

    # Distractors:
    distractors_str = []
    # 1. Using Z=1 (common mistake if z-value forgotten)
    me_z1 = 1 * standard_error
    distractors_str.append(f"({p_hat - me_z1:.3f}, {p_hat + me_z1:.3f})")
    # 2. Incorrect SE formula (e.g., forgetting sqrt)
    se_error = (p_hat * (1-p_hat)) / n_sample
    me_se_err = z_value * se_error
    distractors_str.append(f"({p_hat - me_se_err:.3f}, {p_hat + me_se_err:.3f})")
    # 3. Shifted interval
    shift = random.uniform(0.02, 0.05)
    distractors_str.append(f"({lower_bound + shift:.3f}, {upper_bound + shift:.3f})")
    
    return _format_options(correct_ans_str, distractors_str, is_string_based=True)


def _al_calculate_t_or_z_stat_one_mean(generated_vars: Dict, details: Dict, options_template: List[str]) -> Tuple[float, List[str], int]:
    # Read the variable names directly from the 'params' in the JSON
    # e.g., ["x_bar_brew_time", "mu0_brew_time", "s_brew_time", "n_brew_sample"]
    param_names = details["params"]
    
    sample_mean = float(generated_vars[param_names[0]])
    population_mean = float(generated_vars[param_names[1]])
    std_dev = float(generated_vars[param_names[2]])
    n = int(generated_vars[param_names[3]])

    # The rest of the logic is the same
    if n <= 0 or std_dev <= 0:
        return 0.0, ["Invalid input"]*4, 0

    se = std_dev / math.sqrt(n)
    if se == 0:
        return 0.0, ["Cannot calculate, SE is zero"]*4, 0

    test_statistic = (sample_mean - population_mean) / se

    # For the explanation template
    generated_vars["se_val"] = round(se, 3)
    generated_vars["test_stat_val"] = round(test_statistic, 3)
    generated_vars["correct_ans"] = round(test_statistic, 3) # Make sure 'correct_ans' is available

    distractors = _generate_numerical_distractors(test_statistic, num_distractors=3, decimals=2)
    return _format_options(test_statistic, distractors, is_string_based=False, decimals=2)


def _al_calculate_t_stat_two_means_unequal_var(generated_vars: Dict, details: Dict, options_template: List[str]) -> Tuple[float, List[str], int]:
    x1 = float(generated_vars["mean1"])
    x2 = float(generated_vars["mean2"])
    s1_sq = float(generated_vars["var1"])
    s2_sq = float(generated_vars["var2"])
    n1 = int(generated_vars["n1"])
    n2 = int(generated_vars["n2"])

    se = math.sqrt((s1_sq / n1) + (s2_sq / n2))
    t_stat = (x1 - x2) / se

    generated_vars["se_val"] = round(se, 3)
    generated_vars["t_stat_val"] = round(t_stat, 3)

    distractors = _generate_numerical_distractors(t_stat, num_distractors=3, decimals=2)
    return _format_options(t_stat, distractors, is_string_based=False, decimals=2)


def _al_ci_to_hypothesis_test_decision(generated_vars: Dict, details: Dict, options_template: List[str]) -> Tuple[str, List[str], int]:
    ci_lower = float(generated_vars["ci_lower"])
    ci_upper = float(generated_vars["ci_upper"])
    mu_null = float(generated_vars["mu_null_val"])

    if mu_null < ci_lower or mu_null > ci_upper:
        correct_ans = "Reject H₀"
    else:
        correct_ans = "Fail to reject H₀"

    distractors = [opt for opt in ["Reject H₀", "Fail to reject H₀", "Accept H₀", "More information is needed"] if opt != correct_ans]
    return _format_options(correct_ans, distractors, is_string_based=True)


def _al_compare_ci_width_by_std_dev(generated_vars: Dict, details: Dict, options_template: List[str]) -> Tuple[str, List[str], int]:
    std_a = float(generated_vars["std_dev_a"])
    std_b = float(generated_vars["std_dev_b"])

    if std_a > std_b:
        correct_ans = "Sample A"
    elif std_b > std_a:
        correct_ans = "Sample B"
    else:
        correct_ans = "Both will have the same width"

    distractors = [opt for opt in options_template if opt != correct_ans]
    return _format_options(correct_ans, distractors, is_string_based=True)


def _al_find_mean_from_ci(generated_vars: Dict, details: Dict, options_template: List[str]) -> Tuple[float, List[str], int]:
    lower = float(generated_vars["lower_bound_ci_find_mean"])
    upper = float(generated_vars["upper_bound_ci_find_mean"])

    mean = (lower + upper) / 2

    generated_vars["estimated_mean_from_ci"] = round(mean, 3)
    distractors = _generate_numerical_distractors(mean, num_distractors=3, decimals=1)
    return _format_options(mean, distractors, is_string_based=False, decimals=1)


def _al_hypothesis_decision_worded(generated_vars: Dict, details: Dict, options_template: List[str]) -> Tuple[str, List[str], int]:
    p_val = float(generated_vars["p_value_argument"])
    alpha = float(details["alpha_fixed"])

    interp_reject = details["interpretation_if_reject"]
    interp_fail = details["interpretation_if_fail_reject"]

    # Fill variables inside interpretation strings
    interp_reject_filled = interp_reject.format(**generated_vars)
    interp_fail_filled = interp_fail.format(**generated_vars)

    correct_ans = interp_reject_filled if p_val <= alpha else interp_fail_filled
    distractors = [opt.format(**generated_vars) for opt in options_template if opt.format(**generated_vars) != correct_ans]

    return _format_options(correct_ans, distractors, is_string_based=True)



def _al_interpret_ci_difference_proportions(generated_vars: Dict, details: Dict, options_template: List[str]) -> Tuple[str, List[str], int]:
    lower = float(generated_vars["lower_diff_prop"])
    upper = float(generated_vars["upper_diff_prop"])

    if lower > 0 or upper < 0:
        correct_ans = "Yes, significant difference"
    else:
        correct_ans = "No, not significant"

    generated_vars["ci_includes_zero"] = not (lower > 0 or upper < 0)
    distractors = [opt for opt in ["Yes, significant difference", "No, not significant", "Cannot say", "Need p-value"] if opt != correct_ans]
    return _format_options(correct_ans, distractors, is_string_based=True)


def _al_test_two_proportions_one_tailed(generated_vars: Dict, details: Dict, options_template: List[str]) -> Tuple[str, List[str], int]:
    x1 = int(generated_vars["n1_pref"])
    x2 = int(generated_vars["n2_pref"])
    n1 = int(generated_vars["total1_pref"])
    n2 = int(generated_vars["total2_pref"])
    alpha = float(generated_vars["alpha_pref"])

    p1_hat = x1 / n1
    p2_hat = x2 / n2
    p_pool = (x1 + x2) / (n1 + n2)
    se = math.sqrt(p_pool * (1 - p_pool) * ((1/n1) + (1/n2)))

    z_score = (p1_hat - p2_hat) / se
    p_value = 1 - stats.norm.cdf(z_score)

    generated_vars["z_score_two_prop"] = round(z_score, 3)
    generated_vars["p_value_two_prop"] = round(p_value, 4)

    if p_value <= alpha:
        correct_ans = "Yes, reject H₀ (p1=p2) in favor of H₁ (p1>p2)."
    else:
        correct_ans = "No, fail to reject H₀ (p1=p2)."

    distractors = [opt for opt in [
        "Yes, reject H₀ (p1=p2) in favor of H₁ (p1>p2).",
        "No, fail to reject H₀ (p1=p2).",
        "The sample sizes are too small to conclude.",
        "Yes, because Gamma Inc.'s sample proportion is higher."
    ] if opt != correct_ans]

    return _format_options(correct_ans, distractors, is_string_based=True)





# --- Mapping answer logic types to functions ---
ANSWER_LOGIC_FUNCTIONS: Dict[str, Callable] = {
    "fixed_choice": _al_fixed_choice,
    "fixed_choice_conditional": _al_fixed_choice_conditional,
    "calculate_standard_error_mean": _al_calculate_standard_error_mean,
    "calculate_covariance_from_corr": _al_calculate_covariance_from_corr,
    "calculate_iqr": _al_calculate_iqr,
    "calculate_point_estimate_proportion": _al_calculate_point_estimate_proportion,
    "calculate_binomial_probability": _al_calculate_binomial_probability,
    "calculate_std_dev_from_variance": _al_calculate_std_dev_from_variance,
    "interpret_ci_difference_means": _al_interpret_ci_difference_means,
    "calculate_ci_mean_known_sigma": _al_calculate_ci_mean_known_sigma,
    "p_value_decision": _al_p_value_decision,
    "find_missing_value_for_mean": _al_find_missing_value_for_mean,
    "calculate_z_score": _al_calculate_z_score,
    "calculate_range": _al_calculate_range,
    "calculate_relative_frequency": _al_calculate_relative_frequency,
    "find_median_sorted_odd": _al_find_median_sorted_odd,
    "find_mode_simple": _al_find_mode_simple,
    "calculate_std_dev_from_variance": _al_calculate_std_dev_from_variance,
    "mean_multiplication_effect": _al_mean_multiplication_effect,
    "calculate_binomial_probability": _al_calculate_binomial_probability,
    "calculate_binomial_cumulative_probability_le": _al_calculate_binomial_cumulative_probability_le,
    "calculate_poisson_probability": _al_calculate_poisson_probability,
    "calculate_binomial_at_least_one": _al_calculate_binomial_at_least_one,
    "normal_approx_poisson_gt": _al_normal_approx_poisson_gt,
    "calculate_sample_variance": _al_calculate_sample_variance,
    "calculate_correlation_coefficient": _al_calculate_correlation_coefficient,
    "expected_value_product_independent": _al_expected_value_product_independent,
    "calculate_kth_percentile":_al_calculate_kth_percentile,
    "calculate_mode": _al_calculate_mode,
    "calculate_mean": _al_calculate_mean,
    "variance_sum_independent_vars": _al_variance_sum_independent_vars,
    "sample_size_proportion_no_prior": _al_sample_size_proportion_no_prior,
    "mean_addition_effect": _al_mean_addition_effect,
    "find_median_sorted_even": _al_find_median_sorted_even,
    "calculate_z_score_population_mean_diff": _al_calculate_z_score_population_mean_diff,
    "calculate_margin_of_error": _al_calculate_margin_of_error,
    "calculate_p_value_z_test": _al_calculate_p_value_z_test,
    "calculate_effect_size": _al_calculate_effect_size,
    "calculate_mean_squared_error": _al_calculate_mean_squared_error,
    "calculate_binomial_mean": _al_calculate_binomial_mean,
    "fixed_choice_dynamic_option": _al_fixed_choice_dynamic_option,
    "calculate_x_from_z_word_problem": _al_calculate_x_from_z_word_problem,
    "mean_sum_vars": _al_mean_sum_vars,
    "calculate_weighted_mean_two_values": _al_calculate_weighted_mean_two_values,
    "calculate_binomial_variance": _al_calculate_binomial_variance,
    "variance_linear_combination_two_vars": _al_variance_linear_combination_two_vars,
    "sample_size_two_means": _al_sample_size_two_means,
    "calculate_ci_proportion":_al_calculate_ci_proportion,
    "calculate_t_or_z_stat_one_mean": _al_calculate_t_or_z_stat_one_mean,
    "calculate_t_stat_two_means_unequal_var": _al_calculate_t_stat_two_means_unequal_var,
    "ci_to_hypothesis_test_decision": _al_ci_to_hypothesis_test_decision,
    "compare_ci_width_by_std_dev": _al_compare_ci_width_by_std_dev,
    "find_mean_from_ci": _al_find_mean_from_ci,
    "hypothesis_decision_worded": _al_hypothesis_decision_worded,
    "interpret_ci_difference_proportions": _al_interpret_ci_difference_proportions,
    "test_two_proportions_one_tailed": _al_test_two_proportions_one_tailed

}



def substitute_placeholders(text_template: str, variables: Dict) -> str:
    """Substitutes placeholders like {var_name} in a string with values from the variables dict."""
    # Find all placeholders like {var_name}
    placeholders = re.findall(r"\{([\w_]+)\}", text_template)
    
    formatted_text = text_template
    for placeholder in placeholders:
        if placeholder in variables:
            value = variables[placeholder]
            # Smart formatting for floats
            if isinstance(value, float):
                # If it's essentially an integer (e.g., 5.0)
                if value == int(value):
                    display_value = str(int(value))
                # If it's a very small decimal or needs precision
                elif abs(value) < 0.0001 and value != 0:
                    display_value = f"{value:.4e}" # scientific notation
                elif abs(value) < 1: # Small decimals
                    display_value = f"{value:.3f}".rstrip('0').rstrip('.') # up to 3, remove trailing .0
                else: # Other floats
                    display_value = f"{value:.2f}".rstrip('0').rstrip('.') # up to 2, remove trailing .0
            else:
                display_value = str(value)
            formatted_text = formatted_text.replace(f"{{{placeholder}}}", display_value)
        # else:
            # print(f"Warning: Placeholder {{{placeholder}}} not found in generated variables for template: {text_template[:50]}...")
    return formatted_text


class QuestionEngine:
    def __init__(self, templates_file_path: str):
        self.question_templates: List[Dict] = self._load_templates(templates_file_path)
        # Store a reference to the actual generator functions for variable generation
        self.variable_generator_functions: Dict[str, Callable] = VARIABLE_GENERATOR_FUNCTIONS
        # Store a reference to the actual answer logic functions
        self.answer_logic_functions: Dict[str, Callable] = ANSWER_LOGIC_FUNCTIONS
        
        # For _vg_lookup_from_options dependency, not ideal but works for now
        global template_variable_generators_store 
        self.current_template_var_gens_for_lookup = {}


    def _load_templates(self, file_path: str) -> List[Dict]:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                templates = json.load(f)
            print(f"Successfully loaded {len(templates)} question templates from {file_path}")
            return templates
        except FileNotFoundError:
            print(f"ERROR: Question templates file not found at {file_path}")
            return []
        except json.JSONDecodeError as e:
            print(f"ERROR: Could not decode JSON from {file_path}. Error: {e}")
            return []

    def _generate_variables_for_template(self, template: Dict) -> Dict:
        generated_vars = {}
        
        # Make template's variable_generators accessible for _vg_lookup_from_options
        # This is a hack and should ideally be refactored if _vg_lookup_from_options is frequently used
        # or if dependencies become very complex. A better way is to pass necessary context.
        global template_variable_generators_store 
        template_variable_generators_store = template.get("variable_generators", {})

        to_generate = list(template.get("variable_generators", {}).items())
        max_passes = len(to_generate) + 3 # Allow a few extra passes for dependencies

        for _pass_num in range(max_passes):
            if not to_generate: 
                break 
            
            processed_in_this_pass_count = 0
            still_needs_generation = []

            for var_name, gen_config_or_literal in to_generate:
                if var_name in generated_vars: 
                    continue

                # Check if gen_config_or_literal is a generator instruction (dict with 'type')
                # or a literal value (like a list for 'claim_options')
                if isinstance(gen_config_or_literal, dict) and "type" in gen_config_or_literal:
                    gen_details = gen_config_or_literal # This is a generator instruction
                    gen_type = gen_details.get("type")
                    
                    dependencies_met = True
                    # Check 'source_var'
                    if "source_var" in gen_details and gen_details["source_var"] not in generated_vars:
                        dependencies_met = False
                    
                    # Check other common dependency list keys
                    # (Consolidated the list of potential dependency keys)
                    dep_keys_to_check = [
                        "vars_to_sum", "vars_to_multiply", "known_values_var", "missing_value_var", 
                        "mean_var", "std_dev_var", "z_score_var", "max_var", "alpha_var", 
                        "scenario_var", "lambda_var", "N_var", "n_var", "base_var", "target_corr_var",
                        "std_dev_x_var", "std_dev_y_var", "lower_var", "upper_var", "center_var",
                        "p1_var", "p1_perc_var", "p2_perc_var", "prop_A_var", "prop_B_var", 
                        "mode_val_var", "mode_freq_var", "other_vals_count_var", "conf_level_var",
                        "dataset_arr_percentile", "sample_size_var", "proportion_var",
                        "var1", "var2" # For multiply_vars, subtract_vars etc.
                    ]
                    for dep_list_key in dep_keys_to_check:
                        if dep_list_key in gen_details:
                            dep_value_or_list = gen_details[dep_list_key]
                            if isinstance(dep_value_or_list, str): # Single dependency variable name
                                if dep_value_or_list not in generated_vars:
                                    dependencies_met = False; break
                            
                            # --- vvv THIS IS THE CORRECTED BLOCK vvv ---
                            elif isinstance(dep_value_or_list, list): # List of dependency variable names
                                for dep_var in dep_value_or_list:
                                    # ONLY check dependency if the item is a string (a variable name)
                                    if isinstance(dep_var, str) and dep_var not in generated_vars:
                                        dependencies_met = False
                                        break
                            # --- ^^^ THIS IS THE CORRECTED BLOCK ^^^ ---

                        if not dependencies_met: break
                    
                    # Dependency check for nested generator in target_t_or_z
                    if dependencies_met and "target_t_or_z" in gen_details and isinstance(gen_details["target_t_or_z"], dict):
                        nested_details = gen_details["target_t_or_z"]
                        if "source_var" in nested_details and nested_details["source_var"] not in generated_vars:
                            dependencies_met = False
                        for dep_key in ["var1", "var2"]: # Common for multiply_vars_float
                            if dep_key in nested_details and nested_details[dep_key] not in generated_vars:
                                dependencies_met = False; break
                        if not dependencies_met: break

                    if dependencies_met:
                        if gen_type in self.variable_generator_functions:
                            try:
                                generated_vars[var_name] = self.variable_generator_functions[gen_type](gen_details, generated_vars)
                                processed_in_this_pass_count += 1
                            except Exception as e:
                                print(f"ERROR generating variable '{var_name}' (type: {gen_type}) for template ID '{template.get('id')}': {e}")
                                generated_vars[var_name] = f"ERROR_IN_GENERATION_{var_name}"
                                processed_in_this_pass_count += 1 # Mark as processed to avoid infinite loop
                        else:
                            print(f"Warning: Unknown variable generator type '{gen_type}' for var '{var_name}' in template ID '{template.get('id')}'.")
                            generated_vars[var_name] = f"UNKNOWN_GEN_TYPE_{var_name}"
                            processed_in_this_pass_count += 1
                    else:
                        still_needs_generation.append((var_name, gen_details))
                
                # If it's NOT a dict with a 'type', assume it's a literal value (e.g., a list like 'claim_options')
                # These literals are directly assigned to generated_vars to be used by other generators.
                else: 
                    generated_vars[var_name] = gen_config_or_literal 
                    processed_in_this_pass_count += 1
            
            to_generate = still_needs_generation # Update the list of vars still needing generation
            if processed_in_this_pass_count == 0 and to_generate:
                # print(f"Warning: Could not resolve all variables for template {template.get('id')}. Unresolved: {[item[0] for item in to_generate]}")
                for var_name_unresolved, _ in to_generate: 
                    generated_vars[var_name_unresolved] = f"ERROR_DEP_UNRESOLVED_{var_name_unresolved}"
                break 
        
        template_variable_generators_store = {} # Clear global temporary store
        return generated_vars

    def generate_single_question_instance(self, template: Dict) -> Dict[str, Any]:
        if not template: return {"error": "Empty template provided"}

        generated_variables = self._generate_variables_for_template(template)
        
        question_text = substitute_placeholders(template["question_template"], generated_variables)
        
        options_template_raw = template.get("options_template", [])
        answer_logic_details = template.get("answer_logic", {})
        logic_type = answer_logic_details.get("type")

        correct_answer_value: Any = "N/A"
        final_options_str: List[str] = ["Error"] * 4
        correct_option_index: int = 0 # Default to first option if error

        if logic_type and logic_type in self.answer_logic_functions:
            try:
                correct_answer_value, final_options_str, correct_option_index = \
                    self.answer_logic_functions[logic_type](generated_variables, answer_logic_details, options_template_raw)
            except Exception as e:
                print(f"ERROR executing answer logic '{logic_type}' for template '{template.get('id')}': {e}")
                # final_options_str remains ["Error"]*4
        else:
            print(f"Warning: Answer logic type '{logic_type}' not found for template '{template.get('id')}'. Using raw options.")
            # Try to process options template directly if logic is missing (e.g. for simple fixed choice where index is enough)
            if options_template_raw:
                final_options_str = [substitute_placeholders(opt, generated_variables) for opt in options_template_raw]
                # If it was a simple fixed_choice and correct_option_index was in template directly
                if "correct_option_index" in answer_logic_details and len(final_options_str) > answer_logic_details["correct_option_index"]:
                    correct_option_index = answer_logic_details["correct_option_index"]
                    correct_answer_value = final_options_str[correct_option_index]
            
        # Ensure 4 options, pad if necessary
        final_options_str = [str(opt) for opt in final_options_str] # all options to string
        while len(final_options_str) < 4: final_options_str.append(f"PadOpt{len(final_options_str)}")
        final_options_str = final_options_str[:4]

        if not (0 <= correct_option_index < len(final_options_str)):
             print(f"Warning: Correct option index {correct_option_index} out of bounds for options list length {len(final_options_str)} in template {template.get('id')}. Defaulting to 0.")
             correct_option_index = 0
             if final_options_str: correct_answer_value = final_options_str[0] # Update correct_answer_value if index changed

        explanation = ""
        if "explanation_template" in template:
            # For explanation, ensure 'correct_ans' and other dynamic parts are available
            # The answer_logic functions should ideally add computed values to generated_vars if they are used in explanations
            # For simplicity now, we just add the final correct_answer_value
            vars_for_explanation = generated_variables.copy()
            vars_for_explanation['correct_ans'] = str(correct_answer_value) # The actual value
            # If answer logic added more keys to generated_vars (like intermediate steps), they can be used too.
            # Example: if _al_calculate_mean adds 'sum_of_values', 'sample_size_mean' to generated_vars
            explanation = substitute_placeholders(template["explanation_template"], vars_for_explanation)

        return {
            "id": template.get("id"),
            "unit_name": template.get("unit_name"),
            "topic_name": template.get("topic_name"),
            "subtopic_name": template.get("subtopic_name"),
            "difficulty_level": template.get("difficulty_level"),
            "difficulty_type": template.get("difficulty_type"),
            "question_text": question_text,
            "options": final_options_str,
            "correct_answer_index": correct_option_index,
            "_actual_correct_value": correct_answer_value, # For internal verification or detailed feedback
            "explanation": explanation,
            "_debug_generated_vars": generated_variables 
        }

    def get_all_templates(self) -> List[Dict]:
        return self.question_templates

# --- Example Usage (for testing this file directly) ---
if __name__ == "__main__":
    # Assuming this script is in backend/app/ and templates are in backend/data_initial/
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_backend_dir = os.path.dirname(script_dir) # This should be 'backend'
    templates_path = os.path.join(project_backend_dir, 'data_initial', 'question_templates.json')
    
    print(f"Attempting to load templates from: {templates_path}")
    engine = QuestionEngine(templates_file_path=templates_path)

    if engine.question_templates:
        print(f"\n--- Testing Question Generation from {len(engine.question_templates)} Loaded Templates ---")
        
        # Select a few specific templates to test, or a random sample
        # test_template_ids = [
        #     "STAT_U1_T3_S1_E_D_002", # calculate_mean
        #     "STAT_U3_T2_S1_M_LR_001", # fixed_choice_conditional
        #     "STAT_U2_T2_S2_M_D_001", # calculate_standard_error_mean
        #     "STAT_U5_T1_S2_E_D_001"  # lookup_from_options (complex var gen)
        # ]
        # templates_to_test = [t for t in engine.question_templates if t.get("id") in test_template_ids]
        # if not templates_to_test:
        #     templates_to_test = engine.question_templates[:3] + engine.question_templates[-3:] # first 3 and last 3

        count = 0
        for tpl in engine.question_templates:
            # Test a subset to avoid excessive output
            if count < 5 or count > len(engine.question_templates) - 6 :
                print(f"\nGenerating from Template ID: {tpl.get('id')} (Type: {tpl.get('answer_logic',{}).get('type')})")
                question_instance = engine.generate_single_question_instance(tpl)
                if "error" not in question_instance:
                    print(f"  Q: {question_instance['question_text']}")
                    for idx, opt in enumerate(question_instance['options']):
                        print(f"    {chr(65+idx)}) {opt} {'<-- CORRECT' if idx == question_instance['correct_answer_index'] else ''}")
                    print(f"  Actual Correct Value: {question_instance['_actual_correct_value']}")
                    print(f"  Explanation: {question_instance['explanation']}")
                    # print(f"  Debug Vars: {question_instance['_debug_generated_vars']}") # Uncomment for deep debug
                else:
                    print(f"  Error generating question: {question_instance['error']}")
            elif count == 5:
                print("\n... (skipping some templates for brevity in test output) ...\n")
            count +=1
    else:
        print("No templates loaded from JSON, cannot test generation.")