"""Generates a list of rules for defining valid character blocks.

Given the INI file of word blocks (generated by word_blocks.py), this script
generates an INI file of forbidden letter combinations.
"""

import configparser
import time

# Define global consonant and vowel lists
CONSONANTS = "bcdfghjklmnpqrstvwxyz"
VOWELS = "aeiou"

# Define character codes
_A = ord('a')
_Z = ord('z')

#==============================================================================

def forbid_tuples(fin, fout, num=3, comments=True, ignore=set(), group=set()):
    """forbid_tuples(fin, fout, n[, comments][, ignore][, group])
    Generates a list of substrings forbidden in a given word block list.

    Positional arguments:
    fin (str) -- name of input word list file
    fout (str) -- name of output statistic file
    
    Keyword arguments:
    [num=3] (int) -- maximum size of substring (all n-tuples up to this size
                     are considered, so do not choose too large)
    [comments=True] (bool) -- whether to include comments in the output INI
                              file to explain the naming convention behind the
                              sections
    [ignore={}] (set(str)) -- set of fields to ignore for the purposes of rule
                              creation
    [group={}] (set(str)) -- set of letters to consider grouping (i.e. pairs
                             of letters that often appear together, like "qu"
                             and "th")

    The input file should be an INI file of the format produced by
    word_blocks.py containing various categories of letter blocks.

    The output is an INI file containing forbidden n-letter combinations which
    define the input file's letter blocks. For each of the input file's
    fields, a corresponding field of the output file defines the forbidden
    letter combinations.
    
    A list of letter groups is also included. These are groups of letters that
    commonly appear together, and are explicitly given as an argument
    independent of the word block file.
    """

    # Start timer
    start = time.time()
    
    # Read the input file
    blocks = configparser.ConfigParser(allow_no_value=True)
    blocks.read(fin)

    # Initialize a rule dictionary for each block
    block_rules = {}

    # Define a processing order and rule inheritance for the blocks
    order = ("c", "v", "c_b", "vc", "v_w", "cv_w")
    parents = (tuple(), tuple(), ("c"), ("c", "v"), ("v"), ("c", "v", "c_b"))
    
    # Separately consider each letter block type
    i = 0
    for block in order:

        # Skip default and ignored fields
        if block == "DEFAULT" or block in ignore:
            continue

        # Get the word blocks as a list
        blist = list(blocks[block])

        # Initialize a dictionary of forbidden n-tuple rules
        rules = {} # all considered rules
        out = {} # finalized list of rules to output

        # Consider each block type starting with 2
        for n in range(2, num+1):

            # Generate a dictionary of every possible forbidden n-tuple
            pattern = 'a'*n
            while pattern != None:
                
                # Skip rules that are obviously unneeded for pure C or pure V
                if 'v' not in block and character_types(pattern, vowel=True):
                    pattern = next_word(pattern)
                    continue
                if 'c' not in block and character_types(pattern, vowel=False):
                    pattern = next_word(pattern)
                    continue

                # Skip rules that violate any C/V order of the block
                if "cv" in block and character_order(pattern, vc=True):
                    pattern = next_word(pattern)
                    continue
                if "vc" in block and character_order(pattern, vc=False):
                    pattern = next_word(pattern)
                    continue

                # Skip rules already covered by a smaller substring rule
                skip = False
                for r in out:
                    if r in pattern:
                        skip = True
                        break
                if skip == True:
                    pattern = next_word(pattern)
                    continue

                # Skip rules already covered by a parent rule list
                skip = False
                for par in parents[i]:
                    if par not in block_rules:
                        continue
                    if pattern in block_rules[par]:
                        skip = True
                        break
                if skip == True:
                    pattern = next_word(pattern)
                    continue

                # Add new rules to be considered
                rules[pattern] = None
                pattern = next_word(pattern)

            # Determine number of valid blocks that each rule would eliminate
            for r in rules:
                rules[r] = len(match(r, blist))
                # If there are no violations, immediately add to rule list
                if rules[r] == 0:
                    out[r] = None

        # Keep the final rule list
        block_rules[block] = out

        i += 1
    
    del blocks

    # Initialize output INI file parser
    config = configparser.ConfigParser(allow_no_value=True)

    # Load dictionaries into parser
    for block in block_rules:
        config[block] = block_rules[block]

    # Load letter groups into parser
    config["group"] = {}
    for g in group:
        config["group"][g] = None

    # Write INI file
    with open(fout, 'w') as f:
        config.write(f)

    # Write comments
    if comments == True:
        # Define comment string
        com = "; Substring rules generated from '" + fin + "'.\n"
        com += "; Includes substrings of length 2-" + str(num) + ".\n"
        com += ";\n; Each section below is a block of characters.\n" \
               "; The section names are as follows:\n"
        if "c" not in ignore:
            com += ";     c -- consonants\n"
        if "v" not in ignore:
            com += ";     v -- vowels\n"
        if "vc" not in ignore:
            com += ";     vc -- vowel/consonant\n"
        if "c_b" not in ignore:
            com += ";     c_b -- consonant at beginning\n"
        if "v_w" not in ignore:
            com += ";     v_w -- vowel-only words\n"
        if "cv_w" not in ignore:
            com += ";     cv_w -- consonant/vowel entire words\n"
        com += ';     group -- letter groups\n\n'
        
        # Write comments to beginning of file
        with open(fout, 'r') as f:
            for line in f:
                com += line
        with open(fout, 'w') as f:
            f.writelines(com[:-1])

    # Report total time
    print("Processed '" + fin + "' after " + str(time.time() - start) +
          " seconds.")
    print("Category\tRules")
    for block in block_rules:
        print(block + '\t' + str(len(block_rules[block])))

#==============================================================================

def character_types(w, vowel=False):
    """character_types(w[, vowel]) -> bool
    Determines whether a string contains any consonants or vowels.

    Positional arguments:
    w (str) -- input string to categorize

    Keyword arguments:
    [vowel=False] (bool) -- False to check for the presence of consonants, True
        to check for the presence of vowels

    Returns:
    (bool) -- True if the specified character type is present, False otherwise
    """

    # Process each letter of the input word
    for c in w:
        if vowel == False:
            if c in CONSONANTS:
                return True
        else:
            if c in VOWELS:
                return True

    # If the character type was not found, return False
    return False

#==============================================================================

def character_order(w, vc=False):
    """character_order(w[, vc]) -> bool
    Determines whether a string contains a CV or VC pair.

    Positional arguments:
    w (str) -- input string to categorize

    Keyword arguments:
    [vc=False] (bool) -- False to check CV order, True to check for VC order

    Returns:
    (bool) -- True if the specified progression is present, False otherwise
    """

    # Immediately return False if too short
    if len(w) < 2:
        return False

    # Check for CV pairs
    if vc == False:
        fc = False # whether we've found a consonant
        # Process each character
        for c in w:
            # Mark first found consonant
            if c in CONSONANTS:
                fc = True
            # Found vowel after consonant
            elif fc == True:
                return True
    # Check for VC pairs
    else:
        fv = False # whether we've found a vowel
        # Process each character
        for c in w:
            # Mark first found cvowel
            if c in VOWELS:
                fv = True
            # Found consonant after vowel
            elif fv == True:
                return True

    # If no switch found, return False
    return False

#==============================================================================

def next_word(w):
    """next_word(w) -> str
    Lexicographically increments a word.

    Positional arguments:
    w (str) -- input word

    Returns:
    (str|None) -- input word advanced by one character, or None if the input
        consists of all 'z'
    """

    # Find character code of final letter and increment
    final = ord(w[-1]) + 1

    # If this results in overflow, handle carry-over
    if final > _Z:
        # For single-character words, return None
        if len(w) == 1:
            return None
        # Otherwise recursively translate the head
        else:
            head = next_word(w[:-1])
            if head == None:
                return None
            else:
                return head + 'a'
    # Otherwise return the word with an incremented final character
    else:
        return w[:-1] + chr(final)

#==============================================================================

def match(pat, lst, ignore=set()):
    """match(pat, lst[, ignore]) -> set
    Finds words in a list that match a given pattern.

    Positional arguments:
    pat (str) -- pattern to match
    lst (list(str)) -- list of strings to search

    Keyword arguments:
    [ignore={}] -- set of words on the list to ignore

    Returns:
    (set(str)) -- set of words in the list that contain the pattern

    This is meant as part of the blacklist rule defining process, where the
    goal is to iteratively choose the rules that exclude the fewest valid
    letter blocks, ignoring any defined exceptions. Here the pattern is the
    considered rule, the list is the set of word blocks, and the ignore-list is
    the set of exceptions. The returned set is the set of valid words that
    would be deleted by the rule.
    """

    # Initialize output set
    out = set()

    # Search each word on the list
    for w in lst:
        # Ignore words in the ignore list
        if w in ignore:
            continue
        # Add to output set if there's a match
        if pat in w:
            out.add(w)

    # Return the set of matches
    return out

#==============================================================================

if __name__ == "__main__":
    g = {"ch", "gh", "ph", "sh", "th", "ng", "qu"}
    forbid_tuples("word_blocks_5.ini", "word_rules_5.ini", num=3, group=g)
    forbid_tuples("word_blocks.ini", "word_rules.ini", num=3, group=g)
