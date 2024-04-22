sub get_dump_settings
{
     my %headers = (
    
        );

        my $override_header_sets ='#header,CCF_MEM_DUMP,TIME:12,UNIT:7,HALF:4,ADDRESS:12,TAG:12,SET:3,WAY:2,MAP:3,STATE:5,CV_BITS:8,DATA:129,TAG_ER:6';



        return ( \%headers, $header_title_selector, \@header_title_selector_to_headers_set_name, $merge_cells_headers_set_name_given , \@row_regular_expressions, \@merge_cells_row_regular_expressions, $skip_row_prefix_string ,  $skip_row_suffix_string , $override_header_sets,$column_separator, $skip_row_regex_string);
}

add_user_setting_entry('^ccf_mem_dump.log*$', \&get_dump_settings);

