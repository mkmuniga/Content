sub get_cxm_settings
{
        my %headers = (
                'TIME' => {
                        'type' => 'BIGINT',
                },

                'ADDRESS' => {
                        'type' => 'BIGINT UNSIGNED',
                        'formatting' => '%012lX',
                        'null-value' => '-',
                },

        );

        my $override_header_sets ='#header,cxm_vc,TIME:12,URI_TID_HDR:17,URI_PID_HDR:17,URI_LID_HDR:17,INTERFACE:16,TXN_TYPE:10,OPCODE:12,VC_ID:6,TAG:10,RSP_ID:16,DST_ID:16,ADDRESS:15,SYS_ADDRESS:20,ADDRESS_PARITY:10,TC:5,LBINFO:8,USER_BITS:8,DATA:160,WBE:20,WBE_DATA:160,DATA_PARITY:10,SECURITY_ATTRIBUTE:10,NO_INTERLEAVE:10,META_FIELD:10,META_VALUE:10,SNP_TYPE:10,IDBE:10,DATA_POISON:10,HEADER_PARITY:10,EOP:10,DATA_OFFSET:10,LENGTH:10,DATA_ERROR_TYPE:10';

        return ( \%headers, $header_title_selector, \@header_title_selector_to_headers_set_name, $merge_cells_headers_set_name_given , \@row_regular_expressions, \@merge_cells_row_regular_expressions, $skip_row_prefix_string ,  $skip_row_suffix_string , $override_header_sets,$column_separator, $skip_row_regex_string);
}

add_user_setting_entry('^CCF_CXM_VC_CCF_CFI_VC_SANTA*txn_tracker_cxm_txn_tracker.log.gz*$', \&get_cxm_settings);

