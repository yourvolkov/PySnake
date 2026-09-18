from tkinter import dialog

from PyQt6.QtCore import QRect, QPoint, QEvent, pyqtSignal, QTimer, QSize
from PyQt6.QtWidgets import QApplication, QWidget, QMainWindow, QPushButton, QLabel, QSlider, QDialog, QSpacerItem, QTextEdit

from PyQt6 import QtCore
from PyQt6 import QtGui

from PyQt6.QtGui import QPainter, QPaintDevice, QColor, QKeyEvent, QKeySequence
from PyQt6.QtWidgets import QVBoxLayout, QHBoxLayout

import random
from enum import Enum
import json

from collections import deque
import sys, time
from dataclasses import dataclass

@dataclass(order=True, frozen=True)
class Point:
    """Class for operating with 2-dimensional points on the playground"""
    x: int = 0
    y: int = 0

    def __str__(self) -> str:
        return f'Point: [{self.x},{self.y}]'

    def __add__(self, other):
        if isinstance(other, Point):
            return Point(self.x + other.x, self.y + other.y)
        elif isinstance(other, int):
            return Point(self.x + other, self.y + other)
        else:
            raise TypeError

    def get(self):
        return self.x, self.y

    def is_at_least_one_coordinate_smaller_than(self, other: Point):
        if self.x < other.x or self.y < other.y:
            return True
        return False

    def is_at_least_one_coordinate_greater_than(self, other: Point):
        if self.x > other.x or self.y > other.y:
            return True
        return False

class Direction(Enum):
    UP = 1
    DOWN = 2
    LEFT = 3
    RIGHT = 4

    def get_opposite(self) -> Direction:
        match self:
            case Direction.RIGHT:
                return Direction.LEFT
            case Direction.LEFT:
                return Direction.RIGHT
            case Direction.UP:
                return Direction.DOWN
            case Direction.DOWN:
                return Direction.UP


class SnakePiece:

    def __init__(self, x, y, direction, size, color='black', is_head=True):
        self.size = size
        self.coordinates = Point(x, y)
        self.direction = direction
        self.color = color

        # possibly to refactor/update
        self.is_head = is_head
        self.next = None
        self.prev = None

    def move(self):
        self.coordinates = self.get_next_move()

    def get_next_move(self):
        x, y = self.coordinates.get()
        match self.direction:
            case Direction.RIGHT:
                x += self.size
            case Direction.LEFT:
                x -= self.size
            case Direction.DOWN:
                y += self.size
            case Direction.UP:
                y -= self.size
        return Point(x, y)

    def get_q_properties(self, is_clearing):
        q_point = QtCore.QPoint(*self.coordinates.get())
        q_size = QtCore.QSize(self.size, self.size)
        if is_clearing:
            q_color = QColor('white')
        else:
            q_color = QColor(self.color)

        return QRect(q_point, q_size), q_color

    def set_direction(self, direction):
        self.direction = direction

    def get_location(self):
        return self.coordinates


class Snake:
    def __init__(self, head_x, head_y, size, length):
        self.members = []
        self.head = SnakePiece(head_x, head_y, Direction.RIGHT, size=size, is_head=True)
        self.size = size
        self.members.append(self.head)
        #self.members = [SnakePiece(head_x, head_y, size = size, is_head=True) if i == 0 else SnakePiece(head_x - size*i, head_y, size = size, is_head=False) for i in range(length)]
        self.direction_queue = deque()
        for i in range(1, length):
            self.add_piece(head_x + size * i, head_y, size)

    def move(self, playground, food_location):
        is_food_found = False
        is_collision_happened = False
        is_out_of_border = False

        # Handle the queue of directions first:
        # (multiple arrows might be pressed between one move cycle)
        self.apply_direction()

        next_move = self.head.get_next_move()
        # Check if the next move will exceed the playground borders
        if (not playground.is_point_within_playground(next_move)
                or not playground.is_point_within_playground(next_move + self.size)):
            print('!!!OUT OF BORDER!!!')
            is_out_of_border = True
        # Check if the next move will feed the snake
        if next_move == food_location:
            print('!!!FOOD!!!')
            self.add_piece(*food_location.get(), self.size)
            is_food_found = True
        if not is_out_of_border:
            # Clear the whole snake from the screen first
            for member in self.members:
                playground.draw_area.fillRect(*member.get_q_properties(True))

            # Move and redraw each piece
            for member in self.members:
                member.move()
                playground.draw_area.fillRect(*member.get_q_properties(False))

            #Check for collisions
            for member in self.members:
                if member is not self.head:
                    #check for collisions
                    if member.get_location() == self.head.get_location():
                        print('!!!COLLISION!!!')
                        is_collision_happened = True

            #handle curving
            members_to_update = {}
            for member in self.members:
                if member.prev is not None:
                    if member.direction != member.prev.direction:
                        members_to_update[member.prev] = member.direction

            for key, value in members_to_update.items():
                key.direction = value

        return is_food_found, is_collision_happened, is_out_of_border

    def set_direction(self, direction):
        self.direction_queue.append(direction)

    def apply_direction(self):
        is_applied = False
        while is_applied == False and len(self.direction_queue) > 0:
            curr_dir = self.direction_queue.popleft()
            if self.head.prev is not None:
                if self.head.direction.get_opposite() != curr_dir:
                    self.head.set_direction(curr_dir)
                    is_applied = True
                else:
                    print('Wrong direction!')
            else:
                self.head.set_direction(curr_dir)
                is_applied = True

    def add_piece(self, x, y, size):
        new_peace = SnakePiece(x, y, self.head.direction, size=size, is_head=True)
        new_peace.prev = self.head
        self.head.is_head = False
        self.head.next = new_peace
        self.members.append(new_peace)
        self.head = new_peace

    def get_all_pieces(self):
        return [member.get_location() for member in self.members]

    def __del__(self):
        print('Snake deleted')


class PlayGround(QLabel):

    def __init__(self, size_x, size_y):
        super().__init__()
        self.canvas = QtGui.QPixmap(size_x, size_y)
        self.canvas.fill(QtCore.Qt.GlobalColor.white)
        self.draw_area = QPainter(self.canvas)
        self.setPixmap(self.canvas)

    def clear(self):
        self.canvas.fill(QtCore.Qt.GlobalColor.white)
        self.setPixmap(self.canvas)

    def refresh(self):
        self.setPixmap(self.canvas)

    def get_size(self):
        return self.canvas.size().width(), self.canvas.size().height()

    def is_point_within_playground(self, point: Point):
        if (point.is_at_least_one_coordinate_smaller_than(Point(0, 0)) or
                point.is_at_least_one_coordinate_greater_than(Point(*self.get_size()))):
            return False
        else:
            return True


class SnakeFood:

    def __init__(self, size, playground, all_snake_pieces):
        self.playground = playground
        self.coordinates = Point()
        self.size = size
        self.is_visible = True
        self.place_food(all_snake_pieces)

        #timer init
        self.blinker = QTimer()
        self.blinker.setInterval(500)  # 500ms
        self.blinker.timeout.connect(self.blink)
        self.blinker.start()

    def blink(self):
        q_point = QtCore.QPoint(*self.coordinates.get())
        q_size = QtCore.QSize(self.size, self.size)
        q_food = QRect(q_point, q_size)
        if self.is_visible:
            self.playground.draw_area.fillRect(q_food, QColor('blue'))
            self.is_visible = False
        else:
            self.playground.draw_area.fillRect(q_food, QColor('white'))
            self.is_visible = True
        self.playground.refresh()

    def __del__(self):
        print('food deleted!')
        self.blinker.stop()

    def place_food(self, all_snake_pieces):
        playground_size = self.playground.get_size()
        is_placed = False
        new_location = None
        while not is_placed:
            new_location = Point(random.randrange(0, playground_size[0], self.size),
                                    random.randrange(0, playground_size[1], self.size))
            if new_location not in all_snake_pieces:
                self.coordinates = new_location
                is_placed = True

        self.is_visible = True
        self.blink()

    def get_location(self):
        return self.coordinates


class MyQWidget(QWidget):
    keyPressed = pyqtSignal(Direction)

    def keyPressEvent(self, a0):
        direction = None
        match a0.key():
            case QtCore.Qt.Key.Key_Down:
                direction = Direction.DOWN
                print('Down')
            case QtCore.Qt.Key.Key_Up:
                direction = Direction.UP
                print('Up')
            case QtCore.Qt.Key.Key_Left:
                direction = Direction.LEFT
                print('Left')
            case QtCore.Qt.Key.Key_Right:
                direction = Direction.RIGHT
                print('Right')
        if direction is not None:
            self.keyPressed.emit(direction)


class GameOverDialog(QDialog):
    def __init__(self, score: int, score_board: list, place: int, parent: QWidget|None = ..., ):
        super().__init__(parent)
        self.setWindowTitle('GAME OVER!')
        self.score = score
        self.scoreLabel = QLabel(f'Your score is: {score}')
        self.scoreLabel.setAlignment(QtCore.Qt.AlignmentFlag.AlignHCenter)

        self.nameField = QTextEdit()
        self.nameField.setMaximumHeight(30)
        self.submit_button = QPushButton('Submit')

        layout = QVBoxLayout()
        layout.addWidget(self.scoreLabel)
        layout.addSpacerItem(QSpacerItem(200, 10))
        layout.addWidget(QLabel('SCORE TABLE:'))
        self.score_board = score_board
        self.place = place
        for i, (key, value) in enumerate(score_board):
            if i != place:
                label = QLabel(f'#{i + 1}. {key}: {value}')
                label.setMaximumHeight(30)
                layout.addWidget(label)
            else:
                winner_place_layout = QHBoxLayout()
                label_with_place = QLabel(f'#{i + 1}')
                label_with_place.setMaximumHeight(30)
                winner_place_layout.addWidget(label_with_place)
                winner_place_layout.addWidget(self.nameField)
                winner_place_layout.addWidget(self.submit_button)
                layout.addLayout(winner_place_layout)

        self.setLayout(layout)
        self.submit_button.clicked.connect(self.submit_record)

    def submit_record(self):
        name = self.nameField.toPlainText()
        self.score_board[self.place] = (name, self.score)
        print(self.score_board)
        self.close()


# Subclass QMainWindow to customize application's main window
class MainWindow(QMainWindow):
    playground_size_x = 500
    playground_size_y = 500
    score_board_file_path = 'score_board.txt'

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Snake")

        self.main_widget = MyQWidget()
        self.setCentralWidget(self.main_widget)
        self.main_widget.setFocus()

        self.button = QPushButton()
        self.button.setEnabled(True)
        self.button.setFocusPolicy(QtCore.Qt.FocusPolicy.NoFocus)
        self.button.setText("Start new game!")

        self.game_speed = 800
        self.speed_control_slider = QSlider(QtCore.Qt.Orientation.Horizontal, None)
        self.speed_control_slider.setRange(500, 950)
        self.speed_control_slider.setValue(self.game_speed)
        self.speed_control_slider.valueChanged.connect(self.update_speed_of_the_snake)
        self.speed_control_slider.setFocusPolicy(QtCore.Qt.FocusPolicy.NoFocus)

        self.score = 0
        self.score_label = QLabel()
        self.show_score()

        self.playground = PlayGround(MainWindow.playground_size_x, MainWindow.playground_size_y)  #QLabel()

        layout = QVBoxLayout()
        control_layout = QVBoxLayout()
        control_layout.addWidget(self.speed_control_slider)
        layout.addWidget(self.button)
        layout.addWidget(self.score_label)
        layout.addLayout(control_layout)
        layout.addWidget(self.playground)
        #        layout.addSpacerItem()
        self.main_widget.setLayout(layout)

        self.button.clicked.connect(self.start_new_game)
        self.main_widget.keyPressed.connect(self.direction_changed)

        self.size = 25

        self.timer = QTimer()
        self.set_timer_period()
        self.timer.timeout.connect(self.run)

        self.snake = None
        self.food = None

        self.score_board = []
        try:
            with open(MainWindow.score_board_file_path, 'r', encoding='utf-8') as f:
                try:
                    self.score_board = json.load(f)
                    print(self.score_board)
                except Exception as e:
                    print(f'Exception happened while reading {MainWindow.score_board_file_path} file: {e}')
        except FileNotFoundError:
            print(f'Creating a new {MainWindow.score_board_file_path} as it did not exist')
            with open(MainWindow.score_board_file_path, 'x') as f:
                ...


    def set_timer_period(self):
        self.timer.setInterval(1000 - self.game_speed)

    def direction_changed(self, direction):
        if self.snake is not None:
            self.snake.set_direction(direction)
        print('-' * 5)

    def run(self):
        try:
            if self.snake is not None:
                is_food, is_collision, is_out_of_border = self.snake.move(self.playground, self.food.get_location())
                if is_collision or is_out_of_border:
                    self.timer.stop()
                    is_record, place = self.handle_score_within_score_table()
                    if is_record:
                        game_over_dialog = GameOverDialog(self.score, self.score_board, place, self)
                        game_over_dialog.exec()
                    print(f'Total score: {self.score}')
                elif is_food:
                    self.food.place_food(self.snake.get_all_pieces())
                    self.score += self.game_speed
                    self.show_score()
                self.playground.refresh()
        except Exception as e:
            print('exception happened', e)

    def update_speed_of_the_snake(self, val):
        self.game_speed = val
        self.set_timer_period()

    def start_new_game(self):
        self.playground.clear()
        self.score = 0

        x0 = random.randrange(0, MainWindow.playground_size_x - self.size, self.size)
        y0 = random.randrange(0, MainWindow.playground_size_y - self.size, self.size)

        print(f'Starting point: {x0, y0}')
        print(self.playground.geometry().topLeft())

        self.snake = Snake(x0, y0, self.size, 1)
        self.food = SnakeFood(self.size, self.playground, self.snake.get_all_pieces())
        self.timer.start()
        self.show_score()

    def show_score(self):
        #let's calculate the score as points * speed
        self.score_label.setText(f'Your Score: {self.score}')

    def handle_score_within_score_table(self):
        self.score_board = sorted(self.score_board, key=lambda item:item[1], reverse=True)
        is_new_record = False
        is_already_existing_record = False
        place = 0

        if self.score > 0:
            for i, (name, value) in enumerate(self.score_board.copy()):
                if value < self.score:
                    print(f'Beaten record! #{i + 1} place')
                    self.score_board[i] = (None, self.score)
                    is_new_record = True
                    place = i
                    break
                elif value == self.score:
                    is_already_existing_record = True


            if len(self.score_board) < 3 and is_new_record is False and is_already_existing_record is False: # only 3 record places are stored (gold, silver, bronze)
                self.score_board.append((None, self.score))
                place = len(self.score_board) - 1
                print(f'New record! #{place + 1} place')
                is_new_record = True

        print(self.score_board)
        return is_new_record, place

    # currently not used
    def mousePressEvent(self, e):
        keys = ('x', 'y')
        points = e.position()
        values = (int(points.x()), int(points.y()))
        pos = dict(zip(keys, values))
        start = self.playground.geometry().topLeft()
        start = (int(start.x()), int(start.y()))
        pos['x'] = pos['x'] - start[0]
        pos['y'] = pos['y'] - start[1]

        print(f'x = {pos['x']}, y = {pos['y']}')
        self.main_widget.setFocus()

    def closeEvent(self, e):
        print('del called')
        self.timer.stop()
        del self.food
        print('saving score board')
        with open(MainWindow.score_board_file_path, 'w', encoding='utf-8') as f:
            f.write(json.dumps(self.score_board))


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    app.exec()
