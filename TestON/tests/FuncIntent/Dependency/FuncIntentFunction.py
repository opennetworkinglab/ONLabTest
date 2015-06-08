"""
    Wrapper functions for FuncIntent
    This functions include Onosclidriver and Mininetclidriver driver functions
    Author: kelvin@onlab.us
"""
def __init__( self ):
    self.default = ''

def hostIntent( main,
                name,
                host1,
                host2,
                onosNode=0,
                host1Id="",
                host2Id="",
                mac1="",
                mac2="",
                vlan1="-1",
                vlan2="-1",
                sw1="",
                sw2="",
                expectedLink=0 ):
    """
        Description:
            Verify add-host-intent
        Steps:
            - Discover hosts
            - Add host intents
            - Check intents
            - Verify flows
            - Ping hosts
            - Reroute
                - Link down
                - Verify flows
                - Check topology
                - Ping hosts
                - Link up
                - Verify flows
                - Check topology
                - Ping hosts
            - Remove intents
        Required:
            name - Type of host intent to add eg. IPV4 | VLAN | Dualstack
            host1 - Name of first host
            host2 - Name of second host
        Optional:
            host1Id - ONOS id of the first host eg. 00:00:00:00:00:01/-1
            host2Id - ONOS id of the second host
            mac1 - Mac address of first host
            mac2 - Mac address of the second host
            vlan1 - Vlan tag of first host, defaults to -1
            vlan2 - Vlan tag of second host, defaults to -1
            sw1 - First switch to bring down & up for rerouting purpose
            sw2 - Second switch to bring down & up for rerouting purpose
            expectedLink - Expected link when the switches are down, it should
                           be two links lower than the links before the two
                           switches are down
    """
    import time

    # Assert variables
    assert main, "There is no main variable"
    assert name, "variable name is empty"
    assert host1 and host2, "You must specify hosts"

    global itemName
    itemName = name
    h1Id = host1Id
    h2Id = host2Id
    h1Mac = mac1
    h2Mac = mac2
    vlan1 = vlan1
    vlan2 = vlan2
    hostNames = [ host1 , host2 ]
    intentsId = []
    stepResult = main.TRUE
    pingResult = main.TRUE
    intentResult = main.TRUE
    removeIntentResult = main.TRUE
    flowResult = main.TRUE
    topoResult = main.TRUE
    linkDownResult = main.TRUE
    linkUpResult = main.TRUE
    onosNode = int( onosNode )

    if main.hostsData:
        if not h1Mac:
            h1Mac = main.hostsData[ host1 ][ 'mac' ]
        if not h2Mac:
            h2Mac = main.hostsData[ host2 ][ 'mac' ]
        if main.hostsData[ host1 ][ 'vlan' ] != '-1':
            vlan1 = main.hostsData[ host1 ][ 'vlan' ]
        if main.hostsData[ host2 ][ 'vlan' ] != '-1':
            vlan2 = main.hostsData[ host2 ][ 'vlan' ]
        if not h1Id:
            h1Id = main.hostsData[ host1 ][ 'id' ]
        if not h2Id:
            h2Id = main.hostsData[ host2 ][ 'id' ]

    assert h1Id and h2Id, "You must specify host IDs"
    if not ( h1Id and h2Id ):
        main.log.info( "There are no host IDs" )
        return main.FALSE

    # Discover hosts using arping
    if not main.hostsData:
        main.log.info( itemName + ": Discover host using arping" )
        main.Mininet1.arping( host=host1 )
        main.Mininet1.arping( host=host2 )
        host1 = main.CLIs[ 0 ].getHost( mac=h1Mac )
        host2 = main.CLIs[ 0 ].getHost( mac=h2Mac )

    # Check flows count in each node
    checkFlowsCount( main )

    # Checking connectivity before installing intents
    main.log.info( itemName + ": Check hosts connection before adding intents" )
    checkPing = pingallHosts( main, hostNames )
    if not checkPing:
        main.log.info( itemName + ": Ping did not go through " +
                       "before adding intents" )
    else:
        main.log.debug( itemName + ": Pinged successful before adding " +
                        "intents,please check fwd app if it is activated" )

    # Adding host intents
    main.log.info( itemName + ": Adding host intents" )
    intent1 = main.CLIs[ onosNode ].addHostIntent( hostIdOne=h1Id,
                                           hostIdTwo=h2Id )
    intentsId.append( intent1 )
    time.sleep( 5 )

    # Check intents state
    time.sleep( 30 )
    intentResult = checkIntentState( main, intentsId )
    checkFlowsCount( main )

    # Check intents state again if first check fails...
    if not intentResult:
        intentResult = checkIntentState( main, intentsId )

    # Check flows count in each node
    checkFlowsCount( main )
    # Verify flows
    checkFlowsState( main )

    # Ping hosts
    firstPingResult = pingallHosts( main, hostNames )
    if not firstPingResult:
        main.log.debug( "First ping failed, there must be" +
                       " something wrong with ONOS performance" )

    # Ping hosts again...
    pingResult = pingResult and pingallHosts( main, hostNames )
    time.sleep( 5 )

    # Test rerouting if these variables exist
    if sw1 and sw2 and expectedLink:
        # link down
        linkDownResult = link( main, sw1, sw2, "down" )
        intentResult = intentResult and checkIntentState( main, intentsId )

        # Check flows count in each node
        checkFlowsCount( main )
        # Verify flows
        checkFlowsState( main )

        # Check OnosTopology
        topoResult = checkTopology( main, expectedLink )

        # Ping hosts
        pingResult = pingResult and pingallHosts( main, hostNames )

        intentResult = checkIntentState( main, intentsId )

        # Checks ONOS state in link down
        if linkDownResult and topoResult and pingResult and intentResult:
            main.log.info( itemName + ": Successfully brought link down" )
        else:
            main.log.error( itemName + ": Failed to bring link down" )

        # link up
        linkUpResult = link( main, sw1, sw2, "up" )
        time.sleep( 5 )

        # Check flows count in each node
        checkFlowsCount( main )
        # Verify flows
        checkFlowsState( main )

        # Check OnosTopology
        topoResult = checkTopology( main, main.numLinks )

        # Ping hosts
        pingResult = pingResult and pingallHosts( main, hostNames )

        intentResult = checkIntentState( main, intentsId )

        # Checks ONOS state in link up
        if linkUpResult and topoResult and pingResult and intentResult:
            main.log.info( itemName + ": Successfully brought link back up" )
        else:
            main.log.error( itemName + ": Failed to bring link back up" )

    # Remove all intents
    removeIntentResult = removeAllIntents( main, intentsId )

    stepResult = pingResult and linkDownResult and linkUpResult \
                 and intentResult and removeIntentResult

    return stepResult

def pointIntent( main,
                 name,
                 host1,
                 host2,
                 onosNode=0,
                 deviceId1="",
                 deviceId2="",
                 port1="",
                 port2="",
                 ethType="",
                 mac1="",
                 mac2="",
                 bandwidth="",
                 lambdaAlloc=False,
                 ipProto="",
                 ip1="",
                 ip2="",
                 tcp1="",
                 tcp2="",
                 sw1="",
                 sw2="",
                 expectedLink=0 ):

    """
        Description:
            Verify add-point-intent
        Steps:
            - Get device ids | ports
            - Add point intents
            - Check intents
            - Verify flows
            - Ping hosts
            - Reroute
                - Link down
                - Verify flows
                - Check topology
                - Ping hosts
                - Link up
                - Verify flows
                - Check topology
                - Ping hosts
            - Remove intents
        Required:
            name - Type of point intent to add eg. IPV4 | VLAN | Dualstack
            host1 - Name of first host
            host2 - Name of second host
        Optional:
            deviceId1 - ONOS device id of the first switch, the same as the
                        location of the first host eg. of:0000000000000001/1,
                        located at device 1 port 1
            deviceId2 - ONOS device id of the second switch
            port1 - The port number where the first host is attached
            port2 - The port number where the second host is attached
            ethType - Ethernet type eg. IPV4, IPV6
            mac1 - Mac address of first host
            mac2 - Mac address of the second host
            bandwidth - Bandwidth capacity
            lambdaAlloc - Allocate lambda, defaults to False
            ipProto - IP protocol
            ip1 - IP address of first host
            ip2 - IP address of second host
            tcp1 - TCP port of first host
            tcp2 - TCP port of second host
            sw1 - First switch to bring down & up for rerouting purpose
            sw2 - Second switch to bring down & up for rerouting purpose
            expectedLink - Expected link when the switches are down, it should
                           be two links lower than the links before the two
                           switches are down
    """

    import time
    assert main, "There is no main variable"
    assert name, "variable name is empty"
    assert host1 and host2, "You must specify hosts"

    global itemName
    itemName = name
    host1 = host1
    host2 = host2
    hostNames = [ host1, host2 ]
    intentsId = []

    pingResult = main.TRUE
    intentResult = main.TRUE
    removeIntentResult = main.TRUE
    flowResult = main.TRUE
    topoResult = main.TRUE
    linkDownResult = main.TRUE
    linkUpResult = main.TRUE
    onosNode = int( onosNode )

    # Checking connectivity before installing intents
    main.log.info( itemName + ": Check hosts connection before adding intents" )
    checkPing = pingallHosts( main, hostNames )
    if not checkPing:
        main.log.info( itemName + ": Ping did not go through " +
                       "before adding intents" )
    else:
        main.log.debug( itemName + ": Pinged successful before adding " +
                        "intents,please check fwd app if it is activated" )

    # Adding bidirectional point  intents
    main.log.info( itemName + ": Adding point intents" )
    intent1 = main.CLIs[ onosNode ].addPointIntent( ingressDevice=deviceId1,
                                             egressDevice=deviceId2,
                                             portIngress=port1,
                                             portEgress=port2,
                                             ethType=ethType,
                                             ethSrc=mac1,
                                             ethDst=mac2,
                                             bandwidth=bandwidth,
                                             lambdaAlloc=lambdaAlloc,
                                             ipProto=ipProto,
                                             ipSrc=ip1,
                                             ipDst=ip2,
                                             tcpSrc=tcp1,
                                             tcpDst=tcp2 )

    intentsId.append( intent1 )
    time.sleep( 5 )
    intent2 = main.CLIs[ onosNode ].addPointIntent( ingressDevice=deviceId2,
                                             egressDevice=deviceId1,
                                             portIngress=port2,
                                             portEgress=port1,
                                             ethType=ethType,
                                             ethSrc=mac2,
                                             ethDst=mac1,
                                             bandwidth=bandwidth,
                                             lambdaAlloc=lambdaAlloc,
                                             ipProto=ipProto,
                                             ipSrc=ip2,
                                             ipDst=ip1,
                                             tcpSrc=tcp2,
                                             tcpDst=tcp1 )
    intentsId.append( intent2 )

    # Check intents state
    time.sleep( 30 )
    intentResult = checkIntentState( main, intentsId )
    # Check flows count in each node
    checkFlowsCount( main )

    # Check intents state again if first check fails...
    if not intentResult:
        intentResult = checkIntentState( main, intentsId )

    # Check flows count in each node
    checkFlowsCount( main )
    # Verify flows
    checkFlowsState( main )

    # Ping hosts
    firstPingResult = pingallHosts( main, hostNames )
    if not firstPingResult:
        main.log.debug( "First ping failed, there must be" +
                       " something wrong with ONOS performance" )

    # Ping hosts again...
    pingResult = pingResult and pingallHosts( main, hostNames )
    time.sleep( 5 )

    # Test rerouting if these variables exist
    if sw1 and sw2 and expectedLink:
        # link down
        linkDownResult = link( main, sw1, sw2, "down" )
        intentResult = intentResult and checkIntentState( main, intentsId )

        # Check flows count in each node
        checkFlowsCount( main )
        # Verify flows
        checkFlowsState( main )

        # Check OnosTopology
        topoResult = checkTopology( main, expectedLink )

        # Ping hosts
        pingResult = pingResult and pingallHosts( main, hostNames )

        intentResult = checkIntentState( main, intentsId )

        # Checks ONOS state in link down
        if linkDownResult and topoResult and pingResult and intentResult:
            main.log.info( itemName + ": Successfully brought link down" )
        else:
            main.log.error( itemName + ": Failed to bring link down" )

        # link up
        linkUpResult = link( main, sw1, sw2, "up" )
        time.sleep( 5 )

        # Check flows count in each node
        checkFlowsCount( main )
        # Verify flows
        checkFlowsState( main )

        # Check OnosTopology
        topoResult = checkTopology( main, main.numLinks )

        # Ping hosts
        pingResult = pingResult and pingallHosts( main, hostNames )

        intentResult = checkIntentState( main, intentsId )

        # Checks ONOS state in link up
        if linkUpResult and topoResult and pingResult and intentResult:
            main.log.info( itemName + ": Successfully brought link back up" )
        else:
            main.log.error( itemName + ": Failed to bring link back up" )

    # Remove all intents
    removeIntentResult = removeAllIntents( main, intentsId )

    stepResult = pingResult and linkDownResult and linkUpResult \
                 and intentResult and removeIntentResult

    return stepResult

def singleToMultiIntent( main,
                         name,
                         hostNames,
                         onosNode=0,
                         devices="",
                         ports=None,
                         ethType="",
                         macs=None,
                         bandwidth="",
                         lambdaAlloc=False,
                         ipProto="",
                         ipAddresses="",
                         tcp="",
                         sw1="",
                         sw2="",
                         expectedLink=0 ):
    """
        Verify Single to Multi Point intents
        NOTE:If main.hostsData is not defined, variables data should be passed in the
        same order index wise. All devices in the list should have the same
        format, either all the devices have its port or it doesn't.
        eg. hostName = [ 'h1', 'h2' ,..  ]
            devices = [ 'of:0000000000000001', 'of:0000000000000002', ...]
            ports = [ '1', '1', ..]
            ...
        Description:
            Verify add-single-to-multi-intent iterates through the list of given
            host | devices and add intents
        Steps:
            - Get device ids | ports
            - Add single to multi point intents
            - Check intents
            - Verify flows
            - Ping hosts
            - Reroute
                - Link down
                - Verify flows
                - Check topology
                - Ping hosts
                - Link up
                - Verify flows
                - Check topology
                - Ping hosts
            - Remove intents
        Required:
            name - Type of point intent to add eg. IPV4 | VLAN | Dualstack
            hostNames - List of host names
        Optional:
            devices - List of device ids in the same order as the hosts
                      in hostNames
            ports - List of port numbers in the same order as the device in
                    devices
            ethType - Ethernet type eg. IPV4, IPV6
            macs - List of hosts mac address in the same order as the hosts in
                   hostNames
            bandwidth - Bandwidth capacity
            lambdaAlloc - Allocate lambda, defaults to False
            ipProto - IP protocol
            ipAddresses - IP addresses of host in the same order as the hosts in
                          hostNames
            tcp - TCP ports in the same order as the hosts in hostNames
            sw1 - First switch to bring down & up for rerouting purpose
            sw2 - Second switch to bring down & up for rerouting purpose
            expectedLink - Expected link when the switches are down, it should
                           be two links lower than the links before the two
                           switches are down
    """

    import time
    import copy
    assert main, "There is no main variable"
    assert hostNames, "You must specify hosts"
    assert devices or main.hostsData, "You must specify devices"

    global itemName
    itemName = name
    tempHostsData = {}
    intentsId = []
    onosNode = int( onosNode )

    macsDict = {}
    ipDict = {}
    if hostNames and devices:
        if len( hostNames ) != len( devices ):
            main.log.debug( "hosts and devices does not have the same length" )
            #print "len hostNames = ", len( hostNames )
            #print "len devices = ", len( devices )
            return main.FALSE
        if ports:
            if len( ports ) != len( devices ):
                main.log.error( "Ports and devices does " +
                                "not have the same length" )
                #print "len devices = ", len( devices )
                #print "len ports = ", len( ports )
                return main.FALSE
        else:
            main.log.info( "Device Ports are not specified" )
        if macs:
            for i in range( len( devices ) ):
                macsDict[ devices[ i ] ] = macs[ i ]

    elif hostNames and not devices and main.hostsData:
        devices = []
        main.log.info( "singleToMultiIntent function is using main.hostsData" ) 
        for host in hostNames:
               devices.append( main.hostsData.get( host ).get( 'location' ) )
               macsDict[ main.hostsData.get( host ).get( 'location' ) ] = \
                           main.hostsData.get( host ).get( 'mac' )
               ipDict[ main.hostsData.get( host ).get( 'location' ) ] = \
                           main.hostsData.get( host ).get( 'ipAddresses' )
        #print main.hostsData

    #print 'host names = ', hostNames
    #print 'devices = ', devices
    #print "macsDict = ", macsDict

    pingResult = main.TRUE
    intentResult = main.TRUE
    removeIntentResult = main.TRUE
    flowResult = main.TRUE
    topoResult = main.TRUE
    linkDownResult = main.TRUE
    linkUpResult = main.TRUE

    devicesCopy = copy.copy( devices )
    if ports:
        portsCopy = copy.copy( ports )
    main.log.info( itemName + ": Adding single point to multi point intents" )

    # Check flows count in each node
    checkFlowsCount( main )

    # Checking connectivity before installing intents
    main.log.info( itemName + ": Check hosts connection before adding intents" )
    checkPing = pingallHosts( main, hostNames )
    if not checkPing:
        main.log.info( itemName + ": Ping did not go through " +
                       "before adding intents" )
    else:
        main.log.debug( itemName + ": Pinged successful before adding " +
                        "intents,please check fwd app if it is activated" )

    # Adding bidirectional point  intents
    for i in range( len( devices ) ):
        ingressDevice = devicesCopy[ i ]
        egressDeviceList = copy.copy( devicesCopy )
        egressDeviceList.remove( ingressDevice )
        if ports:
            portIngress = portsCopy[ i ]
            portEgressList = copy.copy( portsCopy )
            del portEgressList[ i ]
        else:
            portIngress = ""
            portEgressList = None
        if not macsDict:
            srcMac = ""
        else:
            srcMac = macsDict[ ingressDevice ]
            if srcMac == None:
                main.log.debug( "There is no MAC in device - " + ingressDevice )
                srcMac = ""

        intentsId.append(
                        main.CLIs[ onosNode ].addSinglepointToMultipointIntent(
                                            ingressDevice=ingressDevice,
                                            egressDeviceList=egressDeviceList,
                                            portIngress=portIngress,
                                            portEgressList=portEgressList,
                                            ethType=ethType,
                                            ethSrc=srcMac,
                                            bandwidth=bandwidth,
                                            lambdaAlloc=lambdaAlloc,
                                            ipProto=ipProto,
                                            ipSrc="",
                                            ipDst="",
                                            tcpSrc="",
                                            tcpDst="" ) )

    # Wait some time for the flow to go through when using multi instance
    time.sleep( 10 )
    pingResult = pingallHosts( main, hostNames )

    # Check intents state
    time.sleep( 30 )
    intentResult = checkIntentState( main, intentsId )

    # Check intents state again if first check fails...
    if not intentResult:
        intentResult = checkIntentState( main, intentsId )

    # Check flows count in each node
    checkFlowsCount( main )
    # Verify flows
    checkFlowsState( main )

    # Ping hosts
    pingResult = pingResult and pingallHosts( main, hostNames )
    # Ping hosts again...
    pingResult = pingResult and pingallHosts( main, hostNames )
    time.sleep( 5 )

    # Test rerouting if these variables exist
    if sw1 and sw2 and expectedLink:
        # link down
        linkDownResult = link( main, sw1, sw2, "down" )
        intentResult = intentResult and checkIntentState( main, intentsId )

        # Check flows count in each node
        checkFlowsCount( main )
        # Verify flows
        checkFlowsState( main )

        # Check OnosTopology
        topoResult = checkTopology( main, expectedLink )

        # Ping hosts
        pingResult = pingResult and pingallHosts( main, hostNames )

        intentResult = checkIntentState( main, intentsId )

        # Checks ONOS state in link down
        if linkDownResult and topoResult and pingResult and intentResult:
            main.log.info( itemName + ": Successfully brought link down" )
        else:
            main.log.error( itemName + ": Failed to bring link down" )

        # link up
        linkUpResult = link( main, sw1, sw2, "up" )
        time.sleep( 5 )

        # Check flows count in each node
        checkFlowsCount( main )
        # Verify flows
        checkFlowsState( main )

        # Check OnosTopology
        topoResult = checkTopology( main, main.numLinks )

        # Ping hosts
        pingResult = pingResult and pingallHosts( main, hostNames )

        intentResult = checkIntentState( main, intentsId )

        # Checks ONOS state in link up
        if linkUpResult and topoResult and pingResult and intentResult:
            main.log.info( itemName + ": Successfully brought link back up" )
        else:
            main.log.error( itemName + ": Failed to bring link back up" )

    # Remove all intents
    removeIntentResult = removeAllIntents( main, intentsId )

    stepResult = pingResult and linkDownResult and linkUpResult \
                 and intentResult and removeIntentResult

    return stepResult

def multiToSingleIntent( main,
                         name,
                         hostNames,
                         onosNode=0,
                         devices="",
                         ports=None,
                         ethType="",
                         macs=None,
                         bandwidth="",
                         lambdaAlloc=False,
                         ipProto="",
                         ipAddresses="",
                         tcp="",
                         sw1="",
                         sw2="",
                         expectedLink=0 ):
    """
        Verify Single to Multi Point intents
        NOTE:If main.hostsData is not defined, variables data should be passed in the
        same order index wise. All devices in the list should have the same
        format, either all the devices have its port or it doesn't.
        eg. hostName = [ 'h1', 'h2' ,..  ]
            devices = [ 'of:0000000000000001', 'of:0000000000000002', ...]
            ports = [ '1', '1', ..]
            ...
        Description:
            Verify add-multi-to-single-intent
        Steps:
            - Get device ids | ports
            - Add multi to single point intents
            - Check intents
            - Verify flows
            - Ping hosts
            - Reroute
                - Link down
                - Verify flows
                - Check topology
                - Ping hosts
                - Link up
                - Verify flows
                - Check topology
                - Ping hosts
            - Remove intents
        Required:
            name - Type of point intent to add eg. IPV4 | VLAN | Dualstack
            hostNames - List of host names
        Optional:
            devices - List of device ids in the same order as the hosts
                      in hostNames
            ports - List of port numbers in the same order as the device in
                    devices
            ethType - Ethernet type eg. IPV4, IPV6
            macs - List of hosts mac address in the same order as the hosts in
                   hostNames
            bandwidth - Bandwidth capacity
            lambdaAlloc - Allocate lambda, defaults to False
            ipProto - IP protocol
            ipAddresses - IP addresses of host in the same order as the hosts in
                          hostNames
            tcp - TCP ports in the same order as the hosts in hostNames
            sw1 - First switch to bring down & up for rerouting purpose
            sw2 - Second switch to bring down & up for rerouting purpose
            expectedLink - Expected link when the switches are down, it should
                           be two links lower than the links before the two
                           switches are down
    """

    import time
    import copy
    assert main, "There is no main variable"
    assert hostNames, "You must specify hosts"
    assert devices or main.hostsData, "You must specify devices"

    global itemName
    itemName = name
    tempHostsData = {}
    intentsId = []
    onosNode = int( onosNode )

    macsDict = {}
    ipDict = {}
    if hostNames and devices:
        if len( hostNames ) != len( devices ):
            main.log.debug( "hosts and devices does not have the same length" )
            #print "len hostNames = ", len( hostNames )
            #print "len devices = ", len( devices )
            return main.FALSE
        if ports:
            if len( ports ) != len( devices ):
                main.log.error( "Ports and devices does " +
                                "not have the same length" )
                #print "len devices = ", len( devices )
                #print "len ports = ", len( ports )
                return main.FALSE
        else:
            main.log.info( "Device Ports are not specified" )
        if macs:
            for i in range( len( devices ) ):
                macsDict[ devices[ i ] ] = macs[ i ]
    elif hostNames and not devices and main.hostsData:
        devices = []
        main.log.info( "multiToSingleIntent function is using main.hostsData" ) 
        for host in hostNames:
               devices.append( main.hostsData.get( host ).get( 'location' ) )
               macsDict[ main.hostsData.get( host ).get( 'location' ) ] = \
                           main.hostsData.get( host ).get( 'mac' )
               ipDict[ main.hostsData.get( host ).get( 'location' ) ] = \
                           main.hostsData.get( host ).get( 'ipAddresses' )
        #print main.hostsData

    #print 'host names = ', hostNames
    #print 'devices = ', devices
    #print "macsDict = ", macsDict

    pingResult = main.TRUE
    intentResult = main.TRUE
    removeIntentResult = main.TRUE
    flowResult = main.TRUE
    topoResult = main.TRUE
    linkDownResult = main.TRUE
    linkUpResult = main.TRUE

    devicesCopy = copy.copy( devices )
    if ports:
        portsCopy = copy.copy( ports )
    main.log.info( itemName + ": Adding multi point to single point intents" )

    # Check flows count in each node
    checkFlowsCount( main )

    # Checking connectivity before installing intents
    main.log.info( itemName + ": Check hosts connection before adding intents" )
    checkPing = pingallHosts( main, hostNames )
    if not checkPing:
        main.log.info( itemName + ": Ping did not go through " +
                       "before adding intents" )
    else:
        main.log.debug( itemName + ": Pinged successful before adding " +
                        "intents,please check fwd app if it is activated" )

    # Adding bidirectional point  intents
    for i in range( len( devices ) ):
        egressDevice = devicesCopy[ i ]
        ingressDeviceList = copy.copy( devicesCopy )
        ingressDeviceList.remove( egressDevice )
        if ports:
            portEgress = portsCopy[ i ]
            portIngressList = copy.copy( portsCopy )
            del portIngressList[ i ]
        else:
            portEgress = ""
            portIngressList = None
        if not macsDict:
            dstMac = ""
        else:
            dstMac = macsDict[ egressDevice ]
            if dstMac == None:
                main.log.debug( "There is no MAC in device - " + egressDevice )
                dstMac = ""

        intentsId.append(
                        main.CLIs[ onosNode ].addMultipointToSinglepointIntent(
                                            ingressDeviceList=ingressDeviceList,
                                            egressDevice=egressDevice,
                                            portIngressList=portIngressList,
                                            portEgress=portEgress,
                                            ethType=ethType,
                                            ethDst=dstMac,
                                            bandwidth=bandwidth,
                                            lambdaAlloc=lambdaAlloc,
                                            ipProto=ipProto,
                                            ipSrc="",
                                            ipDst="",
                                            tcpSrc="",
                                            tcpDst="" ) )

    pingResult = pingallHosts( main, hostNames )

    # Check intents state
    time.sleep( 30 )
    intentResult = checkIntentState( main, intentsId )

    # Check intents state again if first check fails...
    if not intentResult:
        intentResult = checkIntentState( main, intentsId )

    # Check flows count in each node
    checkFlowsCount( main )
    # Verify flows
    checkFlowsState( main )

    # Ping hosts
    pingResult = pingResult and pingallHosts( main, hostNames )
    # Ping hosts again...
    pingResult = pingResult and pingallHosts( main, hostNames )
    time.sleep( 5 )

    # Test rerouting if these variables exist
    if sw1 and sw2 and expectedLink:
        # link down
        linkDownResult = link( main, sw1, sw2, "down" )
        intentResult = intentResult and checkIntentState( main, intentsId )

        # Check flows count in each node
        checkFlowsCount( main )
        # Verify flows
        checkFlowsState( main )

        # Check OnosTopology
        topoResult = checkTopology( main, expectedLink )

        # Ping hosts
        pingResult = pingResult and pingallHosts( main, hostNames )

        intentResult = checkIntentState( main, intentsId )

        # Checks ONOS state in link down
        if linkDownResult and topoResult and pingResult and intentResult:
            main.log.info( itemName + ": Successfully brought link down" )
        else:
            main.log.error( itemName + ": Failed to bring link down" )

        # link up
        linkUpResult = link( main, sw1, sw2, "up" )
        time.sleep( 5 )

        # Check flows count in each node
        checkFlowsCount( main )
        # Verify flows
        checkFlowsState( main )

        # Check OnosTopology
        topoResult = checkTopology( main, main.numLinks )

        # Ping hosts
        pingResult = pingResult and pingallHosts( main, hostNames )

        intentResult = checkIntentState( main, intentsId )

        # Checks ONOS state in link up
        if linkUpResult and topoResult and pingResult and intentResult:
            main.log.info( itemName + ": Successfully brought link back up" )
        else:
            main.log.error( itemName + ": Failed to bring link back up" )

    # Remove all intents
    removeIntentResult = removeAllIntents( main, intentsId )

    stepResult = pingResult and linkDownResult and linkUpResult \
                 and intentResult and removeIntentResult

    return stepResult

def pingallHosts( main, hostList, pingType="ipv4" ):
    # Ping all host in the hosts list variable
    print "Pinging : ", hostList
    pingResult = main.TRUE
    pingResult = main.Mininet1.pingallHosts( hostList, pingType )
    return pingResult

def getHostsData( main ):
    """
        Use fwd app and pingall to discover all the hosts
    """
    import json
    activateResult = main.TRUE
    appCheck = main.TRUE
    getDataResult = main.TRUE
    main.log.info( "Activating reactive forwarding app " )
    activateResult = main.CLIs[ 0 ].activateApp( "org.onosproject.fwd" )

    for i in range( main.numCtrls ):
        appCheck = appCheck and main.CLIs[ i ].appToIDCheck()
        if appCheck != main.TRUE:
            main.log.warn( main.CLIs[ i ].apps() )
            main.log.warn( main.CLIs[ i ].appIDs() )

    pingResult = main.Mininet1.pingall()
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

    main.log.info( "Deactivating reactive forwarding app " )
    deactivateResult = main.CLIs[ 0 ].deactivateApp( "org.onosproject.fwd" )
    if activateResult and deactivateResult and main.hostsData:
        main.log.info( "Successfully used fwd app to discover hosts " )
        getDataResult = main.TRUE
    else:
        main.log.info( "Failed to use fwd app to discover hosts " )
        getDataResult = main.FALSE

    print main.hostsData

    return getDataResult

def checkTopology( main, expectedLink ):
    statusResult = main.TRUE
    # Check onos topology
    main.log.info( itemName + ": Checking ONOS topology " )

    for i in range( main.numCtrls ):
        topologyResult = main.CLIs[ i ].topology()
        statusResult = main.ONOSbench.checkStatus( topologyResult,
                                                   main.numSwitch,
                                                   expectedLink )\
                       and statusResult
    if not statusResult:
        main.log.error( itemName + ": Topology mismatch" )
    else:
        main.log.info( itemName + ": Topology match" )
    return statusResult

def checkIntentState( main, intentsId ):

    intentResult = main.TRUE
    results = []

    main.log.info( itemName + ": Checking intents state" )
    for i in range( main.numCtrls ):
        intentResult = main.CLIs[ i ].checkIntentState( intentsId=intentsId )
        results.append( intentResult )

    if all( result == main.TRUE for result in results ):
        main.log.info( itemName + ": Intents are installed correctly" )
    else:
        main.log.error( itemName + ": Intents are NOT installed correctly" )

    return intentResult

def checkFlowsState( main ):

    main.log.info( itemName + ": Check flows state" )
    checkFlowsResult = main.CLIs[ 0 ].checkFlowsState()
    return checkFlowsResult

def link( main, sw1, sw2, option):

    # link down
    main.log.info( itemName + ": Bring link " + option + "between " +
                       sw1 + " and " + sw2 )
    linkResult = main.Mininet1.link( end1=sw1, end2=sw2, option=option )
    return linkResult

def removeAllIntents( main, intentsId ):
    """
        Remove all intents in the intentsId
    """
    import time
    intentsRemaining = []
    removeIntentResult = main.TRUE
    # Remove intents
    for intent in intentsId:
        main.CLIs[ 0 ].removeIntent( intentId=intent, purge=True )

    time.sleep( 5 )
    # Checks if there is remaining intents using intents()
    intentsRemaining = main.CLIs[ 0 ].intents( jsonFormat=False )
    # If there is remianing intents then remove intents should fail

    if intentsRemaining:
        main.log.info( itemName + ": There are " +
                       str( len( intentsRemaining ) ) + " intents remaining, "
                       + "failed to remove all the intents " )
        removeIntentResult = main.FALSE
        main.log.info( intentsRemaining )
    else:
        main.log.info( itemName + ": There are no intents remaining, " +
                       "successfully removed all the intents." )
        removeIntentResult = main.TRUE
    return removeIntentResult

def checkFlowsCount( main ):
    """
        Check flows count in each node
    """
    import json

    flowsCount = []
    main.log.info( itemName + ": Checking flows count in each ONOS node" )
    for i in range( main.numCtrls ):
        summaryResult = main.CLIs[ i ].summary()
        if not summaryResult:
            main.log.error( itemName + ": There is something wrong with " +
                            "summary command" )
            return main.FALSE
        else:
            summaryJson = json.loads( summaryResult )
            flowsCount.append( summaryJson.get( 'flows' ) )

    if flowsCount:
        if all( flows==flowsCount[ 0 ] for flows in flowsCount ):
            main.log.info( itemName + ": There are " + str( flowsCount[ 0 ] ) +
                           " flows in all ONOS node" )
        else:
            for i in range( main.numCtrls ):
                main.log.debug( itemName + ": ONOS node " + str( i ) + " has " +
                                flowsCount[ i ] + " flows" )
    else:
        main.log.error( "Checking flows count failed, check summary command" )
        return main.FALSE

    return main.TRUE

