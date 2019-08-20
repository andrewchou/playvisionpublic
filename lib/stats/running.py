import math

class RunningStats(object):
    def __init__(self):
        self.distance_by_player = {}

    def update(self, event, fps):
        if 'players' in event:
            for player_name, player_meta in event['players'].items():
                dist = math.sqrt(player_meta['vx'] ** 2 + player_meta['vy'] ** 2)
                if player_name not in self.distance_by_player:
                    self.distance_by_player[player_name] = 0.0
                self.distance_by_player[player_name] += dist / fps
