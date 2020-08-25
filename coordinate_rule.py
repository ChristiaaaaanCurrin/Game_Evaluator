from rule import Rule
from abc import ABC, abstractmethod


class Tile(Rule):
    def __init__(self, *coords, **kwargs):
        super().__init__(**kwargs)
        self.coords = coords

    def __repr__(self):
        return 'Tile%s' % str(self.coords)

    def requirements(self):
        return {"get_coords": lambda x: ()}

    def get_coords(self):
        return self.coords

    def generate_legal_moves(self):
        return []

    def execute_move(self, move):
        self.coords = move[0]
        self.changed(move, undo=False)

    def undo_move(self, move):
        self.coords = move[1]
        self.changed(move, undo=True)


class CoordinateRule(Rule, ABC):
    def __repr__(self):
        if self.name:
            return str(self.name) + str(self.get_coords())
        else:
            return str(type(self).__name__) + '(%s)' % self.sub_rule.__repr__()

    def get_coords(self):
        return self.get_bottom_rule().coords

    def string_legal(self):
        string_legal = []
        for new_coords, old_coords in self.get_legal_moves():
            string_legal.append(new_coords)
        return string_legal

    def execute_move(self, move):
        self.get_bottom_rule().execute_move(move)
        self.changed(move, undo=False)

    def undo_move(self, move):
        self.get_bottom_rule().undo_move(move)
        self.changed(move, undo=True)


# -- Pattern Rule -----------------------------------------

class PatternRule(CoordinateRule, ABC):
    @abstractmethod
    def get_step(self, coords):
        pass

    @abstractmethod
    def does_stop_on(self, coords):
        pass

    @abstractmethod
    def does_skip(self, coords):
        pass

    def generate_legal_moves(self):
        legal = self.sub_rule.get_legal_moves()
        edge = self.get_step(self.get_coords())
        checked = []
        while edge:
            new_edge = []
            for coords in edge:
                if not self.does_skip(coords) and (coords, self.get_coords()) not in legal:
                    legal.append((coords, self.get_bottom_rule().coords))
                if not self.does_stop_on(coords) and coords not in checked:
                    new_edge.extend(self.get_step(coords))
                checked.append(coords)
            edge = new_edge
        return legal


# -- Capture Rule -----------------------------------------

class CaptureRule(Rule, ABC):
    def __init__(self, **kwargs):
        self.radar = []
        super().__init__(**kwargs)

    def __repr__(self):
        if self.name:
            return str(self.name) + str(self.get_coords())
        else:
            return str(type(self).__name__) + '(%s)' % self.sub_rule.__repr__()

    def requirements(self):
        return {"does_attack_piece": lambda x: False}

    def get_coords(self):
        return self.get_bottom_rule().coords

    @staticmethod
    def move_to_string(move):
        sub_rule, (new_coords, old_coords), *to_capture = move
        string = str(new_coords)
        if to_capture:
            string = string + 'X' + str(to_capture).replace('[', '').replace(']', '')
        return string

    def does_attack_piece(self, piece):
        """
        :param piece: piece that self might be 'attacking'
        :return: true if self 'attacks' piece
        """
        for sub_rule, sub_move, *pieces_to_capture in self.get_legal_moves():
            if piece in pieces_to_capture:
                return True
        else:
            return False

    def is_attacked(self):
        for piece in self.game_state.get_top_rules(*self.radar):
            if piece.does_attack_piece(self):
                return True
        else:
            return False

    def execute_move(self, move):
        sub_rule, sub_move, *pieces_to_capture = move
        [piece.game_state.remove_rules(piece) for piece in pieces_to_capture]
        sub_rule.execute_move(sub_move)
        self.changed(move, undo=False)

    def undo_move(self, move):
        sub_rule, sub_move, *pieces_to_capture = move
        sub_rule.undo_move(sub_move)
        [piece.game_state.add_rules(piece) for piece in pieces_to_capture]
        self.changed(move, undo=True)


class SimpleCapture(CaptureRule):
    def generate_legal_moves(self):
        legal = []
        for new_coords, old_coords, *sub_captures in self.sub_rule.get_legal_moves():
            to_capture = []
            for top_rule in self.game_state.get_top_rules(*self.radar):
                if top_rule.get_bottom_rule().coords == new_coords:
                    to_capture.append(top_rule)
            legal.append((self.sub_rule, (new_coords, old_coords), *to_capture, *sub_captures))
        return legal


class NoCapture(CaptureRule):
    def generate_legal_moves(self):
        return self.sub_rule.get_legal_moves()


if __name__ == "__main__":
    pass
