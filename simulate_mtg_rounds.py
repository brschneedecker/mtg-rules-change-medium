import numpy as np
import pandas as pd
# from plotnine import ggplot, aes, geom_density, geom_vline, theme_classic, xlim, 
import plotnine as plt

NUM_MATCHES_PER_ROUND = 85
NUM_MATCHES_PER_ROUND_HUGE = 350
NUM_MATCHES_PER_ROUND_TINY = 16
NUM_MINUTES_PER_ROUND = 50
PROB_WIN_ON_PLAY = 0.55

CASE_1_AVG_MINUTES_PER_GAME = 13.5
CASE_1_SD_MINUTES_PER_GAME = 2.5

CASE_2_BLOWOUT_PROB = 0.10
CASE_2_LOW_SCALE_PARAM = 2.5
CASE_2_LOW_SHAPE_PARAM = 2
CASE_2_HIGH_AVG_MINUTES_PER_GAME = 13.5
CASE_2_HIGH_SD_MINUTES_PER_GAME = 2.5

NUM_ROUNDS_TO_SIMULATE = 1000

prob_of_two_games_new = PROB_WIN_ON_PLAY * PROB_WIN_ON_PLAY + (1 - PROB_WIN_ON_PLAY) * PROB_WIN_ON_PLAY
prob_of_three_games_new = 1 - prob_of_two_games_new
prob_of_two_games_old = PROB_WIN_ON_PLAY * (1 - PROB_WIN_ON_PLAY) + (1 - PROB_WIN_ON_PLAY) * (1 - PROB_WIN_ON_PLAY)
prob_of_three_games_old = 1 - prob_of_two_games_old


def gen_num_games(prob: float):
    """ Returns number of games in the round (either 2 or 3) """
    return np.random.binomial(n=1, p=prob, size=1) + 2


def gen_norm_dist_sum(avg: float, sd: float, size):
    """ Generate sum of normal distribution """
    return sum(np.random.normal(loc=avg, scale=sd, size=size))


def gen_gamma_dist_sum(shape: float, scale: float):
    """ Generate sum of gamma distribution """
    return sum(np.random.gamma(shape=shape, scale=scale, size=2))


def is_blowout(prob: float):
    """ Returns True is round is blowout, False otherwise """
    return bool(np.random.binomial(n=1, p=prob, size=1))


def simulate_match(
    mean_length: float, 
    sd: float, 
    prob_of_three_games: float, 
    is_blowout: bool, 
    gamma_shape: float, 
    gamma_scale: float
):
    """ Simulate the length of a MTG match """

    if is_blowout:
        match_length = gen_gamma_dist_sum(shape=gamma_shape, scale=gamma_scale)
    else:
        num_games = gen_num_games(prob=prob_of_three_games)
        match_length = gen_norm_dist_sum(mean_length, sd, num_games)

    return match_length


def simulate_match_lengths_in_round(
        num_matches_per_round: int,
        average_minutes_per_game: float,
        sd_minutes_per_game: float,
        prob_of_three_games: float = prob_of_three_games_new,
        prob_of_blowout: float = 0,
        blowout_shape_parameter: float = 0,
        blowout_scale_parameter: float = 0,
):
    """ Simulate match lengths for an entire tournament round """

    match_lengths = [simulate_match(average_minutes_per_game, 
                                    sd_minutes_per_game, 
                                    prob_of_three_games,
                                    is_blowout(prob_of_blowout),
                                    blowout_shape_parameter,
                                    blowout_scale_parameter) 
                     for i in range(num_matches_per_round)]

    return match_lengths


def does_round_go_to_time(match_lengths_in_round: list):
    return sum(np.greater_equal(match_lengths_in_round, NUM_MINUTES_PER_ROUND)) > 0


def find_prob_of_going_to_time(
        num_rounds_to_simulate: int,
        num_matches_per_round: int,
        average_minutes_per_game: float,
        sd_minutes_per_game: float,
        prob_of_three_games=prob_of_three_games_new,
        prob_of_blowout: float = 0,
        blowout_shape_parameter: float = 0,
        blowout_scale_parameter: float = 0
):
    """ 
    Simulate many rounds of gameplay and record how 
    many rounds go to time 
    """
    # went_to_time = []
    # for i in range(num_rounds_to_simulate):
    #     went_to_time.append(
    #         does_round_go_to_time(
    #             simulate_match_lengths_in_round(
    #                 num_matches_per_round=num_matches_per_round,
    #                 prob_of_blowout=prob_of_blowout,
    #                 blowout_shape_parameter=blowout_shape_parameter,
    #                 blowout_scale_parameter=blowout_scale_parameter,
    #                 average_minutes_per_game=average_minutes_per_game,
    #                 sd_minutes_per_game=sd_minutes_per_game,
    #                 prob_of_three_games=prob_of_three_games
    #             )
    #         )
    #     )
    
    went_to_time = [does_round_go_to_time(
                simulate_match_lengths_in_round(
                    num_matches_per_round=num_matches_per_round,
                    prob_of_blowout=prob_of_blowout,
                    blowout_shape_parameter=blowout_shape_parameter,
                    blowout_scale_parameter=blowout_scale_parameter,
                    average_minutes_per_game=average_minutes_per_game,
                    sd_minutes_per_game=sd_minutes_per_game,
                    prob_of_three_games=prob_of_three_games
                )
            ) for i in range(num_rounds_to_simulate)]

    return sum(went_to_time) / len(went_to_time)

def plot1(match_lengths_from_one_round: list):
    """ Density plot for match lengths, new rules, no blowouts, 85 matches/round """

    match_lengths = pd.DataFrame({'Match length': match_lengths_from_one_round})
    (
            plt.ggplot(match_lengths, plt.aes(x='Match length'))
            + plt.geom_density()
            + plt.geom_vline(xintercept=50, color='black', size=2)
            + plt.theme_classic()
            + plt.xlim([0, 55])
    ).save(filename='figures/match_length_density_plot.png')


def plot2():
    """ Plot go-to-time probability, new vs. old rules, no blowouts, 85 matches/round """

    average_minutes_per_game_values = [12, 12.5, 13, 13.5, 14, 14.5, 15]
    go_to_time_probs_new = []
    go_to_time_probs_old = []

    loop_dict = {"old": (go_to_time_probs_old, prob_of_three_games_old),
                 "new": (go_to_time_probs_new, prob_of_three_games_new)}

    for key in loop_dict.keys():
        loop_dict[key][0] = [find_prob_of_going_to_time(
            num_rounds_to_simulate=10000,
            num_matches_per_round=NUM_MATCHES_PER_ROUND,
            average_minutes_per_game=average_minutes_per_game_values[i],
            sd_minutes_per_game=CASE_1_SD_MINUTES_PER_GAME,
            prob_of_three_games=loop_dict[key][1]
            ) for i in range(len(average_minutes_per_game_values))]

    time_prob_data = pd.DataFrame({
        'Average minutes per game': np.concatenate([
            average_minutes_per_game_values,
            average_minutes_per_game_values
        ]),
        'P(Go to time)': np.concatenate([
            go_to_time_probs_new,
            go_to_time_probs_old
        ]),
        'Rules': np.concatenate([
            np.repeat('New', len(average_minutes_per_game_values)),
            np.repeat('Old', len(average_minutes_per_game_values))
        ])
    })
    (
        plt.ggplot(time_prob_data, plt.aes(x='Average minutes per game', y='P(Go to time)', color='Rules'))
        + plt.geom_line()
        + plt.geom_point()
        + plt.ylim([0, 1])
        + plt.theme_classic()
    ).save(filename='figures/go_to_time_prob_plot.png')


def main():
    """ Run all simualtions and generate figures """

    np.random.seed(23)

    match_lengths_from_one_round = simulate_match_lengths_in_round(
        num_matches_per_round=NUM_MATCHES_PER_ROUND,
        average_minutes_per_game=CASE_1_AVG_MINUTES_PER_GAME,
        sd_minutes_per_game=CASE_1_SD_MINUTES_PER_GAME
    )

    plot1(match_lengths_from_one_round)

    # match_lengths = pd.DataFrame({'Match length': match_lengths_from_one_round})
    # (
    #         plt.ggplot(match_lengths, plt.aes(x='Match length'))
    #         + plt.geom_density()
    #         + plt.geom_vline(xintercept=50, color='black', size=2)
    #         + plt.theme_classic()
    #         + plt.xlim([0, 55])
    # ).save(filename='figures/match_length_density_plot.png')

    # Plot go-to-time probability, new vs. old rules, no blowouts, 85 matches/round
    average_minutes_per_game_values = [12, 12.5, 13, 13.5, 14, 14.5, 15]
    # go_to_time_probs_new = []
    # go_to_time_probs_old = []

    # loop_dict = {"old": (go_to_time_probs_old, prob_of_three_games_old),
    #              "new": (go_to_time_probs_new, prob_of_three_games_new)}

    # for key in loop_dict.keys():
    #     loop_dict[key][0] = [find_prob_of_going_to_time(
    #         num_rounds_to_simulate=10000,
    #         num_matches_per_round=NUM_MATCHES_PER_ROUND,
    #         average_minutes_per_game=average_minutes_per_game_values[i],
    #         sd_minutes_per_game=CASE_1_SD_MINUTES_PER_GAME,
    #         prob_of_three_games=loop_dict[key][1]
    #         ) for i in range(len(average_minutes_per_game_values))]            

    # for i in range(len(average_minutes_per_game_values)):
    #     go_to_time_probs_new.append(
    #         find_prob_of_going_to_time(
    #             num_rounds_to_simulate=10000,
    #             num_matches_per_round=NUM_MATCHES_PER_ROUND,
    #             average_minutes_per_game=average_minutes_per_game_values[i],
    #             sd_minutes_per_game=CASE_1_SD_MINUTES_PER_GAME
    #         )
    #     )
    #     go_to_time_probs_old.append(
    #         find_prob_of_going_to_time(
    #             num_rounds_to_simulate=10000,
    #             num_matches_per_round=NUM_MATCHES_PER_ROUND,
    #             average_minutes_per_game=average_minutes_per_game_values[i],
    #             sd_minutes_per_game=CASE_1_SD_MINUTES_PER_GAME,
    #             prob_of_three_games=prob_of_three_games_old
    #         )
    #     )

    # time_prob_data = pd.DataFrame({
    #     'Average minutes per game': np.concatenate([
    #         average_minutes_per_game_values,
    #         average_minutes_per_game_values
    #     ]),
    #     'P(Go to time)': np.concatenate([
    #         go_to_time_probs_new,
    #         go_to_time_probs_old
    #     ]),
    #     'Rules': np.concatenate([
    #         np.repeat('New', len(average_minutes_per_game_values)),
    #         np.repeat('Old', len(average_minutes_per_game_values))
    #     ])
    # })
    # (
    #     plt.ggplot(time_prob_data, plt.aes(x='Average minutes per game', y='P(Go to time)', color='Rules'))
    #     + plt.geom_line()
    #     + plt.geom_point()
    #     + plt.ylim([0, 1])
    #     + plt.theme_classic()
    # ).save(filename='figures/go_to_time_prob_plot.png')

    # Density plot for match lengths, new rules, blowouts vs. no blowouts, 85 matches/round
    # match_lengths_from_one_round_with_blowouts = simulate_match_lengths_in_round(
    #     num_matches_per_round=NUM_MATCHES_PER_ROUND,
    #     prob_of_blowout=CASE_2_BLOWOUT_PROB,
    #     blowout_shape_parameter=CASE_2_LOW_SHAPE_PARAM,
    #     blowout_scale_parameter=CASE_2_LOW_SCALE_PARAM,
    #     average_minutes_per_game=CASE_2_HIGH_AVG_MINUTES_PER_GAME,
    #     sd_minutes_per_game=CASE_2_HIGH_SD_MINUTES_PER_GAME
    # )


    # match_lengths_blowout = pd.DataFrame({
    #     'Match length': np.concatenate([match_lengths_from_one_round, match_lengths_from_one_round_with_blowouts]),
    #     'Blowouts': np.concatenate([
    #         np.repeat('No', NUM_MATCHES_PER_ROUND),
    #         np.repeat('Yes', NUM_MATCHES_PER_ROUND)
    #     ])
    # })
    # (
    #     plt.ggplot(match_lengths_blowout, plt.aes(x='Match length', color='Blowouts'))
    #     + plt.geom_density()
    #     + plt.geom_vline(xintercept=50, color='black', size=2)
    #     + plt.xlim([0, 55])
    #     + plt.theme_classic()
    # ).save(filename='figures/match_length_with_blowout_density_plot.png')

    # Plot go-to-time probability, new vs. old rules, blowouts vs. no blowouts, 85 matches/round
    # go_to_time_blowout_probs_new = []
    # go_to_time_blowout_probs_old = []
    # for i in range(len(average_minutes_per_game_values)):
    #     go_to_time_blowout_probs_new.append(
    #         find_prob_of_going_to_time(
    #             num_rounds_to_simulate=10000,
    #             num_matches_per_round=85,
    #             prob_of_blowout=CASE_2_BLOWOUT_PROB,
    #             blowout_shape_parameter=CASE_2_LOW_SHAPE_PARAM,
    #             blowout_scale_parameter=CASE_2_LOW_SCALE_PARAM,
    #             average_minutes_per_game=average_minutes_per_game_values[i],
    #             sd_minutes_per_game=CASE_2_HIGH_SD_MINUTES_PER_GAME
    #         )
    #     )
    #     go_to_time_blowout_probs_old.append(
    #         find_prob_of_going_to_time(
    #             num_rounds_to_simulate=10000,
    #             num_matches_per_round=85,
    #             prob_of_blowout=CASE_2_BLOWOUT_PROB,
    #             blowout_shape_parameter=CASE_2_LOW_SHAPE_PARAM,
    #             blowout_scale_parameter=CASE_2_LOW_SCALE_PARAM,
    #             average_minutes_per_game=average_minutes_per_game_values[i],
    #             sd_minutes_per_game=CASE_2_HIGH_SD_MINUTES_PER_GAME,
    #             prob_of_three_games=prob_of_three_games_old
    #         )
    #     )
    # time_prob_blowout_data = pd.DataFrame({
    #     'Average minutes per game': np.concatenate([
    #         average_minutes_per_game_values,
    #         average_minutes_per_game_values,
    #         average_minutes_per_game_values,
    #         average_minutes_per_game_values
    #     ]),
    #     'P(Go to time)': np.concatenate([
    #         go_to_time_probs_new,
    #         go_to_time_probs_old,
    #         go_to_time_blowout_probs_new,
    #         go_to_time_blowout_probs_old
    #     ]),
    #     'Rules': np.concatenate([
    #         np.repeat('New, no blowouts', len(average_minutes_per_game_values)),
    #         np.repeat('Old, no blowouts', len(average_minutes_per_game_values)),
    #         np.repeat('New, blowouts', len(average_minutes_per_game_values)),
    #         np.repeat('Old, blowouts', len(average_minutes_per_game_values))
    #     ])
    # })
    # (
    #     plt.ggplot(time_prob_blowout_data, plt.aes(x='Average minutes per game', y='P(Go to time)', color='Rules'))
    #     + plt.geom_line()
    #     + plt.geom_point()
    #     + plt.ylim([0, 1])
    #     + plt.theme_classic()
    # ).save(filename='figures/go_to_time_prob_with_blowouts_plot.png')

    # Plot go-to-time probability, old vs. new rules, no blowouts, 300 matches/round
    # average_minutes_per_game_values = [12, 12.5, 13, 13.5, 14, 14.5, 15]
    # large_go_to_time_probs = []
    # large_go_to_time_probs_old = []
    # for i in range(len(average_minutes_per_game_values)):
    #     large_go_to_time_probs.append(
    #         find_prob_of_going_to_time(
    #             num_rounds_to_simulate=1000,
    #             num_matches_per_round=300,
    #             average_minutes_per_game=average_minutes_per_game_values[i],
    #             sd_minutes_per_game=CASE_1_SD_MINUTES_PER_GAME
    #         )
    #     )
    #     large_go_to_time_probs_old.append(
    #         find_prob_of_going_to_time(
    #             num_rounds_to_simulate=1000,
    #             num_matches_per_round=300,
    #             average_minutes_per_game=average_minutes_per_game_values[i],
    #             sd_minutes_per_game=CASE_1_SD_MINUTES_PER_GAME,
    #             prob_of_three_games=prob_of_three_games_old
    #         )
    #     )
    # large_time_prob_data = pd.DataFrame({
    #     'Average minutes per game': np.concatenate([
    #         average_minutes_per_game_values,
    #         average_minutes_per_game_values
    #     ]),
    #     'P(Go to time)': np.concatenate([
    #         large_go_to_time_probs,
    #         large_go_to_time_probs_old
    #     ]),
    #     'Rules': np.concatenate([
    #         np.repeat('New', len(average_minutes_per_game_values)),
    #         np.repeat('Old', len(average_minutes_per_game_values))
    #     ])
    # })
    # (
    #         plt.ggplot(large_time_prob_data, plt.aes(x='Average minutes per game', y='P(Go to time)', color='Rules'))
    #         + plt.geom_line()
    #         + plt.geom_point()
    #         + plt.ylim([0, 1])
    #         + plt.theme_classic()
    # ).save(filename='figures/go_to_time_300_matches_prob_plot.png')

if __name__ == '__main__':
    main()