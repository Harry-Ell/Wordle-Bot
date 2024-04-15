import random
import pandas as pd

class WordleGame:
    
    def __init__(self):
        self.word_list = pd.read_csv('https://raw.githubusercontent.com/tabatkins/wordle-list/main/words').values.flatten().tolist()
        self.target_word = self.pick_random_word().lower()
        self.results_history = []
        self.past_guesses = []
        self.next_guess = None
        self.grey_letters = []

    def check_guess(self, current_guess):
        self.past_guesses.append(current_guess)
        results = [''] * len(current_guess)
        target_letters = list(self.target_word)
        
        for i, guess_letter in enumerate(current_guess):
            if guess_letter == target_letters[i]:
                results[i] = "green"
            elif guess_letter in target_letters:
                results[i] = "yellow"
            else: 
                results[i] = "grey"
                self.grey_letters.append(guess_letter)
        
        self.results_history.append(results)

        return results

    def pick_random_word(self, exclude_word_list=None):
        #removing words to be excluded, if desired
        temp_word_list = self.word_list
        if exclude_word_list: 
            temp_word_list = list(set(self.word_list) - set(exclude_word_list))
        return random.choice(temp_word_list)
    

    def check_guess_against_previous_grey_letters(self,guess):
        for char in guess:
            if char in self.grey_letters:
                return True 
        return False 
            
        

    def take_input(self):
        while True:
            try:
                guess = str(input(f"Enter your Wordle Guess. Past guesses: {self.past_guesses}, Past results: {self.results_history}. Eliminated letters are: {self.grey_letters}.").lower())

                if len(guess) != len(self.target_word):
                    print("Invalid guess. Make sure your guess is 5 letters long.")
                
                if guess not in self.word_list:
                    print("Invalid guess. Word not in corpus.")
                
                if self.check_guess_against_previous_grey_letters(guess): 
                    print("Invalid guess. Make sure your guess doesn't use any previously eliminated characters")
                

                else:
                    self.next_guess = guess
                    print(f"You are guessing: {guess}")
                    break
            
            except KeyboardInterrupt:
                #use Ctrl+C to exit the program
                print("\nExiting...")
                raise

            except Exception as e:
                #some top notch exception handling 
                print("An error occurred:", e)
                continue


    def play_wordle(self):
        while True:
            self.take_input()
            results = self.check_guess(self.next_guess)
            print(f"Guess results are: {results}")
            if results == ["green"] * len(self.target_word):
                print(f"Congratulations, you won! The target word was indeed '{self.next_guess}'. You guessed it in {len(self.past_guesses)} guesses")
                return(len(self.past_guesses))
            

# Example usage. Use Ctrl+C to exit the game: 
if __name__ == "__main__":
    game = WordleGame()
    print(game.target_word)
    game.play_wordle()