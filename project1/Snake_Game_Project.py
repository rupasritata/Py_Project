import tkinter as tk
import random
import os

# --- Game constants ---
WIDTH = 800
HEIGHT = 600
CELL_SIZE = 20

SNAKE_COLOR = "lime"
SNAKE_HEAD_COLOR = "green"
FOOD_COLOR = "red"
BG_COLOR = "black"
OBSTACLE_COLOR = "gray"

INITIAL_SPEED = 140  # milliseconds
SPEED_INCREMENT = 3  # faster after each food
MIN_SPEED = 40       # cap maximum speed

LEVEL_SCORE_STEP = 5  # every 5 points = new level
HIGH_SCORE_FILE = "snake_highscore.txt"


class SnakeGame(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Snake Game 🐍 - Levels, Pause & High Score")
        self.geometry("800x600")   # <-- Increase this as you like
        self.resizable(False, False)

        self.high_score = 0
        self.load_high_score()

        # States
        self.game_running = False
        self.paused = False
        self.after_id = None

        self.create_menu_screen()
        self.create_game_screen()

        # Show menu first
        self.show_menu()

        # Key bindings
        self.bind("<KeyPress>", self.on_key_press)

        # Close handler
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    # =============== HIGH SCORE ===============

    def load_high_score(self):
        if os.path.exists(HIGH_SCORE_FILE):
            try:
                with open(HIGH_SCORE_FILE, "r") as f:
                    self.high_score = int(f.read().strip() or "0")
            except Exception:
                self.high_score = 0

    def save_high_score(self):
        try:
            with open(HIGH_SCORE_FILE, "w") as f:
                f.write(str(self.high_score))
        except Exception:
            pass

    # =============== SCREENS ===============

    def create_menu_screen(self):
        self.menu_frame = tk.Frame(self, padx=20, pady=20)

        title = tk.Label(
            self.menu_frame,
            text="Snake Game",
            font=("Arial", 28, "bold"),
        )
        title.pack(pady=10)

        hs_label = tk.Label(
            self.menu_frame,
            text=f"High Score: {self.high_score}",
            font=("Arial", 14),
        )
        hs_label.pack(pady=5)
        self.menu_high_label = hs_label

        info = tk.Label(
            self.menu_frame,
            text="Controls:\nArrow Keys to move\nP to Pause/Resume",
            font=("Arial", 12),
            justify="center",
        )
        info.pack(pady=10)

        start_btn = tk.Button(
            self.menu_frame,
            text="Start Game",
            font=("Arial", 12),
            width=15,
            command=self.start_from_menu,
        )
        start_btn.pack(pady=5)

        quit_btn = tk.Button(
            self.menu_frame,
            text="Quit",
            font=("Arial", 12),
            width=15,
            command=self.destroy,
        )
        quit_btn.pack(pady=5)

    def create_game_screen(self):
        self.game_frame = tk.Frame(self)

        # Top bar: score + level
        self.score_label = tk.Label(
            self.game_frame,
            text="Score: 0   High: 0   Level: 1",
            font=("Arial", 14),
        )
        self.score_label.pack(pady=5)

        # Canvas
        self.canvas = tk.Canvas(
            self.game_frame,
            width=WIDTH,
            height=HEIGHT,
            bg=BG_COLOR,
            highlightthickness=0,
        )
        self.canvas.pack()

        # Bottom buttons
        btn_frame = tk.Frame(self.game_frame)
        btn_frame.pack(pady=5)

        self.pause_label = tk.Label(
            self.game_frame,
            text="",
            font=("Arial", 14, "bold"),
            fg="yellow",
            bg="black",
        )

        restart_btn = tk.Button(
            btn_frame, text="Play Again", command=self.restart_game
        )
        restart_btn.pack(side=tk.LEFT, padx=5)

        quit_btn = tk.Button(
            btn_frame, text="Quit to Menu", command=self.return_to_menu
        )
        quit_btn.pack(side=tk.LEFT, padx=5)

    def show_menu(self):
        self.game_frame.pack_forget()
        self.menu_high_label.config(text=f"High Score: {self.high_score}")
        self.menu_frame.pack()

    def show_game(self):
        self.menu_frame.pack_forget()
        self.game_frame.pack()

    def start_from_menu(self):
        self.show_game()
        self.start_game()

    # =============== GAME LIFECYCLE ===============

    def start_game(self):
        # Reset game state
        if self.after_id:
            self.after_cancel(self.after_id)
        self.canvas.delete("all")
        self.paused = False
        self.pause_label.place_forget()

        self.score = 0
        self.level = 1
        self.current_speed = INITIAL_SPEED
        self.update_score_label()

        # Snake initial position
        start_x = WIDTH // 2
        start_y = HEIGHT // 2
        self.snake = [
            (start_x, start_y),
            (start_x - CELL_SIZE, start_y),
            (start_x - 2 * CELL_SIZE, start_y),
        ]
        self.direction = "Right"
        self.next_direction = "Right"

        # Obstacles & food
        self.obstacles = []
        self.spawn_initial_obstacles()
        self.draw_obstacles()
        self.draw_snake()
        self.spawn_food()

        self.game_running = True
        self.game_loop()

    def restart_game(self):
        self.start_game()

    def return_to_menu(self):
        # Stop game + go back
        if self.after_id:
            self.after_cancel(self.after_id)
        self.game_running = False
        self.paused = False
        self.pause_label.place_forget()
        self.show_menu()

    # =============== DRAWING ===============

    def draw_snake(self):
        self.canvas.delete("snake")
        for i, (x, y) in enumerate(self.snake):
            color = SNAKE_HEAD_COLOR if i == 0 else SNAKE_COLOR
            self.canvas.create_rectangle(
                x,
                y,
                x + CELL_SIZE,
                y + CELL_SIZE,
                fill=color,
                outline="",
                tags="snake",
            )

    def spawn_food(self):
        self.canvas.delete("food")
        cols = WIDTH // CELL_SIZE
        rows = HEIGHT // CELL_SIZE

        while True:
            fx = random.randint(0, cols - 1) * CELL_SIZE
            fy = random.randint(0, rows - 1) * CELL_SIZE
            if (fx, fy) not in self.snake and (fx, fy) not in self.obstacles:
                break

        self.food = (fx, fy)
        self.canvas.create_oval(
            fx,
            fy,
            fx + CELL_SIZE,
            fy + CELL_SIZE,
            fill=FOOD_COLOR,
            outline="",
            tags="food",
        )

    def draw_obstacles(self):
        self.canvas.delete("obstacle")
        for (x, y) in self.obstacles:
            self.canvas.create_rectangle(
                x,
                y,
                x + CELL_SIZE,
                y + CELL_SIZE,
                fill=OBSTACLE_COLOR,
                outline="",
                tags="obstacle",
            )

    def spawn_initial_obstacles(self):
        self.obstacles.clear()
        # base number of obstacles for level 1
        self.add_obstacles_for_level()

    def add_obstacles_for_level(self):
        """
        Add some obstacles depending on level.
        Level 1: few, more for higher levels.
        """
        cols = WIDTH // CELL_SIZE
        rows = HEIGHT // CELL_SIZE

        # each level adds 2 obstacles
        target_count = self.level * 2
        while len(self.obstacles) < target_count:
            ox = random.randint(0, cols - 1) * CELL_SIZE
            oy = random.randint(0, rows - 1) * CELL_SIZE
            if (ox, oy) in self.snake or (ox, oy) == getattr(self, "food", None):
                continue
            if (ox, oy) in self.obstacles:
                continue
            self.obstacles.append((ox, oy))

    def update_score_label(self):
        self.score_label.config(
            text=f"Score: {self.score}   High: {self.high_score}   Level: {self.level}"
        )

    # =============== GAME LOOP ===============

    def game_loop(self):
        if not self.game_running:
            return

        if self.paused:
            # While paused, just reschedule the loop and do nothing
            self.after_id = self.after(100, self.game_loop)
            return

        # Update direction from buffered key
        self.direction = self.next_direction

        head_x, head_y = self.snake[0]

        if self.direction == "Up":
            head_y -= CELL_SIZE
        elif self.direction == "Down":
            head_y += CELL_SIZE
        elif self.direction == "Left":
            head_x -= CELL_SIZE
        elif self.direction == "Right":
            head_x += CELL_SIZE

        new_head = (head_x, head_y)

        # Collision check
        if self.check_collision(new_head):
            self.game_over()
            return

        # Move snake
        self.snake.insert(0, new_head)

        # Food eaten?
        if new_head == self.food:
            self.score += 1

            # Level up?
            new_level = 1 + self.score // LEVEL_SCORE_STEP
            if new_level > self.level:
                self.level = new_level
                self.add_obstacles_for_level()
                self.draw_obstacles()
                # brief "Level Up" text
                self.show_level_up()

            # update high score
            if self.score > self.high_score:
                self.high_score = self.score
                self.save_high_score()

            self.update_score_label()
            self.spawn_food()

            # Increase speed
            self.current_speed = max(MIN_SPEED, self.current_speed - SPEED_INCREMENT)
        else:
            # normal move, remove tail
            self.snake.pop()

        self.draw_snake()

        # Schedule next step
        self.after_id = self.after(self.current_speed, self.game_loop)

    def show_level_up(self):
        msg_id = self.canvas.create_text(
            WIDTH // 2,
            30,
            text=f"LEVEL {self.level}!",
            fill="yellow",
            font=("Arial", 20, "bold"),
        )
        # remove after 800ms
        self.after(800, lambda: self.canvas.delete(msg_id))

    def check_collision(self, head):
        x, y = head
        # Wall
        if x < 0 or x >= WIDTH or y < 0 or y >= HEIGHT:
            return True
        # Self
        if head in self.snake:
            return True
        # Obstacles
        if head in self.obstacles:
            return True
        return False

    # =============== INPUT HANDLING ===============

    def on_key_press(self, event):
        key = event.keysym

        # Pause toggle
        if key.lower() == "p":
            if self.game_running:
                self.toggle_pause()
            return

        # Movement keys only if game running and not paused
        if not self.game_running or self.paused:
            return

        if key == "Up" and self.direction != "Down":
            self.next_direction = "Up"
        elif key == "Down" and self.direction != "Up":
            self.next_direction = "Down"
        elif key == "Left" and self.direction != "Right":
            self.next_direction = "Left"
        elif key == "Right" and self.direction != "Left":
            self.next_direction = "Right"

    def toggle_pause(self):
        self.paused = not self.paused
        if self.paused:
            # show label across the canvas top
            self.pause_label.config(text="PAUSED")
            self.pause_label.place(x=WIDTH // 2 - 40, y=HEIGHT // 2 - 15)
        else:
            self.pause_label.place_forget()

    # =============== GAME OVER ===============

    def game_over(self):
        self.game_running = False
        self.paused = False
        if self.after_id:
            self.after_cancel(self.after_id)

        self.canvas.create_text(
            WIDTH // 2,
            HEIGHT // 2 - 20,
            text="GAME OVER",
            fill="white",
            font=("Arial", 32, "bold"),
            tags="gameover",
        )
        self.canvas.create_text(
            WIDTH // 2,
            HEIGHT // 2 + 20,
            text=f"Final Score: {self.score}",
            fill="white",
            font=("Arial", 20),
            tags="gameover",
        )

    # =============== CLOSE ===============

    def on_close(self):
        # make sure high score is saved
        self.save_high_score()
        if self.after_id:
            self.after_cancel(self.after_id)
        self.destroy()


if __name__ == "__main__":
    game = SnakeGame()
    game.mainloop()
