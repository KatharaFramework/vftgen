from networking.CollisionDomain import CollisionDomain
from ..node.Node import Node


class Tof(Node):

    def __init__(self, number, plane, aggregation_layer_level, number_of_pods=0,
                 southbound_spines_connected_per_pod=0, number_of_planes=1, tof2tof=False):
        """
        Initialize the tof object assigning name and populating its neighbours
        :param number: (int) the number of the tof in this level and in this plane
        :param plane: (int) the number of the plane of the tof
        :param aggregation_layer_level: (int) the level of the tof in the aggregation layer
        :param number_of_pods: (int, default=0) total number of pods
        :param southbound_spines_connected_per_pod: (int, default=0) number of spines connected southbound per pod
        :param number_of_planes: (int, default=1) the total number of planes in the topology
        :param tof2tof: (bool) if true add tof to tof links else None
        """
        super().__init__()
        self.role = 'tof'
        self.name = 'tof_%d_%d_%d' % (plane, aggregation_layer_level, number)
        self.level = aggregation_layer_level
        self.plane = plane
        self.number = number
        self.number_of_planes = number_of_planes

        self._add_neighbours(aggregation_layer_level, number_of_pods,
                             southbound_spines_connected_per_pod, tof2tof)

        self._assign_ipv4_address_to_interfaces()

    def _add_neighbours(self, aggregation_layer_level, number_of_pods,
                        southbound_spines_connected_per_pod, tof2tof):
        """
        Add all neighbours to the tof
        :param aggregation_layer_level: (int) the level of the tof in the aggregation layer
        :param number_of_pods: (int, default=0) total number of pods
        :param southbound_spines_connected_per_pod: (int, default=0) number of spines connected southbound per pod
        """
        for pod_number in range(1, number_of_pods + 1):
            for spine_number in range(1, southbound_spines_connected_per_pod + 1):
                southern_spine_name = 'spine_%d_%d_%d' % (pod_number, aggregation_layer_level - 1,
                                                          spine_number + (southbound_spines_connected_per_pod *
                                                                          (self.plane - 1)
                                                                          )
                                                          )
                self._add_neighbour(southern_spine_name)

        if tof2tof:
            self._add_tof2tof_links()

    def _add_neighbour(self, node_name):
        """
            Selects a collision domain and adds a neighbour
            (represented by (node_name, collision_domain)) to self.neighbours
            :param node_name: the name of the neighbour to add
            :return:
        """
        collision_domain = CollisionDomain.get_instance().get_collision_domain(self.name, node_name)
        self.neighbours.append((node_name, collision_domain))

    def _add_tof2tof_links(self):
        """
            Add tof to tof (east-west) links
        """
        tof_next_name = None
        if self.plane == 1:
            tof_prev_name = 'tof_%d_%d_%d' % (self.number_of_planes, self.level, self.number)
            if self.number_of_planes > 2:
                tof_next_name = 'tof_%d_%d_%d' % (self.plane + 1, self.level, self.number)
        elif self.plane == self.number_of_planes:
            tof_prev_name = 'tof_%d_%d_%d' % (self.plane - 1, self.level, self.number)
            if self.number_of_planes > 2:
                tof_next_name = 'tof_%d_%d_%d' % (1, self.level, self.number)
        else:
            tof_prev_name = 'tof_%d_%d_%d' % (self.plane - 1, self.level, self.number)
            tof_next_name = 'tof_%d_%d_%d' % (self.plane + 1, self.level, self.number)

        self._add_neighbour(tof_prev_name)
        if tof_next_name:
            self._add_neighbour(tof_next_name)
