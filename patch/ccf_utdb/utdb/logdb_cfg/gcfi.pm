
sub get_gCFI_settings
{
        my %headers = (
                'TIME' => {
                        'type' => 'BIGINT',
                },
       );

        my $override_header_sets ='#header,gCFI,TIME:15,UNIT:9,Santa_ID:9,URI_TID:20,URI_LID:20,URI_PID:20,PROTOCOL_ID:12,EOP:9,OPCODE:18,RTID:9,CoreID:9,CboID:9,TORID:9,RspID:9,TC:9,CREDIT:9';

        return ( \%headers, $header_title_selector, \@header_title_selector_to_headers_set_name, $merge_cells_headers_set_name_given , \@row_regular_expressions, \@merge_cells_row_regular_expressions, $skip_row_prefix_string ,  $skip_row_suffix_string , $override_header_sets,$column_separator, $skip_row_regex_string);
}

add_user_setting_entry('^ccf_gcfi_trk*$', \&get_gCFI_settings);

