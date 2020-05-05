from abc import ABC, abstractmethod
from equality_modifiers import EqualityByType
from player import PlayOn
import numpy as np


# Basic GameState

class GameState(ABC):
    """
    GameStates are moments during the play of a game. They do not hold the rules of the game or other methods that are
    properties of the game as a whole. GameStates should be initialized by a game and should always be paired with an
    appropriate game.
    """
    def __init__(self, players, player_to_move):
        """
        Initiates a "snapshot' of a board game. Includes who's turn it is, where the pieces are, etc.
        :param players: list of players in the game
        :param player_to_move: player whose turn it currently is
        """
        self.all_players = players
        if player_to_move:
            self.player_to_move = player_to_move
        else:
            self.player_to_move = players[0]

        for player in self.all_players:
            player.status = PlayOn()

    def players(self, *player_statuses, not_player=None):
        players = []
        for player in self.all_players:
            if (player.status in player_statuses or not player_statuses) and player != not_player:
                players.append(player)
        return players


# Basic Game

class Game(ABC, EqualityByType):
    """
    A Game is a set of methods outlining how a valid GameState under the Game changes as the players take actions. These
    methods often take a GameState as an input, and the GameState must be a valid GameState under Game, to aid with this,
    Game includes a method for creating a valid GameState (default_game_state).
    """
    @abstractmethod
    def default_game_state(self):
        """
        :return: the default valid game_state under game
        """
        pass

    @abstractmethod
    def utility(self, game_state):
        """
        :return: dictionary of values keyed by players, the values reflect how 'good' the GameState is for each player
                values should be 0 < x < 1,
                1 and 0 are reserved for when a player wins or looses respectively.
        """
        pass

    @abstractmethod
    def make_move(self, move, game_state):
        """
        changes the GameState as specified by 'move'
        changes must be recorded so that they can be undone by the 'revert' method
        """
        pass

    @abstractmethod
    def revert(self, game_state):
        """
        undoes the last move made to the GameState
        :return: True if revert is successful; False if no last move was recorded
        """
        pass

    @abstractmethod
    def legal_moves(self, game_state):
        """
        :return: list of legal moves available to 'player_to_move'
                 must be same type as moves must be same type as 'move' parameter in 'make_move'
        """
        pass

    @abstractmethod
    def evaluate_player_status(self, game_state, player):
        """
        find what player status "should be"
        :param game_state: game state that player belongs to
        :param player: player whose status is to be changed
        :return: PlayerStatusChange
        """
        pass

    @abstractmethod
    def neural_net_input(self, game_state):
        """
        :return: list of values
        """
        pass

    @abstractmethod
    def randomize_position(self, game_state):
        """
        randomizes all attributes of game_state that can vary during the course of a game
        """
        pass


# Static Methods

def n_max(game, game_state, max_depth):
    """
    Similar to minimax, evaluates a game tree given best play (according to the utility method) by all players
    takes an integer depth and examines the tree of game states after all possible moves sequences up to 'max_depth'
    subsequent moves. End nodes (found by depth or by a lack of any legal moves after them) are evaluated by the
    'utility' method. Utilities are assigned to parent game states by which of the children is the best for the
    'player_to_move' of the parent. The resulting utility assigned to the original game state is returned
    :param game: game of game_state
    :param game_state: game state to be tested
    :param max_depth: integer, indicates how many moves to the bottom of the value search tree
    :return: dictionary of values keyed by payers
    """
    move_tree = [game.legal_moves(game_state)]  # tracks unexplored moves of current game state and its parents
    utility_tree = [[]]  # gets an empty list for every node in the current branch, to be populated later
    depth = 0  # start at depth 0

    while True:
        # print(move_tree)
        # Starting from a new position
        player_to_maximize = game_state.player_to_move

        # In the middle of the tree? Go down.
        if depth != max_depth and move_tree[-1]:  # if in the middle of an unexplored branch of the game state tree
            move = move_tree[-1].pop(0)  # grab the first unexplored move and remove it from the move tree

            game.make_move(move, game_state)  # make the move on the game state to convert to child game state
            utility_tree.append([])  # tack on an empty list for utilities
            move_tree.append(game.legal_moves(game_state))  # every legal move from the new game state is a new branch
            depth = depth + 1  # record the change in depth
            continue  # rerun loop from new game state

        # Nowhere to go down? Go up.
        else:
            if (not game.legal_moves(game_state)) or (depth == max_depth):  # only need utility from bottom of the tree
                utility_tree[-1].append(game.utility(game_state))  # add utility to the list of the parent

            # If you're not at the top, you can go up
            if depth != 0:  # unless at the top...
                game.revert(game_state)  # revert from current position to parent position
                # utility of the position is the best child utility for the player to move
                # utility of the position is added to the utility list of the parent
                utility_tree[-2].append(dictionary_max(player_to_maximize, utility_tree.pop(-1)))
                move_tree.pop(-1)  # cut the explored branch from the tree
                depth = depth - 1  # record change in depth
                continue  # rerun loop from new game state
            # Can't go down or up? Must be done.
            else:
                # utility of the position is the best child utility for the player to move
                n_max_utility = dictionary_max(player_to_maximize, utility_tree[-1])
                break
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
        for player in game_state.players:
            neural_net_output.append(n_max(game, game_state, n_max_depth)[player])  # generate output from n_max function
        training_data.append((np.asarray(game.neural_net_input(game_state)), np.asarray(neural_net_output)))
    return training_data  # don't forget to return


def dictionary_max(key, dictionaries):
    """

    :param key: a key in the dictionary
    :param dictionaries: list of dictionaries with the same keys, dictionary entries must be ordered (<,> defined)
    :return: the dictionary where the value of dictionary[key] is maximized
    """
    current_max = dictionaries[0]
    for dictionary in dictionaries:
        if dictionary[key] > current_max[key]:
            current_max = dictionary
    return current_max