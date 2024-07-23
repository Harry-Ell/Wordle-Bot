import pandas as pd
import re
from pathlib import Path

def WordleBot(Greens, Yellows, Repeated, Not_Repeated, Greys, Choices):
    Parameters = {'Common_Letter': 1,               # Points awarded for shared letter 
            'Common_Letter_Same_Index': 2.6556, # Points awarded for shared letter, same index
            'Degeneracy_Penalty_1':0.7489,      # Penalty for 2 times repeated letters
            'Degeneracy_Penalty_2':0.7177,      # Penalty for 2 sets of repeated letters
            'Degeneracy_Penalty_3':0.6007,      # Penalty for 3 times repeated letter
             }
    relative_path = r'..\Wordle Words\WordleInputWords.txt'
    with open(relative_path, 'r') as file:
        result = file.read().replace('\n', ' ')

    # wordle_words_dir = Path('Users\harry\OneDrive\Documents\Applications\Python\Wordle-Bot\Wordle Words\WordleInputWords.txt')
    # list = wordle_words_dir.read_text()
    # result = ' '.join([item for sublist in list for item in sublist])
    counter = 0
    pattern = r'\b'
    for sublist in Yellows:
        if sublist:
            for item1 in sublist:
                pattern += f'(?=[a-z]*{item1})'  # Positive lookahead for required letter
    for item2 in Greys:
        if item2 != '_':
            pattern += f'(?![a-z]*{item2})'  # Negative lookahead for excluded letters
    for item in Greens:
        if item != '_':
            pattern += '[a-z]' * counter + item
            counter = 0
        else:
            counter += 1
    pattern += '[a-z]' * counter + r'\b'
    output = re.findall(pattern, result)
    invalids = set()
    for number in range(5):
        if Yellows[number]:
            for letter in Yellows[number]:
                for word in output:
                    if word[number] == letter:
                        invalids.add(word)  # Add word to the set of words to remove
                    
    for word in output:
    # Check for characters that should not repeat
        for character in Not_Repeated:
            counter1 = 0
            for letter in word:
                if letter == character:
                    counter1 += 1
                    if counter1 >= 2:
                        invalids.add(word)
                        break  # Once a character repeats, we can stop checking this word
        # Check for characters that should repeat
        for character in Repeated:
            counter2 = 0
            for letter in word:
                if letter == character:
                    counter2 += 1
            if counter2 < 2:
                invalids.add(word)
                break  # If any repeated character doesn't appear twice, mark the word as invalid

    output = [word for word in output if word not in invalids]
    scores = []
    for sample in output:
        sample_word_letter = set()
        sample_word_letter_and_place = set()
        sample_degeneracy = 0 
        sample_multiplier = 0
        for i in range(5):
            sample_word_letter.add(sample[i])
            sample_word_letter_and_place.add((sample[i], i))
            for j in range(5):
                if j != i:
                    if sample[j] == sample[i]:
                        sample_degeneracy += 1
            if sample_degeneracy == 0:
                sample_multiplier = 1
            if sample_degeneracy == 2:
                sample_multiplier = Parameters['Degeneracy_Penalty_1']
            if sample_degeneracy == 4:
                sample_multiplier = Parameters['Degeneracy_Penalty_2']
            if sample_degeneracy >= 6:
                sample_multiplier = Parameters['Degeneracy_Penalty_3']
        sample_score = 0
        for word in output:
            working_word_letter = set()
            working_word_letter_and_place = set()
            for i in range(5):
                working_word_letter.add(word[i])
                working_word_letter_and_place.add((word[i], i))
            common_letter = working_word_letter.intersection(sample_word_letter)                                      
            common_letter_and_place = working_word_letter_and_place.intersection(sample_word_letter_and_place)
            sample_score += len(common_letter)*Parameters['Common_Letter'] + len(common_letter_and_place)*Parameters['Common_Letter_Same_Index'] 
        scores.append(sample_score * sample_multiplier)
    try:
        best_guess = output[scores.index(max(scores))]  
        if Choices == False:
            if len(output) != 1:
                return f'Out of {len(output)} options, I think \'{best_guess}\' is the best choice'
            else:
                return f'{best_guess} is the solution'
        else:
            return f'The options are: {output}'
    except ValueError:
        return 'No words match this set of conditions'