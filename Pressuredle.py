import random
import pandas as pd 
import time 
from PIL import Image 

#Macro for time waiting between rounds
time_wait = 30

#Methods:
#Loading the Pressure monsters csv as a dataframe
def load_monsters(filename = 'monsters.csv'):
    try:
        monster_csv = pd.read_csv(filename) 
        monster_csv.set_index('Name:', inplace=True) 
    except FileNotFoundError:
        monster_csv = None 
    return monster_csv

#The below will be worked on whenever
#def load_images(folder_name = 'monster_images' )

# Select a random monster from the dataframe
def set_monster(dataframe): 
    return random.choice(dataframe.index) 

#Handles user input for difficulty setting, affects tries
def difficulty_setting(): 
    turn_amount = 0
    difficulty = input("Select difficulty (easy, medium, hard): ").lower()
    if difficulty == 'easy':
        turn_amount += 12
    elif difficulty == 'medium':
        turn_amount += 9
    elif difficulty == 'hard':
        turn_amount += 5
    else:
        print("Invalid choice, defaulting to medium.")
        turn_amount += 9
    return turn_amount

#Displays the guessed monster's attributes and compares them to the selected monster
def display_monster_info(guess, select, dataframe): 
    guess_attributes = dataframe.loc[guess] 
    select_attributes = dataframe.loc[select] 

    for category in dataframe.columns:
        guess_value = guess_attributes[category]
        secret_value = select_attributes[category]
        if guess_value == secret_value:
            print(f"{category:<12} | {guess_value:<15} ✅")
        else:
            print(f"{category:<12} | {guess_value:<15} ❌")
    print("-" * 50)

#Compares the guessed monster to the selected monster, dictates wins
def compare_guess(guess, select, dataframe):
      if guess == select:
            print(f"Congratulations! You've guessed the monster: {select}")
            return True
      return False

#Countdown timer for next round
def countdown(seconds):
    for i in range(seconds, 0, -1):
        print(f"Next round starts in {i} seconds...", end='\r')
        time.sleep(1)
    print(" " * 30, end='\r')

#Game loop, handles user guesses and attempts
def game_loop(dataframe, max_attempts, chosen_monster, guessed_list=None): 
    attempts = 0
    while attempts < max_attempts:
        guess = input("Enter your guess for the monster's name: ").strip()
        if guess.lower() == 'q' or guess.lower() == "quit":
            print("Thanks for playing! Goodbye.")
            return 'quit'
        elif guess.lower() not in {name.lower() for name in dataframe.index}:
            print(f"{guess} is not a valid monster name. Please try again.")
            continue
        proper_case_guess = dataframe.index[dataframe.index.str.lower() == guess.lower()][0] 
        if proper_case_guess in guessed_list:
            print(f"You've already guessed {guess}. Try a different monster.")
            continue
        guessed_list.append(proper_case_guess) 
        display_monster_info(proper_case_guess, chosen_monster, dataframe)
        if compare_guess(proper_case_guess, chosen_monster, dataframe):
            return 'win'
        if(attempts == max_attempts):
            print(f"\n Sorry, you've used all your attempts. The monster was: {chosen_monster}")
        attempts += 1
    return 'loss'
        

#Main function to start the game
def main(): 
    print("NOTE: Pressure and all items associated with it are by Zeal and his devteam\n")
    monster_list = load_monsters()
    if monster_list is None:
        return
    game_complete = False 
    monster_names = {name.lower() for name in monster_list.index}
    print("Welcome to Pressuredle!\n")
    difficulty = difficulty_setting()
    selected_monster = set_monster(monster_list)
    guessed_monsters = [ ]
    #print(selected_monster)
    game_result = game_loop(monster_list, difficulty, selected_monster, guessed_monsters) 
    if game_result == 'win':
        print("You won the game!")
        display_monster_info(selected_monster, selected_monster, monster_list) 
        countdown(time_wait) 
    elif game_result == 'loss':
        print(f"You lost the game. The correct monster was: {selected_monster}")
        display_monster_info(selected_monster, selected_monster, monster_list) 
        countdown(time_wait)
    elif game_result == 'quit':
        print("Game exited.") 
        pass 
            
if __name__ == "__main__":
    main()
