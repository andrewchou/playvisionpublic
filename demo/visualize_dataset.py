import argparse
import copy
import json

import numpy as np
import cv2
import time

from lib.ball.position.rough_estimate import estimate_ball_position
from lib.geometry.point import Point
from lib.stats.streaming import StreamingStats
from lib.unicode.mapping import best_effort_unicode_to_ascii

RED = (0, 0, 255)
GREEN = (0, 255, 0)
MEDIUM_BLUE = (255, 128, 0)
GRAY = (128, 128, 128)
WHITE = (255, 255, 255)
REF_NAME = 'REFEREE'

def parse_args():
    parser = argparse.ArgumentParser(description='Visualize Dataset')
    parser.add_argument('--dataset', type=str, help='The filename of the json dataset')
    args = parser.parse_args()
    return args

def load_dataset(args):
    with open(args.dataset) as inf:
        dataset = json.loads(inf.read())
        assert dataset['version'] == 0, dataset['version']
        return dataset

def get_events_by_period(events):
    periods = []
    for event in events:
        period = event['period']
        if period >= len(periods):
            periods.append([])
        periods[period].append(event)
    assert len(periods) >= 2, len(periods)
    for i, period in enumerate(periods):
        assert period, i
    return periods

def get_players(dataset):
    players = copy.deepcopy(dataset['teams']['home']['players'])
    players.update(dataset['teams']['away']['players'])
    return players

def get_teams(dataset):
    color_by_team = {}
    color_by_team[dataset['teams']['home']['name']] = RED
    color_by_team[dataset['teams']['away']['name']] = MEDIUM_BLUE
    color_by_team[REF_NAME] = GREEN
    team_by_player = {}
    for team in (dataset['teams']['home'], dataset['teams']['away']):
        for player_name in team['players']:
            team_by_player[player_name] = team['name']
    team_by_player[REF_NAME] = REF_NAME
    return team_by_player, color_by_team

def write_text_on_frame(frame, text, color=RED, bottom_left_corner_of_text=(30, 40), thickness=1, font_scale=0.5):
    font = cv2.FONT_HERSHEY_SIMPLEX
    cv2.putText(frame, text, bottom_left_corner_of_text, font, font_scale, color, thickness)

def draw_line(frame, start, end, magnify, center):
    start = (start * magnify + center).round()
    end = (end * magnify + center).round()
    cv2.line(frame, start, end, WHITE, 1)

def get_2d_drawing(
    unit, stadium, team_by_player, color_by_team, event, teams,
    ball_position_by_time, stats,
):
    current_players = event['players']
    field_height = stadium['field_height']
    field_width = stadium['field_width']
    height = 100
    width = 130
    magnify = 5
    frame = np.zeros(shape=(
            magnify * height,
            magnify * width + 500,
            3,
        ),
        dtype=np.uint8)

    # Draw field
    center = Point(x=int(width / 2.0), y=int(height / 2.0)) * magnify
    top_left = Point(x=-int(field_width / 2.0), y=-int(field_height / 2.0))
    top_right = Point(x=int(field_width / 2.0), y=-int(field_height / 2.0))
    top_center = Point(x=0, y=-int(field_height / 2.0))
    bottom_left = Point(x=-int(field_width / 2.0), y=int(field_height / 2.0))
    bottom_right = Point(x=int(field_width / 2.0), y=int(field_height / 2.0))
    bottom_center = Point(x=0, y=int(field_height / 2.0))
    # Frame
    draw_line(frame, top_left, top_right, magnify, center)
    draw_line(frame, top_right, bottom_right, magnify, center)
    draw_line(frame, bottom_right, bottom_left, magnify, center)
    draw_line(frame, bottom_left, top_left, magnify, center)
    draw_line(frame, top_center, bottom_center, magnify, center)
    # Left 18
    draw_line(frame, Point(x=-int(field_width / 2.0), y=-22), Point(x=-int(field_width / 2.0) + 18, y=-22), magnify, center)
    draw_line(frame, Point(x=-int(field_width / 2.0), y=22), Point(x=-int(field_width / 2.0) + 18, y=22), magnify, center)
    draw_line(frame, Point(x=-int(field_width / 2.0) + 18, y=-22), Point(x=-int(field_width / 2.0) + 18, y=22), magnify, center)
    # Right 18
    draw_line(frame, Point(x=int(field_width / 2.0), y=-22), Point(x=int(field_width / 2.0) - 18, y=-22), magnify, center)
    draw_line(frame, Point(x=int(field_width / 2.0), y=22), Point(x=int(field_width / 2.0) - 18, y=22), magnify, center)
    draw_line(frame, Point(x=int(field_width / 2.0) - 18, y=-22), Point(x=int(field_width / 2.0) - 18, y=22), magnify, center)
    # Left 6
    draw_line(frame, Point(x=-int(field_width / 2.0), y=-10), Point(x=-int(field_width / 2.0) + 6, y=-10), magnify, center)
    draw_line(frame, Point(x=-int(field_width / 2.0), y=10), Point(x=-int(field_width / 2.0) + 6, y=10), magnify, center)
    draw_line(frame, Point(x=-int(field_width / 2.0) + 6, y=-10), Point(x=-int(field_width / 2.0) + 6, y=10), magnify, center)
    # Right 6
    draw_line(frame, Point(x=int(field_width / 2.0), y=-10), Point(x=int(field_width / 2.0) - 6, y=-10), magnify, center)
    draw_line(frame, Point(x=int(field_width / 2.0), y=10), Point(x=int(field_width / 2.0) - 6, y=10), magnify, center)
    draw_line(frame, Point(x=int(field_width / 2.0) - 6, y=-10), Point(x=int(field_width / 2.0) - 6, y=10), magnify, center)
    # PKs
    left_pk = (Point(x=-int(field_width / 2.0) + 12, y=0) * magnify + center).round()
    right_pk = (Point(x=int(field_width / 2.0) - 12, y=0) * magnify + center).round()
    cv2.circle(frame, left_pk, 1, WHITE, 1)
    cv2.circle(frame, right_pk, 1, WHITE, 1)
    deg = np.arcsin(.8) * 180 / np.pi
    cv2.ellipse(frame, left_pk, (10 * magnify, 10 * magnify), 0, -deg, deg, WHITE, thickness=1, lineType=8, shift=0)
    cv2.ellipse(frame, right_pk, (10 * magnify, 10 * magnify), 0, 180-deg, 180+deg, WHITE, thickness=1, lineType=8, shift=0)
    # Center
    cv2.circle(frame, center, 10 * magnify, WHITE, 1)

    # Draw players
    radius = 2
    thickness = 2
    for player_name, player_meta in current_players.items():
        team = team_by_player[player_name]
        color = color_by_team[team]
        point = (Point(x=player_meta['x'], y=player_meta['y'])) * magnify + center
        velocity = Point(x=player_meta['vx'], y=player_meta['vy']) * magnify
        rounded_point = point.round()
        end_velocity = (point + velocity).round()
        cv2.line(frame, rounded_point, end_velocity, WHITE, thickness)
        cv2.circle(frame, rounded_point, radius, color, thickness)

    # Draw ball
    ball_position = ball_position_by_time.get(event['time'])
    if ball_position is not None:
        cv2.circle(frame, (ball_position * magnify + center).round(), radius, WHITE, thickness)

    # Draw camera
    if 'camera' in event:
        camera_polygon = [
            (Point(**pt) * magnify + center).round()
            for pt in event['camera']
        ]
        for i in range(len(camera_polygon)):
            j = (i + 1) % len(camera_polygon)
            cv2.line(
                img=frame,
                pt1=camera_polygon[i],
                pt2=camera_polygon[j], color=WHITE, thickness=2)

    # Draw metadata
    period = event['period']
    assert isinstance(period, int), period
    period_text = {
        0: '1st Half',
        1: '2nd Half',
        2: '1st Overtime',
        3: '2nd Overtime',
    }[period]
    seconds = event['time']
    minutes = int(seconds // 60)
    seconds = seconds % 60
    write_text_on_frame(
        frame=frame, text='%s  %s : %.2f' % (period_text, minutes, seconds), color=GREEN,
        bottom_left_corner_of_text=(int((width - field_width) / 2 * magnify), 40))
    for team in teams.values():
        color = color_by_team[team['name']]
        side = team['sides'][period]
        if side == 'LEFT':
            write_text_on_frame(
                frame=frame, text='%s (%d)' % (team['name'], stats.score_stats.score[team['name']]),
                color=color, bottom_left_corner_of_text=(int((width - field_width) / 2 * magnify), magnify * height - 35))
        elif side == 'RIGHT':
            write_text_on_frame(
                frame=frame, text='%s (%d)' % (team['name'], stats.score_stats.score[team['name']]),
                color=color, bottom_left_corner_of_text=(int(magnify * width / 2), magnify * height - 35))
        else:
            assert 0, side

    # Draw running stats
    write_text_on_frame(
        frame=frame, text='Distance (meters)',
        color=WHITE, bottom_left_corner_of_text=(magnify * width, 20))
    for rank, (player_name, dist) in enumerate(sorted(
        stats.running_stats.distance_by_player.items(), key=lambda d: d[1], reverse=True,
    )):
        team = team_by_player[player_name]
        color = color_by_team[team]
        assert unit == 'YARD', unit
        meters = dist * 36 * 2.54 / 100
        write_text_on_frame(
            frame=frame, text='%dm %s' % (int(meters), best_effort_unicode_to_ascii(u=player_name)),
            color=color, bottom_left_corner_of_text=(magnify * width, 20 * (rank + 2)))
    # Draw touch stats
    write_text_on_frame(
        frame=frame, text='Touches',
        color=WHITE, bottom_left_corner_of_text=(magnify * width + 250, 20))
    for rank, (player_name, num_touches) in enumerate(sorted(
        stats.touch_stats.touches_by_player.items(), key=lambda d: d[1], reverse=True,
    )):
        team = team_by_player[player_name]
        color = color_by_team[team]
        write_text_on_frame(
            frame=frame, text='%d %s' % (num_touches, best_effort_unicode_to_ascii(u=player_name)),
            color=color, bottom_left_corner_of_text=(magnify * width + 250, 20 * (rank + 2)))

    return frame

def get_ball_position_by_time(events):
    touch_types = set([
        'TOUCH',
        'THROW_IN',
        'GOAL_KICK',
        'CORNER',
        'KICKOFF',
        'PK',
        'DIRECT_FREE_KICK',
        'INDIRECT_FREE_KICK',
    ])
    event_types_with_ball_locations = set([
        'BALL_OUT_FOR_THROW_IN',
        'BALL_OUT_FOR_GOAL_KICK',
        'BALL_OUT_FOR_CORNER',
        'GOAL',
        'HANDBALL',
    ])
    ball_position_by_time = {}
    for event in events:
        if event['type'] in touch_types:
            touch_player_name = event['touch']
            touch_player_meta = event['players'][touch_player_name]
            ball_position_by_time[event['time']] = Point(
                x=touch_player_meta['x'], y=touch_player_meta['y'])
        elif event['type'] in event_types_with_ball_locations:
            location = event['location']
            ball_position_by_time[event['time']] = Point(
                x=location['x'], y=location['y'])
    prev_touch_event = None
    events_since_prev_touch = []
    for event in events:
        if (event['type'] in touch_types) or (event['type'] in event_types_with_ball_locations):
            if prev_touch_event:
                prev_time = prev_touch_event['time']
                prev_ball_pos = ball_position_by_time[prev_time]
                next_time = event['time']
                next_ball_pos = ball_position_by_time[next_time]
                for cur_event in events_since_prev_touch:
                    cur_time = cur_event['time']
                    cur_ball_pos = estimate_ball_position(
                        prev_time=prev_time, prev_ball_pos=prev_ball_pos,
                        next_time=next_time, next_ball_pos=next_ball_pos,
                        cur_time=cur_time,
                    )
                    ball_position_by_time[cur_time] = cur_ball_pos
            prev_touch_event = event
            events_since_prev_touch = []
        else:
            events_since_prev_touch.append(event)
    return ball_position_by_time

if __name__ == '__main__':
    args = parse_args()
    dataset = load_dataset(args=args)
    players = get_players(dataset=dataset)
    team_by_player, color_by_team = get_teams(dataset=dataset)
    scenes_by_period = dataset['periods']
    assert isinstance(scenes_by_period, list)
    stats = StreamingStats(dataset=dataset)
    max_wait_ms = 1000
    t0 = time.time()
    for scene in scenes_by_period:
        for events_for_scene in scene:
            ball_position_by_time = get_ball_position_by_time(events=events_for_scene)
            for event in events_for_scene:
                stats.update(event=event, fps=dataset['fps'])
                if 'players' in event:
                    frame = get_2d_drawing(
                        unit=dataset['unit'],
                        stadium=dataset['stadium'],
                        team_by_player=team_by_player,
                        color_by_team=color_by_team,
                        event=event,
                        teams=dataset['teams'],
                        ball_position_by_time=ball_position_by_time,
                        stats=stats)
                    cv2.imshow('frame', frame)
                    # Wait so we can watch in real time (but if there's a gap just wait for 1 second).
                    ellapsed = time.time() - t0
                    wait_time_ms = int((event['time'] - ellapsed) * 1000)
                    if wait_time_ms > max_wait_ms:
                        t0 -= (wait_time_ms - max_wait_ms) / 1000.0
                    cv2.waitKey(min(max_wait_ms, max(1, wait_time_ms)))
