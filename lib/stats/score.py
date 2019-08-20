class ScoreStats(object):
    def __init__(self, teams):
        self.teams = teams
        self.score = {
            team['name']: 0 for team in teams.values()
        }

    def update(self, event):
        if event['type'] != 'GOAL':
            return
        team = self._get_team_that_scored(event=event)
        self.score[team] += 1

    def _get_team_that_scored(self, event):
        location = event['location']
        x = location['x']
        assert abs(x) > 50.0, location
        period = event['period']
        if x < 0:
            # Goal was on the LEFT so the RIGHT team scored.
            side_that_scored = 'RIGHT'
        else:
            # Goal was on the RIGHT so the LEFT team scored.
            side_that_scored = 'LEFT'

        scored = None
        for team in self.teams.values():
            side = team['sides'][period]
            assert side in ['RIGHT', 'LEFT'], side
            if side == side_that_scored:
                assert scored is None
                scored = team['name']
        assert scored is not None
        return scored
