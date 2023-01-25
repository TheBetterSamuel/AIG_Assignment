import pygame

from random import randint, random
from Graph import *

from Character import *
from State import *

class Archer_TeamA(Character):

    def __init__(self, world, image, projectile_image, base, position):

        Character.__init__(self, world, "archer", image)

        self.projectile_image = projectile_image

        self.base = base
        self.position = position
        self.move_target = GameEntity(world, "archer_move_target", None)
        self.prev_node = GameEntity(world, "archer_prev_node", None)
        self.target = None
        self.world.generate_pathfinding_graphs("test_pathfinding.txt")

        self.maxSpeed = 50
        self.min_target_distance = 170
        self.projectile_range = 100
        self.projectile_speed = 100

        seeking_state = ArcherStateSeeking_TeamA(self)
        attacking_state = ArcherStateAttacking_TeamA(self)
        ko_state = ArcherStateKO_TeamA(self)
        fleeing_state = ArcherStateFleeing_TeamA(self)
        hyperfocus_state = ArcherStateFocus_TeamA(self)

        self.brain.add_state(seeking_state)
        self.brain.add_state(attacking_state)
        self.brain.add_state(ko_state)
        self.brain.add_state(fleeing_state)
        self.brain.add_state(hyperfocus_state)

        self.brain.set_state("seeking")

    def render(self, surface):

        Character.render(self, surface)


    def process(self, time_passed):
        
        Character.process(self, time_passed)
        
        level_up_stats = ["ranged cooldown"]
        if self.can_level_up():
            choice = randint(0, len(level_up_stats) - 1)
            self.level_up(level_up_stats[choice])   


class ArcherStateSeeking_TeamA(State):

    def __init__(self, archer):

        State.__init__(self, "seeking")
        self.archer = archer

        self.archer.path_graph = self.archer.world.paths[0]


    def do_actions(self):

        self.archer.velocity = self.archer.move_target.position - self.archer.position
        if self.archer.velocity.length() > 0:
            self.archer.velocity.normalize_ip();
            self.archer.velocity *= self.archer.maxSpeed


    def check_conditions(self):

        # check if opponent is in range
        nearest_opponent = self.archer.world.get_nearest_opponent(self.archer)
        if nearest_opponent is not None:
            opponent_distance = (self.archer.position - nearest_opponent.position).length()
            if opponent_distance <= self.archer.min_target_distance:
                    self.archer.target = nearest_opponent
                    if nearest_opponent.name == "base":
                        return "hyperfocus"
                    else:
                        return "attacking"
        
        if (self.archer.position - self.archer.move_target.position).length() < 8:

            # continue on path
            if self.current_connection < self.path_length:
                if self.current_connection >=1:
                    self.archer.prev_node.position = self.path[self.current_connection].fromNode.position # Remembers the previous node's position
                    

                self.archer.move_target.position = self.path[self.current_connection].toNode.position
                self.current_connection += 1
                
            
        return None

    def entry_actions(self):

        nearest_node = self.archer.path_graph.get_nearest_node(self.archer.position)

        path_node_list = list(self.archer.world.paths[1].nodes.values())
        count = 0
        for node in path_node_list:
            if nearest_node.id == 0:
               break
            if node.id == nearest_node.id and count < len(path_node_list)-1:
                count += 1
                nearest_node = path_node_list[count]
                break
            count += 1

        self.path = pathFindAStar(self.archer.path_graph, \
                                  nearest_node, \
                                  self.archer.path_graph.nodes[self.archer.base.target_node_index])

        
        self.path_length = len(self.path)

        if (self.path_length > 0):
            self.current_connection = 0
            self.archer.move_target.position = self.path[0].fromNode.position

        else:
            self.archer.move_target.position = self.archer.path_graph.nodes[self.archer.base.target_node_index].position


class ArcherStateAttacking_TeamA(State):

    def __init__(self, archer):

        State.__init__(self, "attacking")
        self.archer = archer
        

    def do_actions(self):
        opponent_distance = (self.archer.position - self.archer.target.position).length()
        nearest_opponent = self.archer.world.get_nearest_opponent(self.archer)
                    
        # opponent within range
        if opponent_distance <= (self.archer.min_target_distance):
            if self.archer.current_ranged_cooldown <= 0:
                self.archer.ranged_attack(self.archer.target.position)
            else: #move to maximum range
                avoid = Vector2(randint(-1, 1)*100, randint(-1,1)*100)
                self.archer.velocity =  Vector2(self.archer.position) - Vector2(self.archer.target.position)
                
                if self.archer.velocity.length() > 0:
                    self.archer.velocity.normalize_ip();
                    self.archer.velocity *= self.archer.maxSpeed
        
        #if an enemy approaches the archer, the archer will change targets to the closer enemy and try to avoid the new target
        elif ((self.archer.position - nearest_opponent.position).length() < opponent_distance) & ((self.archer.position - nearest_opponent.position).length()<= self.archer.min_target_distance): 
            self.archer.target = nearest_opponent

            if (self.archer.position - nearest_opponent.position).length() > self.archer.min_target_distance:
                
                return "seeking"
                
        

        else:
            self.archer.velocity = self.archer.target.position - self.archer.position  #Chasing opponent if out of range
            if self.archer.velocity.length() > 0:
                self.archer.velocity.normalize_ip();
                self.archer.velocity *= self.archer.maxSpeed


    def check_conditions(self):

        # target is gone
        if self.archer.world.get(self.archer.target.id) is None or self.archer.target.ko:
            self.archer.target = None
            return "seeking"

        #collision detection == moving to nearest node
        collision_list = pygame.sprite.spritecollide(self.archer, self.archer.world.obstacles, False, pygame.sprite.collide_mask)
        for entity in collision_list:
            if entity.team_id == self.archer.team_id:
                continue
            elif entity.name == "obstacle" or entity.name == "base":
                obj = entity
                current_pos = self.archer.position
                return "fleeing"

        if self.archer.position[0] <= 10 or self.archer.position[0] >= (SCREEN_WIDTH - 10) or \
           self.archer.position[1] <= 10 or self.archer.position[1] >= (SCREEN_HEIGHT - 10):
            return "fleeing"

        return None

    def entry_actions(self):

        return None
        

class ArcherStateFleeing_TeamA(State):

    def __init__(self, archer):

        State.__init__(self, "fleeing")
        self.archer = archer

    def do_actions(self):

        opponent_distance = (self.archer.position - self.archer.target.position).length()
        # self.archer.velocity = self.archer.prev_node.position - self.archer.position
        
        #flee range
        if opponent_distance < (self.archer.min_target_distance + self.archer.min_target_distance):
            self.archer.velocity = self.archer.prev_node.position - self.archer.position

        # opponent within range while fleeing
        if opponent_distance <= (self.archer.min_target_distance):
            if self.archer.current_ranged_cooldown <= 0:
                self.archer.ranged_attack(self.archer.target.position)

        else:
            return "seeking"

        if self.archer.velocity.length() > 0:
            self.archer.velocity.normalize_ip();
            self.archer.velocity *= self.archer.maxSpeed

        
        
    def check_conditions(self):

        opponent_distance = (self.archer.position - self.archer.target.position).length()
        #within node range
        if (self.archer.position - self.archer.prev_node.position).length() < 18:
            return "seeking"

        # target is gone
        if self.archer.world.get(self.archer.target.id) is None or self.archer.target.ko:
            self.archer.target = None
            return "seeking"
        
        #flee range
        if opponent_distance > (self.archer.min_target_distance * 2):
            return "seeking"
            
        return None

    def entry_actions(self):
        return None

        # nearest_node = self.archer.path_graph.get_nearest_node(self.archer.position)

        # self.path = pathFindAStar(self.archer.path_graph, \
        #                           nearest_node, \
        #                           self.archer.path_graph.nodes[self.archer.base.target_node_index])

        
        # self.path_length = len(self.path)

        # if (self.path_length > 0):
        #     self.current_connection = 0
        #     self.archer.move_target.position = self.path[0].fromNode.position

        # else:
        #     self.archer.move_target.position = self.archer.path_graph.nodes[self.archer.base.target_node_index].position

class ArcherStateFocus_TeamA(State):

    def __init__(self, archer):

        State.__init__(self, "hyperfocus")
        self.archer = archer

    def do_actions(self):

        opponent_distance = (self.archer.position - self.archer.target.position).length()

        # opponent within range
        if opponent_distance <= self.archer.min_target_distance:
            self.archer.velocity = Vector2(0, 0)
            if self.archer.current_ranged_cooldown <= 0:
                self.archer.ranged_attack(self.archer.target.position)

        else:
            self.archer.velocity = self.archer.target.position - self.archer.position
            if self.archer.velocity.length() > 0:
                self.archer.velocity.normalize_ip();
                self.archer.velocity *= self.archer.maxSpeed


    def check_conditions(self):

        # target is gone
        if self.archer.world.get(self.archer.target.id) is None or self.archer.target.ko:
            self.archer.target = None
            return "seeking"

        return None

    def entry_actions(self):

        return None


class ArcherStateKO_TeamA(State):

    def __init__(self, archer):

        State.__init__(self, "ko")
        self.archer = archer

    def do_actions(self):

        return None


    def check_conditions(self):

        # respawned
        if self.archer.current_respawn_time <= 0:
            self.archer.current_respawn_time = self.archer.respawn_time
            self.archer.ko = False
            self.archer.path_graph = self.archer.world.paths[0]
            return "seeking"
            
        return None

    def entry_actions(self):

        self.archer.current_hp = self.archer.max_hp
        self.archer.position = Vector2(self.archer.base.spawn_position)
        self.archer.velocity = Vector2(0, 0)
        self.archer.target = None

        return None
