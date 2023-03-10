import pygame

from random import randint, random
from Graph import *

from Character import *
from State import *

class Wizard_Nord(Character):

    def __init__(self, world, image, projectile_image, base, position, explosion_image = None):

        Character.__init__(self, world, "wizard", image)

        self.decided_path = 0

        self.projectile_image = projectile_image
        self.explosion_image = explosion_image

        self.base = base
        self.position = position
        self.move_target = GameEntity(world, "wizard_move_target", None)
        self.target = None


        self.maxSpeed = 50
        self.min_target_distance = 100
        self.projectile_range = 100
        self.projectile_speed = 100

        seeking_state = WizardStateSeeking_Nord(self)
        attacking_state = WizardStateAttacking_Nord(self)
        ko_state = WizardStateKO_Nord(self)
        fleeing_state = WizardStateFleeing_Nord(self)

        self.brain.add_state(seeking_state)
        self.brain.add_state(attacking_state)
        self.brain.add_state(ko_state)
        self.brain.add_state(fleeing_state)

        self.brain.set_state("seeking")

    def render(self, surface):

        Character.render(self, surface)


    def process(self, time_passed):
        
        Character.process(self, time_passed)
        
        level_up_stats = ["hp", "speed", "ranged damage", "ranged cooldown", "projectile range"]
        if self.can_level_up():
            self.level_up(level_up_stats[3])      


class WizardStateSeeking_Nord(State):

    def __init__(self, wizard):

        State.__init__(self, "seeking")
        self.wizard = wizard

        self.wizard.path_graph = self.wizard.world.paths[self.wizard.decided_path]
        

    def do_actions(self):

        self.wizard.velocity = self.wizard.move_target.position - self.wizard.position
        if self.wizard.velocity.length() > 0:
            self.wizard.velocity.normalize_ip();
            self.wizard.velocity *= self.wizard.maxSpeed

    def check_conditions(self):

        # check if opponent is in range
        nearest_opponent = self.wizard.world.get_nearest_opponent(self.wizard)
        if nearest_opponent is not None:
            opponent_distance = (self.wizard.position - nearest_opponent.position).length()
            if opponent_distance <= self.wizard.min_target_distance:
                    self.wizard.target = nearest_opponent
                    return "attacking"
        
        if (self.wizard.position - self.wizard.move_target.position).length() < 8:

            # continue on path
            if self.current_connection < self.path_length:
                self.wizard.move_target.position = self.path[self.current_connection].toNode.position
                self.current_connection += 1
            
        return None

    def entry_actions(self):

        nearest_node = self.wizard.path_graph.get_nearest_node(self.wizard.position)

        self.path = pathFindAStar(self.wizard.path_graph, \
                                  nearest_node, \
                                  self.wizard.path_graph.nodes[self.wizard.base.target_node_index])

        
        self.path_length = len(self.path)

        if (self.path_length > 0):
            self.current_connection = 0
            self.wizard.move_target.position = self.path[0].fromNode.position

        else:
            self.wizard.move_target.position = self.wizard.path_graph.nodes[self.wizard.base.target_node_index].position

class WizardStateFleeing_Nord(State):

    def __init__(self, wizard):

        State.__init__(self, "fleeing")
        self.wizard = wizard

    def do_actions(self):
        nearest_node = self.wizard.path_graph.get_nearest_node(self.wizard.position)
        self.wizard.velocity = self.nearest_node.position - self.wizard.position
        if self.wizard.velocity.length() > 0:
            self.wizard.velocity.normalize_ip();
            self.wizard.velocity *= self.wizard.maxSpeed
        if opponent_distance <= self.wizard.min_target_distance:
            if self.wizard.current_ranged_cooldown <= 0:
                self.wizard.ranged_attack(self.wizard.target.position, self.wizard.explosion_image)

    def check_conditions(self):
        if (self.nearest_node.position - self.wizard.position).length() < 8:
            return "seeking"

    def entry_actions(self):
        return None




class WizardStateAttacking_Nord(State):

    def __init__(self, wizard):

        State.__init__(self, "attacking")
        self.wizard = wizard

    def do_actions(self):

        opponent_distance = (self.wizard.position - self.wizard.target.position).length()

        # opponent within range
        if opponent_distance <= self.wizard.min_target_distance:
            # if wizard too close
            if opponent_distance < self.wizard.min_target_distance - 5:
                self.wizard.velocity = self.wizard.position - self.wizard.target.position
                # ranged attack
                if self.wizard.current_ranged_cooldown <= 0:
                    self.wizard.ranged_attack(self.wizard.target.position, self.wizard.explosion_image)
                if self.wizard.velocity.length() > 0:
                    self.wizard.velocity.normalize_ip();
                    self.wizard.velocity *= self.wizard.maxSpeed
            else:
                self.wizard.velocity = Vector2(0, 0)
                if self.wizard.current_ranged_cooldown <= 0:
                    self.wizard.ranged_attack(self.wizard.target.position, self.wizard.explosion_image)
        else:
            self.wizard.velocity = self.wizard.target.position - self.wizard.position
            if self.wizard.velocity.length() > 0:
                self.wizard.velocity.normalize_ip();
                self.wizard.velocity *= self.wizard.maxSpeed

        # collision detection
        collision_list = pygame.sprite.spritecollide(self.wizard, self.wizard.world.obstacles, False, pygame.sprite.collide_mask)
        for entity in collision_list:
            if entity.team_id == self.wizard.team_id:
                continue
            elif entity.name == "obstacle" or entity.name == "base":
                return "fleeing"

        else:
            self.wizard.move_target.position = self.wizard.path_graph.nodes[self.wizard.base.target_node_index].position


    def check_conditions(self):

        # target is gone
        if self.wizard.world.get(self.wizard.target.id) is None or self.wizard.target.ko:
            self.wizard.target = None
            return "seeking"
            
        return None

    def entry_actions(self):

        return None


class WizardStateKO_Nord(State):

    def __init__(self, wizard):

        State.__init__(self, "ko")
        self.wizard = wizard

    def do_actions(self):

        return None


    def check_conditions(self):

        # respawned
        if self.wizard.current_respawn_time <= 0:
            self.wizard.current_respawn_time = self.wizard.respawn_time
            self.wizard.ko = False
            self.wizard.path_graph = self.wizard.world.paths[self.wizard.decided_path]
            return "seeking"
            
        return None

    def entry_actions(self):

        self.wizard.current_hp = self.wizard.max_hp
        self.wizard.position = Vector2(self.wizard.base.spawn_position)
        self.wizard.velocity = Vector2(0, 0)
        self.wizard.target = None

        return None
