TestON: Testing Infastructure by Paxterra and Open Networking Foundation
=======================================
TestON is the testing platform that all the ONOS tests are being run on currently.



Visit the [ONOS System Testing Guide](https://wiki.onosproject.org/display/ONOS/System+Testing+Guide) on the ONOS Wiki for details about the repo, and our [TestON Contribution Guide](https://wiki.onosproject.org/display/ONOS/How+to+Contribute+to+System+Test?src=contextnavpagetreemode) for how to contribute.

Quick Setup
-------------

1. Clone OnosSystemTest from ONOS Gerrit:

    ```
    $ git clone https://gerrit.onosproject.org/OnosSystemTest
    ```

2. Run the installation script:

    ```
    $ cd OnosSystemTest/TestON
    $ ./install.sh
    ```

Dependencies
------------
- [ONOS](https://github.com/opennetworkinglab/onos) - The system being tested.

- [Mininet](https://github.com/mininet/mininet) - A Network Emulator. NOTE: Some driver functions rely on a modified version of Mininet. These functions are noted in the Mininet driver file. Here's how to checkout this branch from the Mininet folder:

    ```
    $ git remote add jhall11 https://github.com/jhall11/mininet.git
    $ git fetch jhall11
    $ git checkout -b dynamic_topo remotes/jhall11/dynamic_topo
    $ git pull
    ```

    Note that you may need to run ``sudo make develop`` if your ``mnexec.c`` file changed when switching branches.

- Linc-OE - Some testcases use this to emulate optical devices.

    Requirements:

    1. Erlang R15B, R16B, R17 - if possible please use R17

    ```
    $ sudo apt-get install erlang
    ```

    2. libpcap-dev package if eth interfaces will be used

    ```
    $ sudo apt-get install libpcap-dev
    ```

    Building and Running:

    ```
    $ git clone https://github.com/shivarammysore/LINC-Switch.git linc-oe
    $ cd linc-oe
    $ git checkout tags/oe-0.3
    $ cp rel/files/sys.config.orig rel/files/sys.config
    $ make rel
    ```


Tests
-----------------------------------------------

The tests are all located in ``TestON/tests/``.
Each test has its own folder with the following files:

- ``.py`` file:

    - This defines the cases and sequence of events for the test.

- ``.topo`` file:

    - This defines all the components that TestON creates for that test and includes data such as IP address, login info, and device drivers.

    - The components must be defined in this file to be used in the ``.py`` files.

- ``.params`` file:

    - Defines all the test-specific variables that are used by the test.

    - NOTE: The variable `testcases` defines which testcases are run.

Running TestON
------------

1. TestON must be run from its bin directory:

    ```
    $ cd TestON/bin
    ```

2. To run a test:

    ```
    $ ./cli.py run SAMPstartTemplate_1node
    ```

Code Style
-------------
At Open Networking Foundation, we have adopted the [Mininet Python Style](https://github.com/mininet/mininet/wiki/Mininet-Python-Style) formatting for our drivers and testcases. The one exception is that TestON does not correctly parse multiline comments in testcases when the ending triple double quotes are on the same line as the comment. Therefore, in the testcases, the ending triple double quotes must be on it's own line.



Troubleshooting
-----------------------------------------------

- Double check the topo file for that specific test the nodes must be able to run that specific component (Mininet IP is targetting the machine with Mininet installed).

- Enable passwordless logins between your nodes and the TestON node.

- Visit our [FAQ/Troubleshooting](https://wiki.onosproject.org/display/ONOS/TestON+FAQs) page on the ONOS Wiki.
