from submission_helper.bot_battle import BotBattle
from submission_helper.state import *
from submission_helper.enums import *
from typing import Optional
import sys

# print is buggy
print_original = print
print = lambda *args, **kwargs: print_original(*args, **{**kwargs, "flush": True})

# save copy of code of stderr
#print("".join(open(__file__, "r").readlines()))

# Define globals
game_info: Optional[GameInfo] = None
bot_battle = BotBattle()
turns_played = 0
lying = False
VERSIONS = [
    "09-12 13:33 ambassador but targets highest opponent",
    "09-12 13:48 ambassador & assassin",
    "09-12 13:54 ambassador & assassin & duke",
    "09-12 14:02 everthing combined",
    "09-12 14:16 reveal based on priority order & challenge when assassinated with 1 card",
    "09-12 14:27 captain steal action",
    "09-12 14:30 printing bug & more debugging stdout",
    "09-12 14:51 decision to foreign aid or income",
    "09-12 14:58 debugging & finding what to improve",
    "09-12 15:02 enabling ambassador",
    "09-12 15:08 ambassador discard choice priorities", #0.3
    "09-13 15:32 counter actions",
    "09-13 15:41 requires 4 to assassinate",
    "09-13 16:15 counter actions",
    "09-13 16:15 no challenging",
    "09-13 16:31 challenge everything after your primary action",
    "09-13 16:43 lying signal",
    "09-13 16:59 debugging",
    "09-13 17:03 changed reveal and discard order",
    "09-13 17:22 goodnight", # 0.4?
    "09-13 17:37 i worked out what counter does",
    "09-14 05:42 blocks foreign aid properly?",
    "09-14 05:48 dont challenge counter actions", #0.6
    "09-14 12:57 debugging",
    "09-16 00:48 readable debugging",
    "09-16 00:59 even more debugging",
    "09-16 01:17 dont challenge counter actions",
    "09-16 01:31 removed operator library",
    "09-16 01:53 dont steal if unsuccessful",
    "09-16 01:53 look at history to predict steal success",
    "09-16 02:38 always challenge",
    "09-16 02:42 challenge when someone counters you",
    "09-16 02:59 challenge when someone counters your assassin",
    "09-16 02:15 use predictor to chose assassinate victim",
    "09-16 02:21 whoops bug",
    "09-16 02:28 exchange on first turn if {contessa, assassin}",
    "09-16 02:33 bluff foreign aid in endgame (<=3 cards)",
    "09-16 02:38 instead bluff captain in endgame",
    "09-16 02:38 endgame is when 1 opponent",
]
VERSION = VERSIONS[-1]

def indexOf(search_in, target):
    if target in search_in:
        return search_in.index(target)
    else:
        return -1

Action.__repr__ = Action.__str__ = lambda self: f"P{self.player} targets P{self.target} with {self.action!r}"

def get_next_alive_player() -> int:
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


def likely_successful(action, target_id):
    prev_turn = len(game_info.history) - 2
    while prev_turn >= 0:
        prev_action = game_info.history[prev_turn][ActionType.PrimaryAction]
        if prev_action.player == game_info.player_id and prev_action.action == action and prev_action.target == target_id:
            if prev_action.successful:
                # you were successful last time you actioned them, this is the best indicator that it will be successful again
                return 1
            else:
                return -1
        elif prev_action.player == target_id and prev_action.action == PrimaryAction.Exchange and prev_action.successful:
            return 0

        prev_turn -= 1
    
    return 0

def opponent_to_kill():
    # TODO: take into account number of cards
    # TODO: game theory stuff (e.g. 3 players with 1 life each, you should void your turn)
    # TODO: how to properly pass a move?
    # powerful_players = []
    # other_players = []
    # for player_id in get_alive_opponents():
    #     balance = game_info.balances[player_id]
    #     if balance >= 7:
    #         powerful_players.append([balance, player_id])
    #     else:
    #         other_players.append([balance, player_id])

    valid_opponents = [player_id for player_id in get_alive_opponents() if likely_successful(PrimaryAction.Assassinate, player_id) >= 1]
    if not valid_opponents:
        valid_opponents = get_alive_opponents()
    
    choices = [[game_info.balances[player_id], player_id] for player_id in valid_opponents]
    print(choices)
    best_balance, target_player_id = max(choices)
    return target_player_id

def opponent_to_steal():
    valid_opponents = [player_id for player_id in get_alive_opponents() if likely_successful(PrimaryAction.Steal, player_id) >= 0]
    if not valid_opponents:
        return -1

    choices = [[game_info.balances[player_id], player_id] for player_id in valid_opponents]
    best_balance, target_player_id = max(choices)
    if best_balance == 0: # shouldnt this be <= 2
        return -1
    else:
        return target_player_id


def choose_reveal_index():
    REVEAL_ORDER = [
        Character.Duke,
        Character.Contessa,
        Character.Assassin,
        Character.Captain,
        Character.Ambassador,
    ]
    if len(game_info.own_cards) == 0:
        raise Exception("dead already!")
    if len(game_info.own_cards) == 1:
        # we only have 1 card and we are revealing it, this is a rip
        return 0
    elif len(game_info.own_cards) == 2:
        if REVEAL_ORDER.index(game_info.own_cards[0]) < REVEAL_ORDER.index(game_info.own_cards[1]):
            return 0
        else:
            return 1
    else:
        raise Exception("too many cards")



def choose_discard_index():
    DISCARD_ORDER = [
        Character.Ambassador,
        Character.Assassin,
        Character.Duke,
        Character.Contessa,
        Character.Captain,
    ]

    # priority it to get rid of duplicates
    for i, card in enumerate(game_info.own_cards):
        if game_info.own_cards.count(card) > 1:
            return i

    discard_index = [DISCARD_ORDER.index(card) for card in game_info.own_cards]
    return discard_index.index(min(discard_index))


def any_previous_dukes():
    for sequence in game_info.history:
        if ActionType.PrimaryAction in sequence and sequence[ActionType.PrimaryAction].action == PrimaryAction.Tax:
            return True
    return False

def hasDuke():
    return Character.Duke in game_info.own_cards

def hasAssassin():
    return Character.Assassin in game_info.own_cards

def hasAmbassador():
    return Character.Ambassador in game_info.own_cards

def hasCaptain():
    return Character.Captain in game_info.own_cards

def hasContessa():
    return Character.Contessa in game_info.own_cards

def get_action_in_turn(index=-1) -> Action:
    return list(game_info.history[-1].values())[index]





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

# its your turn to play
def primary_action_handler():
    """asassin but target player with highest balance"""
    global lying
    lying = False
    myBalance = game_info.balances[game_info.player_id]

    # FIRSTLY TRY TO KILL
    if myBalance >= 4 and hasAssassin():
        bot_battle.play_primary_action(PrimaryAction.Assassinate, opponent_to_kill())
    elif myBalance >= 7:
        bot_battle.play_primary_action(PrimaryAction.Coup, opponent_to_kill())

    # OTHERWISE TRY RANDOM STUFF
    elif len(game_info.own_cards) == 2 and game_info.own_cards[0] == game_info.own_cards[1]:
        lying = not hasAmbassador()
        bot_battle.play_primary_action(PrimaryAction.Exchange)
    elif sorted(game_info.own_cards) == sorted([Character.Assassin, Character.Contessa]):
        lying = True
        bot_battle.play_primary_action(PrimaryAction.Exchange)
    elif hasDuke():
        bot_battle.play_primary_action(PrimaryAction.Tax)
    elif hasAmbassador():
        bot_battle.play_primary_action(PrimaryAction.Exchange)
    elif False: # TODO: is lying good here?
        lying = True
        bot_battle.play_primary_action(PrimaryAction.Exchange)
    elif hasCaptain() and opponent_to_steal() != -1:
        bot_battle.play_primary_action(PrimaryAction.Steal, opponent_to_steal())

    else:
        #endgame = sum(game_info.players_cards_num) <= 3
        endgame = len(get_alive_opponents()) == 1

        # if endgame:
        #     bot_battle.play_primary_action(PrimaryAction.ForeignAid)
        if endgame and opponent_to_steal() != -1:
            lying = not hasCaptain()
            bot_battle.play_primary_action(PrimaryAction.Steal, opponent_to_steal())
        else:
            bot_battle.play_primary_action(PrimaryAction.Income)

# someone has acted on you so block it as hard as you can
def counter_action_handler():
    previous_action = get_action_in_turn()
    print(".")
    print(".")
    print(f"on turn {turns_played}, do you want to COUNTER: {previous_action.action}")

    if previous_action.action_type == ActionType.PrimaryAction:
        primary_action = previous_action

        foreignAid = primary_action.action == PrimaryAction.ForeignAid
        beingAssassinated = primary_action.action == PrimaryAction.Assassinate and primary_action.target == game_info.player_id
        beingStolenFrom = primary_action.action == PrimaryAction.Steal and primary_action.target == game_info.player_id

        if hasDuke() and foreignAid:
            bot_battle.play_counter_action(CounterAction.BlockForeignAid)
        elif hasContessa() and beingAssassinated:
            bot_battle.play_counter_action(CounterAction.BlockAssassination)
        elif hasCaptain() and beingStolenFrom:
            bot_battle.play_counter_action(CounterAction.BlockStealingAsCaptain)
        elif hasAmbassador() and beingStolenFrom:
            bot_battle.play_counter_action(CounterAction.BlockStealingAsAmbassador)
        elif len(game_info.own_cards) == 1 and beingAssassinated and indexOf(game_info.own_cards, Character.Contessa) == -1:
            bot_battle.play_counter_action(CounterAction.BlockAssassination)
        else:
            bot_battle.play_counter_action(CounterAction.NoCounterAction)

    else:
        bot_battle.play_counter_action(CounterAction.NoCounterAction)


# challenge is when opponent does an action and you want to dispute it
# on the basis that they dont have the required card
def challenge_action_handler():
    previous_action = get_action_in_turn()
    print(".")
    print(".")
    print(f"on turn {turns_played}, do you want to CHALLENGE: {previous_action}")

    # if game_info.current_primary_player != game_info.player_id:
    #     print("NoChallenge", "--", "its not your primary action that is being challenged, dont bother")
    #     bot_battle.play_challenge_action(ChallengeAction.NoChallenge)
    #     return

    global lying
    
    # we played assasssin, they are trying to counter it
    if game_info.current_primary_player == game_info.player_id and previous_action.action == CounterAction.BlockAssassination:
        # if we tried to do something and were blocked, challenge the block
        print("Challenge", "--", "surely youre faking a contessa")
        bot_battle.play_challenge_action(ChallengeAction.Challenge)
    else:
        print("No Challenge", "--")
        bot_battle.play_challenge_action(ChallengeAction.NoChallenge)

# your primary action has been challenge, but i wasnt lying!
# reveal that i have the required card
def challenge_response_handler():
    """
    taken from ambassador code, this looks good, dont touch"""
    previous_action = get_action_in_turn()
    assert previous_action.action == ChallengeAction.Challenge and previous_action.target == game_info.player_id
    
    previous_action = get_action_in_turn(-2)
    print(".")
    print(".")
    print(f"on turn {turns_played}, RESPOND to: {previous_action.action}")
    

    reveal_card_index = -1
    
    # Someone challenged my primary action, reveal card to prove them wrong
    if previous_action.action_type == ActionType.PrimaryAction:
        primary_action = game_info.history[-1][ActionType.PrimaryAction].action

        # If we have the card we used, lets reveal it
        if primary_action == PrimaryAction.Assassinate:
            reveal_card_index = indexOf(game_info.own_cards, Character.Assassin)
        elif primary_action == PrimaryAction.Exchange:
            reveal_card_index = indexOf(game_info.own_cards, Character.Ambassador)
        elif primary_action == PrimaryAction.Steal:
            reveal_card_index = indexOf(game_info.own_cards, Character.Captain)
        elif primary_action == PrimaryAction.Tax:
            reveal_card_index = indexOf(game_info.own_cards, Character.Duke)

    # Challenge was counter action
    elif previous_action.action_type == ActionType.CounterAction:
        counter_action = game_info.history[-1][ActionType.CounterAction].action

        # If we have the card we used, lets reveal it
        if counter_action == CounterAction.BlockAssassination:
            reveal_card_index = indexOf(game_info.own_cards, Character.Contessa)
        elif counter_action == CounterAction.BlockStealingAsAmbassador:
            reveal_card_index = indexOf(game_info.own_cards, Character.Ambassador)
        elif counter_action == CounterAction.BlockStealingAsCaptain:
            reveal_card_index = indexOf(game_info.own_cards, Character.Captain)
        elif counter_action == CounterAction.BlockForeignAid:
            reveal_card_index = indexOf(game_info.own_cards, Character.Duke)

    # If we lied, let's reveal our first card
    if reveal_card_index == -1:
        reveal_card_index = choose_reveal_index()

    bot_battle.play_challenge_response(reveal_card_index)


def discard_choice_handler():
    primary_action = game_info.history[-1][ActionType.PrimaryAction]
    if primary_action.action == PrimaryAction.Exchange and primary_action.successful:
        # We're in the ambassador move

        # Note: on the first discard request after successful exchange, this should return 2 new cards
        print(game_info.own_cards, flush = True)
        bot_battle.play_discard_choice(choose_discard_index())

    else:
        bot_battle.play_discard_choice(choose_reveal_index())

just_started = True
while True:
    game_info = bot_battle.get_game_info()
    turns_played = len(game_info.history)

    # debugging
    if just_started:
        print("VERSION:", VERSION)
        print(f"My player id is {game_info.player_id}")
        just_started = False
        
    print(game_info.own_cards)

    move_controller(game_info.requested_move)
