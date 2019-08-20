from lib.stats.running import RunningStats
from lib.stats.score import ScoreStats
from lib.stats.touches import TouchStats

class StreamingStats(object):
    def __init__(self, dataset):
        self.running_stats = RunningStats()
        self.touch_stats = TouchStats()
        self.score_stats = ScoreStats(teams=dataset['teams'])

    def update(self, event, fps):
        self.running_stats.update(event=event, fps=fps)
        self.touch_stats.update(event=event)
        self.score_stats.update(event=event)
