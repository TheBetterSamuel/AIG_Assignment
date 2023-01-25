import pygame

from random import randint, random
from Graph import *

from Character import *
from State import *

class Knight_TeamA(Character):

    def __init__(self, world, image, base, position):

        Character.__init__(self, world, "knight", image)

        self.level_up_times = 0

        self.next_node_path = None

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
        rushing_state = KnightStateRushing_TeamA(self)

        self.brain.add_state(seeking_state)
        self.brain.add_state(attacking_state)
        self.brain.add_state(ko_state)
        self.brain.add_state(rushing_state)

        self.brain.set_state("seeking")
        

    def render(self, surface):

        Character.render(self, surface)


    def process(self, time_passed):
        
        Character.process(self, time_passed)

        level_up_stats = ["hp", "melee damage"]
        if self.can_level_up():
            if self.level_up_times <= 2:
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
                if distance < 160:
                    nearest_tower = entity
                
            if (entity.name == "base") and (entity.team_id != 2 or entity.team_id != self.team_id):
                distance = (self.position - entity.position).length()
                if distance < 130:
                    return entity
                
        return nearest_tower

    def get_base(self):

        nearest_tower = None
        distance = 0.

        for entity in self.world.entities.values():

            # neutral entity
            if entity.team_id == 2:
                continue

            # same team
            if entity.team_id == self.team_id:
                continue
                
            if (entity.name == "base") and (entity.team_id != 2 or entity.team_id != self.team_id):
                return entity
                
        return nearest_tower

class KnightStateRushing_TeamA(State):

    def __init__(self, knight):

        State.__init__(self, "rushing")
        self.knight = knight

    def do_actions(self):

        self.knight.velocity = self.knight.move_target.position - self.knight.position
        if self.knight.velocity.length() > 0:
            self.knight.velocity.normalize_ip()
            self.knight.velocity *= self.knight.maxSpeed


    def check_conditions(self):

        #if hp is below 100%, heal
        if self.knight.current_hp/self.knight.max_hp < 1 :
            self.knight.heal()

        #set enemy base as target
        opponent = self.knight.get_base()
        if opponent is not None:
            opponent_distance = (self.knight.position - opponent.position).length()
            if opponent_distance <= self.knight.min_target_distance:
                    self.knight.target = opponent
                    return "attacking"

        if (self.knight.position - self.knight.move_target.position).length() < 8:

            #continue on path
            if self.current_connection < self.path_length:
                self.knight.move_target.position = self.path[self.current_connection].toNode.position
                self.current_connection += 1
            
        return None

    def entry_actions(self):

        #find the path where the tower is destroyed
        if self.knight.next_node_path is not None:
            if self.knight.next_node_path.id == 8:
                targetNode_id =17
            elif self.knight.next_node_path.id == 17:
                targetNode_id = 8
            elif self.knight.next_node_path.id == 1:
                targetNode_id = 10
            elif self.knight.next_node_path.id == 10:
                targetNode_id = 1
            else:
                targetNode_id = 9
                    
            for i in range(0,4):
                for node in self.knight.world.paths[i].nodes.values():
                    if node.id == targetNode_id:
                        self.knight.path_graph = self.knight.world.paths[i]

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
  


class KnightStateSeeking_TeamA(State):

    def __init__(self, knight):

        State.__init__(self, "seeking")
        self.knight = knight

        self.knight.path_graph = self.knight.world.paths[0]


    def do_actions(self):

        self.knight.velocity = self.knight.move_target.position - self.knight.position
        if self.knight.velocity.length() > 0:
            self.knight.velocity.normalize_ip()
            self.knight.velocity *= self.knight.maxSpeed


    def check_conditions(self):

        #if hp is below 100%, heal
        if self.knight.current_hp/self.knight.max_hp < 1 :
            self.knight.heal()

        tower_list = self.knight.get_remaining_towers()
        remaining_towers = len(tower_list)
        if remaining_towers == 1:
            final_tower = tower_list[0]
            self.knight.next_node_path = self.knight.get_closest_node(final_tower.position)
            
        #if colliding with obstacle, return to path
        collision_list = pygame.sprite.spritecollide(self.knight, self.knight.world.obstacles, False, pygame.sprite.collide_mask)
        for entity in collision_list:
            if entity.team_id == self.knight.team_id:
                continue
            elif entity.name == "obstacle":
                nearest_node = self.knight.path_graph.get_nearest_node(self.knight.position)
                self.knight.velocity = nearest_node.position - self.knight.position
                if self.knight.velocity.length() > 0:
                    self.knight.velocity.normalize_ip();
                    self.knight.velocity *= self.knight.maxSpeed
                    #self.knight.velocity = self.knight.base.spawn_position - self.knight.position

                
        nearest_opponent = self.knight.world.get_nearest_opponent(self.knight)

        if nearest_opponent is not None:
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

        self.knight.target = None

        #goes to next node instead of moving back
        nearest_node = self.knight.path_graph.get_nearest_node(self.knight.position)
        path_node_list = list(self.knight.world.paths[1].nodes.values())
        count = 0
        for node in path_node_list:
            if nearest_node.id == 0:
               break
            if node.id == nearest_node.id and count < len(path_node_list)-1:
                count += 1
                nearest_node = path_node_list[count]
                break
            count += 1
            
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
            self.knight.colliding_target = True

        else:
            self.knight.velocity = self.knight.target.position - self.knight.position
            if self.knight.velocity.length() > 0:
                self.knight.velocity.normalize_ip();
                self.knight.velocity *= self.knight.maxSpeed

    def check_conditions(self):

        next_nearest = self.knight.world.get_nearest_opponent(self.knight)
        if next_nearest.name != "base" and next_nearest.name != "tower":
            if self.knight.target.name != next_nearest.name:
                self.knight.target = next_nearest

        #if hp is below 30%, heal
        if self.knight.current_hp/self.knight.max_hp < 0.3 :
            self.knight.heal()

        #get location of final tower
        tower_list = self.knight.get_remaining_towers()
        remaining_towers = len(tower_list)
        if remaining_towers == 1:
            final_tower = tower_list[0]
            
        #moves outside of final tower range while attacking base
        if self.knight.target.name == "base":
            if self.knight.colliding_target == True:
                if remaining_towers == 1:
                    if (self.knight.position - final_tower.position).length() < final_tower.min_target_distance:
                        self.knight.velocity = self.knight.position - final_tower.position

        
        #if colliding with obstacle, return to path
        collision_list = pygame.sprite.spritecollide(self.knight, self.knight.world.obstacles, False, pygame.sprite.collide_mask)
        for entity in collision_list:
            if entity.team_id == self.knight.team_id:
                continue
            elif entity.name == "obstacle":
                nearest_node = self.knight.path_graph.get_nearest_node(self.knight.position)
                self.knight.velocity = nearest_node.position - self.knight.position
                if self.knight.velocity.length() > 0:
                    self.knight.velocity.normalize_ip();
                    self.knight.velocity *= self.knight.maxSpeed
                return "seeking"
                    #self.knight.velocity = self.knight.base.spawn_position - self.knight.position

        #if detect tower nearby, target tower instead
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

        self.knight.colliding_target = False

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
                return "rushing"
            else:
                self.knight.path_graph = self.knight.world.paths[0]
            return "seeking"
            
        return None

    def entry_actions(self):

        self.knight.current_hp = self.knight.max_hp
        self.knight.position = Vector2(self.knight.base.spawn_position)
        self.knight.velocity = Vector2(0, 0)
        self.knight.target = None

        return None