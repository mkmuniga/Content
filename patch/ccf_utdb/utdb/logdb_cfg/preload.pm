sub get_preload_settings
{
     my %headers = (
    
        );
        my $override_header_sets ='#header,PRELOAD,TIME:12,UNIT:8,ADDRESS:12,SET:3,WAY:2,MAP:3,STATE:1,CV_BITS:8,PRF_VUL:3,DATA:258,POISON:6,ECC:6,TAG:12,LRU:3,DATA_ER:7,TAG_ER:6,STMAP_ER:8,CV_ER:6'; 

        return ( \%headers, $header_title_selector, \@header_title_selector_to_headers_set_name, $merge_cells_headers_set_name_given , \@row_regular_expressions, \@merge_cells_row_regular_expressions, $skip_row_prefix_string ,  $skip_row_suffix_string , $override_header_sets,$column_separator, $skip_row_regex_string);
}

add_user_setting_entry('^ccf_preload_trk.log*$', \&get_preload_settings);

