import asyncio
import math
import moteus
import moteus_pi3hat
import time

time.sleep(1)


async def main():
    transport = moteus_pi3hat.Pi3HatRouter(servo_bus_map={1: [13, 23, 24],
                                                          2: [14, 18, 17],
                                                          3: [16, 22, 21],
                                                          4: [15, 19, 20]})
    c13 = moteus.Controller(id=13, transport=transport)
    c14 = moteus.Controller(id=14, transport=transport)
    c15 = moteus.Controller(id=15, transport=transport)
    c16 = moteus.Controller(id=16, transport=transport)
    c17 = moteus.Controller(id=17, transport=transport)
    c18 = moteus.Controller(id=18, transport=transport)
    c19 = moteus.Controller(id=19, transport=transport)
    c20 = moteus.Controller(id=20, transport=transport)
    c21 = moteus.Controller(id=21, transport=transport)
    c22 = moteus.Controller(id=22, transport=transport)
    c23 = moteus.Controller(id=23, transport=transport)
    c24 = moteus.Controller(id=24, transport=transport)

    await c13.set_stop()
    await c14.set_stop()
    await c15.set_stop()
    await c16.set_stop()
    await c17.set_stop()
    await c18.set_stop()
    await c19.set_stop()
    await c20.set_stop()
    await c21.set_stop()
    await c22.set_stop()
    await c23.set_stop()
    await c24.set_stop()

    maxT = 0.1

    while True:
        await transport.cycle([
            c13.make_position(position=0.3499, maximum_torque=maxT, query=True),
            c23.make_position(position=0.15617 - 1, maximum_torque=maxT, query=True),
            c24.make_position(position=0.1710, maximum_torque=maxT, query=True),

            c14.make_position(position=0.74639, maximum_torque=maxT, query=True),
            c17.make_position(position=0.32684, maximum_torque=maxT, query=True),
            c18.make_position(position=-0.73236 + 1, maximum_torque=maxT, query=True),

            c16.make_position(position=-0.38513, maximum_torque=maxT, query=True),
            c21.make_position(position=0.50958, maximum_torque=maxT, query=True),
            c22.make_position(position=0.328186, maximum_torque=maxT, query=True),

            c15.make_position(position=-0.920715, maximum_torque=maxT, query=True),
            c19.make_position(position=0.6815185 - 1, maximum_torque=maxT, query=True),
            c20.make_position(position=1.155334 - 1, maximum_torque=maxT, query=True),
        ])
        if maxT < 0.4:
            maxT = maxT + 0.05
        await asyncio.sleep(0.05)


asyncio.run(main())
