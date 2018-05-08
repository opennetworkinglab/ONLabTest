"""
Copyright 2018 Open Networking Foundation ( ONF )

Please refer questions to either the onos test mailing list at <onos-test@onosproject.org>,
the System Testing Plans and Results wiki page at <https://wiki.onosproject.org/x/voMg>,
or the System Testing Guide page at <https://wiki.onosproject.org/x/WYQg>

    TestON is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 2 of the License, or
    ( at your option ) any later version.

    TestON is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with TestON.  If not, see <http://www.gnu.org/licenses/>.
"""

import time

def setupTest( main, test_idx, onosNodes ):
    from tests.USECASE.SegmentRouting.dependencies.Testcaselib import Testcaselib as lib
    skipPackage = False
    init = False
    if not hasattr( main, "apps" ):
        init = True
        lib.initTest( main )
    # Skip onos packaging if the cluster size stays the same
    if not init and onosNodes == main.Cluster.numCtrls:
        skipPackage = True

    main.resultFileName = "CASE%03d" % test_idx
    main.Cluster.setRunningNode( onosNodes )
    lib.installOnos( main, skipPackage=skipPackage, cliSleep=5 )
    # Load configuration files
    main.step( "Load configurations" )
    main.cfgName = "TEST_CONFIG_ipv4=1_ipv6=1_dhcp=1_routers=1"
    lib.loadJson( main )
    time.sleep( float( main.params[ "timers" ][ "loadNetcfgSleep" ] ) )
    main.cfgName = "common"
    lib.loadMulticastConfig( main )

    if hasattr( main, "Mininet1" ):
        # Run the test with Mininet
        mininet_args = " --dhcp=1 --routers=1 --ipv6=1 --ipv4=1"
        lib.startMininet( main, main.params[ "DEPENDENCY" ][ "topology" ], args=mininet_args )
        time.sleep( float( main.params[ "timers" ][ "startMininetSleep" ] ) )
    else:
        # Run the test with physical devices
        lib.connectToPhysicalNetwork( main, self.switchNames )
        # Check if the devices are up
        lib.checkDevices( main, switches=len( self.switchNames ) )

    # Create scapy components
    lib.startScapyHosts( main )

def verifyMcastRoutes( main ):
    """
    Install multicast routes and check traffic
    """
    from tests.USECASE.SegmentRouting.dependencies.Testcaselib import Testcaselib as lib
    for routeName in main.mcastRoutes.keys():
        main.step( "Verify {} multicast route".format( routeName ) )
        installMcastRoute( main, routeName )
        lib.verifyMulticastTraffic( main, routeName, True )

def installMcastRoute( main, routeName ):
    """
    Install a multicast route
    """
    routeData = main.multicastConfig[ routeName ]
    src = main.mcastRoutes[ routeName ][ "src" ]
    dst = main.mcastRoutes[ routeName ][ "dst" ]
    main.Cluster.active( 0 ).CLI.mcastHostJoin( routeData[ "src" ][ src[ 0 ] ][ "ip" ], routeData[ "group" ],
                                                [ routeData[ "src" ][ i ][ "id" ] for i in src ],
                                                [ routeData[ "dst" ][ i ][ "id" ] for i in dst ] )
    time.sleep( float( main.params[ "timers" ][ "mcastSleep" ] ) )

def verifyMcastRouteRemoval( main, routeName ):
    """
    Verify removal of a multicast route
    """
    routeData = main.multicastConfig[ routeName ]
    main.step( "Verify removal of {} route".format( routeName ) )
    main.Cluster.active( 0 ).CLI.mcastSinkDelete( routeData[ "src" ][ 0 ][ "ip" ], routeData[ "group" ] )
    # TODO: verify the deletion

def verifyMcastSinkRemoval( main, routeName, sinkIndex, expect ):
    """
    Verify removal of a multicast sink
    """
    from tests.USECASE.SegmentRouting.dependencies.Testcaselib import Testcaselib as lib
    routeData = main.multicastConfig[ routeName ]
    sinkId = routeData[ "dst" ][ sinkIndex ][ "id" ]
    main.step( "Verify removal of {} sink {}".format( routeName, sinkId ) )
    main.Cluster.active( 0 ).CLI.mcastSinkDelete( routeData[ "src" ][ 0 ][ "ip" ], routeData[ "group" ], sinkId )
    time.sleep( float( main.params[ "timers" ][ "mcastSleep" ] ) )
    lib.verifyMulticastTraffic( main, routeName, expect )

def verifyMcastSourceRemoval( main, routeName, sourceIndex, expect ):
    """
    Verify removal of a multicast source
    """
    from tests.USECASE.SegmentRouting.dependencies.Testcaselib import Testcaselib as lib
    routeData = main.multicastConfig[ routeName ]
    sourceId = [ routeData[ "src" ][ sourceIndex ][ "id" ] ]
    main.step( "Verify removal of {} source {}".format( routeName, sourceId ) )
    main.Cluster.active( 0 ).CLI.mcastSourceDelete( routeData[ "src" ][ 0 ][ "ip" ], routeData[ "group" ], sourceId )
    time.sleep( float( main.params[ "timers" ][ "mcastSleep" ] ) )
    lib.verifyMulticastTraffic( main, routeName, expect )

def verifyMcastRemoval( main, removeDHT1=True ):
    """
    Verify removal of IPv6 route, IPv4 sinks and IPv4 source
    """
    from tests.USECASE.SegmentRouting.dependencies.Testcaselib import Testcaselib as lib
    verifyMcastRouteRemoval( main, "ipv6" )
    if removeDHT1:
        verifyMcastSinkRemoval( main, "ipv4", 0, [ False, True, True ] )
        verifyMcastSinkRemoval( main, "ipv4", 1, [ False, False, True ] )
    else:
        verifyMcastSinkRemoval( main, "ipv4", 2, [ True, True, False ] )
        verifyMcastSinkRemoval( main, "ipv4", 1, [ True, False, False ] )
    verifyMcastSourceRemoval( main, "ipv4", 0, False )

def verifyLinkDown( main, link, affectedLinkNum, expectList={ "ipv4": True, "ipv6": True }, hostsToDiscover=[], hostLocations={} ):
    """
    Kill a batch of links and verify traffic
    Restore the links and verify traffic
    """
    from tests.USECASE.SegmentRouting.dependencies.Testcaselib import Testcaselib as lib
    link = link if ( isinstance( link, list ) and isinstance( link[ 0 ], list ) ) else [ link ]
    # Kill the link(s)
    lib.killLinkBatch( main, link, int( main.params[ "TOPO" ][ "linkNum" ] ) - affectedLinkNum, int( main.params[ "TOPO" ][ "switchNum" ] ) )
    for routeName in expectList.keys():
        lib.verifyMulticastTraffic( main, routeName, expectList[ routeName ] )
    # Restore the link(s)
    lib.restoreLinkBatch( main, link, int( main.params[ "TOPO" ][ "linkNum" ] ), int( main.params[ "TOPO" ][ "switchNum" ] ) )
    if hostsToDiscover:
        main.Network.discoverHosts( hostList=hostsToDiscover )
    for host, loc in hostLocations.items():
        lib.verifyHostLocation( main, host, loc, retry=5 )
    for routeName in expectList.keys():
        lib.verifyMulticastTraffic( main, routeName, True )

def verifyPortDown( main, dpid, port, expectList={ "ipv4": True, "ipv6": True }, hostsToDiscover=[], hostLocations={} ):
    """
    Disable a port and verify traffic
    Reenable the port and verify traffic
    """
    from tests.USECASE.SegmentRouting.dependencies.Testcaselib import Testcaselib as lib
    main.step( "Disable port {}/{}".format( dpid, port ) )
    main.Cluster.active( 0 ).CLI.portstate( dpid=dpid, port=port, state="disable" )
    time.sleep( 10 )
    for routeName in expectList.keys():
        lib.verifyMulticastTraffic( main, routeName, expectList[ routeName ] )
    # Restore the link(s)
    main.Cluster.active( 0 ).CLI.portstate( dpid=dpid, port=port, state="enable" )
    if hostsToDiscover:
        main.Network.discoverHosts( hostList=hostsToDiscover )
    for host, loc in hostLocations.items():
        lib.verifyHostLocation( main, host, loc, retry=5 )
    for routeName in expectList.keys():
        lib.verifyMulticastTraffic( main, routeName, True )

def verifySwitchDown( main, switchName, affectedLinkNum, expectList={ "ipv4": True, "ipv6": True }, hostsToDiscover=[], hostLocations={} ):
    """
    Kill a batch of switches and verify traffic
    Recover the swithces and verify traffic
    """
    from tests.USECASE.SegmentRouting.dependencies.Testcaselib import Testcaselib as lib
    switchName = switchName if isinstance( switchName, list ) else [ switchName ]
    # Kill the switch(es)
    lib.killSwitch( main, switchName, int( main.params[ "TOPO" ][ "switchNum" ] ) - len( switchName ), int( main.params[ "TOPO" ][ "linkNum" ] ) - affectedLinkNum )
    for routeName in expectList.keys():
        lib.verifyMulticastTraffic( main, routeName, expectList[ routeName ] )
    # Recover the switch(es)
    lib.recoverSwitch( main, switchName, int( main.params[ "TOPO" ][ "switchNum" ] ), int( main.params[ "TOPO" ][ "linkNum" ] ), True if hostsToDiscover else False, hostsToDiscover )
    for host, loc in hostLocations.items():
        lib.verifyHostLocation( host, loc, retry=5 )
    for routeName in expectList.keys():
        lib.verifyMulticastTraffic( main, routeName, True )

def verifyOnosDown( main, expectList={ "ipv4": True, "ipv6": True } ):
    """
    Kill and recover ONOS instances Sequencially and check traffic
    """
    from tests.USECASE.SegmentRouting.dependencies.Testcaselib import Testcaselib as lib
    import json
    numCtrls = len( main.Cluster.runningNodes )
    links = len( json.loads( main.Cluster.next().links() ) )
    switches = len( json.loads( main.Cluster.next().devices() ) )
    for ctrl in xrange( numCtrls ):
        # Kill node
        lib.killOnos( main, [ ctrl ], switches, links, ( numCtrls - 1 ) )
        main.Cluster.active(0).CLI.balanceMasters()
        time.sleep( float( main.params[ 'timers' ][ 'balanceMasterSleep' ] ) )
        for routeName in expectList.keys():
            lib.verifyMulticastTraffic( main, routeName, True )
        # Recover node
        lib.recoverOnos( main, [ ctrl ], switches, links, numCtrls )
        main.Cluster.active(0).CLI.balanceMasters()
        time.sleep( float( main.params[ 'timers' ][ 'balanceMasterSleep' ] ) )
        for routeName in expectList.keys():
            lib.verifyMulticastTraffic( main, routeName, True )
