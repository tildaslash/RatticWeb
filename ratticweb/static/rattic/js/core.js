function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie != '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = jQuery.trim(cookies[i]);
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) == (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

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

function copycheckbox(allname, name){
    var checkval = $('input[name="' + allname + '"]').is(':checked');
    $('input[name="' + name + '"]').prop('checked', checkval);
}

function createGroup(name, successcallback, failurecallback) {
    var data = JSON.stringify({
        'name': name
    });

    return $.ajax({
        url: '/api/v1/group/',
        type: 'POST',
        contentType: 'application/json',
        beforeSend: function(jqXHR, settings) {
           jqXHR.setRequestHeader('X-CSRFToken', getCookie('csrftoken'));
        },
        data: data,
        dataType: 'json',
        processData: false,
        success: successcallback,
        error: failurecallback,
    })
}

function groupCreated(group) {
    $("select#id_group").append('<option value="' + group['id'] + '">' + group['name'] + '</option>');
    $("select#id_group").val(group['id']);
}

function createGroupModal() {
    ajax = createGroup(
        $("input#groupname").val(),
        function(){
            // This doesn't get called
            $('#addGroup').modal('hide');
            if (ajax.status == 201) groupCreated(JSON.parse(ajax.responseText))
        },
        function(){
            $('#addGroup').modal('hide');
        }
    );

    // Doesnt seem to work
    //$("button#saveGroupButton").button('loading');

    return false;
}

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

    $(".chzn-select").chosen();

    if ((typeof attachstaffbuttons != 'undefined') && attachstaffbuttons) {
        $("select#id_group").after('<a href="#addGroup" role="button" class="btn" data-toggle="modal" data-loading-text="Adding...">Add</a>');

        $('#addGroup').on('show', function () {
            $("input#groupname").val('');
            $("button#saveGroupbutton").button('reset');
        });
    }
});

