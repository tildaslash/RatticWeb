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
    if ( typeof showpass.password == 'undefined' ) {
        getCred(credId, function(data){
            showpass.password = data['password'];
            $('span#password').html(showpass.password);
            showpass()
        }, function(){});
    } else {
        $('span#password').css('text-shadow', '0 0 0px #000000')
        $('a#showpass').css('display', 'none')
        $('a#hidepass').css('display', 'inline-block')
    }
}

function hidepass(){
    $('span#password').css('text-shadow', '0 0 10px #000000')
    $('a#showpass').css('display', 'inline-block')
    $('a#hidepass').css('display', 'none')
}

function togglepassinput(){
    input = $('input#id_password');
    button = $('button#passtoggle');
    if (input.attr('type') == 'password') {
        input.attr('type', 'text');
        button.html('<i class="icon-eye-close"></i>');
    } else {
        input.attr('type', 'password');
        button.html('<i class="icon-eye-open"></i>');
    }
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

function getCred(id, successcallback, failurecallback) {
    if ( typeof getCred.cred == 'undefined' ) {
        getCred.cred = [];
    }
    if ( typeof getCred.cred[id] == 'undefined' ) {
        $.ajax({
            url: '/api/v1/cred/' + id + '/',
            type: 'GET',
            contentType: 'application/json',
            beforeSend: function(jqXHR, settings) {
               jqXHR.setRequestHeader('X-CSRFToken', getCookie('csrftoken'));
            },
            success: function(data){
               getCred.cred[id] = data;
               successcallback(data);
            },
            error: failurecallback,
        })
    } else {
        successcallback(getCred.cred[id])
    }
}

function getCredWait(id) {
    if ( typeof getCred.cred == 'undefined' ) {
        getCred.cred = [];
    }
    if ( typeof getCred.cred[id] == 'undefined' ) {
        getCred.cred[id] = $.parseJSON($.ajax({
            url: '/api/v1/cred/' + id + '/',
            type: 'GET',
            contentType: 'application/json',
            beforeSend: function(jqXHR, settings) {
               jqXHR.setRequestHeader('X-CSRFToken', getCookie('csrftoken'));
            },
            async: false,
        }).responseText);
        return getCred.cred[id];
    } else {
        return getCred.cred[id]
    }
}

function groupCreated(group) {
    $("select#id_group").append('<option value="' + group['id'] + '">' + group['name'] + '</option>');
    $("select#id_group").val(group['id']);
}

function createGroupModal() {
    ajax = createGroup(
        $("input#groupname").val(),
        function(){
            $('#addGroup').modal('hide');
            if (ajax.status == 201) groupCreated(JSON.parse(ajax.responseText))
        },
        function(){
            $('#addGroup').modal('hide');
        }
    );

    return false;
}

$(document).ready(function(){

    $(".chzn-select").chosen();

    if ((typeof attachstaffbuttons != 'undefined') && attachstaffbuttons) {
        $("select#id_group").after('<a href="#addGroup" role="button" class="btn" data-toggle="modal" data-loading-text="Adding...">Add</a>');

        $('#addGroup').on('show', function () {
            $("input#groupname").val('');
            $("button#saveGroupbutton").button('reset');
        });
    }

    if ($("copyclipboard").length = 1){
        var clip = new ZeroClipboard($("#copyclipboard"));

        clip.on( 'dataRequested', function ( client, args ) {
            clip.setText(getCredWait(credId)['password']);
        } );

        $('#password').on('mouseover', function(){
            getCred(credId, function(data){
                clip.setText(data['password']);
                $('button#copyclipboard').css({visibility: "visible"})
                $('span#password').html(data['password']);
            }, function(){})
        });

        $('#passtd').on('mouseleave', function(){
            $('button#copyclipboard').css({visibility: 'hidden'})
        });

        clip.on('mouseover', function(){
            $('button#copyclipboard').css({visibility: "visible"})
        })
    }
});

