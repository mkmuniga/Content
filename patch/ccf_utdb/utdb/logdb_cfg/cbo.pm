sub get_cbo_settings
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

        my $override_header_sets ='#header,CBO,TIME:12,UNIT:9,URI_TID:20,URI_LID:20,URI_PID:20,ADDRESS:12,REQ:16,QID:2,RING:2,MSG:35,RTID:2,MISC:70,EVENT:30';

        return ( \%headers, $header_title_selector, \@header_title_selector_to_headers_set_name, $merge_cells_headers_set_name_given , \@row_regular_expressions, \@merge_cells_row_regular_expressions, $skip_row_prefix_string ,  $skip_row_suffix_string , $override_header_sets,$column_separator, $skip_row_regex_string);
}

add_user_setting_entry('[^cbo_*$]', \&get_cbo_settings);

