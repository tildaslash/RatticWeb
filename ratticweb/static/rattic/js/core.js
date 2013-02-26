function credsearch() {
    var searchstr = document.forms["search"]["box"].value
    window.location = "/cred/list-by-search/" + searchstr + "/";
    return false;
}

$(document).ready(function(){

    $('a#toclipboard').zclip({
        path:'/static/zclip/1.1.1/ZeroClipboard.swf',
        copy:$('span#password').text()
    });

});
