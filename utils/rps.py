from os.path import join, isdir
from os import mkdir
from json import load, dump
from copy import deepcopy

class BadMoveError(BaseException): pass

class RockPaperScissors:

    _empty_player = {'wins': 0, 'losses': 0, 'draws': 0}
    _winning_moves = {
            'rock':     'paper',
            'paper':    'scissors',
            'scissors': 'rock'
            }
    _losing_moves = {
            'rock': 'scissors',
            'scissors': 'paper',
            'paper': 'rock'
            }

    def __init__(self, conf_dir):
        self.conf_dir = conf_dir
        if not isdir(conf_dir):
            mkdir(conf_dir)
        self.players_file = join(conf_dir, 'players')
        self.games_file = join(conf_dir, 'games')
        self.optouts_file = join(conf_dir, 'optouts')
        self.gamelog_file = join(conf_dir, 'gamelogs')

    def _new_player(self):
        return deepcopy(self._empty_player)

    def _load_players(self):
        try:
            with open(self.players_file, 'r') as f:
                return load(f)
        except IOError:
            return {}

    def _save_players(self, players):
        with open(self.players_file, 'w') as f:
            dump(players, f)

    def get_winning_move(self, move):
        return self._winning_moves[move]

    def get_losing_move(self, move):
        return self._losing_moves[move]

    def get_move(self, cmd):
        # To add more moves we can just add elifs here, as well as to play().
        if 'rock'.startswith(cmd):
            return 'rock'
        elif 'paper'.startswith(cmd):
            return 'paper'
        elif 'scissors'.startswith(cmd):
            return 'scissors'
        else:
            return None

    def _play(self, pm_map):
        """Takes a dict mapping players to their (valid) moves.
        Returns the name of the winning player, or None if it is a draw."""
        (player1, move1), (player2, move2) = zip(pm_map.keys(), pm_map.values())
        mp_map = {move1: player1, move2: player2}
        moves = {move1, move2}
        if len(moves) == 1:
            return False
        elif moves == {'rock', 'paper'}:
            return mp_map['paper']
        elif moves == {'paper', 'scissors'}:
            return mp_map['scissors']
        elif moves == {'scissors', 'rock'}:
            return mp_map['rock']

    def game(self, pm_map):
        """Takes a dict mapping players to their (valid) moves."""
        past_players = self._load_players()
        players = {p: past_players.get(p, self._new_player()) for p in pm_map}
        winner = self._play(pm_map)
        for p in players:
            if winner == False:
                players[p]['draws'] += 1
            elif p == winner:
                players[p]['wins'] += 1
            else:
                players[p]['losses'] += 1
        past_players.update(players)
        self._save_players(past_players)
        self._log_game(pm_map, winner)
        return winner

    def _load_games(self):
        try:
            with open(self.games_file, 'r') as f:
                return load(f)
        except IOError:
            return {}

    def _save_games(self, games):
        with open(self.games_file, 'w') as f:
            dump(games, f)

    def get_player_games(self, player):
        all_games = self._load_games()
        return all_games.get(player, {})

    def challenge(self, challor, challee, move):
        # This function is a bit of a mess.
        # Basically we have to edit each both players' games separately.
        # Remember:
        # - If neither player has previously challenged the other, neither will
        #   be in the other's games.
        # - If A has challenged B previously, A's games will contain (B: A's move)
        #   and B's games will contain (A: None).
        # - If each player challenges the other, the game is played to completion
        #   and each player will be removed from the other's games.
        current_games = self._load_games()
        challor_games = current_games.get(challor, {})
        challee_games = current_games.get(challee, {})
        if challee_games.get(challor, None) is not None:
            # challee has previously challenged challor
            result = self.game({challor: move, challee: challee_games.pop(challor)})
            challor_games.pop(challee)
        else:
            # challee has not previously challenged challor
            challor_games[challee] = move
            challee_games[challor] = None
            result = None
        current_games[challor] = challor_games
        current_games[challee] = challee_games
        self._save_games(current_games)
        return result

    def _log_game(self, pm_map, winner):
        (play1, move1), (play2, move2) = zip(pm_map.keys(), pm_map.values())
        with open(self.gamelog_file, 'a') as f:
            f.write('{} {} {} {} {}\n'.format(play1, move1, play2, move2, winner))

    def get_optouts(self):
        try:
            with open(self.optouts_file, 'r') as f:
                return set(line.strip() for line in f)
        except IOError:
            return set()

    def _save_optouts(self, optouts):
        with open(self.optouts_file, 'w') as f:
            f.write('\n'.join(optouts))

    def toggle_optout(self, player):
        optouts = self.get_optouts()
        if player in optouts:
            optouts.remove(player)
            out = False
        else:
            optouts.add(player)
            out = True
        self._save_optouts(optouts)
        return out
