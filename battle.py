import sqlalchemy as alchemy
from models import Player, Enemy, SkillOwnership, Skill, ItemOwnership, Item
from sqlalchemy.ext.declarative import declarative_base
import random, sys
from termcolor import colored, cprint

engine = alchemy.create_engine("sqlite:///app.db")
# Base = declarative_base()
Session = alchemy.orm.sessionmaker(bind=engine)
session = Session()

# player = Player()
metadata = alchemy.MetaData()
metadata.bind = alchemy.engine


player = session.query(Player).filter_by(id=1).all()[0]
enemy = session.query(Enemy).filter_by(name="Rat").all()[0]
player_max_hp = player.hp
skills = [session.query(Skill).filter_by(id = each.skill_id).all()[0] for each in session.query(SkillOwnership).filter_by(player_id = player.id).all()]
skills_dict = {}
for each in skills:
    skills_dict[each.name] = each
###skills_list should probably be refactored at some point. feels needlessly obfiscated 
skills_list = sorted(list(skills_dict.keys()))
item_ownership = session.query(ItemOwnership).filter_by(player_id = player.id).all()
items_dict = {}
for each in item_ownership:
    item_obj = session.query(Item).filter_by(id = each.item_id).all()[0]
    items_dict[item_obj.name] = [item_obj, each.quantity]
items_list = sorted(list(items_dict.keys()))

dodge_options = ['l', 'r', 'u', 'd']
# items = [session.query(Item).filter_by(id = each.item_id).all()[0] for each in session.query(ItemOwnership).filter_by(player_id = player.id).all()]
# for each in items:
#     items_dict[each.name] = each

#player = alchemy.engine.execute(
   #     player_table.select().where(player_table.c.id == 1)
#)

# forrest = Player()

# print(player[0].name)
# print(enemy[0].name)
def escape_battle():
    F = random.randint(0, 255)
    if ((player.agility*128/enemy.agility)+30)%256 > F:
        print ("You successfully escaped!")
        return True
    else:
        print ("Can't escape!")
        return False

def enemy_attack():
    while True:
        dodge = input("Enemy {} is about to attack!\nDodge:\n[L]eft\n[R]right\n[U]p\n[D]own\n".format(enemy.name))
        if dodge in dodge_options:
            break
    if dodge.lower() == random.choice(dodge_options):
        print("You narrowly dodged {}'s attack!".format(enemy.name))
    else:
        damage = int(((2*enemy.level+10)/250)*(enemy.strength/player.fortitude) * 1 + 2)
        player.hp -= damage
        print("You were hit for {} points! {} hp remaining.".format(damage, player.hp))

def player_attack():
    while True:
        choice = input("What would you like to do?\n[A]ttack\n[I]tem\n[R]un\n")
        if choice.lower() == 'a':
            while True:
                choice = input("How would you like to attack?\n[P]hysical Attack\n[S]kills\n[R]eturn\n")
                if choice.lower() == 'p':
                    damage = int(((2*player.level+10)/250) * (player.strength/enemy.fortitude) * 1 + 2)
                    break
                elif choice.lower() == 's':
                    while True:
                        cant_cast = []
                        for index, skill in enumerate(skills_list, start=1):
                            cost = skills_dict[skill].use_cost
                            output = index, skill, "mp:" + str(cost)
                            if player.mp >= cost:
                                cprint(output, "green")
                            else:
                                cant_cast.append(index)
                                # print(cant_cast)
                                cprint(output, "red")
                        print("[R]eturn")
                        try:
                            attack = input()
                            attack = int(attack)
                            if attack > 0:
                                if attack not in cant_cast:
                                    # print(attack, cant_cast)
                                    try:
                                        # skills_list[attack-1]
                                        player.mp -= skills_dict[skills_list[attack-1]].use_cost
                                        damage = skills_dict[skills_list[attack-1]].damage_heal
                                        damage = int(((2*player.level+10)/250) * (player.strength/enemy.fortitude) * damage + 2)
                                        break
                                    except IndexError:
                                        pass
                                else:
                                    print("You do not have enough mp!")
                                    return player_attack()
                            else:
                                pass
                        except ValueError:
                            if attack.lower() == 'r':
                                return player_attack()
                    break
                elif choice.lower() == 'r':
                    return player_attack()
            if damage > 0:
                enemy.hp -= damage
                if enemy.hp > 0:
                    print("You hit for {} points! Enemy has {} hp remaining.".format(damage, enemy.hp))
            else:
                player.hp -= damage
                if player.hp > player_max_hp:
                    player.hp = player_max_hp
                print("You healed for {} points! {} hp remaining.".format(-damage, player.hp))
            break
        elif choice.lower() == 'i':
##FOR THE MOMENT ONLY IN-BATTLE ITEMS ARE HEALING ITEMS. CODE WILL NEED REFACTORING IF THAT CHANGES
            while True:
                for index, item in enumerate(items_list, start=1):
                    quantity = items_dict[item][1]
                    print(index, item, "Quantity:" + str(quantity))
                print("[R]eturn")
                try:
                    item_use = input()
                    item_use = int(item_use)
                    if item_use > 0:
                        try:
                            # items_list[item_use-1]:
                            #removes 1 of item from inventory
                            items_dict[items_list[item_use-1]][1] -= 1
                            heal = items_dict[items_list[item_use-1]][0].recov_amnt
                            if player.hp + heal > player_max_hp:
                                heal = player_max_hp - player.hp
                                player.hp = player_max_hp
                            else:
                                player.hp += heal
                            print("You were healed for {} points! {} hp remaining.".format(heal, player.hp))
                            if items_dict[items_list[item_use-1]][1] == 0:
                                del items_dict[items_list[item_use-1]][1]
                                items_list.remove(items_list[item_use-1])
                            # print("HELP?")
                        except IndexError:
                            pass
                except ValueError:
                    if item_use.lower() == 'r':
                        return player_attack()
                break
            break
        elif choice.lower() == 'r':
            if escape_battle() == True:
                return "escaped"
            break

def random_encounter():
    print("An enemy {} has appeared!".format(enemy.name))
    # speed check
    if enemy.agility > player.agility:
        while enemy.hp > 0 and player.hp > 0:
            enemy_attack()
            if player.hp > 0:
                if player_attack() == "escaped":
                    break
        if player.hp <= 0:
            print("You were defeated!")
        elif enemy.hp <= 0:
            print("You defeated {}! {} gold!".format(enemy.name, enemy.gold))
            player.gold += enemy.gold
    
    elif player.agility >= enemy.agility:
        while enemy.hp > 0 and player.hp > 0:
            if player_attack() == "escaped":
                break
            if enemy.hp > 0:
                enemy_attack()
        if player.hp <= 0:
            print("You were defeated!")
        elif enemy.hp <= 0:
            print("You defeated {}! You gained {} gold!".format(enemy.name, enemy.gold))
            player.gold += enemy.gold
            
if __name__ == "__main__":
    random_encounter()
    
##TODO
