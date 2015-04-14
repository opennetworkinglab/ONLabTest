"""Custom topology example

Two directly connected switches plus hosts for each switch:

   host(s) --- switch --- switch -- switch --- host(s)

Adding the 'topos' dict with a key/value pair to generate our newly defined
topology enables one to pass in '--topo=mytopo' from the command line.
"""

from mininet.topo import Topo
import sys
import os

class MyTopo( Topo ):
    "Simple topology example."

    def __init__( self ):
        "Create custom topo."

        # Initialize topology
        Topo.__init__( self )

        # Add hosts and switches
        host1 = self.addHost( 'h1' )
        host2 = self.addHost( 'h2' )

	s1 = self.addSwitch('s1')
	s2 = self.addSwitch('s2')
	s3 = self.addSwitch('s3')
	s4 = self.addSwitch('s4')
	s5 = self.addSwitch('s5')
	s6 = self.addSwitch('s6')

        # Add links
        self.addLink( host1, s1)
        self.addLink( host2, s6 )
        self.addLink( s1, s2 )
        self.addLink( s1, s3)
        self.addLink( s2, s3)
        self.addLink( s2, s5 )
        self.addLink( s3, s4 )
	self.addLink( s4, s5 )
	self.addLink( s4, s6)
	self.addLink( s5, s6)



topos = { 'mytopo': ( lambda: MyTopo() ) }
