# Wordle Bot
The most successful wordle bots use an information theory approach, selecting their next best guess based on what groups the subsequent possible words into as many distinct sets as possible. While this is the most effective method, it's very different from how a person plays. The goal here was to make a bot that would play wordle the same way a person would. 
## Overview of Final Bot
- **Notebook**: 'Final Bot/WordleBot.ipynb'
- **Function**: 'WordleBot'
- **Input**: Current state of the board
- **Output**: Best guess for the next word

### Final Algorithm Description
In the notebook 'Final Bot/WordleBot.ipynb' the function 'WordleBot' takes as an input the current state of the board, and returns its best guess for the next word. The algorithm for choosing this word from a list of allowed words is based on how a human may attempt to play wordle. There is a points system, where the bot ranks all possible solutions in terms of how similar they are to other allowed solutions. It then chooses the word which is most similar to others in the set, in the same way a person may take a 'frequentist approach' of picking words with common letters. For example, if the second letter is a h, a human would be inclined to pick words that start with a t or an s, as most words would follow one of those two sequences. 

## Overview of Training Final Bot
- **Script**: 'Optimisation Scripts/Modular_Bot.py'
- **Input**: Set of points/ penalties for scoring words and deciding the best choice word
- **Output**: Average score after playing 1000 games of Wordle
- **Average Score**: 4.38 (backtest on 1000 games with starting word 'crane')
### Training Algorithm Description
The scoring system rewards words that share common letters, and common letters in the same location. It penalises words with degeneracies, e.g., most human players would be hard-pressed to play 'rarer', as a triple repeated letter always seems a waste. The exact values of each of these points (found in the 'Parameters' hashmap) given and degeneracy penalties were decided by running Bayesian Optimisation for 100 iterations, with each iteration playing 1000 games of wordle. This is handled in 'Optimisation Scripts/Modular_Bot.py'. This output forms our 'cost' for a given set of parameters, which is then minimised by Bayesian Optimisation from skopt.

## Wordle Environment
'Wordle Application/wordle_environment.py' is a Wordle environment where you can play as much Wordle as you want. 
## Possible Avenues for  Further Development
Currently, the NYT Wordle allows around 15000 input words and draws solutions from these based on popular words, no plurals etc. This reduces the current allowed set of solutions to around 2000. When tested against words in the 15000 large set, this bot gets an average score of 4.38. This is marginally worse than a 'good' human wordle player, who may average around 4. A possible avenue for further development is incorporating some knowledge of relative word frequencies in English, and then retesting with this knowledge incorporated by the bot and testing against the solution set, which is around 13% the size of the current set from which it picks its guesses. 


