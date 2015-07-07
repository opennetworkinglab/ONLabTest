"""
    Wrapper function for FuncTopo
    Includes onosclidriver and mininetclidriver functions
"""
import time
import json
import re

def __init__( self ):
    self.default = ''

def testTopology( main, topoFile='', args='', mnCmd='', clean=True ):
    """
    Description:
        This function combines different wrapper functions in this module
        to simulate a topology test
    Test Steps:
        - Load topology
        - Discover topology
        - Compare topology
        - pingall
        - Bring links down
        - Compare topology
        - pingall
        - Bring links up
        - Compare topology
        - pingall
    Options:
        clean: Does sudo mn -c to clean mininet residue
        Please read mininetclidriver.py >> startNet( .. ) function for details
    Returns:
        Returns main.TRUE if the test is successful, main.FALSE otherwise
    """
    testTopoResult = main.TRUE
    compareTopoResult = main.TRUE
    topoObjectResult = main.TRUE
    stopResult = main.TRUE

    if clean:
        # Cleans minient
        stopResult = stopMininet( main )

    # Restart ONOS to clear hosts test new mininet topology
    restartONOSResult = restartONOS( main )

    # Starts topology
    startResult = startNewTopology( main, topoFile, args, mnCmd )

    # Gets list of switches in mininet
    assignSwitch( main )

    # This function activates fwd app then does pingall as well as store
    # hosts data in a variable main.hostsData
    getHostsResult = getHostsData( main )

    # Create topology object using sts
    topoObjectResult = createTopoObject( main )

    # Compare Topology
    compareTopoResult = compareTopo( main )

    testTopoResult = startResult and topoObjectResult and \
                     compareTopoResult and getHostsResult


    return testTopoResult

def startNewTopology( main, topoFile='', args='', mnCmd='' ):
    """
    Description:
        This wrapper function starts new topology
    Options:
        Please read mininetclidriver.py >> startNet( .. ) function for details
    Return:
        Returns main.TRUE if topology is successfully created by mininet,
        main.FALSE otherwise
    NOTE:
        Assumes Mininet1 is the name of the handler
    """
    assert main, "There is no main variable"
    assert main.Mininet1, "Mininet 1 is not created"
    result = main.TRUE

    main.log.info( main.topoName + ": Starting new Mininet topology" )

    # log which method is being used
    if topoFile:
        main.log.info( main.topoName + ": Starting topology with " +
                       topoFile + "topology file" )
    elif not topoFile and not mnCmd:
        main.log.info( main.topoName + ": Starting topology using" +
                       " the topo file" )
    elif topoFile and mnCmd:
        main.log.error( main.topoName + ": You can only use one " +
                        "method to start a topology" )
    elif mnCmd:
        main.log.info( main.topoName + ": Starting topology with '" +
                       mnCmd + "' Mininet command" )


    result = main.Mininet1.startNet( topoFile=topoFile,
                                     args=args,
                                     mnCmd=mnCmd )

    return result

def stopMininet( main ):
    """
        Stops current topology and execute mn -c basically triggers
        stopNet in mininetclidrivers

        NOTE: Mininet should be running when issuing this command other wise
        the this function will cause the test to stop
    """
    stopResult = main.TRUE
    stopResult = main.Mininet1.stopNet()
    time.sleep( 30 )
    if not stopResult:
        main.log.info(  main.topoName + ": Did not stop Mininet topology" )
    return stopResult

def createTopoObject( main ):
    """
        Creates topology object using sts module
    """
    from sts.topology.teston_topology import TestONTopology
    global MNTopo
    try:
        ctrls = []
        main.log.info(  main.topoName + ": Creating topology object" +
                        " from mininet" )
        for node in main.nodes:
            temp = ( node, node.name, node.ip_address, 6633 )
            ctrls.append( temp )
        MNTopo = TestONTopology( main.Mininet1, ctrls )
    except Exception:
        objResult = main.FALSE
    else:
        objResult = main.TRUE

    return objResult

def compareTopo( main ):
    """
        Compare topology( devices, links, ports, hosts ) between ONOS and
        mininet using sts
    """
    assert MNTopo, "There is no MNTopo object"
    devices = []
    links = []
    ports = []
    hosts = []
    switchResult = []
    linksResult = []
    portsResult = []
    hostsResult = []
    compareTopoResult = main.TRUE

    for i in range( main.numCtrls ):
        devices.append( json.loads( main.CLIs[ i ].devices() ) )
        links.append( json.loads( main.CLIs[ i ].links() ) )
        ports.append( json.loads(  main.CLIs[ i ].ports() ) )
        hosts.append( json.loads( main.CLIs[ i ].hosts() ) )

    # Comparing switches
    main.log.info( main.topoName + ": Comparing switches in each ONOS nodes" +
                   " with Mininet" )
    for i in range( main.numCtrls ):
        tempResult = main.Mininet1.compareSwitches( MNTopo, devices[ i ] )
        switchResult.append( tempResult )
        if tempResult == main.FALSE:
            main.log.error( main.topoName + ": ONOS-" + str( i + 1 ) +
                            " switch view is incorrect " )

    if all( result == main.TRUE for result in switchResult ):
        main.log.info( main.topoName + ": Switch view in all ONOS nodes "+
                       "are correct " )
    else:
        compareTopoResult = main.FALSE

    # Comparing ports
    main.log.info( main.topoName + ": Comparing ports in each ONOS nodes" +
                   " with Mininet" )
    for i in range( main.numCtrls ):
        tempResult = main.Mininet1.comparePorts( MNTopo, ports[ i ] )
        portsResult.append( tempResult )
        if tempResult == main.FALSE:
            main.log.error( main.topoName + ": ONOS-" + str( i + 1 ) +
                            " ports view are incorrect " )

    if all( result == main.TRUE for result in portsResult ):
        main.log.info( main.topoName + ": Ports view in all ONOS nodes "+
                       "are correct " )
    else:
        compareTopoResult = main.FALSE

    # Comparing links
    main.log.info( main.topoName + ": Comparing links in each ONOS nodes" +
                   " with Mininet" )
    for i in range( main.numCtrls ):
        tempResult = main.Mininet1.compareLinks( MNTopo, links[ i ] )
        linksResult.append( tempResult )
        if tempResult == main.FALSE:
            main.log.error( main.topoName + ": ONOS-" + str( i + 1 ) +
                            " links view are incorrect " )

    if all( result == main.TRUE for result in linksResult ):
        main.log.info( main.topoName + ": Links view in all ONOS nodes "+
                       "are correct " )
    else:
        compareTopoResult = main.FALSE

    # Comparing hosts
    main.log.info( main.topoName + ": Comparing hosts in each ONOS nodes" +
                   " with Mininet" )
    for i in range( main.numCtrls ):
        tempResult = main.Mininet1.compareHosts( MNTopo, hosts[ i ] )
        hostsResult.append( tempResult )
        if tempResult == main.FALSE:
            main.log.error( main.topoName + ": ONOS-" + str( i + 1 ) +
                            " hosts view are incorrect " )

    if all( result == main.TRUE for result in hostsResult ):
        main.log.info( main.topoName + ": Hosts view in all ONOS nodes "+
                       "are correct " )
    else:
        compareTopoResult = main.FALSE

    return compareTopoResult

def assignSwitch( main ):
    """
        Returns switch list using getSwitch in Mininet driver
    """
    switchList = []
    assignResult = main.TRUE
    switchList =  main.Mininet1.getSwitch()
    assignResult = main.Mininet1.assignSwController( sw=switchList,
                                                     ip=main.ONOSip[ 0 ],
                                                     port=6633 )

    for sw in switchList:
        response = main.Mininet1.getSwController( sw )
        if re.search( "tcp:" + main.ONOSip[ 0 ], response ):
            assignResult = assignResult and main.TRUE
        else:
            assignResult = main.FALSE

    return switchList

def getHostsData( main ):
    """
        Use fwd app and pingall to discover all the hosts
    """
    activateResult = main.TRUE
    appCheck = main.TRUE
    getDataResult = main.TRUE
    main.log.info( main.topoName + ": Activating reactive forwarding app " )
    activateResult = main.CLIs[ 0 ].activateApp( "org.onosproject.fwd" )
    if main.hostsData:
        main.hostsData = {}
    for i in range( main.numCtrls ):
        appCheck = appCheck and main.CLIs[ i ].appToIDCheck()
        if appCheck != main.TRUE:
            main.log.warn( main.CLIs[ i ].apps() )
            main.log.warn( main.CLIs[ i ].appIDs() )

    pingResult = main.Mininet1.pingall( timeout=900 )
    hostsJson = json.loads( main.CLIs[ 0 ].hosts() )
    hosts = main.Mininet1.getHosts()
    for host in hosts:
        main.hostsData[ host ] = {}
        main.hostsData[ host ][ 'mac' ] =  \
            main.Mininet1.getMacAddress( host ).upper()
        for hostj in hostsJson:
            if main.hostsData[ host ][ 'mac' ] == hostj[ 'mac' ]:
                main.hostsData[ host ][ 'id' ] = hostj[ 'id' ]
                main.hostsData[ host ][ 'vlan' ] = hostj[ 'vlan' ]
                main.hostsData[ host ][ 'location' ] = \
                            hostj[ 'location' ][ 'elementId' ] + '/' + \
                            hostj[ 'location' ][ 'port' ]
                main.hostsData[ host ][ 'ipAddresses' ] = hostj[ 'ipAddresses' ]

    if activateResult and main.hostsData:
        main.log.info( main.topoName + ": Successfully used fwd app" +
                       " to discover hosts " )
        getDataResult = main.TRUE
    else:
        main.log.info( main.topoName + ": Failed to use fwd app" +
                       " to discover hosts " )
        getDataResult = main.FALSE

    # This data can be use later for intents
    print main.hostsData

    return getDataResult

def restartONOS( main ):
    """
    Description:
        Stop and start ONOS that clears hosts,devices etc. in order to test
        new mininet topology
    Return:
        Retruns main.TRUE for a successful restart, main.FALSE otherwise.
    """
    stopResult = []
    startResult = []
    restartResult = main.TRUE

    main.log.info( main.topoName + ": Stopping ONOS cluster" )
    for node in main.nodes:
        startResult.append( main.ONOSbench.onosStop( nodeIp=node.ip_address ) )

    if all( result == main.TRUE for result in stopResult ):
        main.log.info( main.topoName + ": Successfully stopped ONOS cluster" )
    else:
        restartResult = main.FALSE
        main.log.error( main.topoName + ": Failed to stop ONOS cluster" )

    time.sleep( 25 )

    main.log.info( main.topoName + ": Starting ONOS cluster" )
    for node in main.nodes:
        startResult.append( main.ONOSbench.onosStart( nodeIp=node.ip_address ) )

    if all( result == main.TRUE for result in startResult ):
        main.log.info( main.topoName + ": Successfully start ONOS cluster" )
    else:
        restartResult = main.FALSE
        main.log.error( main.topoName + ": Failed to start ONOS cluster" )

    # Start ONOS CLIs again
    main.log.info( main.topoName + ": Starting ONOS CLI" )
    cliResult = main.TRUE
    for i in range( main.numCtrls ):
        cliResult = cliResult and \
                    main.CLIs[ i ].startOnosCli( main.ONOSip[ i ] )

    time.sleep( 15 )

    return restartResult



