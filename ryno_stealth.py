# print is buggy
print_original = print
print = lambda *args, **kwargs: print_original(*args, **{**kwargs, "flush": True})

from operator import contains
from submission_helper.bot_battle import BotBattle
from submission_helper.state import *
from submission_helper.enums import *
from typing import Optional


game_info: Optional[GameInfo] = None
bot_battle = BotBattle()
turns_played = 0
VERSIONS = [
    "09-12 13:44 stealthy oooo"
]
VERSION = VERSIONS[-1]

def get_next_alive_player():
    next_alive = (game_info.player_id + 1) % 5
    while game_info.players_cards_num[next_alive] == 0:
        next_alive = (next_alive + 1) % 5
    
    return next_alive

def get_alive_opponents():
    """
    return all alive opponent ids except yours"""
    opponents = []
    next_alive = (game_info.player_id + 1) % 5
    while next_alive != game_info.player_id:
        if game_info.players_cards_num[next_alive] > 0:
            opponents.append(next_alive)
        next_alive = (next_alive + 1) % 5
    
    return opponents


def hasDuke():
    return contains(game_info.own_cards, Character.Duke)

def hasAssassin():
    return contains(game_info.own_cards, Character.Assassin)

def hasAmbassador():
    return contains(game_info.own_cards, Character.Ambassador)

def hasCaptain():
    return contains(game_info.own_cards, Character.Captain)

def hasContessa():
    return contains(game_info.own_cards, Character.Contessa)

def opponent_to_kill():
    # TODO: take into account number of cards
    target_player_id = max([[game_info.balances[player_id], player_id] for player_id in get_alive_opponents()])[1]
    return target_player_id

def move_controller(requested_move: RequestedMove):
    if requested_move == RequestedMove.PrimaryAction:
        primary_action_handler()

    elif requested_move == RequestedMove.CounterAction:
        counter_action_handler()

    elif requested_move == RequestedMove.ChallengeAction:
        challenge_action_handler()

    elif requested_move == RequestedMove.ChallengeResponse:
        challenge_response_handler()

    elif requested_move == RequestedMove.DiscardChoice:
        discard_choice_handler()

    else:
        return Exception(f'Unknown requested move: {requested_move}')


def primary_action_handler():
    if game_info.balances[game_info.player_id] < 3:
        # TODO: when to do income and when to do foreign aid
        bot_battle.play_primary_action(PrimaryAction.ForeignAid)
    elif len(get_alive_opponents()) == 1 and hasAssassin():
        bot_battle.play_primary_action(PrimaryAction.Assassinate, get_alive_opponents()[0])
    elif game_info.balances[game_info.player_id] >= 7:
        bot_battle.play_primary_action(PrimaryAction.Coup, opponent_to_kill())
    else:
        bot_battle.play_primary_action(PrimaryAction.Income)
        

def counter_action_handler():
    bot_battle.play_counter_action(CounterAction.NoCounterAction)


def challenge_action_handler():
    bot_battle.play_challenge_action(ChallengeAction.NoChallenge)


def challenge_response_handler():
    bot_battle.play_challenge_response(0)


def discard_choice_handler():
    bot_battle.play_discard_choice(0)


while True:
    game_info = bot_battle.get_game_info()

    # debugging
    if turns_played == 0:
        print("VERSION:", VERSION)
        print(f"My player id is {game_info.player_id}")
        
    print(game_info.own_cards)

    move_controller(game_info.requested_move)

    turns_played += 1
