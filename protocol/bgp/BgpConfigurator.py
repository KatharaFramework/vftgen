import os


from protocol.bgp.ASManager import ASManager
from ..IConfigurator import IConfigurator

ZEBRA_CONFIG = \
"""hostname frr
password frr
enable password frr
"""

ROUTE_MAP = \
"""
ip prefix-list DC_LOCAL_SUBNET 5 permit 10.0.0.0/8 le 26
ip prefix-list DC_LOCAL_SUBNET 10 permit 200.0.0.0/8 le 32
route-map ACCEPT_DC_LOCAL permit 10
 match ip-address DC_LOCAL_SUBNET
 

"""

BGPD_BASIC_CONFIG = \
"""router bgp {as_number}
 timers bgp 3 9
 bgp router-id {router_id}
 bgp bestpath as-path multipath-relax
 bgp bestpath compare-routerid
{neighbor_config}

"""

NEIGHBOR_GROUP_CONFIG = \
""" neighbor {group} peer-group
 neighbor {group} remote-as external
 neighbor {group} advertisement-interval 0
 neighbor {group} timers connect 5"""

NEIGHBOR_PEER = " neighbor eth%d interface peer-group %s\n"

BGPD_ADDRESS_FAMILY = \
"""
{before}
address-family ipv4 unicast
  {neighbours}
  redistribute connected route-map ACCEPT_DC_LOCAL
  maximum-paths 64
exit-address-family"""
BGPD_LEAF_CONFIG = BGPD_ADDRESS_FAMILY.format(before="bgp bestpath as-path multipath-relax",
                                              neighbours="neighbor TOR activate"
                                              )
BGPD_SPINE_CONFIG = BGPD_ADDRESS_FAMILY.format(before="",
                                               neighbours="neighbor fabric activate\n  neighbor TOR activate"
                                               )
BGPD_TOF_CONFIG = BGPD_ADDRESS_FAMILY.format(before="",
                                             neighbours="neighbor fabric activate"
                                             )


class BgpConfigurator(IConfigurator):
    def _configure_node(self, lab, node):
        with open('%s/lab.conf' % lab.lab_dir_name, 'a') as lab_config:
            lab_config.write('%s[image]="kathara/frr"\n' % node.name)

        os.mkdir('%s/%s/etc/frr' % (lab.lab_dir_name, node.name))
        with open('%s/%s/etc/frr/daemons' % (lab.lab_dir_name, node.name), 'w') as daemons:
            daemons.write('zebra=yes\n')
            daemons.write('bgpd=yes\n')

        with open('%s/%s/etc/frr/zebra.conf' % (lab.lab_dir_name, node.name), 'w') as zebra_configuration:
            zebra_configuration.write(ZEBRA_CONFIG)

        with open('%s/%s/etc/frr/bgpd.conf' % (lab.lab_dir_name, node.name), 'w') as bgpd_configuration:
            bgpd_configuration.write(ZEBRA_CONFIG)

            self._write_route_map(bgpd_configuration)

            method_name = "_write_bgp_%s_configuration" % node.role
            write_node_configuration = getattr(self, method_name)
            write_node_configuration(node, bgpd_configuration)

        with open('%s/%s.startup' % (lab.lab_dir_name, node.name), 'a') as startup:
            startup.write('/etc/init.d/frr start\n')
            startup.write('sysctl -w net.ipv4.fib_multipath_hash_policy=1\n')

    @staticmethod
    def _write_route_map(bgpd_configuration):
        bgpd_configuration.write(ROUTE_MAP)

    @staticmethod
    def _write_bgp_leaf_configuration(node, bgpd_configuration):
        bgpd_configuration.write(
            BGPD_BASIC_CONFIG.format(as_number=ASManager.get_instance().get_as_number(node),
                                     router_id=str(node.interfaces[0].ip_address),
                                     neighbor_config=NEIGHBOR_GROUP_CONFIG.format(group="TOR")
                                     )
        )

        for interface in node.interfaces:
            if 'spine' in interface.neighbours[0][0]:
                bgpd_configuration.write(NEIGHBOR_PEER % (interface.number, "TOR"))

        bgpd_configuration.write(BGPD_LEAF_CONFIG)

    @staticmethod
    def _write_bgp_spine_configuration(node, bgpd_configuration):
        bgpd_configuration.write(
            BGPD_BASIC_CONFIG.format(as_number=ASManager.get_instance().get_as_number(node),
                                     router_id=str(node.interfaces[0].ip_address),
                                     neighbor_config="\n".join([NEIGHBOR_GROUP_CONFIG.format(group="TOR"),
                                                                NEIGHBOR_GROUP_CONFIG.format(group="fabric")
                                                                ]
                                                               )
                                     )
        )

        for interface in node.interfaces:
            if 'leaf' in interface.neighbours[0][0]:
                bgpd_configuration.write(NEIGHBOR_PEER % (interface.number, "TOR"))

        for interface in node.interfaces:
            if 'spine' in interface.neighbours[0][0] or 'tof' in interface.neighbours[0][0]:
                bgpd_configuration.write(NEIGHBOR_PEER % (interface.number, "fabric"))

        bgpd_configuration.write(BGPD_SPINE_CONFIG)

    @staticmethod
    def _write_bgp_tof_configuration(node, bgpd_configuration):
        bgpd_configuration.write(
            BGPD_BASIC_CONFIG.format(as_number=ASManager.get_instance().get_as_number(node),
                                     router_id=str(node.interfaces[0].ip_address),
                                     neighbor_config=NEIGHBOR_GROUP_CONFIG.format(group="fabric")
                                     )
        )

        for interface in node.interfaces:
            if 'spine' in interface.neighbours[0][0] or 'tof' in interface.neighbours[0][0]:
                bgpd_configuration.write(NEIGHBOR_PEER % (interface.number, "fabric"))

        bgpd_configuration.write(BGPD_TOF_CONFIG)
