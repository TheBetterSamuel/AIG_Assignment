import pygame

from random import randint, random
from Graph import *

from Character import *
from State import *

class Knight_TeamA(Character):

    def __init__(self, world, image, base, position):

        Character.__init__(self, world, "knight", image)

        self.level_up_times = 0

        self.base = base
        self.position = position
        self.move_target = GameEntity(world, "knight_move_target", None)
        self.target = None

        self.maxSpeed = 80
        self.min_target_distance = 100
        self.melee_damage = 20
        self.melee_cooldown = 2.

        seeking_state = KnightStateSeeking_TeamA(self)
        attacking_state = KnightStateAttacking_TeamA(self)
        ko_state = KnightStateKO_TeamA(self)

        self.brain.add_state(seeking_state)
        self.brain.add_state(attacking_state)
        self.brain.add_state(ko_state)

        self.brain.set_state("seeking")
        

    def render(self, surface):

        Character.render(self, surface)


    def process(self, time_passed):
        
        Character.process(self, time_passed)

        level_up_stats = ["hp", "healing cooldown"]
        if self.can_level_up():
            if self.level_up_times <= 1:
                choice = 0
                self.level_up(level_up_stats[choice])
            else:
                choice = 1
                self.level_up(level_up_stats[choice])
            self.level_up_times += 1


    def get_closest_node(self, position):

        nearest = None
        for node in self.world.graph.nodes.values():
            if (node.id != 4) and (node.id != 0):
                if nearest is None:
                    nearest = node
                    nearest_distance = (position - Vector2(nearest.position)).length()
                else:
                    distance = (position - Vector2(node.position)).length()
                    if distance < nearest_distance:
                        nearest = node
                        nearest_distance = distance

        return nearest


    def get_remaining_towers(self):

        tower_list = []

        for entity in self.world.entities.values():

            # neutral entity
            if entity.team_id == 2:
                continue

            # same team
            if entity.team_id == self.team_id:
                continue
            
            if (entity.name == "tower") and (entity.team_id != 2 or entity.team_id != self.team_id):
                tower_list.append(entity)
                    
        return tower_list

    def get_nearest_tower(self):

        nearest_tower = None
        distance = 0.

        for entity in self.world.entities.values():

            # neutral entity
            if entity.team_id == 2:
                continue

            # same team
            if entity.team_id == self.team_id:
                continue
            
            if (entity.name == "tower") and (entity.team_id != 2 or entity.team_id != self.team_id):
                distance = (self.position - entity.position).length()
                if distance < 150:
                    nearest_tower = entity
                
            if (entity.name == "base") and (entity.team_id != 2 or entity.team_id != self.team_id):
                distance = (self.position - entity.position).length()
                if distance < 150:
                    return entity
                
        return nearest_tower

   


class KnightStateSeeking_TeamA(State):

    def __init__(self, knight):

        State.__init__(self, "seeking")
        self.knight = knight

        self.knight.path_graph = self.knight.world.paths[3]


    def do_actions(self):

        self.knight.velocity = self.knight.move_target.position - self.knight.position
        if self.knight.velocity.length() > 0:
            self.knight.velocity.normalize_ip()
            self.knight.velocity *= self.knight.maxSpeed

        #if hp is below 50, heal
        if self.knight.current_hp <= 50:
            self.knight.heal()


    def check_conditions(self):

        tower_list = self.knight.get_remaining_towers()
        remaining_towers = len(tower_list)
        if remaining_towers == 1:
            final_tower = tower_list[0]
            self.knight.next_node_path = self.knight.get_closest_node(final_tower.position)
            

        collision_list = pygame.sprite.spritecollide(self.knight, self.knight.world.obstacles, False, pygame.sprite.collide_mask)
        for entity in collision_list:
            if entity.team_id == self.knight.team_id:
                continue
            elif entity.name == "obstacle" or entity.name == "base":
                continue
                
        #use this section here to code different actions when encountering different entities
        #nearest_opponent.name to get type of entity
        # check if opponent is in range
        nearest_opponent = self.knight.world.get_nearest_opponent(self.knight)
        #nearest_tower = self.knight.get_nearest_tower()
        nearest_tower = None

        if nearest_opponent is not None:
            if nearest_tower is not None:
                nearest_opponent = nearest_tower
                opponent_distance = (self.knight.position - nearest_opponent.position).length()
                if opponent_distance <= self.knight.min_target_distance:
                        self.knight.target = nearest_opponent
                        return "attacking"
            else:
                opponent_distance = (self.knight.position - nearest_opponent.position).length()
                if opponent_distance <= self.knight.min_target_distance:
                        self.knight.target = nearest_opponent
                        return "attacking"
        
        if (self.knight.position - self.knight.move_target.position).length() < 8:

            #continue on path
            if self.current_connection < self.path_length:
                self.knight.move_target.position = self.path[self.current_connection].toNode.position
                self.current_connection += 1
            
        return None


    def entry_actions(self):
        nearest_node = self.knight.path_graph.get_nearest_node(self.knight.position)

        self.path = pathFindAStar(self.knight.path_graph, \
                                  nearest_node, \
                                  self.knight.path_graph.nodes[self.knight.base.target_node_index])

        
        self.path_length = len(self.path)

        if (self.path_length > 0):
            self.current_connection = 0
            self.knight.move_target.position = self.path[0].fromNode.position

        else:
            self.knight.move_target.position = self.knight.path_graph.nodes[self.knight.base.target_node_index].position


class KnightStateAttacking_TeamA(State):

    def __init__(self, knight):

        State.__init__(self, "attacking")
        self.knight = knight

    def do_actions(self):

        # colliding with target
        if pygame.sprite.collide_rect(self.knight, self.knight.target):
            self.knight.velocity = Vector2(0, 0)
            self.knight.melee_attack(self.knight.target)

        else:
            self.knight.velocity = self.knight.target.position - self.knight.position
            if self.knight.velocity.length() > 0:
                self.knight.velocity.normalize_ip();
                self.knight.velocity *= self.knight.maxSpeed

        #if hp is below 50, heal
        if self.knight.current_hp <= 50:
            self.knight.heal()
            


    def check_conditions(self):
        tower_list = self.knight.get_remaining_towers()
        remaining_towers = len(tower_list)
        if remaining_towers == 1:
            final_tower = tower_list[0]
            self.knight.next_node_path = self.knight.get_closest_node(final_tower.position)

        collision_list = pygame.sprite.spritecollide(self.knight, self.knight.world.obstacles, False, pygame.sprite.collide_mask)
        for entity in collision_list:
            if entity.team_id == self.knight.team_id:
                continue
            elif entity.name == "obstacle" or entity.name == "base":
                self.knight.velocity = self.knight.base.spawn_position - self.knight.position
                if self.knight.velocity.length() > 0:
                    self.knight.velocity.normalize_ip();
                    self.knight.velocity *= self.knight.maxSpeed

        
        nearest_tower = self.knight.get_nearest_tower()

        if nearest_tower is not None:
            nearest_opponent = nearest_tower
            opponent_distance = (self.knight.position - nearest_opponent.position).length()
            if opponent_distance <= self.knight.min_target_distance:
                    self.knight.target = nearest_opponent

        # target is gone
        if self.knight.world.get(self.knight.target.id) is None or self.knight.target.ko:
            self.knight.target = None
            return "seeking"
            
        return None

    def entry_actions(self):

        return None


class KnightStateKO_TeamA(State):

    def __init__(self, knight):

        State.__init__(self, "ko")
        self.knight = knight

    def do_actions(self):

        return None


    def check_conditions(self):

        tower_list = self.knight.get_remaining_towers()
        remaining_towers = len(tower_list)
        if remaining_towers == 1:
            final_tower = tower_list[0]
            self.knight.next_node_path = self.knight.get_closest_node(final_tower.position)

        # respawned
        if self.knight.current_respawn_time <= 0:

            self.knight.current_respawn_time = self.knight.respawn_time
            self.knight.ko = False

            if self.knight.next_node_path is not None:
                if self.knight.next_node_path.id == 3:
                    targetNode_id = 7
                elif self.knight.next_node_path.id == 7:
                    targetNode_id = 3
                elif self.knight.next_node_path.id == 1:
                    targetNode_id = 5
                elif self.knight.next_node_path.id == 5:
                    targetNode_id = 1
                    
                for i in range(0,4):
                    for node in self.knight.world.paths[i].nodes.values():
                        if node.id == targetNode_id:
                            self.knight.path_graph = self.knight.world.paths[i]
            else:
                self.knight.path_graph = self.knight.world.paths[3]
            return "seeking"
            
        return None

    def entry_actions(self):

        self.knight.current_hp = self.knight.max_hp
        self.knight.position = Vector2(self.knight.base.spawn_position)
        self.knight.velocity = Vector2(0, 0)
        self.knight.target = None

        return None
