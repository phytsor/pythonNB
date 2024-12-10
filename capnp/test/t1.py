#!/usr/bin/env python3

import capnp

interface1 = capnp.load("interface1.capnp")


pps = interface1.Person.new_message()

pps.id = 112
pps.name = "foo"

f = open("example.bin", "w")
pps.write(f)
f.close()



f = open("example.bin")
pps = interface1.Person.read(f)

print(pps.name)
print(interface1.qux)