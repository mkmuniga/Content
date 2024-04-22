sub get_idi_settings
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
                'LPID' => {
                        'type' => 'BIGINT',
                        'formatting' => '%0X',
                        'null-value' => '-',
                },
                'CHUNK' => {
                        'type' => 'BIGINT',
                        'formatting' => '%0X',
                        'null-value' => '-',
                },
       );

        my $override_header_sets ='#header,idi,TIME:15,UNIT:10,URI_TID:20,URI_LID:20,URI_PID:20,ADDRESS:12,OPCODE:18,TYPE:8,HASH:4,CQID:4,UQID:4,LPID:2,SRC_TGT:5,PARITY:4,PAR_ERR:4,DATA_ER:4,POISON:4,TRACE:3,ATTR:49,CHUNK:4,DATA:128,EVENT:30';
	                          

        return ( \%headers, $header_title_selector, \@header_title_selector_to_headers_set_name, $merge_cells_headers_set_name_given , \@row_regular_expressions, \@merge_cells_row_regular_expressions, $skip_row_prefix_string ,  $skip_row_suffix_string , $override_header_sets,$column_separator, $skip_row_regex_string);
}

add_user_setting_entry('^idi.log*$', \&get_idi_settings);

