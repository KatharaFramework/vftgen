from ..node.Node import Node
from networking.CollisionDomain import CollisionDomain


class Tof(Node):
    def __init__(self, name, level, aggregation_layer_levels, tofs_per_level, pod_levels, number_of_pods=0,
                 southbound_spines_connected_per_pod=0):
        """
        Initialize the tof object assigning name and populating its neighbours
        :param name: (string) the name of the tof
        :param level: (int) the level of the tof in the aggregation layer
        :param aggregation_layer_levels: (int) total number of aggregation levels
        :param tofs_per_level: (int list) each element in pos x represents the number of tof at level x+1
        :param pod_levels: (int) total number of level in a pod
        :param number_of_pods: (int, default=0) total number of pods
        :param southbound_spines_connected_per_pod: (int, default=0) number of spines at the last level of each pod
        """
        super().__init__()
        self.role = 'tof'
        self.name = name
        self.level = level
        self._add_neighbours(level, aggregation_layer_levels, tofs_per_level, pod_levels, number_of_pods,
                             southbound_spines_connected_per_pod)
        self._assign_ipv4_address_to_interfaces()

    def _add_neighbours(self, level, aggregation_layer_levels, tofs_per_level, pod_levels, number_of_pods,
                        southbound_spines_connected_per_pod):
        """
        Adds all the neighbours of this spine in self.neighbours as (neighbour_name, collision_domain)
        :param level: (int) the level of the tof in the aggregation layer
        :param aggregation_layer_levels: (int) total number of aggregation levels
        :param tofs_per_level: (int list) each element in pos x represents the number of tof at level x+1
        :param pod_levels: (int) total number of level in a pod
        :param number_of_pods: (int) total number of pods
        :param southbound_spines_connected_per_pod: (int) number of spines at the last level of each pod
        :return:
        """
        current_aggregation_layer_level = level - pod_levels    # The current aggregation layer level

        if current_aggregation_layer_level == 1:
            # If this is the first level of the aggregation layer
            # Connects southbound to all the spines at the last levels of each pod
            for pod_number in range(1, number_of_pods + 1):
                for spine_number in range(1, southbound_spines_connected_per_pod + 1):
                    southern_spine_name = 'spine_%d_%d_%d' % (pod_number, pod_levels, spine_number)

                    self._add_neighbour(southern_spine_name)

            if current_aggregation_layer_level < aggregation_layer_levels:
                # If this is not the last level of the aggregation level
                # Connects northbound to all the ToFs in the level above (of the aggregation level)
                for northern_tof_num in range(1, tofs_per_level[current_aggregation_layer_level - 1 + 1] + 1):
                    northern_tof_name = 'tof_%d_%d' % (level + 1, northern_tof_num)

                    self._add_neighbour(northern_tof_name)
        else:
            # If this is not the first level of the aggregation layer
            # Connects southbound to all the ToFs in previous level
            for southern_tof_num in range(1, tofs_per_level[current_aggregation_layer_level - 1 - 1] + 1):
                southern_tof_name = 'tof_%d_%d' % (level - 1, southern_tof_num)

                self._add_neighbour(southern_tof_name)

            if current_aggregation_layer_level < aggregation_layer_levels:
                # This is not the last level of the aggregation layer
                # Connects northbound to all the ToFs in the level above
                for northern_tof_num in range(1, tofs_per_level[current_aggregation_layer_level - 1 + 1] + 1):
                    northern_tof_name = 'tof_%d_%d' % (level + 1, northern_tof_num)

                    self._add_neighbour(northern_tof_name)

    def _add_neighbour(self, node_name):
        """
            Selects a collision domain and adds a neighbour
            (represented by (node_name, collision_domain)) to self.neighbours
            :param node_name: the name of the neighbour to add
            :return:
        """
        collision_domain = CollisionDomain.get_instance().get_collision_domain(self.name, node_name)
        self.neighbours.append((node_name, collision_domain))
