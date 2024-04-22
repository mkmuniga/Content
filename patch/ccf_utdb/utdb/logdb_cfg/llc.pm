sub get_llc_settings
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
        my $override_header_sets ='#header,LLC,TIME:12,LLC_SLICE:5,URI_TID:20,URI_LID:20,URI_PID:20,REJ:3,ADDRESS:12,LLC_UOP:8,ARBCMD:8,HIT_MISS:4,TAG_ECC:13,SET:4,WAY:2,MAP:3,HALF:1,WAY_IN:4,STATE:5,NEW_STATE:5,NEW_MAP:3,STATE_WRWAY:8,STATE_INWAY:8,CV_RD:8,CV_WR:8,LRU_RD:15,LRU_WR:15,DATA:135,POISON:6,ECC:6,DBP_LLCHIT:4,EVENT:30,LINESTATES:16,REQCV:1';

        return ( \%headers, $header_title_selector, \@header_title_selector_to_headers_set_name, $merge_cells_headers_set_name_given , \@row_regular_expressions, \@merge_cells_row_regular_expressions, $skip_row_prefix_string ,  $skip_row_suffix_string , $override_header_sets,$column_separator, $skip_row_regex_string);
}

add_user_setting_entry('[^llc_*$]', \&get_llc_settings);

