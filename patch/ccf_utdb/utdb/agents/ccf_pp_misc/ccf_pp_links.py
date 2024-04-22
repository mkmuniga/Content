#!/usr/bin/env python3.6.3


import os

replay_path = os.environ["TEST_WORK_AREA"] + "/tlm_post/ccf_replay_base_env"
tlm_path = os.environ["TEST_WORK_AREA"] + "/tlm_post"

for file in os.listdir(replay_path):
    if ("llc_" in file or "cbo_" in file) and "trk.log" in file and not "register" in file:
        relative_path = os.path.relpath(replay_path + "/" + file, tlm_path)
        os.symlink(relative_path, tlm_path + "/" + file)
    if ("register_cbo_trk" in file):
        relative_path = os.path.relpath(replay_path + "/" + file, os.environ["TEST_WORK_AREA"])
        os.system('cp' + " " + relative_path +" " + file )  
