import csv
import re
import os
import argparse
from collections import defaultdict

# --- Installation of Required Libraries ---
# This script requires the following libraries. Install them by running this command:
# pip install rapidfuzz Metaphone tqdm

try:
    from rapidfuzz import process, fuzz
except ImportError:
    print("Error: The 'rapidfuzz' library is not installed. This is required for fuzzy matching.")
    print("Please install it by running: pip install rapidfuzz")
    exit()

try:
    from metaphone import doublemetaphone
except ImportError:
    print("Error: The 'Metaphone' library is not installed. This is required for phonetic blocking.")
    print("Please install it by running: pip install Metaphone")
    exit()

try:
    from tqdm import tqdm
except ImportError:
    print("Error: The 'tqdm' library is not installed. This is required for the progress bar.")
    print("Please install it by running: pip install tqdm")
    exit()


# --- Configuration ---
SPECIAL_SCORING_GUIDE = {
    'name': 'a',
    'email': 'a',
    'company_name__c': 'b',
    'website': 'b',
    'phone': 'b',
    'billingstreet': 'b',
    'billingpostalcode': 'b',
    'billingcountry': 'a',
}
GRADE_WEIGHTS = {'a': 3, 'b': 2, 'c': 1}
UNIQUE_ID_COLUMN = 'Id'
DUPLICATE_FIELD_WEIGHTS = {
    'name': 40,
    'email': 30,
    'company_name__c': 20,
    'phone': 10
}
BLOCKING_FIELDS = ['name', 'email', 'company_name__c']
SIMILARITY_THRESHOLD = 80


def get_field_score(field_name, value, debug=False):
    """
    Scores a single field. It applies basic checks to all fields,
    and special checks for fields containing certain keywords.
    """
    if value is None or not value.strip():
        if debug: print(f"         - Field '{field_name}' failed: Value is empty.")
        return 0
    if not re.search(r'[a-zA-Z0-9]', value):
        if debug: print(f"         - Field '{field_name}' failed: Value contains only symbols.")
        return 0
    field_name_lower = field_name.lower()
    if 'phone' in field_name_lower and sum(c.isdigit() for c in value) < 5:
        if debug: print(f"         - Field '{field_name}' failed: Phone number has fewer than 5 digits.")
        return 0
    elif 'website' in field_name_lower and not re.search(r'\.[a-zA-Z]{2,}', value):
        if debug: print(f"         - Field '{field_name}' failed: Website does not look like a valid domain.")
        return 0
    elif 'postalcode' in field_name_lower and value.strip() and not re.fullmatch(r'([Gg][Ii][Rr] 0[Aa]{2})|((([A-Za-z][0-9]{1,2})|(([A-Za-z][A-Ha-hJ-Yj-y][0-9]{1,2})|(([A-Za-z][0-9][A-Za-z])|([A-Za-z][A-Ha-hJ-Yj-y][0-9][A-Za-z]?))))\s?[0-9][A-Za-z]{2})', value.strip()):
         if debug: print(f"         - Field '{field_name}' failed: Does not match UK postcode format.")
         return 0
    return 1

def create_visualizations(processed_file_path):
    pass

def normalize_value(key, value):
    """
    Helper function to normalize values for comparison using robust cleaning techniques.
    """
    if not value or not isinstance(value, str) or not value.strip():
        return ""
    value = value.lower().strip()
    if key == 'phone':
        return re.sub(r'\D', '', value)
    if key == 'website':
        value = re.sub(r'https?://', '', value, flags=re.IGNORECASE)
        value = re.sub(r'www.', '', value, flags=re.IGNORECASE)
        return value.rstrip('/')
    if key == 'email':
        # Remove dots before @ and ignore case, ignore common typos like double letters
        local, _, domain = value.partition('@')
        local = re.sub(r'\.+', '', local)
        domain = re.sub(r'\.+', '.', domain)
        return f"{local}@{domain}"
    if key == 'company_name__c':
        # Remove common company suffixes and punctuation
        value = re.sub(r'[.,\/#!$%\^&\*;:{}=\-_`~()]', '', value)
        value = re.sub(r'\s+',' ', value)
        value = re.sub(r'\blimited\b|\bltd\b', 'limited', value, flags=re.IGNORECASE)
        value = re.sub(r'\bincorporated\b|\binc\b', 'incorporated', value, flags=re.IGNORECASE)
        value = re.sub(r'\bcompany\b|\bco\b', 'company', value, flags=re.IGNORECASE)
        value = re.sub(r'\bsolutions\b|\bsolns\b', 'solutions', value, flags=re.IGNORECASE)
        value = re.sub(r'\bgroup\b|\bgrp\b', 'group', value, flags=re.IGNORECASE)
        return value.strip()
    if key == 'name':
        replacements = {
            r'[.,\/#!$%\^&\*;:{}=\-_`~()]': '',
            r'\s+': ' ',
            r'\blimited\b|\bltd\b': 'limited',
            r'\bincorporated\b|\binc\b': 'incorporated',
            r'\bcompany\b|\bco\b': 'company',
            r'\bsolutions\b|\bsolns\b': 'solutions',
            r'\bgroup\b|\bgrp\b': 'group'
        }
        for pattern, repl in replacements.items():
            value = re.sub(pattern, repl, value, flags=re.IGNORECASE)
        return value.strip()
    return value

def process_csv(input_file_path, output_file_path, debug=False):
    if sum(DUPLICATE_FIELD_WEIGHTS.values()) != 100:
        print(f"Error: The values in DUPLICATE_FIELD_WEIGHTS must sum to 100, but they sum to {sum(DUPLICATE_FIELD_WEIGHTS.values())}.")
        return False
    try:
        # --- PRE-LOAD: Read all data into memory to allow for a two-pass approach ---
        with open(input_file_path, mode='r', newline='', encoding='utf-8-sig') as infile:
            reader = csv.DictReader(infile)
            original_header = list(reader.fieldnames)
            if UNIQUE_ID_COLUMN not in original_header:
                print(f"Error: The specified UNIQUE_ID_COLUMN '{UNIQUE_ID_COLUMN}' was not found in the CSV header.")
                print(f"Available headers are: {original_header}")
                return False
            all_rows = list(reader)

        # --- SETUP ---
        header_map = {key: next((h for h in original_header if key in h.lower()), None) for key in DUPLICATE_FIELD_WEIGHTS.keys()}
        # For blocking, get all relevant columns
        blocking_header_map = {key: next((h for h in original_header if key in h.lower()), None) for key in BLOCKING_FIELDS}
        seen_records_blocked = defaultdict(list)
        
        duplicate_of = {}
        matched_by = defaultdict(list)
        match_key_counter = 1
        match_key_map = {}  # Maps row index to match key

        # --- PASS 1: FIND ALL DUPLICATE PAIRS ---
        print("Pass 1: Finding all duplicate pairs...")
        for i, row_dict in enumerate(tqdm(all_rows, desc="Finding Duplicates", unit="row")):
            current_record_normalized = {key: normalize_value(key, row_dict.get(header_map[key])) for key in DUPLICATE_FIELD_WEIGHTS.keys()}
            # Build blocking keys set
            blocking_keys = set()
            # Name blocking (Double Metaphone)
            name_val = normalize_value('name', row_dict.get(blocking_header_map.get('name')))
            if name_val:
                dmeta = doublemetaphone(name_val)
                if dmeta[0]: blocking_keys.add(f"name:{dmeta[0]}")
                if dmeta[1]: blocking_keys.add(f"name:{dmeta[1]}")
            # Email blocking
            email_val = normalize_value('email', row_dict.get(blocking_header_map.get('email')))
            if email_val:
                blocking_keys.add(f"email:{email_val}")
            # Company name blocking
            company_val = normalize_value('company_name__c', row_dict.get(blocking_header_map.get('company_name__c')))
            if company_val:
                blocking_keys.add(f"company:{company_val}")

            max_similarity_score = 0
            best_match_info = None
            candidate_records = []
            for block_key in blocking_keys:
                candidate_records.extend(seen_records_blocked[block_key])
            # Remove self-matches and duplicates
            candidate_records = {cr['row_index']: cr for cr in candidate_records if cr['row_index'] != i}.values()
            for seen_record in candidate_records:
                weighted_score = 0
                field_scores_for_log = {}
                for key, weight in DUPLICATE_FIELD_WEIGHTS.items():
                    new_val, seen_val = current_record_normalized[key], seen_record['data'][key]
                    if new_val and seen_val:
                        field_score = fuzz.token_set_ratio(new_val, seen_val)
                        weighted_score += (field_score / 100.0) * weight
                        field_scores_for_log[key] = int(field_score)
                if weighted_score > max_similarity_score:
                    max_similarity_score = weighted_score
                    best_match_info = {'seen_record': seen_record, 'scores': field_scores_for_log}
            if max_similarity_score >= SIMILARITY_THRESHOLD and best_match_info:
                original_index = best_match_info['seen_record']['row_index']
                details_str = ", ".join([f"{k.capitalize()}:{v}" for k,v in best_match_info['scores'].items()])
                duplicate_of[i] = {
                    'score': int(max_similarity_score),
                    'details': f"Best match with row {best_match_info['seen_record']['row_num']} [ID: {best_match_info['seen_record']['unique_id']}] ({details_str})"
                }
                matched_by[original_index].append({
                    'dupe_row_num': i + 1,
                    'dupe_id': row_dict.get(UNIQUE_ID_COLUMN),
                    'score': int(max_similarity_score)
                })
                # --- Assign a unique match key ---
                if original_index in match_key_map:
                    match_key_map[i] = match_key_map[original_index]
                else:
                    match_key_map[original_index] = match_key_counter
                    match_key_map[i] = match_key_counter
                    match_key_counter += 1
            # Add current record to all blocks
            for block_key in blocking_keys:
                seen_records_blocked[block_key].append({
                    'row_index': i,
                    'row_num': i + 1, 
                    'data': current_record_normalized,
                    'unique_id': row_dict.get(UNIQUE_ID_COLUMN)
                })

        # --- PASS 2: BUILD OUTPUT WITH ALL FLAGS ---
        print("\nPass 2: Generating final output file with all flags...")
        with open(output_file_path, mode='w', newline='', encoding='utf-8') as outfile:
            score_headers = [f"{h.strip()}_score" for h in original_header]
            # --- Add the new match key column to the header ---
            new_header = original_header + score_headers + [
                'total_row_score', 'final_status', 'duplicate_score', 'duplicate_match_details', 'is_matched_to', 'is_duplicate_or_matched', 'match_key'
            ]
            writer = csv.writer(outfile)
            writer.writerow(new_header)

            for i, row_dict in enumerate(tqdm(all_rows, desc="Writing Output", unit="row")):
                total_row_score, any_a_field_failed, scores_list = 0, False, []
                for col_name in original_header:
                    value = row_dict.get(col_name, "")
                    guide_key = next((g_key for g_key in SPECIAL_SCORING_GUIDE if g_key in col_name.lower()), col_name.lower())
                    grade = SPECIAL_SCORING_GUIDE.get(guide_key, 'c')
                    base_score = get_field_score(col_name, value, debug)
                    if grade == 'a' and base_score == 0: any_a_field_failed = True
                    weight = GRADE_WEIGHTS.get(grade, 0)
                    scores_list.append(base_score * weight)
                    total_row_score += base_score * weight
                final_status = "Fail" if any_a_field_failed else "Pass"

                dupe_info = duplicate_of.get(i)
                original_info = matched_by.get(i)
                
                final_score_val = dupe_info['score'] if dupe_info else ""
                final_details = dupe_info['details'] if dupe_info else ""
                is_matched_to_details = ""
                if original_info:
                    is_matched_to_details = "; ".join([f"Matched by row {m['dupe_row_num']} [ID: {m['dupe_id']}] (Score: {m['score']})" for m in original_info])

                # --- NEW: Set the final boolean flag ---
                is_involved_flag = True if dupe_info or original_info else False
                original_row_values = [row_dict.get(h, "") for h in original_header]
                # --- Add the match key to the row being written ---
                match_key_val = match_key_map.get(i, "")
                writer.writerow(original_row_values + scores_list + [total_row_score, final_status, final_score_val, final_details, is_matched_to_details, is_involved_flag, match_key_val])
            
        print(f"\nProcessing complete. The output file is saved at: {output_file_path}")
        return True
            
    except FileNotFoundError:
        print(f"Error: The file '{input_file_path}' was not found.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        import traceback
        traceback.print_exc()
    return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Validates, scores, and performs robust, weighted record-level duplicate checking on CSV data.")
    parser.add_argument("input_file", help="Path to the input CSV file.")
    parser.add_argument("-o", "--output_file", help="Path for the output CSV file. (Optional)")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode to print detailed scoring information.")
    parser.add_argument("--graph", action="store_true", help="Generate interactive HTML graphs summarizing the results.")
    args = parser.parse_args()
    if args.output_file:
        output_path = args.output_file
    else:
        base, ext = os.path.splitext(args.input_file)
        output_path = f"{base}_processed{ext}"
    process_csv(args.input_file, output_path, args.debug)