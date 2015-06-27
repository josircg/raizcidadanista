tinyMCE.init({
    mode : "textareas",
    theme : "advanced",
    //content_css : "/appmedia/blog/style.css",
    theme_advanced_toolbar_location : "top",
    theme_advanced_toolbar_align : "left",
    theme_advanced_buttons1 : "bold,italic,underline,strikethrough,separator,formatselect,separator,bullist,numlist,outdent,indent,separator,undo,redo,separator,link,unlink,anchor,separator,cleanup,cut,copy,paste",
    theme_advanced_buttons2 : "",
    theme_advanced_buttons3 : "",
    auto_cleanup_word : false,
    plugins : "table,save,advhr,advimage,advlink,emotions,iespell,insertdatetime,preview,searchreplace,print,contextmenu",
    plugin_insertdate_dateFormat : "%m/%d/%Y",
    plugin_insertdate_timeFormat : "%H:%M:%S",
    extended_valid_elements : "a[name|href|target=_blank|title|onclick],img[class|src|border=0|alt|title|hspace|vspace|width|height|align|onmouseover|onmouseout|name],hr[class|width|size|noshade],font[],span[class|align]",
    valid_styles : { '*' : 'color,font-size,font-weight,font-style,text-decoration' },
    height: 400,
    // fix empty alt attributes
    verify_html : false,
    entity_encoding: 'utf-8',
    // URL
    remove_script_host : false,
    schema: "html5",
    forced_root_block : '',
    elements : 'nourlconvert',
    convert_urls : false,
    plugins : "paste"
});
