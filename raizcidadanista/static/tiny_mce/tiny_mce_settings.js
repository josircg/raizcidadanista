function CustomFileBrowser(field_name, url, type, win) {

    var cmsURL = "/admin/filebrowser/browse/?pop=2";
    cmsURL = cmsURL + "&type=" + type;

    tinyMCE.activeEditor.windowManager.open({
        file: cmsURL,
        width: 820,  // Your dimensions may differ - toy around with them!
        height: 500,
        resizable: "yes",
        scrollbars: "yes",
        inline: "no",  // This parameter only has an effect if you use the inlinepopups plugin!
        close_previous: "no"
    }, {
        window: win,
        input: field_name,
        editor_id: tinyMCE.selectedInstance.editorId
    });
    return false;
}

tinyMCE.init({
    mode : "textareas",
    theme : "advanced",
    plugins : "table,save,advhr,advimage,advlink,emotions,iespell,insertdatetime,preview,searchreplace,print,contextmenu,fullscreen,media,paste",

    theme_advanced_buttons1 : "bold,italic,underline,strikethrough,|,justifyleft,justifycenter,justifyright,justifyfull,|,fontsizeselect,|,bullist,numlist,outdent,indent,|,undo,redo,|,link,unlink,anchor,|,cleanup,cut,copy,paste,|,image,media,|,code",
    theme_advanced_buttons2 : "",
    theme_advanced_buttons3 : "",
    theme_advanced_buttons4 : "",
    theme_advanced_toolbar_location : "top",
    theme_advanced_toolbar_align : "left",
    theme_advanced_statusbar_location : "bottom",
    theme_advanced_resizing : true,
    auto_cleanup_word : false,
    
    plugin_insertdate_dateFormat : "%m/%d/%Y",
    plugin_insertdate_timeFormat : "%H:%M:%S",
    extended_valid_elements : "a[name|href|target=_blank|title|onclick],img[class|src|border=0|alt|title|hspace|vspace|align|onmouseover|onmouseout|name],hr[class|width|size|noshade],font[]",
    file_browser_callback: "CustomFileBrowser",
    // fix empty alt attributes
    verify_html : false,
    entity_encoding: 'utf-8',
    // URL
    remove_script_host : false,
    schema: "html5",
    forced_root_block : '',
    elements : 'nourlconvert',
    convert_urls : false,
    height:400,
});