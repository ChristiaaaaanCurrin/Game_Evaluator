from abc import ABC, abstractmethod
from random import sample, random


class Evaluator(ABC):
    def __init__(self, **kwargs):
        self.__dict__.update(**kwargs)

    @abstractmethod
    def evaluate(self, game):
        pass

    def explore(self, game, depth, width=-1, temp=1, k=1):
        """
        searches game tree and applies max_n algorithm to evaluate current game
        :param game: game to be explored
        :param depth: maximum depth of search
        :param width: maximum branches from this node
        :param temp: probability of selecting the child branches randomly
        :param k: depth of intermediate searches for determining continuation line
        :return: evaluation of current game ( = utility from the end of the expected branch)
        """
        player = game.get_player()
        legal = game.get_legal_moves()
        if 0 <= width < len(legal):
            if temp < random():
                def evaluate(m):
                    game.execute_move(m)
                    utility = self.explore(game, k)[player]
                    game.undo_move(m)
                    return utility
                legal = sorted(legal, key=evaluate)[:width]
            else:
                legal = sample(game.get_legal_moves(), width)
        if depth == 0 or not legal:
            return self.evaluate(game)
        else:
            utilities = []
            for move in legal:
                game.execute_move(move)
                utilities.append(self.explore(depth - 1, width, temp))
                game.undo_move(move)
            return max_by_key(player, utilities)


def max_by_key(key, dictionaries):
    """
    :param key: a key in the dictionary
    :param dictionaries: list of dictionaries with the same keys, dictionary entries must be ordered (<, > defined)
    :return: the dictionary where the value of dictionary[key] is maximized
    """
    current_max = dictionaries[0]
    for dictionary in dictionaries:
        if dictionary[key] > current_max[key]:
            current_max = dictionary
    return current_max

'''
def max_n(game, max_depth):
    """
    Similar to minimax, evaluates a game tree given best play (according to the utility method) by all players
    takes an integer depth and examines the tree of game states after all possible moves sequences up to 'max_depth'
    subsequent moves. End nodes (found by depth or by a lack of any legal moves after them) are evaluated by the
    'utility' method. Utilities are assigned to parent game states by which of the children is the best for the
    'player_to_move' of the parent. The resulting utility assigned to the original game state is returned
    :param game: game to be tested
    :param max_depth: integer, indicates how many moves to the bottom of the value search tree
    :return: dictionary of values keyed by payers
    """
    move_tree = [game.get_legal_moves()]  # tracks unexplored moves of current game state and its parents
    utility_tree = [[]]  # gets an empty list for every node in the current branch, to be populated later
    depth = 0  # start at depth 0

    while True:
        # Starting from a new position
        player_to_maximize = game.get_bottom_rule().player

        # In the middle of the tree? Go down.
        if depth != max_depth and move_tree[-1]:  # if in the middle of an unexplored branch of the game state tree
            move = move_tree[-1].pop(0)  # grab the first unexplored move and remove it from the move tree

            game.execute_move(move)  # make the move on the game_state
            utility_tree.append([])  # tack on an empty list for utilities
            move_tree.append(game.get_legal_moves())  # every legal move from the new_game state is a new branch
            depth = depth + 1  # record the change in depth
            continue  # rerun loop from new game state

        # Nowhere to go down? Go up.
        else:
            if (not game.get_legal_moves()) or (depth == max_depth):  # only need utility from bottom of the tree
                utility_tree[-1].append(game.get_utility())  # add utility to the list of the parent

            # If you're not at the top, you can go up
            if depth != 0:  # unless at the top...
                game.revert()  # revert from current position to parent position
                # utility of the position is the best child utility for the player to move
                # utility of the position is added to the utility list of the parent
                utility_tree[-2].append(max_by_key(player_to_maximize, utility_tree.pop(-1)))
                move_tree.pop(-1)  # cut the explored branch from the tree
                depth = depth - 1  # record change in depth
                continue  # rerun loop from new game state
            # Can't go down or up? Must be done.
            else:
                # utility of the position is the best child utility for the player to move
                n_max_utility = max_by_key(player_to_maximize, utility_tree[-1])
                break  # exit the loop
    return n_max_utility  # don't forget why you came here


def neural_net_training_data(game, game_state, n_max_depth, batch_size):
    """
    creates a list containing 'batch size' tuples of inputs and outputs for the neural net
    inputs are lists of values that contain all the information for the position
    outputs are lists of values that contain the n_max evaluation for the position to depth 'n_max_depth'
    :param game: game of game_state
    :param game_state: game state to be evaluated
    :param n_max_depth: integer, indicates the depth to which the neural net inputs are evaluated
    :param batch_size: integer, indicates the number of positions used as training data
    :return: list of tuples of lists of values
    """
    training_data = []
    for i in range(batch_size):
        game.randomize_position(game_state)  # create random position
        neural_net_output = []
        for player in game_state.get_players:
            neural_net_output.append(max_n(game_state, n_max_depth)[player])  # generate output from n_max function
        training_data.append((np.asarray(game.neural_net_input(game_state)), np.asarray(neural_net_output)))
    return training_data  # don't forget to return

'''