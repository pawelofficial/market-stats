import tkinter as tk
import random

class NBackGame:
    def __init__(self, master, n, grid_size, time_step, total_rounds):
        self.master = master
        self.n = n
        self.grid_size = grid_size
        self.time_step = time_step
        self.positions = []
        self.colors = []
        self.score = {'position': 0, 'color': 0}
        self.errors = 0  # Initialize error counter
        self.total_score = 0
        self.total_rounds = total_rounds
        self.current_round = 0
        self.is_waiting_for_input = False
        self.user_input = {'position': False, 'color': False}

        self.color_options = ['red', 'green', 'blue', 'yellow', 'orange', 'purple']
        self.create_widgets()
        self.master.bind('<Key>', self.key_pressed)
        self.next_step()

    def create_widgets(self):
        # Main frames
        self.left_frame = tk.Frame(self.master)
        self.left_frame.grid(row=0, column=0, padx=10)

        self.center_frame = tk.Frame(self.master)
        self.center_frame.grid(row=0, column=1)

        self.right_frame = tk.Frame(self.master)
        self.right_frame.grid(row=0, column=2, padx=10)

        # Left Frame - Color Score and Indicator
        self.color_score_label = tk.Label(self.left_frame, text="Color Score: 0", font=('Arial', 14))
        self.color_score_label.pack(pady=10)

        self.color_indicator = tk.Label(self.left_frame, text="Color Match", font=('Arial', 12), width=15, height=2, bg='grey')
        self.color_indicator.pack(pady=5)

        # Center Frame - Grid
        self.cells = {}
        for row in range(self.grid_size):
            for col in range(self.grid_size):
                frame = tk.Frame(self.center_frame, width=100, height=100, bg='white',
                                 highlightbackground="black", highlightthickness=1)
                frame.grid(row=row, column=col)
                self.cells[(row, col)] = frame

        # Status Label below Grid
        self.status_label = tk.Label(self.center_frame, text="Press 'p' for position match, 'c' for color match.", font=('Arial', 12))
        self.status_label.grid(row=self.grid_size, column=0, columnspan=self.grid_size, pady=10)

        # Right Frame - Position Score and Indicator
        self.position_score_label = tk.Label(self.right_frame, text="Position Score: 0", font=('Arial', 14))
        self.position_score_label.pack(pady=10)

        self.position_indicator = tk.Label(self.right_frame, text="Position Match", font=('Arial', 12), width=15, height=2, bg='grey')
        self.position_indicator.pack(pady=5)

        # Total Score Label
        self.total_score_label = tk.Label(self.master, text="Total Score: 0", font=('Arial', 14))
        self.total_score_label.grid(row=1, column=0, columnspan=3, pady=5)

        # Total Errors Label
        self.total_errors_label = tk.Label(self.master, text="Total Errors: 0", font=('Arial', 14))
        self.total_errors_label.grid(row=2, column=0, columnspan=3, pady=5)

    def next_step(self):
        if self.current_round >= self.total_rounds:
            self.status_label.config(text=f"Game Over! Final Score: {self.total_score}, Errors: {self.errors}")
            return

        # Reset indicators and user input
        self.master.after(500, self.reset_indicators)

        if self.current_round > 0:
            # After the time step, check for missed matches
            self.check_missed_matches()

        # Clear previous highlights
        for cell in self.cells.values():
            cell.config(bg='white')

        # Generate new position and color
        row = random.randint(0, self.grid_size - 1)
        col = random.randint(0, self.grid_size - 1)
        color = random.choice(self.color_options)

        # Highlight the new cell
        self.cells[(row, col)].config(bg=color)

        # Store the position and color
        self.positions.append((row, col))
        self.colors.append(color)

        self.current_round += 1
        self.is_waiting_for_input = True

        # Schedule next update
        self.master.after(self.time_step, self.next_step)

    def reset_indicators(self):
        self.position_indicator.config(bg='grey')
        self.color_indicator.config(bg='grey')
        self.user_input = {'position': False, 'color': False}

    def key_pressed(self, event):
        if not self.is_waiting_for_input:
            return

        key = event.char.lower()
        if key == 'p' and not self.user_input['position']:
            self.user_input['position'] = True
            self.check_match('position')
        elif key == 'c' and not self.user_input['color']:
            self.user_input['color'] = True
            self.check_match('color')

    def check_match(self, match_type):
        if len(self.positions) <= self.n:
            # Not enough history to compare
            return

        if match_type == 'position':
            current = self.positions[-1]
            previous = self.positions[-(self.n + 1)]
            indicator = self.position_indicator
            score_label = self.position_score_label
        elif match_type == 'color':
            current = self.colors[-1]
            previous = self.colors[-(self.n + 1)]
            indicator = self.color_indicator
            score_label = self.color_score_label

        if current == previous:
            self.score[match_type] += 1
            self.total_score += 1
            indicator.config(bg='green')  # Correct answer indicator
        else:
            self.errors += 1  # Increment errors for incorrect input
            indicator.config(bg='red')  # Incorrect answer indicator

        # Update individual and total scores
        score_label.config(text=f"{match_type.capitalize()} Score: {self.score[match_type]}")
        self.update_score()

    def check_missed_matches(self):
        if len(self.positions) <= self.n:
            return

        # Check for missed position match
        position_match = self.positions[-1] == self.positions[-(self.n + 1)]
        if position_match and not self.user_input['position']:
            # Missed a position match
            self.errors += 1  # Increment errors for missed match
            self.position_indicator.config(bg='red')  # Missed match indicator

        # Check for missed color match
        color_match = self.colors[-1] == self.colors[-(self.n + 1)]
        if color_match and not self.user_input['color']:
            # Missed a color match
            self.errors += 1  # Increment errors for missed match
            self.color_indicator.config(bg='red')  # Missed match indicator

        self.update_score()

    def update_score(self):
        self.total_score_label.config(text=f"Total Score: {self.total_score}")
        self.total_errors_label.config(text=f"Total Errors: {self.errors}")

def main():
    root = tk.Tk()
    root.title("n-Back Game")
    time_step = 2000
    grid_size = 3
    n = 1
    total_rounds = 100

    game = NBackGame(root, n, grid_size, time_step, total_rounds)
    root.mainloop()

if __name__ == "__main__":
    main()
