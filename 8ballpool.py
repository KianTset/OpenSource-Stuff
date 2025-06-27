import tkinter as tk
import sys
import math
import random
import time

# --- Game Constants ---
# Updated resolution and scaled dependent constants
SCREEN_WIDTH, SCREEN_HEIGHT = 1600, 900
TABLE_COLOR = "#006400"  # A nice dark green
CUSHION_COLOR = "#663300"
BALL_RADIUS = 15  # Slightly larger for the bigger screen
POCKET_RADIUS = 30 # Scaled up pocket size
FRICTION = 0.988
STOP_THRESHOLD = 0.08
TABLE_MARGIN = 75 # Increased margin for the larger screen

# Table dimensions
TABLE_RECT = (TABLE_MARGIN, TABLE_MARGIN, SCREEN_WIDTH - TABLE_MARGIN, SCREEN_HEIGHT - TABLE_MARGIN)

# Pocket positions
POCKETS = [
    (TABLE_MARGIN, TABLE_MARGIN), (SCREEN_WIDTH / 2, TABLE_MARGIN - 10), (SCREEN_WIDTH - TABLE_MARGIN, TABLE_MARGIN),
    (TABLE_MARGIN, SCREEN_HEIGHT - TABLE_MARGIN), (SCREEN_WIDTH / 2, SCREEN_HEIGHT - TABLE_MARGIN + 10), (SCREEN_WIDTH - TABLE_MARGIN, SCREEN_HEIGHT - TABLE_MARGIN)
]

# Ball colors and types
BALL_COLORS = {
    'cue': 'white', '1': '#ffcc00', '2': '#0000cc', '3': '#ff0000', '4': '#4b0082',
    '5': '#ff8000', '6': '#006600', '7': '#800000', '8': 'black', '9': '#ffcc00',
    '10': '#0000cc', '11': '#ff0000', '12': '#4b0082', '13': '#ff8000', '14': '#006600', '15': '#800000'
}
BALL_TYPES = {'solid': list(range(1, 8)), 'stripe': list(range(9, 16))}

class Ball:
    """Represents a single billiard ball."""
    def __init__(self, x, y, number, is_cue=False):
        self.x, self.y = x, y
        self.vx, self.vy = 0, 0
        self.number = number
        self.is_cue = is_cue
        self.is_pocketed = False
        self.radius = BALL_RADIUS
        
        # Canvas item IDs for efficient updating
        self.canvas_id = None
        self.stripe_id = None
        self.text_id = None

    def get_type(self):
        if self.is_cue: return 'cue'
        if self.number == 8: return '8-ball'
        if self.number in BALL_TYPES['solid']: return 'solid'
        return 'stripe'

    def update(self):
        """Update ball position and apply friction."""
        if not self.is_pocketed:
            self.x += self.vx
            self.y += self.vy
            self.vx *= FRICTION
            self.vy *= FRICTION
            if math.hypot(self.vx, self.vy) < STOP_THRESHOLD:
                self.vx, self.vy = 0, 0

    def create_canvas_items(self, canvas):
        """Creates the ball's visual representation on the canvas once."""
        x1, y1 = self.x - self.radius, self.y - self.radius
        x2, y2 = self.x + self.radius, self.y + self.radius
        
        self.canvas_id = canvas.create_oval(x1, y1, x2, y2, fill=BALL_COLORS[str(self.number)], outline='black', width=1)
        
        if self.get_type() == 'stripe':
            stripe_height = 6
            self.stripe_id = canvas.create_rectangle(x1, self.y - stripe_height, x2, self.y + stripe_height, fill='white', outline='')
        
        if not self.is_cue:
            text_color = 'white' if self.get_type() == '8-ball' else 'black'
            self.text_id = canvas.create_text(self.x, self.y, text=str(self.number), fill=text_color, font=('Arial', 10, 'bold'))

    def update_drawing(self, canvas):
        """Efficiently moves or hides the ball on the canvas."""
        if self.is_pocketed:
            if self.canvas_id: canvas.itemconfig(self.canvas_id, state='hidden')
            if self.stripe_id: canvas.itemconfig(self.stripe_id, state='hidden')
            if self.text_id: canvas.itemconfig(self.text_id, state='hidden')
            return

        if canvas.itemcget(self.canvas_id, 'state') == 'hidden':
            canvas.itemconfig(self.canvas_id, state='normal')
            if self.stripe_id: canvas.itemconfig(self.stripe_id, state='normal')
            if self.text_id: canvas.itemconfig(self.text_id, state='normal')

        x1, y1 = self.x - self.radius, self.y - self.radius
        x2, y2 = self.x + self.radius, self.y + self.radius
        canvas.coords(self.canvas_id, x1, y1, x2, y2)
        if self.stripe_id:
            stripe_height = 6
            canvas.coords(self.stripe_id, x1, self.y - stripe_height, x2, self.y + stripe_height)
        if self.text_id:
            canvas.coords(self.text_id, self.x, self.y)


class PoolGame:
    def __init__(self, root):
        self.root = root
        self.root.title("8 Ball Pool (Fullscreen)")
        
        self.canvas = tk.Canvas(root, width=SCREEN_WIDTH, height=SCREEN_HEIGHT, bg="#323232", highlightthickness=0)
        self.canvas.pack()

        # Bind mouse events
        self.canvas.bind("<Motion>", self.on_mouse_move)
        self.canvas.bind("<ButtonPress-1>", self.on_mouse_down)
        self.canvas.bind("<ButtonRelease-1>", self.on_mouse_up)
        
        self.mouse_pos = (0, 0)
        self.is_mouse_pressed = False
        
        self.draw_table()
        self.create_ui_elements()
        self.setup_game()
        self.update_game()

    def draw_table(self):
        """Draws the static table elements once."""
        self.canvas.create_rectangle(TABLE_MARGIN - 25, TABLE_MARGIN - 25, SCREEN_WIDTH - TABLE_MARGIN + 25, SCREEN_HEIGHT - TABLE_MARGIN + 25, fill=CUSHION_COLOR, outline=CUSHION_COLOR)
        self.canvas.create_rectangle(TABLE_RECT, fill=TABLE_COLOR)
        for p in POCKETS:
            self.canvas.create_oval(p[0]-POCKET_RADIUS, p[1]-POCKET_RADIUS, p[0]+POCKET_RADIUS, p[1]+POCKET_RADIUS, fill='black')

    def create_ui_elements(self):
        """Creates the UI elements that will be updated, not recreated."""
        self.aim_line_id = self.canvas.create_line(0, 0, 0, 0, fill='white', dash=(5, 5), state='hidden')
        self.cue_stick_id = self.canvas.create_line(0, 0, 0, 0, fill=CUSHION_COLOR, width=10, state='hidden')
        self.power_bar_bg_id = self.canvas.create_rectangle(SCREEN_WIDTH/2 - 100, SCREEN_HEIGHT - 40, SCREEN_WIDTH/2 + 100, SCREEN_HEIGHT - 20, outline='white', state='hidden')
        self.power_bar_id = self.canvas.create_rectangle(SCREEN_WIDTH/2 - 100, SCREEN_HEIGHT - 40, SCREEN_WIDTH/2 - 100, SCREEN_HEIGHT - 20, fill='#ff4136', state='hidden')
        self.player_turn_text_id = self.canvas.create_text(40, SCREEN_HEIGHT - 35, text="", fill='white', font=('Arial', 18), anchor='w')
        self.player_target_text_id = self.canvas.create_text(300, SCREEN_HEIGHT - 35, text="", fill='white', font=('Arial', 18), anchor='w')
        self.message_text_id = self.canvas.create_text(SCREEN_WIDTH/2, 40, text="", fill='#ffcc00', font=('Arial', 24, 'bold'))

    def setup_game(self):
        """Initialize or reset all game variables and balls."""
        if hasattr(self, 'balls'):
            for ball in self.balls:
                if ball.canvas_id: self.canvas.delete(ball.canvas_id)
                if ball.stripe_id: self.canvas.delete(ball.stripe_id)
                if ball.text_id: self.canvas.delete(ball.text_id)

        self.balls, self.cue_ball = self.setup_balls_on_table()
        
        for ball in self.balls:
            ball.create_canvas_items(self.canvas)

        self.game_state = 'aiming'
        self.current_player = 1
        self.player_targets = {1: 'open', 2: 'open'}
        self.first_contact = None
        self.pocketed_this_turn = []
        self.message = "Break Shot! Player 1"

    def setup_balls_on_table(self):
        """Create and position all balls in the rack."""
        balls = []
        cue_x = TABLE_RECT[0] + (TABLE_RECT[2] - TABLE_RECT[0]) * 0.25
        cue_y = (TABLE_RECT[1] + TABLE_RECT[3]) / 2
        cue_ball = Ball(cue_x, cue_y, 'cue', is_cue=True)
        balls.append(cue_ball)
        
        ball_numbers = list(range(1, 8)) + list(range(9, 16))
        random.shuffle(ball_numbers)
        ball_numbers.insert(4, 8) # 8-ball in the middle
        
        triangle_x = TABLE_RECT[0] + (TABLE_RECT[2] - TABLE_RECT[0]) * 0.75
        triangle_y = (TABLE_RECT[1] + TABLE_RECT[3]) / 2
        
        ball_idx = 0
        for row in range(5):
            for col in range(row + 1):
                x = triangle_x + row * (BALL_RADIUS * 1.732)
                y = triangle_y + col * (BALL_RADIUS * 2) - row * BALL_RADIUS
                if ball_idx < len(ball_numbers):
                    balls.append(Ball(x, y, ball_numbers[ball_idx]))
                    ball_idx += 1
        return balls, cue_ball

    def update_game(self):
        """The main game loop, called repeatedly by root.after()."""
        if self.game_state == 'aiming':
            dx = self.mouse_pos[0] - self.cue_ball.x
            dy = self.mouse_pos[1] - self.cue_ball.y
            if dx == 0 and dy == 0:
                self.angle = 0
            else:
                self.angle = math.atan2(dy, dx)
            
        elif self.game_state == 'charging':
            if not self.is_mouse_pressed:
                power_duration = time.time() - self.power_start_time
                power = min(power_duration * 60, 150)
                
                self.cue_ball.vx = math.cos(self.angle) * power * 0.2
                self.cue_ball.vy = math.sin(self.angle) * power * 0.2
                
                self.game_state = 'simulating'
                self.first_contact = None
                self.pocketed_this_turn = []
                self.message = ""

        elif self.game_state == 'simulating':
            is_moving = False
            for _ in range(4): 
                for ball in self.balls:
                    ball.update()
                    if ball.vx != 0 or ball.vy != 0:
                        is_moving = True
                self.handle_collisions()

            if not is_moving:
                self.handle_turn_end()

        self.update_all_drawings()
        self.root.after(16, self.update_game)

    def handle_collisions(self):
        # Ball-ball
        for i in range(len(self.balls)):
            for j in range(i + 1, len(self.balls)):
                b1, b2 = self.balls[i], self.balls[j]
                if b1.is_pocketed or b2.is_pocketed: continue
                dx, dy = b2.x - b1.x, b2.y - b1.y
                dist_sq = dx*dx + dy*dy
                if dist_sq < (b1.radius + b2.radius)**2:
                    dist = math.sqrt(dist_sq)
                    if self.first_contact is None and (b1.is_cue or b2.is_cue):
                        self.first_contact = b2 if b1.is_cue else b1
                    
                    nx, ny = dx / dist, dy / dist
                    p = (b1.vx * nx + b1.vy * ny) - (b2.vx * nx + b2.vy * ny)
                    b1.vx -= p * nx; b1.vy -= p * ny
                    b2.vx += p * nx; b2.vy += p * ny
                    
                    overlap = 0.5 * (b1.radius + b2.radius - dist)
                    b1.x -= overlap * nx; b1.y -= overlap * ny
                    b2.x += overlap * nx; b2.y += overlap * ny
        
        # Cushion and pocket
        for ball in self.balls:
            if ball.is_pocketed: continue
            
            pocketed = False
            for p in POCKETS:
                if math.hypot(ball.x - p[0], ball.y - p[1]) < POCKET_RADIUS:
                    ball.is_pocketed = True
                    ball.vx, ball.vy = 0, 0
                    self.pocketed_this_turn.append(ball)
                    pocketed = True
                    break
            if pocketed: continue

            if ball.x < TABLE_RECT[0] + ball.radius:
                ball.x = TABLE_RECT[0] + ball.radius
                ball.vx *= -1
            elif ball.x > TABLE_RECT[2] - ball.radius:
                ball.x = TABLE_RECT[2] - ball.radius
                ball.vx *= -1
            if ball.y < TABLE_RECT[1] + ball.radius:
                ball.y = TABLE_RECT[1] + ball.radius
                ball.vy *= -1
            elif ball.y > TABLE_RECT[3] - ball.radius:
                ball.y = TABLE_RECT[3] - ball.radius
                ball.vy *= -1

    def handle_turn_end(self):
        """Check rules and determine next game state after balls stop."""
        is_foul, switch_player, self.message = self.check_rules()

        if self.game_state == 'game_over': return

        if is_foul:
            if not self.cue_ball.is_pocketed:
                self.message += " Ball in hand."
                
            self.current_player = 3 - self.current_player
            self.game_state = 'ball_in_hand'
            self.cue_ball.is_pocketed = True 
        elif switch_player:
            self.current_player = 3 - self.current_player
            self.game_state = 'aiming'
            self.message = f"Player {self.current_player}'s Turn"
        else:
            self.game_state = 'aiming'
            self.message = "Good shot! Go again."

    def check_rules(self):
        """Contains all 8-ball rule logic."""
        is_foul = False
        switch_player = True
        message = ""

        if self.cue_ball.is_pocketed:
            is_foul = True
            message = "Scratch!"
        
        if not self.first_contact and not is_foul:
            is_foul = True
            message = "Foul! No ball hit."
        elif not is_foul:
            target_type = self.player_targets[self.current_player]
            if target_type != 'open' and self.first_contact.get_type() != target_type and self.first_contact.get_type() != '8-ball':
                is_foul = True
                message = f"Foul! Hit a {self.first_contact.get_type()} first."
        
        potted_solids = any(b.get_type() == 'solid' for b in self.pocketed_this_turn)
        potted_stripes = any(b.get_type() == 'stripe' for b in self.pocketed_this_turn)
        eight_ball_pocketed = any(b.get_type() == '8-ball' for b in self.pocketed_this_turn)

        if not is_foul:
            current_target = self.player_targets[self.current_player]
            potted_own_ball = False
            if current_target == 'solid' and potted_solids: potted_own_ball = True
            if current_target == 'stripe' and potted_stripes: potted_own_ball = True
            if current_target == 'open' and (potted_solids or potted_stripes):
                potted_own_ball = True

            if potted_own_ball:
                switch_player = False

        if self.player_targets[1] == 'open' and not is_foul and not eight_ball_pocketed:
            if potted_solids and not potted_stripes:
                self.player_targets[self.current_player] = 'solid'
                self.player_targets[3 - self.current_player] = 'stripe'
                message = f"Player {self.current_player} is SOLIDS"
            elif potted_stripes and not potted_solids:
                self.player_targets[self.current_player] = 'stripe'
                self.player_targets[3 - self.current_player] = 'solid'
                message = f"Player {self.current_player} is STRIPES"
            elif potted_solids and potted_stripes:
                message = "Solids and Stripes potted. Table is still open."

        if eight_ball_pocketed:
            player_has_balls_left = any(not b.is_pocketed and b.get_type() == self.player_targets[self.current_player] for b in self.balls)
            
            if is_foul or (self.player_targets[self.current_player] != 'open' and player_has_balls_left):
                message = f"Player {3 - self.current_player} WINS! Player {self.current_player} pocketed the 8-ball illegally."
                self.game_state = 'game_over'
            else:
                message = f"Player {self.current_player} WINS!"
                self.game_state = 'game_over'

        return is_foul, switch_player, message

    def update_all_drawings(self):
        """Update all visual elements on the canvas efficiently."""
        for ball in self.balls:
            ball.update_drawing(self.canvas)

        if self.game_state == 'aiming' or self.game_state == 'charging':
            self.canvas.itemconfig(self.aim_line_id, state='normal')
            self.canvas.itemconfig(self.cue_stick_id, state='normal')
            self.canvas.coords(self.aim_line_id, self.cue_ball.x, self.cue_ball.y, self.cue_ball.x + math.cos(self.angle)*2000, self.cue_ball.y + math.sin(self.angle)*2000)
            stick_start_x = self.cue_ball.x - math.cos(self.angle) * (BALL_RADIUS + 10)
            stick_start_y = self.cue_ball.y - math.sin(self.angle) * (BALL_RADIUS + 10)
            stick_end_x = self.cue_ball.x - math.cos(self.angle) * 350
            stick_end_y = self.cue_ball.y - math.sin(self.angle) * 350
            self.canvas.coords(self.cue_stick_id, stick_start_x, stick_start_y, stick_end_x, stick_end_y)
        else:
            self.canvas.itemconfig(self.aim_line_id, state='hidden')
            self.canvas.itemconfig(self.cue_stick_id, state='hidden')
        
        if self.game_state == 'charging':
            self.canvas.itemconfig(self.power_bar_bg_id, state='normal')
            self.canvas.itemconfig(self.power_bar_id, state='normal')
            power_duration = time.time() - self.power_start_time
            power_width = min(power_duration * 60, 150) * (200 / 150)
            self.canvas.coords(self.power_bar_id, SCREEN_WIDTH/2 - 100, SCREEN_HEIGHT - 40, SCREEN_WIDTH/2 - 100 + power_width, SCREEN_HEIGHT - 20)
        else:
            self.canvas.itemconfig(self.power_bar_bg_id, state='hidden')
            self.canvas.itemconfig(self.power_bar_id, state='hidden')
        
        if self.game_state == 'ball_in_hand':
            self.cue_ball.x, self.cue_ball.y = self.mouse_pos
            self.cue_ball.update_drawing(self.canvas)
        
        self.canvas.itemconfig(self.player_turn_text_id, text=f"Player {self.current_player}'s Turn")
        self.canvas.itemconfig(self.player_target_text_id, text=f"Target: {self.player_targets[self.current_player].upper()}")
        self.canvas.itemconfig(self.message_text_id, text=self.message)

    def on_mouse_move(self, event):
        self.mouse_pos = (event.x, event.y)
    
    def on_mouse_down(self, event):
        self.is_mouse_pressed = True
        if self.game_state == 'aiming':
            self.game_state = 'charging'
            self.power_start_time = time.time()
        elif self.game_state == 'ball_in_hand':
            can_place = True
            for b in self.balls:
                if b != self.cue_ball and not b.is_pocketed and math.hypot(event.x - b.x, event.y - b.y) < b.radius * 2:
                    can_place = False
                    break
            if can_place and TABLE_RECT[0] < event.x < TABLE_RECT[2] and TABLE_RECT[1] < event.y < TABLE_RECT[3]:
                self.cue_ball.is_pocketed = False
                self.game_state = 'aiming'
                self.message = f"Player {self.current_player}'s Turn"
    
    def on_mouse_up(self, event):
        self.is_mouse_pressed = False

if __name__ == '__main__':
    root = tk.Tk()
    
    # --- NEW: Set to fullscreen and add an exit binding ---
    root.attributes('-fullscreen', True)
    root.bind("<Escape>", lambda event: root.destroy()) # Press ESC to exit

    game = PoolGame(root)
    root.mainloop()