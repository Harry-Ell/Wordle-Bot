import pandas as pd 
import numpy as np 
import re
import random 
from pathlib import Path

path1 = Path('WordleInputWords.txt')
path2 = Path('WordleSolutionWords.txt')

df1 = path1.read_text()
df2 = path2.read_text()

word_list = df1.splitlines()
sol_list  = df2.splitlines()

# Parameters for scoring
Parameters = {'Play_wordle_with': 100,    # Sets the number of wordle words we play with (14850 = max)
              'Common_Letter': 1,           # Points awarded for shared letter 
              'Common_Letter_Same_Index': 3,# Points awarded for shared letter, same index
              'Degeneracy_Penalty_1':0.9,   # Penalty for 2 times repeated letters
              'Degeneracy_Penalty_2':0.8,   # Penalty for 2 sets of repeated letters
              'Degeneracy_Penalty_3':0.7,   # Penalty for 3 times repeated letter
              'Degeneracy_Penalty_4':0.6,   # Higher degeneracy penalty ()
              }


def Load_Words_and_Populate_Score_Array(Parameters, word_list):
# Purpose of function: define collection of allowed words, and create an array from which scores (i.e.
# ranking of word similarities) can be drawn. 
# This function should only be ran once per usage of a set of params
    trimmed_word_list = word_list[:Parameters['Play_wordle_with']] 
    n = len(word_list)
    nn = len(trimmed_word_list)
    Scores = np.zeros((nn, nn))
    for i in range(nn): 
        sample = word_list[i]
        sample_word_letter = set(sample)
        sample_word_letter_and_place = {(sample[k], k) for k in range(5)}
        for j in range(i + 1, nn):
            working_word = word_list[j]
            working_word_letter = set(working_word)
            working_word_letter_and_place = {(working_word[l], l) for l in range(5)}
            common_letter = working_word_letter.intersection(sample_word_letter)
            common_letter_and_place = working_word_letter_and_place.intersection(sample_word_letter_and_place)
            sample_score = len(common_letter) * Parameters['Common_Letter'] + len(common_letter_and_place) * Parameters['Common_Letter_Same_Index']
            Scores[i, j] = sample_score
    return Scores 
         
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
            if sample_degeneracy == 6:
                sample_multiplier = Parameters['Degeneracy_Penalty_3']
            if sample_degeneracy >= 6:
                sample_multiplier = Parameters['Degeneracy_Penalty_4']
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

def average_guesses_for_random_words(Score_Array, first_guess, Parameters, word_list, num_words=100):
# Function to play Wordle with 100 random words and return the average length of guesses 
    Score_Array = Load_Words_and_Populate_Score_Array(Parameters, word_list)
    random_words = random.sample(word_list[:Parameters['Play_wordle_with']], num_words)
    lengths = []
    
    for target_word in random_words:
        Game = Play_Wordle(Score_Array, target_word, first_guess, Parameters, word_list)
        lengths.append(len(Game))
        print(f"Target Word: {target_word}, Guesses: {Game}")
    
    average_length = sum(lengths) / len(lengths)
    return average_length
average_length = average_guesses_for_random_words([], 'tares', Parameters, word_list)
print(f"Average number of guesses: {average_length}")