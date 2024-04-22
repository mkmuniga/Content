sub get_cpipe_windows_settings
{
        my %headers = (
                'TIME' => {
                        'type' => 'BIGINT',
                },

                'ADDRESS' => {
                        'type' => 'BIGINT UNSIGNED',
                        'formatting' => '%015lX',
                        'null-value' => '-',
                },

        );

        my $override_header_sets ='#header,CPIPE_WINDOWS,TIME:12,UNIT:9,URI_TID:20,URI_LID:20,URI_PID:20,REQ:20,ADDRESS:15,TORID:5,TOR_OCCUP:10,MonHit:6,MISC:70,HALF:4,EVENT:70';

        return ( \%headers, $header_title_selector, \@header_title_selector_to_headers_set_name, $merge_cells_headers_set_name_given , \@row_regular_expressions, \@merge_cells_row_regular_expressions, $skip_row_prefix_string ,  $skip_row_suffix_string , $override_header_sets,$column_separator, $skip_row_regex_string);
}

add_user_setting_entry('[^cpipe_windows_*$]', \&get_cpipe_windows_settings);

