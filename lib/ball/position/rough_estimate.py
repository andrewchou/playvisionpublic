from lib.geometry.point import Point


# TODO This is a super hacky estimate.
def estimate_ball_position(
    prev_time, prev_ball_pos, next_time, next_ball_pos, cur_time,
):
    if cur_time == prev_time:
        return prev_ball_pos
    if cur_time == next_time:
        return next_ball_pos
    assert prev_time < cur_time < next_time, (prev_time, cur_time, next_time)
    frac = (cur_time - prev_time) / (next_time - prev_time)
    assert isinstance(prev_ball_pos, Point), prev_ball_pos
    assert isinstance(next_ball_pos, Point), next_ball_pos
    return prev_ball_pos * (1.0 - frac) + next_ball_pos * frac
