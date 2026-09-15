from PyQt6.QtCore import QRect, QPoint, QEvent, pyqtSignal, QTimer
from PyQt6.QtWidgets import QApplication, QWidget, QMainWindow, QPushButton, QLabel

from PyQt6 import QtCore
from PyQt6 import QtGui
from PyQt6.QtGui import QPainter, QPaintDevice, QColor, QKeyEvent, QKeySequence
from PyQt6.QtWidgets import QVBoxLayout

import random
from enum import Enum

from collections import deque
import sys, time


class Point:
    def __init__(self, x=0, y=0):
        self.x = x
        self.y = y

    def __eq__(self, value: object, /) -> bool:
        if self.x == value.x and self.y == value.y:
            return True
        else:
            return False

    def __le__(self, other):
        if self.x <= other.x or self.y <= other.y:
            return True
        else:
            return False

    def __ge__(self, other):
        if self.x >= other.x or self.y >= other.y:
            return True
        else:
            return False

    def __lt__(self, other):
        if self.x < other.x or self.y < other.y:
            return True
        else:
            return False

    def __gt__(self, other):
        if self.x > other.x or self.y > other.y:
            return True
        else:
            return False

    def __str__(self) -> str:
        return f'Point: [{self.x},{self.y}]'

    def __add__(self, other):
        if other.__class__ == Point:
            return Point(self.x + other.x, self.y + other.y)
        elif other.__class__ == int:
            return Point(self.x + other, self.y + other)
        else:
            raise TypeError

    def get(self):
        return self.x, self.y

    def set(self, x, y):
        self.x = x
        self.y = y

    def set_x(self, x):
        self.x = x

    def set_y(self, y):
        self.y = y

    def get_x(self):
        return self.x

    def get_y(self):
        return self.y


class Direction(Enum):
    UP = 1,
    DOWN = 2,
    LEFT = 3,
    RIGHT = 4


def get_opposite(direction):
    match direction:
        case Direction.RIGHT:
            return Direction.LEFT
        case Direction.LEFT:
            return Direction.RIGHT
        case Direction.UP:
            return Direction.DOWN
        case Direction.DOWN:
            return Direction.UP
    return None


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
#            print(self.direction_queue)
            curr_dir = self.direction_queue.popleft()
            if self.head.prev is not None:
                if get_opposite(self.head.direction) != curr_dir:
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
        if point < Point(0, 0) or point > Point(*self.get_size()):
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
        self.blinker.setInterval(750)  # 750ms
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
        new_location = Point()
        while not is_placed:
            new_location.set(random.randrange(0, playground_size[0], self.size),
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


# Subclass QMainWindow to customize application's main window
class MainWindow(QMainWindow):
    playground_size_x = 500
    playground_size_y = 500

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

        self.playground = PlayGround(MainWindow.playground_size_x, MainWindow.playground_size_y)  #QLabel()

        layout = QVBoxLayout()
        layout.addWidget(self.button)
        layout.addWidget(self.playground)
        #        layout.addSpacerItem()
        self.main_widget.setLayout(layout)

        self.button.clicked.connect(self.start_new_game)
        self.main_widget.keyPressed.connect(self.direction_changed)
        self.score = 0
        self.size = 25

        self.timer = QTimer()
        self.timer.setInterval(200)
        self.timer.timeout.connect(self.run)

        self.snake = None
        self.food = None

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
                    print(f'Total score: {self.score}')
                elif is_food:
                    self.food.place_food(self.snake.get_all_pieces())
                    self.score += 1
                self.playground.refresh()
        except Exception as e:
            print('exception happened', e)

    def start_new_game(self):
        self.playground.clear()
        self.score = 0

        x0 = random.randrange(0, MainWindow.playground_size_x - self.size, self.size)
        y0 = random.randrange(0, MainWindow.playground_size_y - self.size, self.size)

        print(f'Starting point: {x0, y0}')
        print(self.playground.geometry().topLeft())

        #print(sys.getrefcount(self.snake))
        #print(sys.getrefcount(self.food))
        self.snake = None
        self.food = None

        self.snake = Snake(x0, y0, self.size, 1)
        self.food = SnakeFood(self.size, self.playground, self.snake.get_all_pieces())
        self.timer.start()

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


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    app.exec()
