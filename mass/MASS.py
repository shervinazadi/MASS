import topogenesis as tg
import numpy as np
import pandas as pd

# Environment class
class environment():
    def __init__(self, avail_lattice : tg.lattice ,lattices : dict, agents_dict : dict, stencils: dict):
        self.lattices = lattices
        self.lattice_names = [lattices.keys()]
        self.avail_lattice = avail_lattice
        self.occ_lattice = avail_lattice * 0 - 1
        self.bounds = avail_lattice.bounds
        self.shape = avail_lattice.shape
        self.stencils = stencils
        self.initialization(agents_dict)

        #TODO: do we need distance matrix?

    def all_lattice_update(self):
        # TODO: run lattice update on all dynamic lattices
        
        pass

    def lattice_update(self, lattice_key: str):
        # TODO: recompute the specified lattice

        pass

    def all_agents_action(self):
        # TODO: run the action method of all agents
        pass

    def agent_action(self, agent_key: str):
        # TODO: run the action method of specified agents
        pass

    def all_agents_evaluation(self):
        # TODO: run the evaluation method of all agents
        pass

    def agent_evaluation(self, agent_key: str):
        # TODO: run the evaluation method of specified agents
        pass

    def all_neighbours_evaluation(self):
        # TODO: run the evaluation method of all neighbours
        for agn in self.agents:
            for lat in self.lattices:
                pass
                
        pass

    def all_agents_initialization(self, agents_dict : dict):
        env_agents = {}
        for name, a in agents_dict.items():
            # TODO: Check if the agents preferences are matching with the environment lattices
            agent_preferences = a["preferences"].keys()
            agent_pref_name_check = agent_preferences == self.lattices.keys()
            if agent_pref_name_check:
                agn_id = a["aid"]
                # TODO: Check if the specified stencils by agent is available in the environment stencils
                # TODO: Run agent initialization method
                env_agents[name] = agent(agn_id, name, self, a["preferences"], a["behaviors"])
                #env_agents[name] = agent(agn_id, name, self, a["preferences"], a["stencil_names"], a["behaviors"])
            else:
                pass

        
        self.agents = env_agents

    def initialization(self, agents_dict):
        if self.lattice_check():
            self.all_agents_initialization(agents_dict)
            self.init_neighbour_matrices()
        else:
            return

    def lattice_check(self):
        shapes, bounds, mins, maxs = [],[],[],[]
        # iterate over all lattices
        for l in self.lattices.values():
            shapes.append(l.shape)
            bounds.append(l.bounds.flatten())
            mins.append(l.min())
            maxs.append(l.max())
        # access lattice names in self.lattice_names --> Bahar: what is this?

        shape_check = np.all(np.array(shapes) == self.shape)
        bound_check = np.all(np.array(bounds) == self.bounds.flatten())
        mins_check = np.array(mins).astype(float).min() >= 0.0
        maxs_check = np.array(maxs).astype(float).max() <= 1.0
        if (shape_check and bound_check and mins_check and maxs_check):
            print("Valid environment created, shape =" + str(self.shape))
            return True
        else:
            error = "Couldn't initialize the environment. Error: "
            if not shape_check:
                error += "lattice shapes doesn't match, "
            if not bound_check:
                error += "lattice bounds' doesn't match, "
            if not mins_check:
                error += "negative value found in lattice, "
            if not maxs_check:
                error += "maximum value in lattice is more than one."
            print(error)
            return False

    def init_neighbour_matrices(self):
        neigh_matrices = {}
        for stencil_name, stencil in self.stencils.items():
            neigh_matrices[stencil_name] = self.avail_lattice.find_neighbours(stencil)
        self.neigh_matrices = neigh_matrices

# Agent class
class agent():
    def __init__(self, aid: int, name: str, env: environment, preferences: dict, behaviors: list, origin: list = None):
        self.name = name
        self.id = aid
        self.preferences = preferences
        self.behaviors = behaviors

        if origin:
            self.origin = origin
        else:
            self.origin = agent.find_seed(self, env)   
        
        self.occ_lattice = (env.occ_lattice * 0).astype(np.bool)
        self.occ_lattice[tuple(self.origin.flatten())] = True

        self.update_env_lattices(env)
        self.evaluation(env)
        # TODO: initialize the agent's available neighbour lattice per stencil
        # self.neighbours = {}
        # self.update_neighbor(env)
            

    def find_seed(self, env: environment):
        # TODO: run the initial seed finding
        avail_voxels = np.argwhere(env.avail_lattice == 1)
        select_id = np.random.choice(len(avail_voxels), 1)
        return avail_voxels[select_id]
    
    def update_env_lattices(self, env:environment):
        env.occ_lattice[self.occ_lattice] = self.id
        env.avail_lattice[self.occ_lattice] = 0

    # def evaluation(self, env : environment):
    #     # needs to be completed
    #     eval_lat = tg.to_lattice(np.ones(self.occ_lattice.shape), self.occ_lattice)
    #     self.eval_lat = eval_lat

    def evaluation(self, env:environment):
        eval_lattice = tg.to_lattice(np.ones(env.avail_lattice.shape), env.avail_lattice.shape)
        for lat_name, lat in env.lattices.items():
            eval_lattice *= lat.astype(float) ** self.preferences[lat_name]["weight"]
        self.eval_lat = eval_lattice

    @property
    def satisfaction(self):
        # Bahar: I guess we have a problem here!
        return np.mean(self.eval_lat[self.occ_lattice])

    @property
    def bounding_box(self):
        b_box = np.copy(self.occ_lattice)
        b_slice = np.nonzero(self.occ_lattice)
        b_box[b_slice.min(1,2): b_slice.max(1,2) + 1, b_slice.min(0,2): b_slice.max(0,2) + 1, b_slice.min(0,1) : b_slice.max(0,1) + 1] = 1
        return b_box
    
    @property
    def shape(self):
        return np.nonzero(self.bounding_box).shape

    def bhv_occupy(self, env : environment, vox_lattice : tg.lattice):
        self.occ_lattice[vox_lattice] = 1.0
        self.update_env_lattices(env)

    def bhv_leave(self, env : environment, vox_lattice : tg.lattice):
        self.occ_lattice[vox_lattice] = 0.0
        self.update_env_lattices(env)

    def bhv_find_neighbour (self, stencil_name : str, env: environment, return_counts=False, return_neigh_ind=False):
        all_neighs = env.neigh_matrices[stencil_name]
        agn_neighs = all_neighs[np.where(np.array(self.occ_lattice).flatten())].flatten()
        neighbourhood_flat = self.occ_lattice.flatten() * 0
        # all_neighbours = env.neigh_matrix[np.where(np.array(self.occ_lattice).flatten())].reshape(tuple([-1] + list(self.occ_lattice.shape))).sum(0)
        if return_counts:
            unq_neighs, unq_counts = np.unique(agn_neighs, return_counts=True)
            neighbourhood_flat[unq_neighs] = unq_counts
        else:
            neighbourhood_flat[agn_neighs] = 1

        neighbourhood = tg.to_lattice(neighbourhood_flat.reshape(self.occ_lattice.shape), self.occ_lattice)

        if return_neigh_ind:
            if return_neigh_ind=="1D":
                indices_1d = np.argwhere(neighbourhood_flat > 0)
                return (neighbourhood, indices_1d)
            elif return_neigh_ind=="3D":
                indices_3d = np.argwhere(neighbourhood > 0)
                return (neighbourhood, indices_3d)
        else:
            return neighbourhood

    def bhv_squareness(self):
        pass
    # TODO : box character
    def char_embed_box(self):
        #self.bounding_box *= self.character[box]
        pass

    # TODO : depth behavior
    def char_building_depth(self, env : environment):
        pass

    def action(self):
        # TODO: run all the specified behaviors of the agents with their corresponding parameters
        pass

# Dynamic Lattice class
class dynamic_lattice(tg.lattice):
    def __init__(self):
        pass

    def euclidian_distance(self):
        pass

    def manifold_distance(self):
        pass

    def sightline(self):
        pass