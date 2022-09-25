# SYNCS coup

Thanks to everyone who organised this! I appreciate the insane amount of effort you put in. This is a really interesting contest, I'm looking forward to the next one :D

## Cool stuffs
Fix print
```python
print_original = print
print = lambda *args, **kwargs: print_original(*args, **{**kwargs, "flush": True})
```

Printing actions easily - useful for debugging
```python
Action.__repr__ = Action.__str__ = lambda self: f"P{self.player} targets P{self.target} with {self.action!r}"
```

Keep your code in the debug output, so its easier to keep track of versions
```python
print("".join(open(__file__, "r").readlines()))
```

Very useful generalisation of `get_next_alive_player`
```python
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
```

## Observations
Its really hard to tell how well my bot is doing, I measured it by the percentage wins over 30 games (30 games because thats the history of games I can see).

The leaderboard has high variance for many reasons, but also because your rank is not independant from other players ranks. e.g. you might be very good at beating this player even though other people arent => its not even a partial order! I took screenshots of the leaderboard every once in a while to see how other players are moving around on the leaderboard (especially example bots!).

At one point I tried to find Shrek by collected games where the winner isnt me and doesnt look like sample submissions. Then I tried to find a common strategy of some sort. Couldn't find strategy, i guess annonymous players are effective. In fact its probably for the best that players are annonymous, otherwise we can analyse each other (this is boring), and make bots that explicitly counter other bots.

I unintentionally did all my work on this at unearthly hours. This turned out to be good, because other players aren't changing their bots at the same time (controlled environment). I guess all nighters aren't so bad after all :')

> Editor’s note: a Very advanced strat is to fake losing a challenge by discarding your
This seems very aggressive, would this actually work?

Timeout if we predict we are going to lose, so the game ends up in a tie. :)))))))


## Ideas I've tried
The points with bolded bullet points are things that seem to work well and are interesting ideas. In roughly sequential order, they are:
 * a honest bot, which doesn't challenge or counter (adapted heavily from the sample bots)
 * smarter stuff like a) challenging opponents' primary action when its blindingly obvious b) challenging counters when you actually have the card, and reveal appropriately
 - an order for discarding cards and a seperate order for revealing cards (trying combinations that seems to make sense). avoid getting double of the same card
 * order of actions are killing (assassin, couop), exchanging if start of game and "bad" hand, gaining $$$ (duke, ambassador, captain, income)
 * take foreign aid instead of income if no dukes and midgame
 * endgame is when only 1 opponent, or at most 3 remaining cards
 - only assassinate when >=4 coins (this means that you are slightly passive, in the hope that other people kill each other)
 * extended idea to make a stealth bot (startgame: as little impact as possible, try to get assassin then duke. endgame: kill, gain $$)
 - try to lie in certain cases, and dont challenge opponents who counter your lies (lying ambassador op)
 * writing an engine, wrote about 20 lines then gave up :(. i realised pipes seem annoying (no async?!?!), and i dont really know how the logic of engine even works. (btw i spent way too long figuring what actions mean, and the order of actions)
 -  challenge things like BlockStealing, but especially BlockAssasinate
 * i realised a majority of my games were lost because my starting hand was {contessa, assassin}, avoid it by faking assassin in startgame
 - crashing my bot intentionally so it doesnt play any more games, so people cant explicitly counter my strategy (idk how much effect this has)
 * now i usually get to endgame, but i lose because i am behind tempo by 1 or 2 moves (by tempo im referring to the chess concept)
 - kill players based on both income and number of cards remaining. thought about minimax to simulate actions of opponents and test chances of win given which opponent i kill
 - fake duke/captain (which one is better) to gain tempo
 - kill players who i am likely to get away with - maybe they havent countered the last time it was actioned to them

## Ideas I wanted to try
 - system to calculate probabilities of each possible hand for player, given their decisions (but data seems too small and messy because lying)
 - additionally, using ambassador to update probabilities and 
 - making an engine, but cbbs
 - forfeit a turn using an ambassador, but this is an still unnecessarily risky option
 - ... TODO
 