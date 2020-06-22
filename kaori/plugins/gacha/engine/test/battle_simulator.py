import copy
from random import random, sample
from typing import Optional

from . import cards as card_pool
from .utils import find_card
from .. import *
from .. import Card


class BattleResult:

    def __init__(self,
                 winner: Card,
                 loser: Card,
                 turns: int) -> None:
        self.turns = turns
        self.loser = loser
        self.winner = winner


def run_battle_simulator(card_a: Card,
                         card_b: Card,
                         debug: bool = False,
                         interactive: bool = False,
                         print_header: bool = True) -> Optional[BattleResult]:
    
    def debug_print(out):
        if debug:
            print(out)
        
    for card in [card_a, card_b]:
        card.is_valid_card()

    if Card.detect_standoff(card_a, card_b, debug=False):
        debug_print(f"These two cards could go at it all day and not harm eachother due to armor, dmg, etc.")
        debug_print(f"They agree to be friends instead of fighting.")
        return None

    if card_a.speed != card_b.speed:
        cards = sorted([card_a, card_b], key=lambda card: -card.speed)
    else:
        cards = sample([card_a, card_b], 2)

    first, second = cards

    debug_print(f"{first.name} goes first because of higher speed. {first.speed} vs {second.speed}")

    winner = None
    loser = None
    turn = 0

    while card_a.current_hp > 0 and card_b.current_hp > 0:
        if turn > 100:
            raise RuntimeError('This battle is taking too long...')

        current_card = cards[turn % len(cards)]
        target_card = cards[(turn + 1) % len(cards)]
        debug_print(f"{current_card.name} is attacking")
        # evasion check
        if random() < target_card.evasion:
            debug_print(f"**{target_card.name} dodged the attack**")
            turn += 1
            continue

        crit_multiplier = 1
        # crit
        if random() < current_card.crit:
            crit_multiplier = CRIT_MULTIPLIER
            debug_print(f"**{current_card.name} hit a crit!**")

        damage = current_card.attack_damage(target_card, crit_multiplier=crit_multiplier, debug=debug)
        debug_print(f"{current_card.name} will hit {target_card.name} for {damage}!")
        target_card.accept_damage(damage)

        if target_card.current_hp < 1:
            debug_print(f"{target_card.name} was killed!!")
            winner = current_card
            loser = target_card
            break
        else:
            debug_print(f"{target_card.name} has {target_card.current_hp} HP left")

        turn += 1

    debug_print("battle over")
    br = BattleResult(winner=copy.deepcopy(winner), loser=copy.deepcopy(loser), turns=turn + 1)
    for card in cards:
        card.reset_hp()
    return br