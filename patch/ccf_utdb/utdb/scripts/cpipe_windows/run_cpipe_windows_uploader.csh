`cth_query -tool jem params jem_path -resolve`/jem_py_rt/jem_py_replay.py --trace_index_file jem/tlm_map.txt --reader_lib_name $WORKAREA/output/ccf_4c/jem/model/tlmgen_ccf_typ_4c/libtlmgen_ccf_typ_4c_py.so --replay_env ufi_uploader.Uploader -- -s "" -ld "$PWD/uxi_ufi.logdb" -txt "$PWD/ufi_uxi.log"
