from abc import ABC, abstractmethod
from game_state import GameState, max_by_key
from random import sample, random


class Rule(ABC):
    def __init__(self, game_state=None, player=None, sub_rule=None, name="*"):
        self.game_state = game_state
        self.player = player
        self.sub_rule = sub_rule
        self.name = name

    def __repr__(self):
        return str(self.name)

    @abstractmethod
    def get_legal_moves(self):
        """
        :return: list of legal moves for self in game state
                 moves must contain enough information to be reversed
        """
        pass

    @abstractmethod
    def execute_move(self, move):  # TODO add optional *args for open ended moves?
        """
        carries out instructions in move
        :param move: same type as an element of self.legal_moves() output
        """
        pass

    @abstractmethod
    def undo_move(self, move):
        """
        carries out inverse operation of self.execute_move(move)
        :param move: same type as an element of self.legal_moves() output
        """
        pass

    @abstractmethod
    def get_utility(self):
        """
        :return: dictionary of values keyed by players. should be between 0 and 1
        """
        pass

    @staticmethod
    def move_to_string(move):
        """
        :param move: same type as element of self.get_legal_moves()
        :return: human - friendly string of move
        """
        return str(move)

    def get_bottom_rule(self):
        """
        :return: last element of linked list of sub_rules ( =self.get_piece()[-1] )
        """
        if self.sub_rule:
            return self.sub_rule.get_bottom_rule()
        else:
            return self

    def get_piece(self):
        """
        :return: linked list of sub_rules
        """
        if self.sub_rule:
            return [self] + self.sub_rule.get_piece()
        else:
            return [self]

    def max_n(self, depth, width=None, temp=1, k=1):
        """
        searches game tree and applies max_n algorithm to evaluate current game
        :param depth: maximum depth of search
        :param width: maximum branches from this node
        :param temp: probability of selecting the child branches randomly
        :param k: depth of intermediate searches for determining continuation line
        :return: evaluation of current game ( = utility from the end of the expected branch)
        """
        if self.player:
            player = self.player
        else:
            player = self.get_bottom_rule().player
        legal = self.get_legal_moves()
        if width and width < len(legal):
            if temp < random():
                def evaluate(m):
                    self.execute_move(m)
                    utility = self.max_n(k)[player]
                    self.undo_move(m)
                    return utility
                legal = sorted(legal, key=evaluate)[:width]
            else:
                legal = sample(self.get_legal_moves(), width)
        if depth == 0 or not legal:
            return self.get_utility()
        else:
            utilities = []
            for move in legal:
                self.execute_move(move)
                utilities.append(self.max_n(depth - 1, width, temp))
                self.undo_move(move)
            return max_by_key(player, utilities)


# -- Game -------------------------------------------------

class Game(Rule, ABC):
    def __init__(self, game_state=GameState(), sub_rule=None):
        super().__init__(game_state=game_state, player=None, sub_rule=sub_rule)
        self.game_state.add_pieces(self)

    def __repr__(self):
        return 'turn: ' + str(self.sub_rule)

    def execute_move(self, move):
        self.sub_rule = move[0]
        for rule, sub_move in move[2]:
            rule.execute_move(sub_move)

    def undo_move(self, move):
        for rule, sub_move in move[2]:
            rule.undo_move(sub_move)
        self.sub_rule = move[1]


class SimpleTurn(Game):
    def __init__(self, game_state, *sub_rules, turn=0):
        self.sequence = sub_rules
        self.turn = turn % len(self.sequence)
        super().__init__(game_state=game_state, sub_rule=self.sequence[0])

    def get_legal_moves(self):
        legal = []
        for sub_move in self.sub_rule.get_legal_moves():
            legal.append((self.sub_rule, sub_move))
        return legal

    @staticmethod
    def move_to_string(move):
        sub_rule, sub_move = move
        return sub_rule.move_to_string(sub_move)

    def execute_move(self, move=None):
        self.turn = (self.turn + 1) % len(self.sequence)
        self.sub_rule = self.sequence[self.turn]
        if move:
            sub_rule, sub_move = move
            sub_rule.execute_move(sub_move)

    def undo_move(self, move=None):
        if move:
            sub_rule, sub_move = move
            sub_rule.undo_move(sub_move)
        self.turn = (self.turn - 1) % len(self.sequence)
        self.sub_rule = self.sequence[self.turn]

    def get_utility(self):
        utility = {}
        for sub_rule in self.sequence:
            utility.update(sub_rule.get_utility())
        return utility


# -- Combining Rule ---------------------------------------

class RuleSum(Rule):  # TODO This may be a little janky and unnecessary...
    def __init__(self, game_state=GameState(), player=None, *sub_rules):
        self.all_subs = []
        for rule in sub_rules:
            self.all_subs.append(rule)
        super().__init__(game_state=game_state, player=player, sub_rule=sub_rules)

    def __repr__(self):
        return 'Sum' + str([str(rule) for rule in self.sub_rule])

    def get_legal_moves(self):
        legal = []
        for rule in self.sub_rule:
            for sub_move in rule.get_legal_moves():
                legal.append((rule, sub_move))
        return legal

    def execute_move(self, move):
        rule, sub_move = move
        rule.execute_move(sub_move)

    def undo_move(self, move):
        rule, sub_move = move
        rule.undo_move(sub_move)

    def get_bottom_rule(self):
        if self.sub_rule:
            return self.sub_rule[-1].get_bottom_rule()
        else:
            return self

    def get_piece(self):
        this_piece = [self]
        [this_piece.extend(rule.get_piece()) for rule in self.sub_rule]
        return this_piece

    def get_utility(self):
        return max_by_key(self.player, [rule.get_utility() for rule in self.sub_rule])


# -- Piece creator Method ---------------------------------

def piece(*rules):
    player = rules[0].player
    for i, rule in enumerate(rules[:-1]):
        rule.sub_rule = rules[i+1]
        rule.player = player
    rules[0].game_state.add_pieces(rules[0])
    return rules[0]
