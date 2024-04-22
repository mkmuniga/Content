#!/usr/bin/env python3.6.3

class expected_interfaces:
    def __init__(self):
        self.reset()

    def reset(self):
        self.next_bubble = None
        self.cpipe_req = None
        self.idi_u2c_req = None
        self.idi_u2c_rsp = None
        self.idi_u2c_data = None
        self.idi_c2u_data = None
        self.idi_c2u_rsp = None
        self.uxi_u2c_req = None
        self.uxi_u2c_rsp = None
        self.uxi_u2c_data = None
        self.uxi_c2u_req = None
        self.uxi_c2u_data = None
        self.uxi_c2u_rsp = None
        self.direct2core_indication = None
