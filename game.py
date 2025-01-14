# -*- coding: utf-8 -*-
"""
@author: Junxiao Song
"""

from __future__ import print_function
import numpy as np

INPUT_STATE_CHANNEL_SIZE = 19

class Board(object):
    """board for the game"""

    """
    0: blank
    1: black
    2: white
    """
    forbidden_hands_of_three_patterns = [
        [0, 1, 1, 1, 0],
        [0, 1, 0, 1, 1, 0],
        [0, 1, 1, 0, 1, 0],
    ]

    forbidden_hands_of_four_patterns = [
        [0, 1, 1, 1, 1, 0],
        [0, 1, 1, 1, 0, 1],
        [0, 1, 0, 1, 1, 1],
        [1, 1, 1, 0, 1, 0],
        [1, 0, 1, 1, 1, 0],
        [2, 1, 1, 1, 1, 0],
        [2, 1, 1, 1, 0, 1],
        [2, 1, 0, 1, 1, 1],
        [0, 1, 1, 1, 1, 2],
        [1, 1, 1, 0, 1, 2],
        [1, 0, 1, 1, 1, 2],
    ]

    def __init__(self, **kwargs):
        self.width = int(kwargs.get('width', 8))
        self.height = int(kwargs.get('height', 8))
        # board states stored as a dict,
        # key: move as location on the board,
        # value: player as pieces type
        self.states = {}
        # need how many pieces in a row to win
        self.n_in_row = int(kwargs.get('n_in_row', 5))
        self.forbidden_hands = bool(kwargs.get('forbidden_hands', False))
        self.players = [1, 2]  # player1 and player2

    def init_board(self, start_player=0):
        if self.width < self.n_in_row or self.height < self.n_in_row:
            raise Exception('board width and height can not be '
                            'less than {}'.format(self.n_in_row))
        self.start_player = start_player
        self.current_player = self.players[start_player]  # start player
        # keep available moves in a list
        self.availables = list(range(self.width * self.height))
        self.states = {}
        self.last_move = -1
        self.last_16_move = [0]*(INPUT_STATE_CHANNEL_SIZE-3)

    def move_to_location(self, move):
        """
        3*3 board's moves like:
        6 7 8
        3 4 5
        0 1 2
        and move 5's location is (1,2)
        """
        h = move // self.width
        w = move % self.width
        return [h, w]

    def location_to_move(self, location):
        if len(location) != 2:
            return -1
        h = location[0]
        w = location[1]
        if h < 0 or h >= self.height:
            return -1
        if w < 0 or w >= self.width:
            return -1

        move = h * self.width + w
        if move not in range(self.width * self.height):
            return -1
        return move

    def current_last16move_state(self):
        """return the board state from the perspective of the current res30 player.
        state shape: INPUT_STATE_CHANNEL_SIZE*width*height
        """

        square_state = np.zeros((INPUT_STATE_CHANNEL_SIZE, self.width, self.height))
        if self.states:
            moves, players = np.array(list(zip(*self.states.items())))
            move_curr = moves[players == self.current_player]
            move_oppo = moves[players != self.current_player]

            square_state[0][move_curr // self.width,
                            move_curr % self.height] = 1.0
            square_state[1][move_oppo // self.width,
                            move_oppo % self.height] = 1.0
            # indicate the last 16 move location
            for i in range(INPUT_STATE_CHANNEL_SIZE-3):
                square_state[2+i][np.array(self.last_16_move[i::2]) // self.width,
                                np.array(self.last_16_move[i::2]) % self.height] = 1.0
        if len(self.states) % 2 == 0:
            square_state[INPUT_STATE_CHANNEL_SIZE-1][:, :] = 1.0  # indicate the colour to play
        return square_state[:, ::-1, :]

    def current_state(self):
        """return the board state from the perspective of the current baseline player.
        state shape: 4*width*height
        """

        square_state = np.zeros((4, self.width, self.height))
        if self.states:
            moves, players = np.array(list(zip(*self.states.items())))
            move_curr = moves[players == self.current_player]
            move_oppo = moves[players != self.current_player]
            square_state[0][move_curr // self.width,
                            move_curr % self.height] = 1.0
            square_state[1][move_oppo // self.width,
                            move_oppo % self.height] = 1.0
            # indicate the last move location
            square_state[2][self.last_move // self.width,
                            self.last_move % self.height] = 1.0
        if len(self.states) % 2 == 0:
            square_state[3][:, :] = 1.0  # indicate the colour to play
        return square_state[:, ::-1, :]

    def do_move(self, move):
        self.states[move] = self.current_player
        self.availables.remove(move)
        self.current_player = (
            self.players[0] if self.current_player == self.players[1]
            else self.players[1]
        )
        self.last_move = move
        self.last_16_move.pop(0)
        self.last_16_move.append(move)

    def has_a_winner(self):
        width = self.width
        height = self.height
        states = self.states
        n = self.n_in_row

        if self.forbidden_hands and self.states and self.states[self.last_move] == self.players[self.start_player] and self.check_forbidden_hands():
            return True, self.players[(self.start_player + 1) % 2]

        moved = list(set(range(width * height)) - set(self.availables))
        if len(moved) < self.n_in_row *2-1:
            return False, -1

        for m in moved:
            h = m // width
            w = m % width
            player = states[m]

            if (w in range(width - n + 1) and
                    len(set(states.get(i, -1) for i in range(m, m + n))) == 1):
                return True, player

            if (h in range(height - n + 1) and
                    len(set(states.get(i, -1) for i in range(m, m + n * width, width))) == 1):
                return True, player

            if (w in range(width - n + 1) and h in range(height - n + 1) and
                    len(set(states.get(i, -1) for i in range(m, m + n * (width + 1), width + 1))) == 1):
                return True, player

            if (w in range(n - 1, width) and h in range(height - n + 1) and
                    len(set(states.get(i, -1) for i in range(m, m + n * (width - 1), width - 1))) == 1):
                return True, player

        return False, -1

    def check_forbidden_hands(self):
        directions = [
            [1, 0],
            [1, 1],
            [0, 1],
            [-1, 1],
        ]
        
        patterns_of_three_matches = [
            1 if self.check_forbidden_pattern(p, d) else 0
            for d in directions
            for p in self.forbidden_hands_of_three_patterns
        ]
        
        patterns_of_four_matches = [
            1 if self.check_forbidden_pattern(p, d) else 0
            for d in directions
            for p in self.forbidden_hands_of_four_patterns
        ]
        
        if sum(patterns_of_three_matches) > 1 or sum(patterns_of_four_matches) > 1:
            return True
    
    def check_forbidden_pattern(self, pattern, direction):
        for (i, x) in enumerate(pattern):
            if x == 1:
                pieces = self.collect_pieces(self.last_move, direction, i, len(pattern))
                if pieces != [] and Board.list_equal(pieces, pattern):
                    return True
        
        return False
    
    def list_equal(list1, list2):
        if len(list1) != len(list2):
            return False

        for (a, b) in zip(list1, list2):
            if a != b:
                return False

        return True

    def collect_pieces(self, move, direction, look_back, length):
        cur_location = self.move_to_location(move)
        start_location = [
            cur_location[0] - direction[0] * look_back,
            cur_location[1] - direction[1] * look_back,
        ]

        pieces = []
        for i in range(length):
            location = [
                start_location[0] + i * direction[0],
                start_location[1] + i * direction[1],
            ]
            move = self.location_to_move(location)
            if move == -1:
                return []
            else:
                if move in self.states:
                    pieces.append(1 if self.states[move] == self.players[self.start_player] else 2)
                else:
                    pieces.append(0)
        return pieces

    def game_end(self):
        """Check whether the game is ended or not"""
        win, winner = self.has_a_winner()
        if win:
            return True, winner
        elif not len(self.availables):
            return True, -1
        return False, -1

    def get_current_player(self):
        return self.current_player


class Game(object):
    """game server"""

    def __init__(self, board, **kwargs):
        self.board = board

    def graphic(self, board, player1, player2):
        """Draw the board and show game info"""
        width = board.width
        height = board.height

        print("Player", player1, "with X".rjust(3))
        print("Player", player2, "with O".rjust(3))
        print()
        for x in range(width):
            print("{0:8}".format(x), end='')
        print('\r\n')
        for i in range(height - 1, -1, -1):
            print("{0:4d}".format(i), end='')
            for j in range(width):
                loc = i * width + j
                p = board.states.get(loc, -1)
                if p == player1:
                    print('X'.center(8), end='')
                elif p == player2:
                    print('O'.center(8), end='')
                else:
                    print('_'.center(8), end='')
            print('\r\n\r\n')

    def start_play(self, player1, player2, start_player=0, is_shown=1):
        """start a game between two players"""
        if start_player not in (0, 1):
            raise Exception('start_player should be either 0 (player1 first) '
                            'or 1 (player2 first)')
        self.board.init_board(start_player)
        p1, p2 = self.board.players
        player1.set_player_ind(p1)
        player2.set_player_ind(p2)
        players = {p1: player1, p2: player2}
        if is_shown:
            self.graphic(self.board, player1.player, player2.player)
        while True:
            current_player = self.board.get_current_player()
            player_in_turn = players[current_player]
            move = player_in_turn.get_action(self.board)
            self.board.do_move(move)
            if is_shown:
                self.graphic(self.board, player1.player, player2.player)
            end, winner = self.board.game_end()
            if end:
                if winner != -1:
                        print("Game end. Winner is", players[winner])
                else:
                    print("Game end. Tie")
                return winner

    def start_self_play(self, player, model_name, is_shown=0, temp=1e-3):
        """ start a self-play game using a MCTS player, reuse the search tree,
        and store the self-play data: (state, mcts_probs, z) for training
        """
        self.board.init_board()
        p1, p2 = self.board.players
        states, mcts_probs, current_players = [], [], []
        while True:
            move, move_probs = player.get_action(self.board,
                                                 temp=temp,
                                                 return_prob=1)
            # store the data
            states.append(self.board.current_state() if model_name == 'baseline' else self.board.current_last16move_state())
            mcts_probs.append(move_probs)
            current_players.append(self.board.current_player)
            # perform a move
            self.board.do_move(move)
            if is_shown:
                self.graphic(self.board, p1, p2)
            end, winner = self.board.game_end()
            if end:
                # winner from the perspective of the current player of each state
                winners_z = np.zeros(len(current_players))
                if winner != -1:
                    winners_z[np.array(current_players) == winner] = 1.0
                    winners_z[np.array(current_players) != winner] = -1.0
                # reset MCTS root node
                player.reset_player()
                if is_shown:
                    if winner != -1:
                        print("Game end. Winner is player:", winner)
                    else:
                        print("Game end. Tie")
                return winner, zip(states, mcts_probs, winners_z)