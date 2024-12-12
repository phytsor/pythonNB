#!/usr/bin/env python3

import capnp  # noqa: F401

# interface1 = capnp.load("interface1.capnp")
import interface1_capnp as interface1  # type:ignore

pps = interface1.Person.new_message()

pps.id = 112
pps.name = "foo"
attrs = pps.init("attrs", 2)
attrs[0].name = "c"
attrs[0].number = "t2"

pps.hobby.h2 = 123
pps.hobby.h3 = "124"

attrs[1].name = "b"
attrs[1].number = "t3"

#pps.f1 = 938
pps.testgroup.f2 = "sf"

f = open("example.bin", "w")
pps.write(f)
f.close()


f = open("example.bin")
pps = interface1.Person.read(f)

which = pps.hobby.which()
print(which)
#print(pps.hobby.h2)

print(pps.name)
print(pps.testgroup.f2)
print(pps.attrs[1].number)
