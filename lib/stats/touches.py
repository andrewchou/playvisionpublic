class TouchStats(object):
    def __init__(self):
        self.touches_by_player = {}

    def update(self, event):
        if 'touch' in event:
            player_name = event['touch']
            if player_name not in self.touches_by_player:
                self.touches_by_player[player_name] = 0
            self.touches_by_player[player_name] += 1
