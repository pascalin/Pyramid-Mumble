import sys, Ice
import Murmur

with Ice.initialize(sys.argv) as communicator:
    base = communicator.stringToProxy("Meta:tcp -h 127.0.0.1 -p 6502")
    meta = Murmur.MetaPrx.checkedCast(base)
    if not meta:
        raise RuntimeError("Invalid proxy")

    servers = meta.getAllServers()

    if len(servers) == 0:
        print("No servers found")

    for currentServer in servers:
        # registered_users = currentServer.
        if currentServer.isRunning():
            print("Found server (id=%d):\tOnline since %d seconds" % (currentServer.id(), currentServer.getUptime()))
            online = currentServer.getUsers()
            print("There are currently %d online users." % len(online))
            for k,v in online.items():
                    print("\t", k, v.name)
        else:
            print("Found server (id=%d):\tOffline" % currentServer.id())
