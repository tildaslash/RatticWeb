$(document).ready(function(){

    $('a#toclipboard').zclip({
        path:'/static/zclip/1.1.1/ZeroClipboard.swf',
        copy:$('span#password').text(),
        afterCopy:function(){
            alert("Copied to clipboard. Remember to remove it when done.");
        }
    });

    $('a#clearclip').zclip({
        path:'/static/zclip/1.1.1/ZeroClipboard.swf',
        copy: '',
        afterCopy:function(){
            alert("Clipboard Cleared.");
        }
    });

});

function credsearch() {
    var searchstr = document.forms["search"]["box"].value
    window.location = "/cred/list-by-search/" + searchstr + "/";
    return false;
}

function showpass(){
    $('span#password').css('display', 'inline')
    $('a#showpass').css('display', 'none')
    $('a#hidepass').css('display', 'inline-block')
}

function hidepass(){
    $('span#password').css('display', 'none')
    $('a#showpass').css('display', 'inline-block')
    $('a#hidepass').css('display', 'none')
}

