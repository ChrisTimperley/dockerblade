#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import xmlrpc.server


def setup_server(server: xmlrpc.server.SimpleXMLRPCServer) -> None:
    server.register_function(os.path.exists, "exists")
    server.register_function(os.mkdir, "mkdir")


def main() -> None:
    with xmlrpc.server.SimpleXMLRPCServer(
        ("localhost", 26591),
    ) as server:
        setup_server(server)
        server.serve_forever()


if __name__ == "__main__":
    main()
