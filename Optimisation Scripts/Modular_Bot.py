"""
This script runs the Bayesian optimization procedure for the Wordle bot.
In addition to building the bot, it includes the supporting infrastructure
necessary for its operation. This infrastructure involves a virtual environment
that plays Wordle with the bot, updates the board with each guess, returns the 
new board state, and signals to the bot when it has correctly guessed the word.

Note, this script is resource-intensive and may be too demanding to run 
locally. Loading the score array requires approximately 2GB of working memory.
"""

import numpy as np 
from skopt import gp_minimize
from skopt.space import Real
from skopt.utils import use_named_args
import re
import random 
from pathlib import Path

path1 = Path('Wordle Words/WordleInputWords.txt')
path2 = Path('Wordle Words/WordleSolutionWords.txt')

df1 = path1.read_text()
df2 = path2.read_text()

word_list = df1.splitlines()
sol_list  = df2.splitlines()

def Load_Words_and_Populate_Raw_Score_Tensor(word_list):
# Purpose of function: define collection of allowed words, and create an array from which scores (i.e.
# ranking of word similarities) can be drawn. 
# This function is only ran once per optimisation procedure
    number_of_words = len(word_list)
    Yellow_Tally = np.zeros((number_of_words, number_of_words))
    Green_Tally = np.zeros((number_of_words, number_of_words))
    
    for i in range(number_of_words): 
        sample = word_list[i]
        sample_word_letter = set(sample)
        sample_word_letter_and_place = {(sample[k], k) for k in range(5)}
        for j in range(i + 1, number_of_words):
            working_word = word_list[j]
            working_word_letter = set(working_word)
            working_word_letter_and_place = {(working_word[l], l) for l in range(5)}
            common_letter = working_word_letter.intersection(sample_word_letter)
            common_letter_and_place = working_word_letter_and_place.intersection(sample_word_letter_and_place)
            sample_score_yellow = len(common_letter) 
            sample_score_green  = len(common_letter_and_place) 
            Yellow_Tally[i, j] = sample_score_yellow
            Green_Tally[i, j]  = sample_score_green
    Score_tensor = np.stack((Yellow_Tally.astype(int), Green_Tally.astype(int)), axis = -1)
    return Score_tensor
Score_Tensor = Load_Words_and_Populate_Raw_Score_Tensor(word_list)

def Score_tensor_for_set_of_params(Score_Tensor, Parameters):
    v = np.array([Parameters['Common_Letter'], Parameters['Common_Letter_Same_Index']])  # first index yellow, second is green 
    v_broadcasted = v[np.newaxis, np.newaxis, :]  # shape will be (1, 1, 2)
    output = np.sum(Score_Tensor * v_broadcasted, axis=-1)  # Sum along the last axis (axis=-1)
    return output
    
def Possible_Words(Board_State, word_list, Parameters):
    Greens, Yellows, Greys, Repeated, Not_Repeated = Board_State
    list = word_list[:Parameters['Play_wordle_with']]
    pattern = r'\b'
    counter = 0
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
    result = ' '.join(list)
    output = re.findall(pattern, result)
    invalids = set()
    for number in range(5):
        if Yellows[number]:
            for letter in Yellows[number]:
                for word in output:
                    if word[number] == letter:
                        invalids.add(word)
                    
    for word in output:
        for character in Not_Repeated:
            if word.count(character) >= 2:
                invalids.add(word)
        for character in Repeated:
            if word.count(character) < 2:
                invalids.add(word)
    output = [word for word in output if word not in invalids]
    return output

def Possible_Words_and_degeneracies(Board_State, word_list, Parameters):
    Available_Words = Possible_Words(Board_State, word_list, Parameters)
    Collection_of_Words = []
    for word in Available_Words:
        index = word_list.index(word)
        sample_word_letter = set()
        sample_word_letter_and_place = set()
        sample_degeneracy = 0 
        sample_multiplier = 0
        for i in range(5):
            sample_word_letter.add(word[i])
            sample_word_letter_and_place.add((word[i], i))
            for j in range(5):
                if j != i:
                    if word[j] == word[i]:
                        sample_degeneracy += 1
            if sample_degeneracy == 0:
                sample_multiplier = 1
            if sample_degeneracy == 2:
                sample_multiplier = Parameters['Degeneracy_Penalty_1']
            if sample_degeneracy == 4:
                sample_multiplier = Parameters['Degeneracy_Penalty_2']
            if sample_degeneracy >= 6:
                sample_multiplier = Parameters['Degeneracy_Penalty_3']
        Collection_of_Words.append([word, index, sample_multiplier])
    return Collection_of_Words

def Best_Choice_Word(Available_Word_Lists, Score_Array):
    best_total = -1
    best_word = 'placeholder'
    if len(Available_Word_Lists) == 0:
        best_word = 'no_choices'
    for column in Available_Word_Lists:
        degen = column[-1]
        first_index = column[1]
        total = sum(Score_Array[min(first_index, columns[1]), max(first_index, columns[1])] for columns in Available_Word_Lists)
        column.append(total * degen)
        if total * degen > best_total:
            best_total = total * degen
            best_word = column[0]
    return best_word
    
def find_duplicate_letters(word):
    seen_letters = set()
    duplicates = []
    
    for letter in word.lower():  # convert to lowercase
        if letter in seen_letters and letter not in duplicates:
            duplicates.append(letter)
        seen_letters.add(letter)
    return duplicates

def Update_Board(Guesses, Target_Word):
    greens = ['_', '_', '_', '_', '_']
    yellows = [[], [], [], [], []]
    greys = []
    known_repeated = []
    known_not_repeated = []
    target_repeated = []
    hashmap_of_target_word = {}
    target_letters = list(Target_Word)
    
    # Build a hashmap for the target word
    for letter in Target_Word:
        if letter in hashmap_of_target_word:
            hashmap_of_target_word[letter] += 1
        else:
            hashmap_of_target_word[letter] = 1
    
    # Identify repeated letters in the target word
    for letter, count in hashmap_of_target_word.items():
        if count > 1:
            target_repeated.append(letter)

    # Process each guess
    for word in Guesses:
        if len(word) != 5:
            continue  # Skip any invalid guesses
        for i in range(5):
            if word[i] == Target_Word[i]:
                greens[i] = word[i]
            elif word[i] in target_letters:
                if word[i] != Target_Word[i]:
                    yellows[i].append(word[i])
                if word[i] not in greens and word[i] not in [y for sublist in yellows for y in sublist]:
                    known_repeated.append(word[i])
            else:
                greys.append(word[i])
    duplicates = find_duplicate_letters(word)
    
    if duplicates: 
        for item in duplicates:
            if item in target_repeated: 
                known_repeated.append(item)
            else: 
                known_not_repeated.append(item)         
    # Remove duplicate gray letters
    greys = list(set(greys))
    return [greens, yellows, greys, known_repeated, known_not_repeated]

def Play_Wordle(Score_Array, Target_Word, First_Guess, Parameters, word_list):
# This function is designed to play a game of wordle from scratch. This involves it running through 
# the process of optimal word selection, define new state of game, repeat until solved. 
    Guesses = [First_Guess]
    Board = Update_Board(Guesses, Target_Word)
    Next_Guess = Guesses[-1]
    
    while Next_Guess != Target_Word and len(Guesses) < 8:
        Available_words = Possible_Words_and_degeneracies(Board, word_list, Parameters)
        Next_Guess = Best_Choice_Word(Available_words, Score_Array)
        
        if Next_Guess not in Guesses:
            Guesses.append(Next_Guess)
            Board = Update_Board(Guesses, Target_Word)
        else:
            Guesses.append('Forcefully Stopped')  # To prevent an infinite loop if the same guess is chosen again
            break
    return Guesses

def average_guesses_for_random_words(Score_Array, first_guess, Parameters, word_list, num_words=1000):
# Function to play Wordle with 100 random words and return the average length of guesses 
    Score_Array = Score_tensor_for_set_of_params(Score_Tensor, Parameters)
    random_words = random.sample(word_list[:Parameters['Play_wordle_with']], num_words)
    lengths = []
    
    for target_word in random_words:
        Game = Play_Wordle(Score_Array, target_word, first_guess, Parameters, word_list)
        lengths.append(len(Game))
       # print(f"Target Word: {target_word}, Guesses: {Game}")
    
    average_length = sum(lengths) / len(lengths)
    return average_length

# The final function to be made is the one for the task of optimisation. This will be done using 'skopt'
# This function needs to be a built in testing environment, where the only input taken is the parameters. 
param_space = [
    Real(2.5, 3.5, name='common_letter_same_index_bonus'),
    Real(0.7, 1,   name='duplicate_letter_penalty'),
    Real(0.6, 1,   name='double_duplicate_letter_penalty'),
    Real(0.4, 1,   name='more_degenerate')
]

# Define the objective function to be optimised
def opt_funct(common_letter_same_index_bonus, duplicate_letter_penalty, double_duplicate_letter_penalty,
            more_degenerate):
    Parameters = {'Play_wordle_with': 14855,                                # Sets the number of wordle words we play with (14855 = max)
                'Common_Letter': 1,                       # Points awarded for shared letter 
                'Common_Letter_Same_Index': common_letter_same_index_bonus, # Points awarded for shared letter, same index
                'Degeneracy_Penalty_1':duplicate_letter_penalty,            # Penalty for 2 times repeated letters
                'Degeneracy_Penalty_2':double_duplicate_letter_penalty,     # Penalty for 2 sets of repeated letters
                'Degeneracy_Penalty_3':more_degenerate,                     # Higher degeneracy penalty ()
                }
    average_length = average_guesses_for_random_words([], 'crane', Parameters, word_list)
    print(average_length)
    return average_length

@use_named_args(param_space)
def objective(**params):
    return opt_funct(**params)

result = gp_minimize(objective, param_space, n_calls=100, random_state=0, n_initial_points=10, n_jobs=1, verbose=True)
print(result)