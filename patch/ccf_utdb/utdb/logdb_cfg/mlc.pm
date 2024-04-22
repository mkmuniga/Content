sub get_mlc_settings
{
     my %headers = (
    
        );

        my $override_header_sets ='#header,,TIME:15,UNIT:10,ADDRESS:12,C.ST:2,SQST:2,DATA:135';


        return ( \%headers, $header_title_selector, \@header_title_selector_to_headers_set_name, $merge_cells_headers_set_name_given , \@row_regular_expressions, \@merge_cells_row_regular_expressions, $skip_row_prefix_string ,  $skip_row_suffix_string , $override_header_sets,$column_separator, $skip_row_regex_string);
}

add_user_setting_entry('^mlc_trk.log*$', \&get_mlc_settings);

